"""
The oscilloscope hardware control code depends on LabRAD.  The LabRAD manager
must be running to test this code.

TODO: better implementation where LabRAD is started somehow from this code/or
overall code testing on Magic to make this more automatic.
"""

from twisted.trial.unittest import TestCase
import labrad


class TestPulser(TestCase):

    def setUp(self):
        """
        Connect to labrad
        """
        self.cxn = labrad.connect()  # host='localhost')
        self.pulser = self._get_pulser_server()

    def tearDown(self):
        """
        Disconnect from labrad, delete server.
        """
        self.pulser = None
        del self.pulser
        self.cxn.disconnect()

    def _get_pulser_server(self):
        """
        Connect to pulser.

        Check that the labrad connection has this servers attribute.

        Returns
        -------
        cxn.pulser: labrad server
        """
        self.assert_(hasattr(self.cxn, "pulser"))
        return self.cxn.pulser

    def test_echo(self):
        """
        Test that server has basic function echo
        """
        self.assert_(hasattr(self.pulser, "echo"))

    def test_name(self):
        """
        Test server name
        """
        self.assertEquals(self.pulser.name, "Pulser")
