import sys
import pprint
pprint.pprint(sys.path)

import emzed
import emzed.core
import emzed.core.r_connect

def test_install_xcms(tmpdir):
    # order of next three lines is important for sucessfull  patching
    from emzed.core.r_connect import RExecutor
    RExecutor._patched_rlibs_folder = tmpdir.strpath
    from emzed.core.r_connect import (installXcmsIfNeeded,
                                       checkIfxcmsIsInstalled,
                                       lookForXcmsUpgrades,
                                       doXcmsUpgrade)

    assert installXcmsIfNeeded() == 1
    assert checkIfxcmsIsInstalled() == 1
    lookForXcmsUpgrades()
    doXcmsUpgrade()
