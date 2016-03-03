from emzed.r import RInterpreter, RError
from emzed.utils import toTable
from emzed.core import Table


def test_native_types():

    ip = RInterpreter()
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


def test_table_full(regtest):

    t = toTable("names", ("uwe", "schmit"), type_=str)
    t.addColumn("idx", (1, 2), type_=int)
    t.addColumn("mass", (1.0, 1.11), type_=float)
    t.addColumn("class", (True, False), type_=bool)

    ip = RInterpreter()
    ip.t = t

    print >> regtest, t
    print >> regtest, ip.t
    print >> regtest, ip.get_df_as_table("t")
    print >> regtest, ip.get_df_as_table("t", types=dict(idx=long))

    print >> regtest, map(type, t._colNames)
    print >> regtest, map(type, ip.t._colNames)
    print >> regtest, t._colTypes
    print >> regtest, ip.t._colTypes



def test_r_error_pickling():
    import dill

    # loads failed because the old constructor or RError had no "default constructor"
    err = dill.loads(dill.dumps(RError("test")))
    assert err.value == "test"

def test_interpolation():
    ip = RInterpreter()
    ip.execute("x<-%(name)r", name="Uwe")
    assert ip.x == "Uwe"
