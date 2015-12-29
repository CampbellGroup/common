"""
Mock the parameter vault
"""
from labrad.units import WithUnit


class Mock_parameter_vault(object):
    """
    """

    name = 'ParameterVault'

    def get_parameter(self, collection=None, parameter_name=None):
        """
        This should return a labrad WithUnit type.

        This will permit basic WithUnit math to function.
        """
        default_value = WithUnit(1.0, 's')
        return default_value
