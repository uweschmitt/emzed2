from emzed.r import RInterpreter, RError, RInterpreterFast
from emzed.utils import toTable


def test_native_types():

    ip = RInterpreter()
    _test_native_types(ip)

def test_native_types_fast():

    ip = RInterpreterFast()
    _test_native_types(ip)

def _test_native_types(ip):

    assert ip.execute("x <-3").x == 3
    assert ip.execute("x <-1.0").x == 1.0
    assert ip.execute("x <-'abc'").x == 'abc'

    ip.y = 42
    assert ip.execute("x <- y").x == 42

    ip.y = 1.0
    assert ip.execute("x <- y").x == 1.0

    ip.y = "abc"
    assert ip.execute("x <- y").x == "abc"


def test_tables(regtest):
    ip = RInterpreter()
    _test_tables(ip, regtest)

def test_tables_fast(regtest):
    ip = RInterpreterFast()
    _test_tables(ip, regtest)

def _test_tables(ip, regtest):
    t = toTable("a", [1, 2])

    # transfer Table tor R:
    ip.t = t

    # fetch Table from R
    assert ip.execute("s <- t").s.rows == t.rows

    # fetch pandas.DataFrame from R
    df = ip.get_raw("s")
    assert df.as_matrix().tolist() == [[1], [2]]

    df = ip.get_raw("mtcars")
    print >> regtest, df

    ip.ddf = df

    print >> regtest, ip.ddf
    print >> regtest, ip.mtcars


def test_r_error_pickling():
    import dill

    # loads failed because the old constructor or RError had no "default constructor"
    err = dill.loads(dill.dumps(RError("test")))
    assert err.value == "test"
