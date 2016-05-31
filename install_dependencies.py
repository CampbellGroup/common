"""
Install dependent packages for common repo.

Also add LabRAD system environmental variables.

The functions used to hoist to admin status is found in the following link:
http://stackoverflow.com/questions/19672352/how-to-run-python-script-with-elevated-privilege-on-windows

Packages installed in this script:

pylabrad
pyvisa
pyserial
service_identity
pyqtgraph
qt4reactor
"""
import sys
import os
import traceback
import types
import pip
import subprocess
import platform


def is_user_admin():
    if os.name == 'nt':
        import ctypes
        # WARNING: requires Windows XP SP2 or higher!
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            traceback.print_exc()
            print "Admin check failed, assuming not an admin."
            return False
    elif os.name == 'posix':
        # Check for root on Posix
        return os.getuid() == 0
    else:
        raise RuntimeError, "Unsupported operating system for this module: %s" \
            % (os.name,)


def run_as_admin(cmdLine=None, wait=True):

    if os.name != 'nt':
        raise RuntimeError, "This function is only implemented on Windows."

    import win32con, win32event, win32process
    from win32com.shell.shell import ShellExecuteEx
    from win32com.shell import shellcon

    python_exe = sys.executable

    if cmdLine is None:
        cmdLine = [python_exe] + sys.argv
    elif type(cmdLine) not in (types.TupleType,types.ListType):
        raise ValueError, "cmdLine is not a sequence."
    cmd = '"%s"' % (cmdLine[0],)
    params = " ".join(['"%s"' % (x,) for x in cmdLine[1:]])
    showCmd = win32con.SW_SHOWNORMAL
    #showCmd = win32con.SW_HIDE
    lpVerb = 'runas'  # causes UAC elevation prompt.

    # print "Running", cmd, params

    # ShellExecute() doesn't seem to allow us to fetch the PID or handle
    # of the process, so we can't get anything useful from it. Therefore
    # the more complex ShellExecuteEx() must be used.

    # procHandle = win32api.ShellExecute(0, lpVerb, cmd, params, cmdDir, showCmd)

    procInfo = ShellExecuteEx(nShow=showCmd,
                              fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
                              lpVerb=lpVerb,
                              lpFile=cmd,
                              lpParameters=params)
    if wait:
        procHandle = procInfo['hProcess']
        obj = win32event.WaitForSingleObject(procHandle, win32event.INFINITE)
        rc = win32process.GetExitCodeProcess(procHandle)
        #print "Process handle %s returned code %s" % (procHandle, rc)
    else:
        rc = None
    return rc


def install_vcpython27():
    install_choco = subprocess.call(["installChocolatey.cmd"])
    install_vcpython = subprocess.call(['choco', 'install', 'vcpython27'])


def install(package):
    pip.main(['install', package])


def set_environmental_variables():
    os = platform.system()
    if os == "Windows":
        _set_windows_environmental_variables()
    else:
        _set_unix_environmental_variables()


def _set_windows_environmental_variables():
    _set_win_envar("LABRAD_TLS", "off")
    _set_win_envar("LABRAD_TLS_PORT", "7643")
    # You may need to change the default labrad host manually after
    # installation. For example, for molecules it really should be
    # "10.97.112.6".
    _set_win_envar("LABRADHOST", "localhost")
    computer_name = platform.node()
    _set_win_envar("LABRADNODE", computer_name.lower())
    _set_win_envar("LABRADPASSWORD", "lab")
    _set_win_envar("LABRADPORT", "7682")


def _set_win_envar(var, value):
    subprocess.call(["setx", "-m", var, value])


def _set_unix_environmental_variables():
    # TODO: enable this functionality
    pass


if __name__ == '__main__':
    system = platform.system()
    if system == "Windows":
        if not is_user_admin():
            run_as_admin()
        install_vcpython27()
    install('pylabrad')
    install('pyserial')
    install('pyvisa')
    install('service_identity')
    install('pyqtgraph')
    install('qt4reactor')
    set_environmental_variables()
