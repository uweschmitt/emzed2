

def test_install_xcms(tmpdir):
    # order of next three lines is important for sucessfull  patching
    from emzed.core.r_connect.r_executor import RExecutor
    RExecutor._patched_rlibs_folder = tmpdir.strpath
    from emzed.core.r_connect import *

    installXcmsIfNeeded()
    checkIfxcmsIsInstalled()
    lookForXcmsUpgrades()
    doXcmsUpgrade()
