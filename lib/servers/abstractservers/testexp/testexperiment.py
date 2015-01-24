import labrad
from common.lib.servers.abstractservers.script_scanner.scan_methods import experiment

class testexperiment(experiment):
    
    name = 'testexperiment'



    def initialize(self, cxn, context, ident): 
        self.ident = ident
        self.cxn = labrad.connect(name = 'Tickle Scan')
        self.dv = self.cxn.data_vault
        self.pv = self.cxn.parametervault
        self.max = self.pv.get_parameter('testscan', 'maxvalue')
        self.min = self.pv.get_parameter('testscan', 'minvalue')
        self.stepsize = self.pv.get_parameter('testscan', 'stepsize')
        self.width = self.pv.get_parameter('testscan','width')  
	self.offset = self.pv.get_parameter('testscan', 'offset')
	self.xvalues = range(int(self.min), int(self.max), int(self.stepsize))

        self.dv.cd('Test Experiment', True)
        self.dv.new('Test Experiment',[('freq', 'num')], [('kilocounts/sec','','num')])
        window_name = ['Test Experiment']
        self.dv.add_parameter('Window', window_name)
        self.dv.add_parameter('plotLive', True)

    def run(self, cxn, context):
        
        '''
        Main loop 
        '''
        for i, x in enumerate(self.xvalues):
                should_stop = self.pause_or_stop()
                if should_stop: break
                self.dv.add(x, self.width*x**2 + self.offset)
                progress = 100*float(i)/len(self.xvalues)
                self.sc.script_set_progress(self.ident, progress)
        
    def finalize(self, cxn, context):
	pass

if __name__ == '__main__':
    #normal way to launch
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    exprt = set_high_volt(cxn = cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
