"""
Mock the dual PMT flow server.
"""


class Mock_Dual_PMTFlow(object):
    """
    """

    name = 'Dual PMTFlow'

    def pmt_state(self, pmt=None, value=None):
        """
        Mock pmt_state method.  Returns value.
        """
        return value
