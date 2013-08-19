
from emzed.core.r_connect import RExecutor

def test_one():
    status = RExecutor().run_command("q(status=123)")
    assert status == 123, repr(status)
    status = RExecutor().run_command("q(status=12)")
    assert status == 12, repr(status)



