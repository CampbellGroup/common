import labrad

from lib.servers.script_scanner.scan_methods import Experiment, ScanSingle


class FFTSpectrum(Experiment):

    name = "FFT Spectrum"
    required_parameters = []

    def initialize(self, cxn, context, ident):
        print("init")

    def run(self, cxn, context):
        print("running")

    def finalize(self, cxn, context):
        print("finalize")


class ConflictingExperiment(FFTSpectrum):

    name = "conflicting_experiment"
    required_parameters = [("TrapFrequencies", "axial_frequency")]


class NonConflictingExperiment(FFTSpectrum):

    name = "non_conflicting_experiment"


class CrashingExample(FFTSpectrum):

    name = "crashing_example"

    def initialize(self, cxn, context, ident):
        print("in initialize", self.name, ident)
        raise Exception("In a case of a crash, real message would follow")


if __name__ == "__main__":
    # normal way to launch
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    exprt = FFTSpectrum(cxn=cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
    # testing single launch
    cxn = labrad.connect()
    scanner = cxn.scriptscanner

    exprt = ScanSingle(FFTSpectrum)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
    # testing repeat launch
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    from scan_methods import ScanRepeatReload

    exprt = ScanRepeatReload(FFTSpectrum, 10)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
    # testing scan
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    from scan_methods import ScanExperiment1D

    exprt = ScanExperiment1D(
        FFTSpectrum, ("TrapFrequencies", "rf_drive_frequency"), 10.0, 20.0, 10, "MHZ"
    )
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
