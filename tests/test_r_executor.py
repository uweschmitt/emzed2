
from emzed.core.r_connect import RExecutor, installXcmsIfNeeded


def test_one():
    RExecutor().runTest()

def test_two():
    installXcmsIfNeeded()



