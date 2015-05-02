"""
dds_device_server Mock
"""

class Mock_dds_device_server(object):
    """
    """

    def select_device(self, number=1):
        pass

    def amplitude(self, chan=1, amp=None):
        if amp == None:
            pass
        else:
            return amp

    def frequency(self, chan=1, freq=None):
        if freq == None:
            pass
        else:
            return freq
        