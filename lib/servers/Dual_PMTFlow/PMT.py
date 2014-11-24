class PMT(object):
    def __init__(self, pmt_id):
        self.id = pmt_id
        self.suffix = ' ' + str(pmt_id)
        self.enabled = False
        self.context = None


    def enable(self):
        self.enabled = True
    
    
    def disable(self):
        self.enabled = False