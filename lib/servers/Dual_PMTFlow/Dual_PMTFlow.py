# Created on Aug 12, 2011
# @author: Michael Ramm

"""
### BEGIN NODE INFO
[info]
name = Dual PMTFlow
version = 1.5
description =
instancename = Dual PMTFlow

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
from labrad.server import LabradServer, setting, Signal
from labrad import types as T
from twisted.internet.defer import Deferred, returnValue, inlineCallbacks
from twisted.internet.task import LoopingCall
from PMT import PMT
import time

SIGNALID = 331483


class Dual_PMTFlow(LabradServer):

    debug = False
    name = "Dual PMTFlow"
    onNewCount = Signal(SIGNALID, "signal: new count", "v")
    onNewCount2 = Signal(SIGNALID + 10, "signal: new count 2", "v")
    onNewSetting = Signal(SIGNALID + 1, "signal: new setting", "(ss)")
    onNewState = Signal(SIGNALID + 2, "signal: new state", "(ss)")
    # onNewState2 = Signal(SIGNALID+12, 'signal: new state 2', '(ss)')

    @inlineCallbacks
    def initServer(self):
        self.saveFolder = ["", "PMT Counts"]
        self.dataSetName = "PMT Counts"
        self.modes = ["Normal", "Differential"]
        self.collection_period = T.Value(0.100, "s")
        self.lastDifferential = {"ON": 0, "OFF": 0}
        self.currentMode = "Normal"
        self.dv = None
        self.pulser = None
        self.collectTimeRange = None
        self.openDataSet = None
        self.recordingInterrupted = False
        self.requestList = []
        self.listeners = set()
        self.recording = LoopingCall(self._record)
        yield self.connect_data_vault()
        yield self.connect_pulser()
        yield self.setupListeners()

    @inlineCallbacks
    def setupListeners(self):
        yield self.client.manager.subscribe_to_named_message(
            "Server Connect", 9898989, True
        )
        yield self.client.manager.subscribe_to_named_message(
            "Server Disconnect", 9898989 + 1, True
        )
        yield self.client.manager.addListener(
            listener=self.followServerConnect, source=None, ID=9898989
        )
        yield self.client.manager.addListener(
            listener=self.followServerDisconnect, source=None, ID=9898989 + 1
        )

    @inlineCallbacks
    def followServerConnect(self, cntx, serverName):
        serverName = serverName[1]
        if serverName == "Pulser":
            yield self.connect_pulser()
        elif serverName == "Data Vault":
            yield self.connect_data_vault()

    @inlineCallbacks
    def followServerDisconnect(self, cntx, serverName):
        serverName = serverName[1]
        if serverName == "Pulser":
            yield self.disconnect_pulser()
        elif serverName == "Data Vault":
            yield self.disconnect_data_vault()

    @inlineCallbacks
    def connect_data_vault(self):
        try:
            # reconnect to data vault and navigate to the directory
            self.dv = yield self.client.data_vault
            yield self.dv.cd(self.saveFolder, True)
            if self.openDataSet is not None:
                self.openDataSet = yield self.makeNewDataSet(
                    self.saveFolder, self.dataSetName
                )
                self.onNewSetting(("dataset", self.openDataSet))
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
            self.collectTimeRange = yield self.pulser.get_collection_time()
            pmt_id_list = yield self.pulser.get_pmt_id_list()
            self.pmt_list = [PMT(pmt_id) for pmt_id in pmt_id_list]
            self.pmt_list[0].enable()
            if self.recordingInterrupted:
                yield self.dorecordData()
                self.onNewState("on")
                self.recordingInterrupted = False
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
            self.onNewState("off")
            self.recordingInterrupted = True

    def initContext(self, c):
        """Initialize a new context object."""
        self.listeners.add(c.ID)

    def expireContext(self, c):
        self.listeners.remove(c.ID)

    def getOtherListeners(self, c):
        notified = self.listeners.copy()
        notified.remove(c.ID)
        return notified

    @inlineCallbacks
    def makeNewDataSet(self, folder, name):

        for pmt in self.pmt_list:
            pmt.context = self.dv.context()
            yield self.dv.cd(folder, True, context=pmt.context)
            newSet = yield self.dv.new(
                name + pmt.suffix,
                [("t", "num")],
                [
                    ("KiloCounts/sec", "866 ON", "num"),
                    ("KiloCounts/sec", "866 OFF", "num"),
                    ("KiloCounts/sec", "Differential Signal", "num"),
                ],
                context=pmt.context,
            )
        self.startTime = time.time()
        yield self.addParameters(self.startTime)
        name = newSet[1][:-2]
        returnValue(name)

    @inlineCallbacks
    def addParameters(self, start):
        for pmt in self.pmt_list:
            yield self.dv.add_parameter("Window", ["PMT Counts"], context=pmt.context)
            yield self.dv.add_parameter("plotLive", True, context=pmt.context)
            yield self.dv.add_parameter("startTime", start, context=pmt.context)

    @setting(0, folder="*s", returns="")
    def set_save_folder(self, c, folder):
        yield self.dv.cd(folder, True)
        self.saveFolder = folder

    @setting(1, setName="s", returns="s")
    def start_new_dataset(self, c, setName=None):
        """Starts new dataset, if name not provided, it will be the same"""
        if setName is not None:
            self.dataSetName = setName
        self.openDataSet = yield self.makeNewDataSet(self.saveFolder, self.dataSetName)
        otherListeners = self.getOtherListeners(c)
        self.onNewSetting(("dataset", self.openDataSet), otherListeners)
        returnValue(self.openDataSet)

    @setting(2, mode="s", returns="")
    def set_mode(self, c, mode):
        """
        Start recording Time Resolved Counts into Data Vault
        """
        if mode not in self.modes:
            raise ValueError("Incorrect Mode")
        if not self.recording.running:
            self.currentMode = mode
            yield self.pulser.set_mode(mode)
        else:
            yield self.dostopRecording()
            self.currentMode = mode
            yield self.dorecordData()
        otherListeners = self.getOtherListeners(c)
        self.onNewSetting(("mode", mode), otherListeners)

    @setting(3, returns="s")
    def getcurrentmode(self, c):
        """
        Returns the currently running mode
        """
        return self.currentMode

    @setting(4, returns="")
    def record_data(self, c):
        """
        Starts recording data of the current PMT mode into datavault
        """
        setname = yield self.dorecordData()
        otherListeners = self.getOtherListeners(c)
        if setname is not None:
            setname = setname[1]
            self.onNewSetting(("dataset", setname), otherListeners)
        self.onNewState("on", otherListeners)

    @inlineCallbacks
    def dorecordData(self):
        """
        Begins the process of data record sets the collection time and mode,
        programs the pulser if necessary and opens the dataset if necessasry
        then starts the recording loop.
        """
        newSet = None
        self.keepRunning = True
        yield self.pulser.set_collection_time(self.collection_period, self.currentMode)
        yield self.pulser.set_mode(self.currentMode)
        if self.currentMode == "Differential":
            yield self._programPulserDiff()
        if self.openDataSet is None:
            self.openDataSet = yield self.makeNewDataSet(
                self.saveFolder, self.dataSetName
            )
        self.recording.start(self.collection_period["s"] / 2.0)
        returnValue(newSet)

    @setting(5, returns="")
    def stopRecording(self, c):
        """
        Stop recording counts into Data Vault
        """
        yield self.dostopRecording()
        otherListeners = self.getOtherListeners(c)
        self.onNewState("off", otherListeners)

    @inlineCallbacks
    def dostopRecording(self):
        yield self.recording.stop()
        if self.currentMode == "Differential":
            yield self._stopPulserDiff()

    @setting(6, returns="b")
    def isRunning(self, c):
        """
        Returns whether or not currently recording
        """
        return self.recording.running

    @setting(7, returns="s")
    def currentDataSet(self, c):
        if self.openDataSet is None:
            return ""
        return self.openDataSet

    @setting(8, timelength="v[s]")
    def set_time_length(self, c, timelength):
        """Sets the time length for the current mode"""
        mode = self.currentMode
        if not self.collectTimeRange[0] <= timelength["s"] <= self.collectTimeRange[1]:
            raise Exception("Incorrect Recording Time")
        self.collection_period = timelength
        initrunning = (
            self.recording.running
        )  # if recording when the call is made, need to stop and restart
        if initrunning:
            yield self.recording.stop()
        yield self.pulser.set_collection_time(timelength["s"], mode)
        if initrunning:
            if mode == "Differential":
                yield self._stopPulserDiff()
                yield self._programPulserDiff()
            self.recording.start(timelength["s"] / 2.0)
        otherListeners = self.getOtherListeners(c)
        self.onNewSetting(("timelength", str(timelength["s"])), otherListeners)

    @setting(9, kind="s", number="w", average="b", returns=["*v", "v"])
    def get_next_counts(self, c, kind, number, average=False):
        """
        Acquires next number of counts, where type can be 'ON' or 'OFF' or 'DIFF'
        Average is optionally True if the counts should be averaged

        Note in differential mode, Diff counts get updates every time, but ON and OFF
        get updated every 2 times.
        """
        if kind not in ["ON", "OFF", "DIFF"]:
            raise Exception("Incorrect type")
        if kind in ["OFF", "DIFF"] and self.currentMode == "Normal":
            raise Exception("in the wrong mode to process this request")
        if not 0 < number < 1000:
            raise Exception("Incorrect Number")
        if not self.recording.running:
            raise Exception("Not currently recording")

        d = Deferred()
        self.requestList.append(self.readingRequest(d, kind, number))
        data = yield d
        if average:
            data = sum(data) / len(data)
        returnValue(data)

    @setting(10, returns="v")
    def get_time_length(self, c):
        """
        Returns the current timelength of in the current mode
        """
        return self.collection_period

    @setting(11, returns="(vv)")
    def get_time_length_range(self, c):
        if self.collectTimeRange is not None:
            return self.collectTimeRange
        else:
            raise Exception("Not available because Pulser Server is not available")

    # TODO: deprecate in favor of pmt_state()
    @setting(12, pmt_id="i", state="b", returns="")
    def set_pmt_state(self, c, pmt_id, state):
        """
        pmt_id: int, which PMT to turn on or off
        state: bool, PMT state
        """
        self.pmt_list[pmt_id - 1].enabled = state

    @setting(13, pmt="i", value="b", returns="?")
    def pmt_state(self, c, pmt, value=None):
        """
        Set the state of pmt with value.  If value=None returns
        the state of pmt.

        pmt_id: int, which PMT to turn on or off
        value: bool, PMT state
        """
        if value is not None:
            self.pmt_list[pmt - 1].enabled = value
        else:
            out_val = yield self.pmt_list[pmt - 1].enabled
            returnValue(out_val)

    @inlineCallbacks
    def _programPulserDiff(self):
        yield self.pulser.new_sequence()
        yield self.pulser.add_ttl_pulse(
            "DiffCountTrigger", T.Value(0.0, "us"), T.Value(10.0, "us")
        )
        yield self.pulser.add_ttl_pulse(
            "DiffCountTrigger", self.collection_period, T.Value(10.0, "us")
        )
        yield self.pulser.add_ttl_pulse(
            "866DP", T.Value(0.0, "us"), self.collection_period
        )
        yield self.pulser.extend_sequence_length(2 * self.collection_period)
        yield self.pulser.program_sequence()
        yield self.pulser.start_infinite()

    @inlineCallbacks
    def _stopPulserDiff(self):
        yield self.pulser.complete_infinite_iteration()
        yield self.pulser.wait_sequence_done()
        yield self.pulser.stop_sequence()

    class readingRequest:

        def __init__(self, d, kind, count):
            """
            d: Deffered()
            kind: str, 'ON', etc.
            count:
            """
            self.d = d
            self.count = count
            self.kind = kind
            self.data = []

        def is_fulfilled(self):
            return len(self.data) == self.count

    def processRequests(self, data):
        """
        This function is continually running after record_data is called.
        """
        #        if self.debug : print "processRequests()"
        if not len(self.requestList):
            return
        for dataPoint in data:
            for item, req in enumerate(self.requestList):
                if dataPoint[1] != 0 and req.kind == "ON":
                    req.data.append(dataPoint[1])
                if dataPoint[2] != 0 and req.kind == "OFF":
                    req.data.append(dataPoint[2])
                if dataPoint[3] != 0 and req.kind == "DIFF":
                    req.data.append(dataPoint[3])
                if req.is_fulfilled():
                    req.d.callback(req.data)
                    del self.requestList[item]

    @inlineCallbacks
    def _record(self):
        """
        Called continuously after running record_data()
        """
        for pmt in self.pmt_list:
            if not pmt.enabled:
                if self.debug:
                    print(pmt.id, "not enabled.")
            #                return
            else:
                try:
                    yield self.getPMTCounts(pmt.id)
                except:
                    print("Not Able to Get PMT Counts")
                    self.rawdata = []
                if len(self.rawdata) != 0:
                    if self.currentMode == "Normal":
                        if self.debug:
                            print("_record() self.rawdata=", self.rawdata)
                        # converting to format [time, normal count, 0 , 0]
                        toDataVault = [
                            [elem[2] - self.startTime, elem[0], 0, 0]
                            for elem in self.rawdata
                        ]
                    elif self.currentMode == "Differential":
                        toDataVault = self.convertDifferential(self.rawdata)
                    self.processRequests(toDataVault)
                    self.processSignals(toDataVault, pmt.id)
                    try:
                        yield self.dv.add(toDataVault, context=pmt.context)
                    except:
                        print("Not Able to Save To Data Vault")

    @inlineCallbacks
    def getPMTCounts(self, pmt_id):
        if pmt_id == 2:
            self.rawdata = yield self.pulser.get_secondary_pmt_counts()
        else:
            self.rawdata = yield self.pulser.get_pmt_counts()

    def processSignals(self, data, pmt_id):
        lastPt = data[-1]
        NormalCount = lastPt[1]
        if pmt_id == 2:
            self.onNewCount2(NormalCount)
        else:
            self.onNewCount(NormalCount)

    def convertDifferential(self, rawdata):
        totalData = []
        for dataPoint in rawdata:
            t = str(dataPoint[1])
            self.lastDifferential[t] = float(dataPoint[0])
            diff = self.lastDifferential["ON"] - self.lastDifferential["OFF"]
            totalData.append(
                [
                    dataPoint[2] - self.startTime,
                    self.lastDifferential["ON"],
                    self.lastDifferential["OFF"],
                    diff,
                ]
            )
        return totalData


if __name__ == "__main__":
    from labrad import util

    util.runServer(Dual_PMTFlow())
