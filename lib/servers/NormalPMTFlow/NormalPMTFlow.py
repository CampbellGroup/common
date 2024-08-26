# Created on Aug 12, 2011
# @author: Michael Ramm

"""
### BEGIN NODE INFO
[info]
name = NormalPMTFlow
version = 1.4
description = 
instancename = NormalPMTFlow

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from labrad.server import LabradServer, setting, Signal
from labrad.types import Value
from twisted.internet.defer import Deferred, returnValue, inlineCallbacks
from twisted.internet.task import LoopingCall
import time

SIGNALID = 331483


class NormalPMTFlow(LabradServer):

    name = "NormalPMTFlow"
    onNewCount = Signal(SIGNALID, "signal: new count", "v")
    onNewSetting = Signal(SIGNALID + 1, "signal: new setting", "(ss)")

    @inlineCallbacks
    def initServer(self):
        self.save_folder = ["", "PMT Counts"]
        self.dataset_name = "PMT Counts"
        self.modes = ["Normal", "Differential"]
        self.collection_period = Value(0.100, "s")
        self.last_differential = {"ON": 0, "OFF": 0}
        self.current_mode = "Normal"
        self.dv = None
        self.pulser = None
        self.collect_time_range = None
        self.open_data_set = None
        self.recording_interrupted = False
        self.request_list = []
        self.listeners = set()
        self.recording = LoopingCall(self._record)
        yield self.connect_data_vault()
        yield self.connect_pulser()
        yield self.setup_listeners()

    @inlineCallbacks
    def setup_listeners(self):
        yield self.client.manager.subscribe_to_named_message(
            "Server Connect", 9898989, True
        )
        yield self.client.manager.subscribe_to_named_message(
            "Server Disconnect", 9898989 + 1, True
        )
        yield self.client.manager.addListener(
            listener=self.follow_server_connect, source=None, ID=9898989
        )
        yield self.client.manager.addListener(
            listener=self.follow_server_disconnect, source=None, ID=9898989 + 1
        )

    @inlineCallbacks
    def follow_server_connect(self, cntx, server_name):
        server_name = server_name[1]
        if server_name == "Pulser":
            yield self.client.refresh()
            yield self.connect_pulser()
        elif server_name == "Data Vault":
            yield self.client.refresh()
            yield self.connect_data_vault()

    @inlineCallbacks
    def follow_server_disconnect(self, cntx, server_name):
        server_name = server_name[1]
        if server_name == "Pulser":
            yield self.disconnect_pulser()
        elif server_name == "Data Vault":
            yield self.disconnect_data_vault()

    @inlineCallbacks
    def connect_data_vault(self):
        try:
            # reconnect to data vault and navigate to the directory
            self.dv = yield self.client.data_vault
            yield self.dv.cd(self.save_folder, True)
            if self.open_data_set is not None:
                self.open_data_set = yield self.start_new_dataset(
                    self.save_folder, self.dataset_name
                )
                self.onNewSetting(("dataset", self.open_data_set))
            print("Connected: Data Vault")
        except AttributeError:
            self.dv = None
            print("Not Connected: Data Vault")

    @inlineCallbacks
    def disconnect_data_vault(self):
        print("Not Connected: Data Vault")
        self.dv = None
        yield None

    @inlineCallbacks
    def connect_pulser(self):
        try:
            self.pulser = yield self.client.pulser
            self.collect_time_range = yield self.pulser.get_collection_time()
            if self.recording_interrupted:
                yield self.do_record_data()
                self.onNewSetting(("state", "on"))
                self.recording_interrupted = False
            print("Connected: Pulser")
        except AttributeError:
            self.pulser = None
            print("Not Connected: Pulser")

    @inlineCallbacks
    def disconnect_pulser(self):
        print("Not Connected: Pulser")
        self.pulser = None
        if self.recording.running:
            yield self.recording.stop()
            self.onNewSetting(("state", "off"))
            self.recording_interrupted = True

    def initContext(self, c):
        """Initialize a new context object."""
        self.listeners.add(c.ID)

    def expireContext(self, c):
        self.listeners.remove(c.ID)

    def get_other_listeners(self, c):
        notified = self.listeners.copy()
        notified.remove(c.ID)
        return notified

    @inlineCallbacks
    def start_new_dataset(self, folder, name):
        yield self.dv.cd(folder, True)
        ds = yield self.dv.new(
            name,
            [("t", "num")],
            [
                ("KiloCounts/sec", "Differential High", "num"),
                ("KiloCounts/sec", "Differential Low", "num"),
                ("KiloCounts/sec", "Differential Signal", "num"),
            ],
        )
        self.startTime = time.time()
        yield self.add_parameters(self.startTime)
        try:
            self.grapher = yield self.client.real_simple_grapher
            self.grapher.plot(ds, "pmt", False)
        except AttributeError:
            self.grapher = None
            print("no grapher")
        returnValue(name)

    @inlineCallbacks
    def add_parameters(self, start):

        yield self.dv.add_parameter("Window", ["PMT Counts"])
        yield self.dv.add_parameter("plotLive", True)
        yield self.dv.add_parameter("startTime", start)

    @setting(0, "Set Save Folder", folder="*s", returns="")
    def set_save_folder(self, c, folder):
        yield self.dv.cd(folder, True)
        self.save_folder = folder

    @setting(1, "Start New Dataset", set_name="s", returns="s")
    def set_new_data_set(self, c, set_name=None):
        """Starts new dataset, if name not provided, it will be the same"""
        if set_name is not None:
            self.dataset_name = set_name
        self.open_data_set = yield self.start_new_dataset(
            self.save_folder, self.dataset_name
        )
        other_listeners = self.get_other_listeners(c)
        self.onNewSetting(("dataset", self.open_data_set), other_listeners)
        returnValue(self.open_data_set)

    @setting(2, "Set Mode", mode="s", returns="")
    def set_mode(self, c, mode):
        """
        Start recording Time Resolved Counts into Data Vault
        """
        if mode not in self.modes:
            raise Exception("Incorrect Mode")
        if not self.recording.running:
            self.current_mode = mode
            yield self.pulser.set_mode(mode)
        else:
            yield self.do_stop_recording()
            self.current_mode = mode
            yield self.do_record_data()
        other_listeners = self.get_other_listeners(c)
        self.onNewSetting(("mode", mode), other_listeners)

    @setting(3, "get Current Mode", returns="s")
    def get_current_mode(self, c):
        """
        Returns the currently running mode
        """
        return self.current_mode

    @setting(4, "Record Data", returns="")
    def record_data(self, c):
        """
        Starts recording data of the current PMT mode into datavault
        """
        setname = yield self.do_record_data()
        other_listeners = self.get_other_listeners(c)
        if setname is not None:
            setname = setname[1]
            self.onNewSetting(("dataset", setname), other_listeners)
        self.onNewSetting(("state", "on"), other_listeners)

    @inlineCallbacks
    def do_record_data(self):
        # begins the process of data record
        # sets the collection time and mode, programs the pulser if necessary and opens the dataset if necessasry
        # then starts the recording loop
        new_set = None
        self.keepRunning = True
        yield self.pulser.set_collection_time(self.collection_period, self.current_mode)
        yield self.pulser.set_mode(self.current_mode)
        if self.current_mode == "Differential":
            yield self._program_pulser_diff()
        if self.open_data_set is None:
            self.open_data_set = yield self.start_new_dataset(
                self.save_folder, self.dataset_name
            )
        self.recording.start(self.collection_period["s"] / 2.0)
        returnValue(new_set)

    @setting(5, returns="")
    def stop_recording(self, c):
        """
        Stop recording counts into Data Vault
        """
        yield self.do_stop_recording()
        other_listeners = self.get_other_listeners(c)
        self.onNewSetting(("state", "off"), other_listeners)

    @inlineCallbacks
    def do_stop_recording(self):
        yield self.recording.stop()
        if self.current_mode == "Differential":
            yield self._stop_pulser_diff()

    @setting(6, returns="b")
    def is_running(self, c):
        """Returns whether currently recording"""
        return self.recording.running

    @setting(7, returns="s")
    def current_dataset(self, c):
        if self.open_data_set is None:
            return ""
        return self.open_data_set

    @setting(8, "Set Time Length", timelength="v[s]")
    def set_time_length(self, c, timelength):
        """Sets the time length for the current mode"""
        mode = self.current_mode
        if (
            not self.collect_time_range[0]
            <= timelength["s"]
            <= self.collect_time_range[1]
        ):
            raise Exception("Incorrect Recording Time")
        self.collection_period = timelength
        initrunning = (
            self.recording.running
        )  # if recording when the call is made, need to stop and restart
        if initrunning:
            yield self.recording.stop()
        yield self.pulser.set_collection_time(timelength, mode)
        if initrunning:
            if mode == "Differential":
                yield self._stop_pulser_diff()
                yield self._program_pulser_diff()
            self.recording.start(timelength["s"] / 2.0)
        other_listeners = self.get_other_listeners(c)
        self.onNewSetting(("timelength", str(timelength["s"])), other_listeners)

    @setting(
        9, "Get Next Counts", kind="s", number="w", average="b", returns=["*v", "v"]
    )
    def get_next_counts(self, c, kind, number, average=False):
        """
        Acquires next number of counts, where type can be 'ON' or 'OFF' or 'DIFF'
        Average is optionally True if the counts should be averaged

        Note in differential mode, Diff counts get updates every time, but ON and OFF
        get updated every 2 times.
        """
        if kind not in ["ON", "OFF", "DIFF"]:
            raise Exception("Incorrect type")
        if kind in ["OFF", "DIFF"] and self.current_mode == "Normal":
            raise Exception("in the wrong mode to process this request")
        if not 0 < number < 1000:
            raise Exception("Incorrect Number")
        if not self.recording.running:
            raise Exception("Not currently recording")
        d = Deferred()
        self.request_list.append(self.ReadingRequest(d, kind, number))
        data = yield d
        if average:
            data = sum(data) / len(data)
        returnValue(data)

    @setting(10, "Get Time Length", returns="v")
    def get_mode(self, c):
        """
        Returns the current timelength of in the current mode
        """
        return self.collection_period

    @setting(11, "Get Time Length Range", returns="(vv)")
    def get_time_length_range(self, c):
        if self.collect_time_range is not None:
            return self.collect_time_range
        else:
            raise Exception("Not available because Pulser Server is not available")

    @inlineCallbacks
    def _program_pulser_diff(self):
        """
        Programs the Pulse for differential mode with the following pulse sequence
        DiffCountTrigger |██▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁██▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
        866DP            |████████████████████████████████████▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
        Internal866      |████████████████████████████████████▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
        """
        yield self.pulser.new_sequence()
        yield self.pulser.add_ttl_pulse(
            "DiffCountTrigger", Value(0.0, "us"), Value(10.0, "us")
        )
        yield self.pulser.add_ttl_pulse(
            "DiffCountTrigger", self.collection_period, Value(10.0, "us")
        )
        yield self.pulser.add_ttl_pulse(
            "866DP", Value(0.0, "us"), self.collection_period
        )
        yield self.pulser.add_ttl_pulse(
            "Internal866", Value(0.0, "us"), self.collection_period
        )
        yield self.pulser.extend_sequence_length(2 * self.collection_period)
        yield self.pulser.program_sequence()
        yield self.pulser.start_infinite()

    @inlineCallbacks
    def _stop_pulser_diff(self):
        yield self.pulser.complete_infinite_iteration()
        yield self.pulser.wait_sequence_done()
        yield self.pulser.stop_sequence()

    class ReadingRequest:
        def __init__(self, d, kind, count):
            self.d = d
            self.count = count
            self.kind = kind
            self.data = []

        def is_fulfilled(self):
            return len(self.data) == self.count

    def process_requests(self, data):
        if not len(self.request_list):
            return
        for dataPoint in data:
            for item, req in enumerate(self.request_list):
                if dataPoint[1] != 0 and req.kind == "ON":
                    req.data.append(dataPoint[1])
                if dataPoint[2] != 0 and req.kind == "OFF":
                    req.data.append(dataPoint[2])
                if dataPoint[3] != 0 and req.kind == "DIFF":
                    req.data.append(dataPoint[3])
                if req.is_fulfilled():
                    req.d.callback(req.data)
                    del self.request_list[item]

    @inlineCallbacks
    def _record(self):
        try:
            rawdata = yield self.pulser.get_pmt_counts()
        except Exception as e:
            print("Not Able to Get PMT Counts: \n", e)
            rawdata = []
        if len(rawdata) != 0:
            if self.current_mode == "Normal":
                # converting to format [time, normal count, 0 , 0]
                to_data_vault = [
                    [elem[2] - self.startTime, elem[0], 0, 0] for elem in rawdata
                ]
            elif self.current_mode == "Differential":
                to_data_vault = self.convert_differential(rawdata)
            else:
                raise Exception("Mode is not correctly set")
            self.process_requests(
                to_data_vault
            )  # if we have any requests, process them
            self.process_signals(to_data_vault)
            try:
                yield self.dv.add(to_data_vault)
            except Exception as e:
                print("Not able to save to DataVault: \n", e)

    def process_signals(self, data):
        last_pt = data[-1]
        normal_count = last_pt[1]
        self.onNewCount(normal_count)

    def convert_differential(self, rawdata):
        total_data = []
        for dataPoint in rawdata:
            t = str(dataPoint[1])
            self.last_differential[t] = float(dataPoint[0])
            diff = self.last_differential["ON"] - self.last_differential["OFF"]
            total_data.append(
                [
                    dataPoint[2] - self.startTime,
                    self.last_differential["ON"],
                    self.last_differential["OFF"],
                    diff,
                ]
            )
        return total_data


if __name__ == "__main__":
    from labrad import util

    util.runServer(NormalPMTFlow())
