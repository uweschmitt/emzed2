from emzed.core.r_connect import *
import pytest

@pytest.mark.slow
def test_install_xcms():
    installXcmsIfNeeded()
    checkIfxcmsIsInstalled()
    lookForXcmsUpgrades()
    doXcmsUpgrade()
