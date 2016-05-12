"""
### BEGIN NODE INFO
[info]
name = HP Server
version = 1.1
description =
instancename = %LABRADNODE% Agilent 1024A
[startup]
cmdline = %PYTHON% %FILE%
timeout = 20
[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from serialdeviceserver import SerialDeviceServer, setting, inlineCallbacks, SerialDeviceError, SerialConnectionError, PortRegError
from twisted.internet.defer import returnValue

class HPServer( SerialDeviceServer ):
    """Controls HP8648A Signal Generator"""

    name = '%LABRADNODE% Agilent 1024A SERVER'
    regKey = 'Agilent1024A'
    port = None
    serNode = 'magic'
    timeout = 1.0
    gpibaddr = 0
