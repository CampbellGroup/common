"""
### BEGIN NODE INFO
[info]
name = ScriptScanner
version = 0.10
description =
instancename = ScriptScanner

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from labrad.server import setting
from labrad.units import WithUnit
from twisted.internet.defer import inlineCallbacks, DeferredList, returnValue

from script_signals_server import ScriptSignalsServer

try:
    import config.scriptscanner_config as sc_config
except ImportError:
    import common.lib.config.scriptscanner_config as sc_config
import scan_methods
from scriptscheduler import ScriptScheduler
import sys
from importlib import reload, import_module
import traceback


class ScriptInfo:
    """
    storage class for information about the launchable script
    """

    def __init__(self, name, cls, parameters):
        """
        self.name: str, the experiment name
        cls: a handle to the experiment class, this can be used to instantiate
            an experiment, e.g. a = cls() will give an instance.
        parameters: list, required experiment parameters
        """
        self.name = name
        self.cls = cls
        self.parameters = parameters


class ScriptScanner(ScriptSignalsServer):
    """
    Attributes
    ----------
    scheduler: scheduler instance.
    scripts: dict, experiment names are keys, values are
        script_class_parameters instances.
    """

    name = "ScriptScanner"

    def initServer(self):

        # Dictionary with experiment.name as keys and
        # script_class_parameters instances are the values.
        self.scripts = {}
        # Instance of a complicated object
        self.scheduler = ScriptScheduler(ScriptSignalsServer)
        self.load_scripts()

    def load_scripts(self):
        """
        loads script information from the configuration file
        """
        config = sc_config.Config
        for import_path, class_name in config.scripts:
            module = None
            try:
                # imports the file
                import_module(import_path)
                # gets the file
                module = sys.modules[import_path]
                # gets the experiment class from the module
                cls = getattr(module, class_name)
            except ImportError as e:
                print("Script Control Error importing: ", str(e))
            except AttributeError as e:
                print(
                    "There is no class {0} in module {1}: {2}".format(
                        class_name, module, e
                    )
                )
            except SyntaxError as e:
                print("Incorrect syntax in file {0}".format(import_path, class_name))
                print(traceback.format_exc())
            except Exception as e:
                print("There was an error in {0} : {1}".format(class_name, e))
            else:
                try:
                    name = cls.name
                    parameters = cls.all_required_parameters()
                except AttributeError:
                    name_not_provided = "Name is not provided for class {0} in"
                    name_not_provided += " module {1}"
                    print(name_not_provided.format(class_name, module))
                else:
                    self.scripts[name] = ScriptInfo(name, cls, parameters)

    @setting(0, "get_available_scripts", returns="*s")
    def get_available_scripts(self, c):
        return list(self.scripts.keys())

    @setting(1, "get_script_parameters", script_name="s", returns="*(ss)")
    def get_script_parameters(self, c, script_name):
        if script_name not in self.scripts.keys():
            raise Exception("Script {} Not Found".format(script_name))
        return self.scripts[script_name].parameters

    @setting(7, "get_script_docstring", script_name="s", returns="s")
    def get_script_docstring(self, c, script_name):
        if script_name == "":
            return ""
        if script_name not in self.scripts.keys():
            print("Script {} Not Found".format(script_name))
        return self.scripts[script_name].cls.__doc__ or ""

    @setting(2, "get_running", returns="*(ws)")
    def get_running(self, c):
        """
        Returns the list of currently running scripts and their IDs.
        """
        return self.scheduler.get_running()

    @setting(3, "get_scheduled", returns="*(wsv[s])")
    def get_scheduled(self, c):
        """
        Returns the list of currently scheduled scans with their IDs and
        duration
        """
        scheduled = self.scheduler.get_scheduled()
        scheduled = [
            (ident, name, WithUnit(dur, "s")) for (ident, name, dur) in scheduled
        ]
        return scheduled

    @setting(4, "get_queue", returns="*(wsw)")
    def get_queue(self, c):
        """
        Returns the current queue of scans in the form ID / Name / order
        """
        return self.scheduler.get_queue()

    @setting(5, "remove_queued_script", script_id="w")
    def remove_queued_script(self, c, script_id):
        self.scheduler.remove_queued_script(script_id)

    @setting(6, "get_progress", script_id="w", returns="sv")
    def get_progress(self, c, script_id):
        """
        Get progress of a currently running experiment
        """
        status = self.scheduler.get_running_status(script_id)
        if status is None:
            try_progress = "Trying to get progress of script with ID {0} but"
            try_progress += "it was not running"
            raise Exception(try_progress.format(script_id))
        return status.get_progress()

    @setting(10, "new_experiment", script_name="s", returns="w")
    def new_experiment(self, c, script_name):
        """
        Queue an experiment for launching.  Returns the scan ID of the queued
        experiment from a scheduler instance.

        Parameter
        ---------
        script: str, experiment to run.

        TODO: change name.  The name itself should actually be something
        like add_new_experiment_to_queue

        Returns
        -------
        scan_id: int
        """
        if script_name not in self.scripts.keys():
            raise Exception("Script {} Not Found".format(script_name))
        # Grabs an instance of ScriptInfo that holds
        # the experiment name, the experiment class, and the list of
        # required parameters for the experiment.
        script = self.scripts[script_name]
        # single_launch is an experiment instance.
        single_launch = scan_methods.single(script.cls)
        scan_id = self.scheduler.add_scan_to_queue(single_launch)
        return scan_id

    @setting(11, "new_script_repeat", script_name="s", repeat="w", save_data="b")
    def new_script_repeat(self, c, script_name, repeat, save_data=True):
        if script_name not in self.scripts.keys():
            raise Exception("Script {} Not Found".format(script_name))
        script = self.scripts[script_name]
        repeat_launch = scan_methods.repeat_reload(script.cls, repeat, save_data)

        scan_id = self.scheduler.add_scan_to_queue(repeat_launch)
        return scan_id

    @setting(
        12,
        "new_script_scan",
        scan_script_name="s",
        measure_script_name="s",
        collection="s",
        parameter_name="s",
        minim="v[]",
        maxim="v[]",
        steps="w",
        units="s",
    )
    def new_scan(
        self,
        c,
        scan_script_name,
        measure_script_name,
        collection,
        parameter_name,
        minim,
        maxim,
        steps,
        units,
    ):
        # need error checking that parameters are valid
        if scan_script_name not in self.scripts.keys():
            raise Exception("Script {} Not Found".format(scan_script_name))
        if measure_script_name not in self.scripts.keys():
            raise Exception("Script {} Not Found".format(measure_script_name))
        scan_script = self.scripts[scan_script_name]
        measure_script = self.scripts[measure_script_name]
        parameter = (collection, parameter_name)
        if scan_script == measure_script:
            scan_launch = scan_methods.scan_experiment_1D(
                scan_script.cls, parameter, minim, maxim, steps, units
            )
        else:
            scan_launch = scan_methods.scan_experiment_1D_measure(
                scan_script.cls,
                measure_script.cls,
                parameter,
                minim,
                maxim,
                steps,
                units,
            )
        scan_id = self.scheduler.add_scan_to_queue(scan_launch)
        return scan_id

    @setting(
        13,
        "new_script_schedule",
        script_name="s",
        duration="v[s]",
        priority="s",
        start_now="b",
        returns="w",
    )
    def new_script_schedule(
        self, c, script_name, duration, priority="Normal", start_now=True
    ):
        """
        Schedule the script to run every specified duration of seconds.
        Priority indicates the priority with which the script is scheduled.
        """
        if script_name not in self.scripts.keys():
            raise Exception("Script {} Not Found".format(script_name))
        if priority not in ["Normal", "First in Queue", "Pause All Others"]:
            raise Exception("Priority not recognized")
        script = self.scripts[script_name]
        single_launch = scan_methods.single(script.cls)
        schedule_id = self.scheduler.new_scheduled_scan(
            single_launch, duration["s"], priority, start_now
        )

        return schedule_id

    @setting(14, "change_scheduled_duration", scheduled_id="w", duration="v[s]")
    def change_scheduled_duration(self, c, scheduled_id, duration):
        """
        Change duration of the scheduled script execution
        """
        self.scheduler.change_period_scheduled_script(scheduled_id, duration["s"])

    @setting(15, "cancel_scheduled_script", scheduled_id="w")
    def cancel_scheduled_script(self, c, scheduled_id):
        """
        Cancel the currently scheduled script
        """
        self.scheduler.cancel_scheduled_script(scheduled_id)

    @setting(20, "pause_script", script_id="w", should_pause="b")
    def pause_script(self, c, script_id, should_pause):
        status = self.scheduler.get_running_status(script_id)
        if status is None:
            try_pause = "Trying to pause script with ID {0} but it was not"
            try_pause += " running"
            raise Exception(try_pause.format(script_id))
        status.set_pausing(should_pause)

    @setting(21, "stop_script", script_id="w")
    def stop_script(self, c, script_id):
        status = self.scheduler.get_running_status(script_id)
        if status is None:
            try_stop = "Trying to stop script with ID {0} but it was not"
            try_stop += " running"
            raise Exception(try_stop.format(script_id))
        status.set_stopping()

    @setting(30, "register_external_launch", name="s", returns="w")
    def register_external_launch(self, c, name):
        """
        Issues a running ID to a script that is launched externally and not
        through this server. The external script can then update its status, be
        paused or stopped.
        """
        external_scan = scan_methods.experiment_info(name)
        ident = self.scheduler.add_external_scan(external_scan)
        return ident

    @setting(31, "script_set_progress", script_id="w", progress="v")
    def script_set_progress(self, c, script_id, progress):
        status = self.scheduler.get_running_status(script_id)
        if status is None:
            try_set = "Trying to set progress of script with ID {0} but it was"
            try_set += " not running"
            raise Exception(try_set.format(script_id))
        status.set_percentage(progress)

    @setting(32, "launch_confirmed", script_id="w")
    def launch_confirmed(self, c, script_id):
        status = self.scheduler.get_running_status(script_id)
        if status is None:
            try_confirm = "Trying to confirm launch of script with ID {0} but "
            try_confirm += "it was not running"
            raise Exception(try_confirm.format(script_id))
        status.launch_confirmed()

    @setting(33, "finish_confirmed", script_id="w")
    def finish_confirmed(self, c, script_id):
        status = self.scheduler.get_running_status(script_id)
        if status is None:
            try_confirm = "Trying to confirm Finish of script with ID {0} but "
            try_confirm += "it was not running"
            raise Exception(try_confirm.format(script_id))
        status.finish_confirmed()
        self.scheduler.remove_if_external(script_id)

    @setting(34, "stop_confirmed", script_id="w")
    def stop_confirmed(self, c, script_id):
        status = self.scheduler.get_running_status(script_id)
        if status is None:
            try_confirm = "Trying to confirm Stop of script with ID {0} but it"
            try_confirm += " was not running"
            raise Exception(try_confirm.format(script_id))
        status.stop_confirmed()

    @setting(35, "pause_or_stop", script_id="w", returns="b")
    def pause_or_stop(self, c, script_id):
        """
        Returns the boolean whether the script should be stopped. This
        request blocks while the script is to be paused.
        """
        status = self.scheduler.get_running_status(script_id)
        if status is None:
            try_confirm = "Trying to confirm Pause/Stop of script with ID {0} "
            try_confirm += "but it was not running"
            raise Exception(try_confirm.format(script_id))
        yield status.pause()
        returnValue(status.should_stop)

    @setting(36, "error_finish_confirmed", script_id="w", error_message="s")
    def error_finish_confirmed(self, c, script_id, error_message):
        status = self.scheduler.get_running_status(script_id)
        if status is None:
            try_confirm = "Trying to confirm error finish of script with ID "
            try_confirm += "{0} but it was not running"
            raise Exception(try_confirm.format(script_id))
        status.error_finish_confirmed(error_message)
        self.scheduler.remove_if_external(script_id)

    @setting(37, "reload_available_scripts")
    def reload_available_scripts(self, c):
        reload(sc_config)
        self.scripts = {}
        self.load_scripts()

    @inlineCallbacks
    def stopServer(self):
        """
        stop all the running scripts and exit
        """
        yield None
        try:
            # cancel all scheduled scripts
            for scheduled, name, loop in self.scheduler.get_scheduled():
                self.scheduler.cancel_scheduled_script(scheduled)
            for ident, scan, priority in self.scheduler.get_queue():
                self.scheduler.remove_queued_script(ident)
            # stop all running scripts
            for ident, name in self.scheduler.get_running():
                self.scheduler.stop_running(ident)
            # wait for all deferred to finish
            running = DeferredList(self.scheduler.running_deferred_list())
            yield running
        except AttributeError:
            # if dictionary doesn't exist yet (i.e bad identification error),
            # do nothing
            pass


if __name__ == "__main__":
    from labrad import util

    util.runServer(ScriptScanner())
