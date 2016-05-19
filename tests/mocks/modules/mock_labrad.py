"""
pylabrad module mock with common repository servers.
"""
# We don't want to mock the units module
import labrad.units as units

from molecules.tests.mocks.lib.control.servers.mock_data_vault \
    import Mock_data_vault

from common.tests.mocks.lib.servers.AD9910_DDS_Box.mock_dds_device_server \
    import Mock_dds_device_server

from common.tests.mocks.lib.servers.mock_registry \
    import Mock_registry

from common.tests.mocks.lib.servers.abstractservers.script_scanner.mock_script_scanner \
    import Mock_script_scanner

from common.tests.mocks.lib.servers.parameter_vault.mock_parameter_vault \
    import Mock_parameter_vault

from common.tests.mocks.lib.servers.shutterandswitch.mock_Arduinoshutterandswitchserver \
    import Mock_ArduinoTTL

from common.tests.mocks.lib.servers.Dual_PMTFlow.mock_Dual_PMTFlow \
    import Mock_Dual_PMTFlow


class MockLabrad(object):
    """
    """
    def __init__(self, name=None):
        self.make_server_connections()

    def connect(self, name=None):
        return MockConnect()

    def make_server_connections(self):
        self.cxn = MockConnection()


class MockConnect(object):
    """
    """
    def __init__(self, name=None):
        self.registry = Mock_registry()
        self.data_vault = Mock_data_vault()
        self.parametervault = Mock_parameter_vault()
        self.pulser = None
        self.dds_device_server = Mock_dds_device_server()
        self.scriptscanner = Mock_script_scanner()
        self.arduinottl = Mock_ArduinoTTL()
        self.dual_pmtflow = Mock_Dual_PMTFlow()
        self._set_servers_dict()

        self.make_server_connections()

    def make_server_connections(self):
        self.cxn = MockConnection()

    def _set_servers_dict(self):
        """
        mock labrad's cxn.servers dict.
        """
        self.servers = {}
        self.servers[self.scriptscanner.name] = self.scriptscanner
        self.servers[self.parametervault.name] = self.parametervault

    def context(self):
        """
        mock the cxn.context() method
        """
        return None

    def disconnect(self):
        pass


class MockConnection(object):
    """
    Mock the labrad connection
    """
    def __init__(self):
        pass
