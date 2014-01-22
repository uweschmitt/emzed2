
from emzed.core.data_types import Table
import emzed.utils
import emzed.mass
import numpy as np


def testBinary():
    t = emzed.utils.toTable("compound", ["Na", "NaCl", "H2O"])
    t2 = t.filter(t.compound.containsElement("Na") | t.compound.containsElement("Cl"))
    assert len(t2) == 2


def testJoinNameGeneration():

    t = emzed.utils.toTable("a", [])
    t2 = t.copy()
    t = t.join(t2, False)
    assert t.getColNames() == ["a", "a__0"]
    t = t.join(t2, False)
    assert t.getColNames() == ["a", "a__0", "a__1"]
    t = t.join(t.copy(), False)
    assert t.getColNames() == ["a", "a__0", "a__1", "a__2", "a__3", "a__4"]
    t.dropColumns("a")
    t = t.join(t.copy(), False)
    assert t.getColNames() == ["a__%d" % i for i in range(10)]


def testEmptyApply():
    t = emzed.utils.toTable("a", [])
    t.addColumn("b", t.a.apply(len))
    assert len(t) == 0
    assert t.getColTypes() == [None, None], t.getColTypes()


def testRound():
    # failed in ealrier versions, as np.vectorize does not like round !
    t = emzed.utils.toTable("a", [1.23, 0.5])
    t.addColumn("b", t.a.apply(round))
    assert len(t) == 2
    assert t.b.values == [1.0, 1.0]


def testFullJoin():
    t = emzed.utils.toTable("a", [None, 2, 3])
    t2 = t.join(t)
    t2.print_()
    assert len(t2) == 9
    assert t2.a.values == [None, None, None, 2, 2, 2, 3, 3, 3]
    assert t2.a__0.values == t.a.values * 3


def testIfNotNoneElse():
    t = emzed.utils.toTable("a", [None, 2, 3])
    t.print_()
    t.addColumn("b", t.a.ifNotNoneElse(3))
    t.print_()
    t.addColumn("c", t.a.ifNotNoneElse(t.b + 1))

    t.print_()

    assert t.b.values == [3, 2, 3]
    assert t.c.values == [4, 2, 3]


def testPow():
    t = emzed.utils.toTable("a", [None, 2, 3])
    t.addColumn("square", t.a.pow(2))
    assert t.square.values == [None, 4, 9], t.square.values


def testApply():
    t = emzed.utils.toTable("a", [None, 2, 3])
    t.addColumn("id", (t.a * t.a).apply(lambda v: int(v ** 0.5)))
    assert t.id.values == [None, 2, 3]

    sub = emzed.utils.toTable("mf", ["Na", "H2O", None])

    # apply with Nones in cols
    expr = sub.mf.apply(emzed.mass.of)
    sub.addColumn("m0", expr)

    sub.addColumn("m0s", sub.m0.apply(str))
    sub.print_()
    assert sub.getColTypes() == [str, float, str], sub.getColTypes()

    # apply without None values:
    sub = sub.filter(sub.m0.isNotNone())
    assert len(sub) == 2
    sub.addColumn("m02", sub.mf.apply(emzed.mass.of))
    sub.addColumn("m0s2", sub.m0.apply(str))
    assert sub.getColTypes() == [str, float, str, float, str], sub.getColTypes()


def testNumpyTypeCoercion():
    t = emzed.utils.toTable("a", [np.int32(1)])
    t.info()
    assert t.getColTypes() == [int], t.getColTypes()
    t = emzed.utils.toTable("a", [None, np.int32(1)])
    t.info()
    assert t.getColTypes() == [int], t.getColTypes()

    t.addColumn("b", np.int32(1))
    assert t.getColTypes() == [int, int], t.getColTypes()
    t.replaceColumn("b", [None, np.int32(1)])
    assert t.getColTypes() == [int, int], t.getColTypes()

    t.replaceColumn("b", np.int64(1))
    assert t.getColTypes() == [int, int], t.getColTypes()
    t.replaceColumn("b", [None, np.int64(1)])
    assert t.getColTypes() == [int, int], t.getColTypes()

    t.replaceColumn("b", np.float32(1.0))
    assert t.getColTypes() == [int, float], t.getColTypes()
    t.replaceColumn("b", [None, np.float32(1.0)])
    assert t.getColTypes() == [int, float], t.getColTypes()

    t.replaceColumn("b", np.float64(2.0))
    assert t.getColTypes() == [int, float], t.getColTypes()
    t.replaceColumn("b", [None, np.float64(2.0)])
    assert t.getColTypes() == [int, float], t.getColTypes()


def testApplyUfun():
    t = emzed.utils.toTable("a", [None, 2.0, 3])

    print np.log
    t.addColumn("log", t.a.apply(np.log))
    assert t.getColTypes() == [float, float], t.getColTypes()


def testNonBoolean():
    t = emzed.utils.toTable("a", [])
    try:
        not t.a  # this was a common mistake: ~t.a is the correct way to express negation
    except:
        pass
    else:
        raise Exception()


def testIllegalRows():
    try:
        Table(["a", "b"], [float, float], ["%f", "%f"], [(1, 2)])
    except Exception, e:
        assert "not all rows are lists" in str(e), str(e)
    else:
        pass


def test_adduct_table():
    import emzed.adducts
    tab = emzed.adducts.all.toTable()
    assert len(tab) > 0


def testForDanglingReferences():
    t = emzed.utils.toTable("a", [None, 2, 2])
    t2 = t.join(t, True)

    # test if result is a real copy, no references to original
    # tables are left
    t2.rows[0][0] = 3
    assert t.rows[0][0] is None
    t2.rows[0][1] = 3
    assert t.rows[0][0] is None

    t2 = t.leftJoin(t, True)
    t2.rows[0][0] = 3
    assert t.rows[0][0] is None
    t2.rows[0][1] = 3
    assert t.rows[0][0] is None

    t2 = t.filter(True)
    t2.rows[0][0] = 3
    assert t.rows[0][0] is None

    tis = t.splitBy("a")
    tis[0].rows[0][0] = 7
    assert t.a.values == [None, 2, 2]

    tis[1].rows[0][0] = 7
    assert t.a.values == [None, 2, 2]

    tn = t.uniqueRows()
    tn.rows[0][0] = 7
    tn.rows[-1][0] = 7
    assert t.a.values == [None, 2, 2]


def testSupportedPostfixes():

    names = "mz mzmin mzmax mz0 mzmin0 mzmax0 mz1 mzmax1 mzmin__0 mzmax__0 mz__0 "\
            "mzmax3 mz4 mzmin4".split()

    t = Table._create(names, [float] * len(names), [])
    assert len(t.supportedPostfixes(["mz"])) == len(names)
    assert t.supportedPostfixes(["mz", "mzmin"]) == ["", "0", "4", "__0"]
    assert t.supportedPostfixes(["mz", "mzmin", "mzmax"]) == ["", "0", "__0"]


def testNumericSTuff():
    t = emzed.utils.toTable("a", [None, 2, 3])
    t._print()
    t.replaceColumn("a", t.a + 1.0)
    t._print()
    t.info()


def testSomeExpressions():
    t = emzed.utils.toTable("mf", ["Ag", "P", "Pb", "P3Pb", "PbP"])
    tn = t.filter(t.mf.containsElement("P"))
    assert len(tn) == 3
    tn = t.filter(t.mf.containsElement("Pb"))
    assert len(tn) == 3


def testColumnAggFunctions():
    t = emzed.utils.toTable("a", [None, 2, 3])
    r = t.a.max()
    assert r == 3
    assert t.a.min() == 2
    assert t.a.mean() == 2.5
    assert t.a.std() == 0.5

    assert t.a.hasNone(), t.a.hasNone()
    assert t.a.len() == 3, t.a.len()
    assert t.a.countNone() == 1, t.a.countNone()

    t.addColumn("b", None)
    assert t.b.max() is None
    assert t.b.min() is None
    assert t.b.mean() is None
    assert t.b.std() is None
    assert t.b.hasNone()
    assert t.b.len() == 3
    assert t.b.countNone() == 3

    t.addColumn("c", [None, None, 1])

    assert t.c.uniqueNotNone() == 1

    assert (t.a + t.c).values == [None, None, 4]
    assert (t.a + t.c).sum() == 4
    apc = (t.a + t.c).toTable("a_plus_c")
    assert apc.getColNames() == ["a_plus_c"]
    assert apc.getColTypes() == [int]
    assert apc.a_plus_c.values == [None, None, 4]

    assert (apc.a_plus_c - t.a).values == [None, None, 1]

    # column from other table !
    t.addColumn("apc", apc.a_plus_c)
    assert t.apc.values == [None, None, 4], t.apc.values

    # column from other table !
    t2 = t.filter(apc.a_plus_c)
    assert len(t2) == 1
    assert t2.apc.values == [4]




def testUniqeRows():
    t = emzed.utils.toTable("a", [1, 1, 2, 2, 3, 3])
    t.addColumn("b", [1, 1, 1, 2, 3, 3])
    u = t.uniqueRows()
    assert u.a.values == [1, 2, 2, 3]
    assert u.b.values == [1, 1, 2, 3]
    assert len(u.getColNames()) == 2
    u.info()


def testInplaceColumnmodification():
    t = emzed.utils.toTable("a", [1, 2, 3, 4])
    t.a += 1
    assert t.a.values == [2, 3, 4, 5]
    t.a *= 2
    assert t.a.values == [4, 6, 8, 10]
    t.a /= 2
    assert t.a.values == [2, 3, 4, 5]
    t.a -= 1
    assert t.a.values == [1, 2, 3, 4]

    t.a.modify(lambda v: 0)
    assert t.a.values == [0, 0, 0, 0]


def testIndex():
    t = emzed.utils.toTable("a", [1, 2, 3, 4, 5])
    t.addColumn("b", [2, 0, 1, 5, 6])
    t.sortBy("a")
    print t.primaryIndex
    a = t.a

    es = [a <= 2, a <= 0, a <= 5, a <= 6]
    vs = [2, 0, 5, 5]
    es += [a < 2, a < 0, a < 1, a < 5, a < 6]
    vs += [1, 0, 0, 4, 5]
    es += [a >= 2, a >= 0, a >= 1, a >= 5, a >= 6]
    vs += [4, 5, 5, 1, 0]
    es += [a > 2, a > 0, a > -2, a > 1, a > 5, a > 6]
    vs += [3, 5, 5, 4, 0, 0]

    assert len(es) == len(vs)

    for e, v in zip(es, vs):
        print e, v
        assert len(t.filter(e)) == v, len(t.filter(e))

    t2 = t.copy()
    assert t.join(t2, t.b < t2.a).a__0.values == [3, 4, 5, 1, 2, 3, 4, 5, 2, 3, 4, 5]
    assert t.join(t2, t.b > t2.a).a__0.values == [1, 1, 2, 3, 4, 1, 2, 3, 4, 5]
    assert t.join(t2, t.b <= t2.a).a__0.values == [2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 5]
    assert t.join(t2, t.b >= t2.a).a__0.values == [1, 2, 1, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5]

    assert t.join(t2, t.b == t2.a).a__0.values == [2, 1, 5]
    assert t.join(t2, t.b != t2.a).a__0.values == [1, 3, 4, 5, 1, 2, 3, 4, 5, 2, 3, 4, 5, 1,
                                                   2, 3, 4, 1, 2, 3, 4, 5]


def testBools():
    t = emzed.utils.toTable("bool", [True, False, True, None])
    assert t.bool.sum() == 2
    print repr(t.bool.max()), repr(True)
    print type(t.bool.max()), type(True)
    print id(t.bool.max()), id(True)
    assert t.bool.max() == True, t.bool.max()
    assert t.bool.min() == False, t.bool.min()

    t.addColumn("int", [1, 2, 3, 4])
    t.addColumn("float", [1.0, 2, 3, 4])
    t.addColumn("int_bool", (t.bool).thenElse(t.bool, t.int))

    # test coercion (bool, int) to int:
    assert t.int_bool.values == [1, 2, 1, None]
    t.addColumn("int_float", (t.bool).thenElse(t.int, t.float))
    assert t.int_float.values == [1.0, 2.0, 3.0, None], t.int_float.values

    t.addColumn("bool_float", (t.bool).thenElse(t.bool, t.float))
    assert t.bool_float.values == [1.0, 2.0, 1.0, None]


def testUniqueValue():
    t = emzed.utils.toTable("a", [1, 1, 1])
    assert t.a.uniqueValue() == 1

    t = emzed.utils.toTable("a", [1.2, 1.21, 1.19])
    assert t.a.uniqueValue(up_to_digits=1) == 1.2

    a = dict(b=3)
    b = dict(b=3)

    t = emzed.utils.toTable("a", [a, b])
    print t.a.uniqueValue()


def testSpecialFormats():
    for name in ["mz", "mzmin", "mzmax", "mw", "m0"]:
        t = emzed.utils.toTable(name, [1.0, 2, None])
        assert t.colFormatters[0](1) == "1.00000", t.colFormatters[0](1)

    for name in ["rt", "rtmin", "rtmax"]:
        t = emzed.utils.toTable(name, [1.0, 2, None])
        assert t.colFormatters[0](120) == "2.00m"


def testLogics():
    t = emzed.utils.toTable("a", [True, False])
    t.addColumn("nota", ~t.a)
    t.addColumn("true", t.a | True)
    t.addColumn("false", t.a & False)

    assert t.getColTypes() == 4 * [bool]

    assert len(t.filter(t.a & t.nota)) == 0
    assert len(t.filter(t.a | t.true)) == 2
    assert len(t.filter(t.a ^ t.nota)) == 2
    assert len(t.filter(t.a ^ t.a)) == 0

    bunch = t.getValues(t.rows[0])
    assert bunch.a is True
    assert bunch.nota is False
    assert bunch.true is True
    assert bunch.false is False


def testAppend():
    t = emzed.utils.toTable("a", [1, 2])
    t2 = t.copy()
    t.append(t2, [t2, t2], (t2,))
    assert len(t) == 10
    assert t.a.values == [1, 2] * 5


def testRenamePostfixes():
    t = emzed.utils.toTable("a", [1, 2])
    t.addColumn("b", t.a + 1)
    t = t.join(t)
    assert t.getColNames() == ["a", "b", "a__0", "b__0"], t.getColNames()
    t.renamePostfixes(__0="_new")
    assert t.getColNames() == ["a", "b", "a_new", "b_new"], t.getColNames()


def testToOpenMSFeatureMap():
    t = Table("mz rt".split(), [float, float], 2 * ["%.6f"])
    fm = t.toOpenMSFeatureMap()
    assert fm.size() == 0

    t.addRow([1.0, 2.0])
    fm = t.toOpenMSFeatureMap()
    assert fm.size() == 1

    f = fm[0]
    assert f.getMZ() == 1.0  # == ok, as no digits after decimal point
    assert f.getRT() == 2.0  # dito


def test_removePostfixes():
    t = Table._create(["abb__0", "bcb__0"], [str] * 2, ["%s"] * 2)
    assert t.getColNames() == ["abb__0", "bcb__0"]
    t.removePostfixes()
    assert t.getColNames() == ["abb", "bcb"]
    t.removePostfixes("bb", "cb")
    assert t.getColNames() == ["a", "b"]
    try:
        t.print_()
        t.removePostfixes("a", "b")
        t.print_()

    except:
        pass
    else:
        assert False, "expected exception"


def test_getters_and_setters():
    t = emzed.utils.toTable("a", [1, 2, 3])
    assert t.getColType("a") == int
    assert t.getColFormat("a") == "%d"

    t.setColType("a", float)
    assert t.getColType("a") == float
    t.setColFormat("a", "%.3f")
    assert t.getColFormat("a") == "%.3f"


def test_unique_not_none_for_empty_list():
    t = emzed.utils.toTable("z", [], type_=int)
    # those did raise exceptions:
    t.z.uniqueNotNone.values
    t.z.value()
    t.z.mean()


def test_drop_last_column():
    t = emzed.utils.toTable("z", [1, 2])
    t.dropColumns("z")
    assert len(t) == 0


def test_replace_dunder_coloumn():
    t = emzed.utils.toTable("z", [1, 2])
    t = t.join(t, True)
    # should not throw exception, as we do not create a new columns with "__" in its name:
    t.replaceColumn("z__0", t.z__0.apply(float))
    t.print_()


def test_multi_sort():
    t = emzed.utils.toTable("z", [1, 3, 2])
    t.addColumn("y", [1, 2, 2])

    t.sortBy(["y", "z"])
    assert t.y.values == [1, 2, 2]
    assert t.z.values == [1, 2, 3]

    t.sortBy(["y", "z"], ascending=False)
    assert t.y.values == [2, 2, 1]
    assert t.z.values == [3, 2, 1]


def test_collapse():
    t = emzed.utils.toTable("id", [1, 1, 2])
    t.addColumn("a", [1, 2, 3])
    t.addColumn("b", [3, 4, 5])
    t2 = t.collapse("id")
    assert len(t2) == 2
    assert t2.getColNames() == ["id", "collapsed"]
    assert t2.getColTypes() == [int, t.__class__]

    subs = t2.collapsed.values
    assert subs[0].getColNames() == ["id", "a", "b"]
    assert len(subs[0]) == 2
    assert subs[1].getColNames() == ["id", "a", "b"]
    assert len(subs[1]) == 1

    t2 = t.collapse("id", "a")
    assert len(t2) == 3
    assert t2.getColNames() == ["id", "a", "collapsed"]
    assert t2.getColTypes() == [int, int, t.__class__]

    subs = t2.collapsed.values
    assert subs[0].getColNames() == ["id", "a", "b"]
    assert len(subs[0]) == 1
    assert subs[1].getColNames() == ["id", "a", "b"]
    assert len(subs[1]) == 1
    assert subs[2].getColNames() == ["id", "a", "b"]
    assert len(subs[2]) == 1


def test_missing_values_binary_expressions():

    # column x has type None, this is a special case which failed before
    t = emzed.utils.toTable("x", [None])
    assert (t.x + t.x).values == [None]
    assert (t.x * t.x).values == [None]
    assert (t.x - t.x).values == [None]
    assert (t.x / t.x).values == [None]

    t.addColumn("y", [1])
    assert (t.x + t.y).values == [None]
    assert (t.x * t.y).values == [None]
    assert (t.x - t.y).values == [None]
    assert (t.x / t.y).values == [None]

    assert (t.y + t.x).values == [None]
    assert (t.y * t.x).values == [None]
    assert (t.y - t.x).values == [None]
    assert (t.y / t.x).values == [None]


def test_grouped_aggregate_expressions():

    # without missing values #########################################

    # int types aggregated
    t = emzed.utils.toTable("group", [1, 1, 2])
    t.addColumn("values", [1, 2, 3])
    t.addColumn("grouped_min", t.values.min.group_by(t.group))
    assert t.grouped_min.values == [1, 1, 3]
    t.print_()

    # float types aggregated
    t = emzed.utils.toTable("group", [1, 1, 2])
    t.addColumn("values", [1, 2, 3])
    t.addColumn("grouped_mean", t.values.mean.group_by(t.group))
    assert t.grouped_mean.values == [1.5, 1.5, 3]
    t.print_()

    # str types aggregated
    t = emzed.utils.toTable("group", [1, 1, 2])
    t.addColumn("values", ["1", "2", "3"])
    t.addColumn("grouped_max", t.values.max.group_by(t.group))
    assert t.grouped_max.values == ["2", "2", "3"]
    t.print_()

    # with missing values ############################################

    # int types aggregated
    t = emzed.utils.toTable("group", [1, 1, 2])
    t.addColumn("values", [None, 2, None])
    t.addColumn("grouped_min", t.values.min.group_by(t.group))
    assert t.grouped_min.values == [2, 2, None]
    t.print_()

    # float types aggregated
    t = emzed.utils.toTable("group", [1, 1, 2])
    t.addColumn("values", [None, 2.0, None])
    t.addColumn("grouped_min", t.values.min.group_by(t.group))
    assert t.grouped_min.values == [2.0, 2.0, None]
    t.print_()

    # str types aggregated
    t = emzed.utils.toTable("group", [1, 1, 2])
    t.addColumn("values", [None, "2", None])
    t.addColumn("grouped_min", t.values.min.group_by(t.group))
    assert t.grouped_min.values == ["2", "2", None]
    t.print_()

    # empty columns ##################################################

    # only None values
    t = emzed.utils.toTable("group", [1, 1, 2])
    t.addColumn("values", [None, None, None])
    t.addColumn("grouped_min", t.values.min.group_by(t.group))
    assert t.grouped_min.values == [None, None, None]
    t.print_()

    # empty table
    t = emzed.utils.toTable("group", [])
    t.addColumn("values", [])
    t.addColumn("grouped_min", t.values.min.group_by(t.group))
    assert t.grouped_min.values == []
    t.print_()


def test_own_aggregate_functions():

    # int types aggregated
    t = emzed.utils.toTable("group", [1, 1, 2])
    t.addColumn("values", [1, 2, 3])
    t.addColumn("grouped_min", t.values.aggregate(lambda v: min(v)).group_by(t.group))
    assert t.grouped_min.values == [1, 1, 3]
    t.print_()
    # int types aggregated
    t = emzed.utils.toTable("group", [1, 1, 2])
    t.addColumn("values", [1, 2, 3])
    t.addColumn("grouped_min", t.values.aggregate(np.min).group_by(t.group))
    assert t.grouped_min.values == [1, 1, 3]
    t.print_()

    def my_min(li):
        return min(li) + 42

    t.addColumn("strange", t.values.aggregate(my_min))
    assert t.strange.values == [43, 43, 43], t.strange.values
    t.addColumn("strange2", t.values.aggregate(my_min).group_by(t.group))
    assert t.strange2.values == [43, 43, 45], t.strange2.values

    t.print_()


def test_aggregate_types():
    t = emzed.utils.toTable("group", [1, 1, 2])
    assert type(t.group.max()) in (int, long)





