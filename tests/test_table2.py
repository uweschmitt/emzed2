# encoding: utf-8

from __future__ import print_function

from datetime import datetime
import os

from emzed.core.data_types import Table, PeakMap, Blob, TimeSeries
from emzed.core.data_types.table import relative_path
import emzed.utils
import emzed.mass
import numpy as np
import pytest


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
    assert t.b.values == (1.0, 1.0,)


def testFullJoin():
    t = emzed.utils.toTable("a", [None, 2, 3])
    t2 = t.join(t)
    t2.print_()
    assert len(t2) == 9
    assert t2.a.values == (None, None, None, 2, 2, 2, 3, 3, 3,)
    assert t2.a__0.values == t.a.values * 3


def testFastJoin(regtest_redirect):

    def ttt(t, other):
        joined = t.fastJoin(other, "a", "b")
        print()
        print("join")
        joined.print_()
        joined = t.fastLeftJoin(other, "a", "b")
        print()
        print("left join")
        joined.print_()

    with regtest_redirect():
        t = emzed.utils.toTable("a", [None, 2, 3], type_=int)
        joined = t.fastJoin(t, "a")
        print()
        print("join")
        joined.print_()
        joined = t.fastLeftJoin(t, "a")
        print()
        print("left join")
        joined.print_()

        other = emzed.utils.toTable("b", [2, 2, 2, 2, 2], type_=int)
        other.addColumn("i", range(len(other)), type_=int, insertBefore=0)
        ttt(t, other)

        other = emzed.utils.toTable("b", [2, 2, 2, 3, 3], type_=int)
        other.addColumn("i", range(len(other)), type_=int)
        ttt(t, other)

        other = emzed.utils.toTable("b", [2, 2, 2, 3, 3], type_=int)
        other.addColumn("i", range(len(other)), type_=int)
        ttt(t, other)

        other = emzed.utils.toTable("b", [7, 7, 7, 7, 7], type_=int)
        other.addColumn("i", range(len(other)), type_=int)
        ttt(t, other)

        other = emzed.utils.toTable("b", [], type_=int)
        other.addColumn("i", range(len(other)), type_=int)
        ttt(t, other)


def testFastApproxLookup(regtest):
    t = emzed.utils.toTable("a", (None, 1.0, 2.0, 3.0, 4.0, 5.0))
    t2 = t.fastJoin(t, "a", abs_tol=.001)
    print(t2, file=regtest)

    t2 = t.fastJoin(t, "a", rel_tol=.5)
    print(t2, file=regtest)

    t2 = t.fastLeftJoin(t, "a", abs_tol=.001)
    print(t2, file=regtest)

    t2 = t.fastLeftJoin(t, "a", rel_tol=.5)
    print(t2, file=regtest)

    t = emzed.utils.toTable("ix", range(300))
    import random

    random.seed(4711)

    t.addColumn("r", t.apply(random.random, ()))
    t2 = t.copy()

    import time

    t2.sortBy("r")

    started = time.time()
    r = t.fastJoin(t2, "r", abs_tol=0.0002)
    print()
    print("fastJoin: ", end="")
    print(len(r), "rows", time.time() - started, "seconds needed")
    print()

    started = time.time()
    r1 = t.join(t2, t.r.approxEqual(t2.r, 0.0002))
    print()
    print("join with approxEqual: ", end="")
    print(len(r), "rows", time.time() - started, "seconds needed")
    print()

    assert r.uniqueId() == r1.uniqueId()

    started = time.time()
    r2 = t.join(t2, t.r.equals(t2.r, abs_tol=0.0002))
    print()
    print("join with equals: ", end="")
    print(len(r), "rows", time.time() - started, "seconds needed")
    print()

    assert r.uniqueId() == r2.uniqueId()

    started = time.time()
    r3 = t.join(t2, t.r.equals(t2.r, abs_tol=1.00) & t.r.equals(t2.r, abs_tol=0.0002))
    print()
    print("join with equals, two times: ", end="")
    print(len(r), "rows", time.time() - started, "seconds needed")
    print()

    assert r.uniqueId() == r3.uniqueId()

    started = time.time()
    r4 = t.join(t2, (t.r - t2.r).apply(abs) <= 0.0002)
    print()
    print("join with computing distance, two times: ", end="")
    print(len(r), "rows", time.time() - started, "seconds needed")
    print()

    assert r.uniqueId() == r4.uniqueId()

    # now we test for matching with relative tolerance:

    r = t.fastJoin(t2, "r", rel_tol=0.02)
    r2 = t.join(t2, t.r.equals(t2.r, rel_tol=0.02))
    assert r.uniqueId() == r2.uniqueId()

    r3 = t.join(t2, t.r.equals(t2.r, rel_tol=0.2) & t.r.equals(t2.r, rel_tol=0.02))

    assert r.uniqueId() == r3.uniqueId()

    started = time.time()
    r4 = t.join(t2, (t.r - t2.r).apply(abs) / t.r <= 0.02)

    assert r.uniqueId() == r4.uniqueId()


def testIfNotNoneElse():
    t = emzed.utils.toTable("a", [None, 2, 3])
    t.print_()
    t.addColumn("b", t.a.ifNotNoneElse(3))
    t.print_()
    t.addColumn("c", t.a.ifNotNoneElse(t.b + 1))

    t.print_()

    assert t.b.values == (3, 2, 3,)
    assert t.c.values == (4, 2, 3,)


def testPow():
    t = emzed.utils.toTable("a", [None, 2, 3])
    t.addColumn("square", t.a.pow(2))
    assert t.square.values == (None, 4, 9,), t.square.values


def testApply():
    t = emzed.utils.toTable("a", [None, 2, 3])
    t.addColumn("id", (t.a * t.a).apply(lambda v: int(v ** 0.5)))
    assert t.id.values == (None, 2, 3,)

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

    t.addColumn("log", t.a.apply(np.log))
    assert t.getColTypes() == [float, float], t.getColTypes()


def testNonBoolean():
    t = emzed.utils.toTable("a", [])
    with pytest.raises(Exception):
        not t.a  # this was a common mistake: ~t.a is the correct way to express negation


def testIllegalRows():
    with pytest.raises(Exception):
        Table(["a", "b"], [float, float], ["%f", "%f"], [(1, 2)])


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
    assert t.a.values == (None, 2, 2,)

    tis[1].rows[0][0] = 7
    assert t.a.values == (None, 2, 2,)

    tn = t.uniqueRows()
    tn.rows[0][0] = 7
    tn.rows[-1][0] = 7
    assert t.a.values == (None, 2, 2,)


def testSupportedPostfixes():

    names = "mz mzmin mzmax mz0 mzmin0 mzmax0 mz1 mzmax1 mzmin__0 mzmax__0 mz__0 "\
            "mzmax3 mz4 mzmin4".split()

    t = Table._create(names, [float] * len(names), [None] * len(names))
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

    assert (t.a + t.c).values == (None, None, 4,)
    assert (t.a + t.c).sum() == 4
    apc = (t.a + t.c).toTable("a_plus_c")
    assert apc.getColNames() == ["a_plus_c"]
    assert apc.getColTypes() == [int]
    assert apc.a_plus_c.values == (None, None, 4,)

    assert (apc.a_plus_c - t.a).values == (None, None, 1,)

    # column from other table !
    t.addColumn("apc", apc.a_plus_c)
    assert t.apc.values == (None, None, 4,), t.apc.values

    # column from other table !
    t2 = t.filter(apc.a_plus_c)
    assert len(t2) == 1
    assert t2.apc.values == (4,)


def testUniqeRows():
    t = emzed.utils.toTable("a", [1, 1, 2, 2, 3, 3])
    t.addColumn("b",             [1, 1, 1, 2, 3, 3])
    u = t.uniqueRows()
    assert u.a.values == (1, 2, 2, 3,)
    assert u.b.values == (1, 1, 2, 3,)
    assert len(u.getColNames()) == 2
    u.info()

    u = t.uniqueRows(byColumns=("a",))
    assert u.a.values == (1, 2, 3)
    assert u.b.values == (1, 1, 3)


def testInplaceColumnmodification():
    t = emzed.utils.toTable("a", [1, 2, 3, 4])
    t.a += 1
    assert t.a.values == (2, 3, 4, 5,)
    t.a *= 2
    assert t.a.values == (4, 6, 8, 10,)
    t.a /= 2
    assert t.a.values == (2, 3, 4, 5,)
    t.a -= 1
    assert t.a.values == (1, 2, 3, 4,)

    t.a.modify(lambda v: 0)
    assert t.a.values == (0, 0, 0, 0,)


def testIndex():
    t = emzed.utils.toTable("a", [1, 2, 3, 4, 5])
    t.addColumn("b", [2, 0, 1, 5, 6])
    t.sortBy("a")
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
        assert len(t.filter(e)) == v, len(t.filter(e))

    t2 = t.copy()
    assert t.join(t2, t.b < t2.a).a__0.values == (3, 4, 5, 1, 2, 3, 4, 5, 2, 3, 4, 5,)
    assert t.join(t2, t.b > t2.a).a__0.values == (1, 1, 2, 3, 4, 1, 2, 3, 4, 5,)
    assert t.join(t2, t.b <= t2.a).a__0.values == (2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 5,)
    assert t.join(t2, t.b >= t2.a).a__0.values == (1, 2, 1, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5,)

    assert t.join(t2, t.b == t2.a).a__0.values == (2, 1, 5,)
    assert t.join(t2, t.b != t2.a).a__0.values == (1, 3, 4, 5, 1, 2, 3, 4, 5, 2, 3, 4, 5, 1,
                                                   2, 3, 4, 1, 2, 3, 4, 5,)


def testBools():
    t = emzed.utils.toTable("bool", [True, False, True, None])
    assert t.bool.sum() == 2
    assert t.bool.max() is True, t.bool.max()
    assert t.bool.min() is False, t.bool.min()

    t.addColumn("int", [1, 2, 3, 4])
    t.addColumn("float", [1.0, 2, 3, 4])
    t.addColumn("int_bool", (t.bool).thenElse(t.bool, t.int))

    # test coercion (bool, int) to int:
    assert t.int_bool.values == (1, 2, 1, None,)
    t.addColumn("int_float", (t.bool).thenElse(t.int, t.float))
    assert t.int_float.values == (1.0, 2.0, 3.0, None,), t.int_float.values

    t.addColumn("bool_float", (t.bool).thenElse(t.bool, t.float))
    assert t.bool_float.values == (1.0, 2.0, 1.0, None,)


def testUniqueValue():
    t = emzed.utils.toTable("a", [1, 1, 1])
    assert t.a.uniqueValue() == 1

    t = emzed.utils.toTable("a", [1.2, 1.21, 1.19])
    assert t.a.uniqueValue(up_to_digits=1) == 1.2

    a = dict(b=3)
    b = dict(b=3)

    t = emzed.utils.toTable("a", [a, b])
    assert t.a.uniqueValue() is a


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
    assert t.a.values == (1, 2,) * 5


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


def test_removePostfixes(regtest):
    t = Table._create(["abb__0", "bcb__0"], [str] * 2, ["%s"] * 2)
    assert t.getColNames() == ["abb__0", "bcb__0"]
    t.removePostfixes()
    assert t.getColNames() == ["abb", "bcb"]
    t.removePostfixes("bb", "cb")
    assert t.getColNames() == ["a", "b"]

    t = Table._create(["abb__0", "bcb__0", "abb"], [str] * 3, ["%s"] * 3)
    with pytest.raises(Exception) as e:
        t.removePostfixes()

    print(e.value, file=regtest)


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
    t = emzed.utils.toTable("z", [1, 2], type_=int)
    t = t.join(t, True)
    # should not throw exception, as we do not create a new columns with "__" in its name:
    t.replaceColumn("z__0", t.z__0.apply(float))
    t.print_()


def test_sort_empty_table():
    t = emzed.utils.toTable("z", (), type_=int)
    print(t)
    t.sortBy("z")


def test_multi_sort(regtest):
    t = emzed.utils.toTable("x", [1, 1, 2, 2])
    t.addColumn("y", [1, 2, 3, 4])
    t.addColumn("z", [2, 1, 4, 3])

    print(t, file=regtest)

    print("x then y", file=regtest)
    t.sortBy(["x", "y"])
    print(t, file=regtest)

    print("x then z", file=regtest)
    t.sortBy(["x", "z"])
    print(t, file=regtest)

    print("y then z", file=regtest)
    t.sortBy(["y", "z"])
    print(t, file=regtest)

    print("y then x", file=regtest)
    t.sortBy(["y", "x"])
    print(t, file=regtest)

    print("z then x", file=regtest)
    t.sortBy(["z", "x"])
    print(t, file=regtest)

    print("z then y", file=regtest)
    t.sortBy(["z", "y"])
    print(t, file=regtest)

    print("x then y (desc)", file=regtest)
    t.sortBy(["x", "y"], (True, False))
    print(t, file=regtest)

    print("x then z (desc)", file=regtest)
    t.sortBy(["x", "z"], (True, False))
    print(t, file=regtest)

    print("y then z (desc)", file=regtest)
    t.sortBy(["y", "z"], (True, False))
    print(t, file=regtest)

    print("y then x (desc)", file=regtest)
    t.sortBy(["y", "x"], (True, False))
    print(t, file=regtest)

    print("z then x (desc)", file=regtest)
    t.sortBy(["z", "x"], (True, False))
    print(t, file=regtest)

    print("z then y (desc)", file=regtest)
    t.sortBy(["z", "y"], (True, False))
    print(t, file=regtest)


def test_collapse(regtest):
    t = emzed.utils.toTable("id", [1, 1, 2])
    t.addColumn("a", [1, 2, 3])
    t.addColumn("b", [3, 4, 5])
    print(1, t, file=regtest)

    t2 = t.collapse("id", efficient=False)
    t2.sortBy("id")
    assert len(t2) == 2
    assert t2.getColNames() == ["id", "collapsed"]
    assert t2.getColTypes() == [int, t.__class__]

    subs = t2.collapsed.values
    assert subs[0].getColNames() == ["id", "a", "b"]
    assert len(subs[0]) == 2
    assert subs[1].getColNames() == ["id", "a", "b"]
    assert len(subs[1]) == 1

    t2 = t.collapse("id", "a", efficient=False)
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

    print(2, t2, file=regtest)

    t2 = t.collapse("id", efficient=True)

    t2.sortBy("id")
    assert len(t2) == 2
    assert t2.getColNames() == ["id", "collapsed"]
    assert t2.getColTypes() == [int, t.__class__]

    subs = t2.collapsed.values
    assert subs[0].getColNames() == ["id", "a", "b"]
    assert len(subs[0]) == 2
    assert subs[1].getColNames() == ["id", "a", "b"]
    assert len(subs[1]) == 1

    print(3, t2, file=regtest)

    import cPickle
    tneu = cPickle.loads(cPickle.dumps(t2))
    print(4, tneu, file=regtest)
    # this cause recursion because pickling/unpickling was broken due to using slots:
    print(5, tneu.rows, file=regtest)
    ts0 = tneu.collapsed.values[0]
    ts1 = tneu.collapsed.values[1]
    print(6, ts0.a.values, file=regtest)
    print(7, ts0.b.values, file=regtest)
    print(8, ts1.a.values, file=regtest)
    print(9, ts1.b.values, file=regtest)
    print(10, ts0, file=regtest)


def test_uniuqe_id():
    ti = emzed.utils.toTable("id", [1, 1, 2])
    t = emzed.utils.toTable("t", (ti, ti, None))
    # peakmap unique id already tested by compression of peakmap:
    t.addColumn("pm", PeakMap([]), type_=object)
    t.addColumn("blob", Blob("data"))
    assert t.uniqueId() == "cb786c8bcfd7287459f8ba0b6a10cb7e845798c9fcdbea76dcb695e2c22d76a4"

    ti = emzed.utils.toTable("id", [1, 1, 2])
    t = emzed.utils.toTable("t", (ti, ti, None))
    # peakmap unique id already tested by compression of peakmap:
    t.addColumn("pm", PeakMap([]), type_=PeakMap)
    t.addColumn("blob", Blob("data"))
    assert t.uniqueId() == "a03470ffc2876f1c12becb55e5f82f4fd59d9f906afe6f07484755755c4807e0"

    ti = emzed.utils.toTable("id", [1, 1, 2])
    t = emzed.utils.toTable("t", (ti, ti, None))
    # peakmap unique id already tested by compression of peakmap:
    t.addColumn("pm", PeakMap([]))
    t.addColumn("blob", Blob("data"))
    assert t.uniqueId() == "a03470ffc2876f1c12becb55e5f82f4fd59d9f906afe6f07484755755c4807e0"


def test_ts(regtest_redirect):
    t = emzed.utils.toTable("id", [1, 1, 2])

    x = [None, 1, 2, 3, 4, None, None, 4, None]
    x = [None if xi is None else datetime.fromordinal(xi) for xi in x]

    y = [None, 11, 12, 14, 13, None, None, 100, None]
    ts = TimeSeries(x, y)
    t.addColumn("ts", ts, format_="%s")

    with regtest_redirect():
        for xi, yi in ts.for_plotting():
            print(xi, yi)
        print(TimeSeries([], []))
        print(t)
        print(t.ts[0].uniqueId())
        print(t.uniqueId())


def test_missing_values_binary_expressions():

    # column x has type None, this is a special case which failed before
    t = emzed.utils.toTable("x", [None])
    assert (t.x + t.x).values == (None,)
    assert (t.x * t.x).values == (None,)
    assert (t.x - t.x).values == (None,)
    assert (t.x / t.x).values == (None,)

    t.addColumn("y", [1])
    assert (t.x + t.y).values == (None,)
    assert (t.x * t.y).values == (None,)
    assert (t.x - t.y).values == (None,)
    assert (t.x / t.y).values == (None,)

    assert (t.y + t.x).values == (None,)
    assert (t.y * t.x).values == (None,)
    assert (t.y - t.x).values == (None,)
    assert (t.y / t.x).values == (None,)


def test_enumeration():
    t = emzed.utils.toTable("group_1", ["a", "a", "b", "b"])
    t.addColumn("group_2", (3, 3, 3, 7))

    t.addColumn("group_1_id", t.enumerateBy("group_1"), insertBefore="group_1")
    t.addColumn("group_2_id", t.enumerateBy("group_2"), insertAfter="group_1_id")
    t.addColumn("group_12_id", t.enumerateBy("group_1", "group_2"), insertAfter="group_2_id")

    assert t.getColNames() == ["group_1_id", "group_2_id", "group_12_id", "group_1", "group_2"]
    assert t.group_1_id.values == (0, 0, 1, 1)
    assert t.group_2_id.values == (0, 0, 0, 1)
    assert t.group_12_id.values == (0, 0, 1, 2)


def test_grouped_aggregate_expressions():

    # without missing values #########################################

    # int types aggregated
    t = emzed.utils.toTable("group", [1, 1, 2])
    t.addColumn("values", [1, 2, 3])
    t.addColumn("grouped_min", t.values.min.group_by(t.group))
    assert t.grouped_min.values == (1, 1, 3,)
    t.print_()

    # int types aggregated by two columns
    t = emzed.utils.toTable("group_1", [1, 1, 2, 2])
    t.addColumn("group_2", (1, 1, 1, 2))
    t.addColumn("values", [1, 2, 3, 4])
    t.addColumn("grouped_min", t.values.min.group_by(t.group_1, t.group_2))
    assert t.grouped_min.values == (1, 1, 3, 4,)
    t.print_()

    # float types aggregated
    t = emzed.utils.toTable("group", [1, 1, 2])
    t.addColumn("values", [1, 2, 3])
    t.addColumn("grouped_mean", t.values.mean.group_by(t.group))
    assert t.grouped_mean.values == (1.5, 1.5, 3,)
    t.print_()

    # str types aggregated
    t = emzed.utils.toTable("group", [1, 1, 2])
    t.addColumn("values", ["1", "2", "3"])
    t.addColumn("grouped_max", t.values.max.group_by(t.group))
    assert t.grouped_max.values == ("2", "2", "3",)
    t.print_()

    # with missing values ############################################

    # int types aggregated
    t = emzed.utils.toTable("group", [1, 1, 2])
    t.addColumn("values", [None, 2, None])
    t.addColumn("grouped_min", t.values.min.group_by(t.group))
    assert t.grouped_min.values == (2, 2, None,)
    t.print_()

    # float types aggregated
    t = emzed.utils.toTable("group", [1, 1, 2])
    t.addColumn("values", [None, 2.0, None])
    t.addColumn("grouped_min", t.values.min.group_by(t.group))
    assert t.grouped_min.values == (2.0, 2.0, None,)
    t.print_()

    # str types aggregated
    t = emzed.utils.toTable("group", [1, 1, 2])
    t.addColumn("values", [None, "2", None])
    t.addColumn("grouped_min", t.values.min.group_by(t.group))
    assert t.grouped_min.values == ("2", "2", None,)
    t.print_()

    # empty columns ##################################################

    # only None values
    t = emzed.utils.toTable("group", [1, 1, 2])
    t.addColumn("values", [None, None, None])
    t.addColumn("grouped_min", t.values.min.group_by(t.group))
    assert t.grouped_min.values == (None, None, None,)
    t.print_()

    # empty table
    t = emzed.utils.toTable("group", [])
    t.addColumn("values", [])
    t.addColumn("grouped_min", t.values.min.group_by(t.group))
    assert t.grouped_min.values == ()
    t.print_()


def test_own_aggregate_functions():

    # int types aggregated
    t = emzed.utils.toTable("group", [1, 1, 2])
    t.addColumn("values", [1, 2, 3])
    t.addColumn("grouped_min", t.values.aggregate(lambda v: min(v)).group_by(t.group))
    assert t.grouped_min.values == (1, 1, 3,)
    t.print_()
    # int types aggregated
    t = emzed.utils.toTable("group", [1, 1, 2])
    t.addColumn("values", [1, 2, 3])
    t.addColumn("grouped_min", t.values.aggregate(np.min).group_by(t.group))
    assert t.grouped_min.values == (1, 1, 3,)
    t.print_()

    def my_min(li):
        return min(li) + 42

    t.addColumn("strange", t.values.aggregate(my_min))
    assert t.strange.values == (43, 43, 43,), t.strange.values
    t.addColumn("strange2", t.values.aggregate(my_min).group_by(t.group))
    assert t.strange2.values == (43, 43, 45,), t.strange2.values

    t.print_()


def test_aggregate_types():
    t = emzed.utils.toTable("group", [1, 1, 2])
    assert type(t.group.max()) in (int, long)


def test_any_all_agg_expressions():
    t = emzed.utils.toTable("v", [0, 0])
    # pep8 would recomment "is" instead of "==" below, but py.tests assert rewriting can not
    # handle this
    assert t.v.allTrue() is False
    assert t.v.allFalse() is True
    assert t.v.anyTrue() is False
    assert t.v.anyFalse() is True

    t = emzed.utils.toTable("v", [0, 1])
    assert t.v.allTrue() is False
    assert t.v.allFalse() is False
    assert t.v.anyTrue() is True
    assert t.v.anyFalse() is True

    t = emzed.utils.toTable("v", [1, 1])
    assert t.v.allTrue() is True
    assert t.v.allFalse() is False
    assert t.v.anyTrue() is True
    assert t.v.anyFalse() is False

    t = emzed.utils.toTable("v", [None, 0, 0])
    # pep8 would recomment "is" instead of "==" below, but py.tests assert rewriting can not
    # handle this
    assert t.v.allTrue() is False
    assert t.v.allFalse() is False
    assert t.v.anyTrue() is False
    assert t.v.anyFalse() is True

    t = emzed.utils.toTable("v", [None, 0, 1])
    assert t.v.allTrue() is False
    assert t.v.allFalse() is False
    assert t.v.anyTrue() is True
    assert t.v.anyFalse() is True

    t = emzed.utils.toTable("v", [None, 1, 1])
    assert t.v.allTrue() is False
    assert t.v.allFalse() is False
    assert t.v.anyTrue() is True
    assert t.v.anyFalse() is False


def test_getitem_variations():
    t = emzed.utils.toTable("v", range(3))
    t1 = t[0:2]
    t2 = t[[0, 1]]
    t3 = t[[True, True, False]]
    t4 = t[np.array((True, True, False), dtype=bool)]
    t5 = t[np.array((0, 1), dtype=int)]

    assert t1.shape == (2, 1)
    assert t2.shape == (2, 1)
    assert t3.shape == (2, 1)
    assert t4.shape == (2, 1)
    assert t5.shape == (2, 1)

    assert t1.rows == [[0], [1]]

    for ti in (t1, t2, t3, t4, t5):
        assert ti.getColNames() == t.getColNames()
        assert ti.getColTypes() == t.getColTypes()
        assert ti.getColFormats() == t.getColFormats()
        assert ti.rows == t1.rows

    t1 = t[0:2, :]
    t2 = t[[0, 1], :]
    t3 = t[[True, True, False], :]
    t4 = t[np.array((True, True, False), dtype=bool), :]
    t5 = t[np.array((0, 1), dtype=int), :]

    assert t1.rows == [[0], [1]]

    for ti in (t1, t2, t3, t4, t5):
        assert ti.getColNames() == t.getColNames()
        assert ti.getColTypes() == t.getColTypes()
        assert ti.getColFormats() == t.getColFormats()
        assert ti.rows == t1.rows

    t.addColumn("w", t.v * 2.0)

    t1 = t[0:2, :]
    t2 = t[[0, 1], :]
    t3 = t[[True, True, False], :]
    t4 = t[np.array((True, True, False), dtype=bool), :]
    t5 = t[np.array((0, 1), dtype=int), :]

    assert t1.rows == [[0, 0.0], [1, 2.0]]

    for ti in (t1, t2, t3, t4, t5):
        assert ti.getColNames() == t.getColNames()
        assert ti.getColTypes() == t.getColTypes()
        assert ti.getColFormats() == t.getColFormats()
        assert ti.rows == t1.rows

    t1 = t[0:2, :1]
    t2 = t[[0, 1], :1]
    t3 = t[[True, True, False], :1]
    t4 = t[np.array((True, True, False), dtype=bool), :1]
    t5 = t[np.array((0, 1), dtype=int), :1]

    assert t1.rows == [[0], [1]]
    assert t1.getColNames() == ["v"]
    assert t1.getColTypes() == [int]
    assert t1.getColFormats() == ["%d"]

    for ti in (t2, t3, t4, t5):
        assert ti.getColNames() == t1.getColNames()
        assert ti.getColTypes() == t1.getColTypes()
        assert ti.getColFormats() == t1.getColFormats()
        assert ti.rows == t1.rows

    t1 = t[0:2, 0:]
    t2 = t[[0, 1], (0, 1)]
    t3 = t[[True, True, False], [True, True]]
    t4 = t[np.array((True, True, False), dtype=bool), np.array((True, True), dtype=bool)]
    t5 = t[np.array((0, 1), dtype=int), np.array((0, 1), dtype=int)]

    assert t1.rows == t.rows[:2]

    for ti in (t1, t2, t3, t4, t5):
        assert ti.getColNames() == t.getColNames()
        assert ti.getColTypes() == t.getColTypes()
        assert ti.getColFormats() == t.getColFormats()
        assert ti.rows == t1.rows

    t1 = t[0:2, 0:2]
    t2 = t[[0, 1], 0:2]

    assert t1.rows == t.rows[:2]

    for ti in (t1, t2):
        assert ti.getColNames() == t.getColNames()
        assert ti.getColTypes() == t.getColTypes()
        assert ti.getColFormats() == t.getColFormats()
        assert ti.rows == t1.rows

    t1 = t[0:2, 0:2:1]
    t2 = t[[0, 1], 0:2:1]

    assert t1.rows == t.rows[:2]

    for ti in (t1, t2):
        assert ti.getColNames() == t.getColNames()
        assert ti.getColTypes() == t.getColTypes()
        assert ti.getColFormats() == t.getColFormats()
        assert ti.rows == t1.rows

    t1 = t[:, :]

    assert t1.rows == t.rows

    for ti in (t1,):
        assert ti.getColNames() == t.getColNames()
        assert ti.getColTypes() == t.getColTypes()
        assert ti.getColFormats() == t.getColFormats()
        assert ti.rows == t1.rows

    t1 = t[::-1, ::-1]

    assert t1.rows == [r[::-1] for r in t.rows[::-1]]

    for ti in (t1,):
        assert ti.getColNames() == t.getColNames()[::-1]
        assert ti.getColTypes() == t.getColTypes()[::-1]
        assert ti.getColFormats() == t.getColFormats()[::-1]


def test_t():
    t = emzed.utils.toTable("v", range(1, 3))

    t.addColumn("a", 12 / t.v)
    assert t.a.values == (12, 6)
    t.replaceColumn("a", 12 - t.v)
    assert t.a.values == (11, 10)
    t.replaceColumn("a", 12 * t.v)
    assert t.a.values == (12, 24)
    t.replaceColumn("a", 12 + t.v)
    assert t.a.values == (13, 14)

    t.replaceColumn("a", t.v / 12)
    assert t.a.values == (0, 0)
    t.replaceColumn("a", t.v - 12)
    assert t.a.values == (-11, -10)
    t.replaceColumn("a", t.v * 12)
    assert t.a.values == (12, 24)
    t.replaceColumn("a", t.v + 12)
    assert t.a.values == (13, 14)


def test_reset_internals():
    t = emzed.utils.toTable("x", (1,), format_="%d")
    t.uniqueId()  # forces setting or unique_id in table meta dict
    assert "unique_id" in t.meta

    # brute force column rename:
    t._colNames = ["y"]
    t._colFormats = ["%2d"]
    t.resetInternals()

    # no chech if reset worked:
    assert t.y.values == (1,)
    assert not hasattr(t, "x")
    assert t.colFormatters[0](1) == " 1"
    assert t.colIndizes == {"y": 0}
    assert "unique_id" not in t.meta


def test_add_postfix():
    t = emzed.utils.toTable("x", (1,))
    t.addColumn("y", t.x + 1)

    t.addPostfix("_1")
    assert t.getColNames() == ["x_1", "y_1"]

    with pytest.raises(Exception):
        t.addPostfix("__2")

    t._addPostfix("__2")
    assert t.getColNames() == ["x_1__2", "y_1__2"]


def test_write_csv(tmpdir, regtest):
    t = emzed.utils.toTable("a", (1, 2), format_="%03d")
    t.addColumn("b", (2, 3), format_=None)

    path = tmpdir.join("1.csv").strpath
    t.storeCSV(path, as_printed=True)
    regtest.write(open(path).read())

    path = tmpdir.join("1.csv").strpath
    t.storeCSV(path, as_printed=False)
    regtest.write(open(path).read())


def test_div_by_zeros():
    t = emzed.utils.toTable("x", (1, 0,))
    assert (t.x / t.x).values == (1, None)
    assert (t.x / 0).values == (None, None)
    assert (0 / t.x).values == (0, None)
    assert (t.x / 0.0).values == (None, None)
    assert (0.0 / t.x).values == (0, None)

    t = emzed.utils.toTable("x", (1.0, 0.0,))
    assert (t.x / t.x).values == (1, None)
    assert (t.x / 0).values == (None, None)
    assert (0 / t.x).values == (0, None)
    assert (t.x / 0.0).values == (None, None)
    assert (0.0 / t.x).values == (0, None)


def test_empty_median():
    t = emzed.utils.toTable("x", ())
    assert t.x.median() is None


def test_enhanced_dropcolumns():
    t = emzed.utils.toTable("x", ())
    t.addColumn("y", None)
    t.addColumn("x2", None)
    assert t.getColNames() == ["x", "y", "x2"]

    t.dropColumns("z*")
    assert t.getColNames() == ["x", "y", "x2"]

    t.dropColumns("z*", "x*")
    assert t.getColNames() == ["y"]

    t.dropColumns("z*", "x*")
    assert t.getColNames() == ["y"]

    with pytest.raises(Exception):
        t.dropColumns("x")

    with pytest.raises(Exception):
        t.dropColumns("x", "x*")


def test_col_name_trans(regtest):
    t = emzed.utils.toTable("x", ())
    t.addColumn("y", ())
    import string

    t.transformColumnNames(string.upper)
    assert t.getColNames() == ["X", "Y"]

    with pytest.raises(Exception) as e:
        t.transformColumnNames(lambda s: "xx")

    print(e.value, file=regtest)


def test_expr_to_iter():
    t = emzed.utils.toTable("x", (1, 2, 3.0))

    assert tuple(t.x + 1) == (2, 3, 4.0)


def test_slicing():
    t = emzed.utils.toTable("x", (1, 2, 3.0))
    assert t.x[:] == t.x.values
    assert t.x[:0] == ()


def test_vertical_split(regtest):
    t = emzed.utils.toTable("x", (1, 2, 3.0), type_=int)
    t.addColumn("xi", (1, None, -1), type_=int, format_="%03d")
    t.addColumn("yi", 1.0, type_=float, format_="%.7e")

    t1, t2 = t.splitVertically("x")
    print(t1, t2, file=regtest)
    t1, t2 = t.splitVertically("x*")
    print(t1, t2, file=regtest)
    t1, t2 = t.splitVertically(["x", "xi"])
    print(t1, t2, file=regtest)
    t1, t2 = t.splitVertically("?i")
    print(t1, t2, file=regtest)

    t1, t2 = t.splitVertically("abc")
    print(t1, t2, file=regtest)
    assert t1.shape == (3, 0)
    assert t2.shape == (3, 3)

    t_empty = t.filter(t.x == -1)
    assert t_empty.shape == (0, 3)

    assert t1.shape == (3, 0)
    t1, t2 = t_empty.splitVertically("x")
    print(t1, t2, file=regtest)


def test_iter(regtest):

    t = emzed.utils.toTable("x", (1, 2, 3.0), type_=int)
    t.addColumn("yi", "1.0", type_=str, format_="%5s", insertAfter="x")
    t.addColumn("xi", (1, None, -1), type_=int, format_="%03d", insertBefore=1)

    # we record the ids of the internal dict to make sure that this is only created
    # once per iteration over t, which saves a huge amount of memory !
    ids = set()

    print(file=regtest)
    print(t, file=regtest)
    print(file=regtest)

    for i, row in enumerate(t):
        ids.add(id(row._dict))
        assert len(row) == 3

        assert row.x in (1, 2, 3.0)
        assert row.xi in (1, None, -1)
        assert row.yi == "1.0"

        assert row["x"] == row.x
        assert row["xi"] == row.xi
        assert row["yi"] == row.yi

        assert row[0] == row.x
        assert row[1] == row.xi
        assert row[2] == row.yi

        print(file=regtest)
        print("iter", i, file=regtest)
        print("row %d before modification is" % i, row, file=regtest)

        row[0] = 4711
        row.yi = "42"
        print("row %d after modification is" % i, row, file=regtest)
        print("table is\n", t, file=regtest)
        print(file=regtest)
        print("row copy is", row[:], file=regtest)
        print("row[:-1] is", row[:-1], file=regtest)
        print("row[1:] is", row[1:], file=regtest)
        print("row[1:3] is", row[1:3], file=regtest)
        print("keys=", row.keys(), file=regtest)
        print("values=", row.values(), file=regtest)
        print("items=", row.items(), file=regtest)
        print("as list=", list(row), file=regtest)
        print("as str=", str(row), file=regtest)
        print(file=regtest)

    print(t, file=regtest)

    # we changed the table in place, now check this:

    assert len(ids) == 1

    # we record the ids of the internal dict again to make sure that _dict is a different one
    # as before, but still unique for the iteration:
    for row in t:
        print(row)
        ids.add(id(row._dict))
        assert len(row) == 3

        assert row.x == 4711
        assert row.xi in (1, None, -1)
        assert row.yi == "42"

        assert row["x"] == row.x
        assert row["xi"] == row.xi
        assert row["yi"] == row.yi

        assert row[0] == row.x
        assert row[1] == row.xi
        assert row[2] == row.yi

    for a, b, c in t:
        print(a, b, c, file=regtest)

    assert len(ids) == 2


def test_all_none():
    t = emzed.utils.toTable("a", (1, 2, None))
    assert t.a.allNone() is False

    t = emzed.utils.toTable("a", (None, None, None))
    assert t.a.allNone() is True


def test_all_x():
    t = emzed.utils.toTable("a", ())
    assert t.a.allNone() is True
    assert t.a.allFalse() is True
    assert t.a.allTrue() is True

    t = emzed.utils.toTable("a", (None, None))
    assert t.a.allNone() is True
    assert t.a.allFalse() is False
    assert t.a.allTrue() is False


def test_any_x():
    t = emzed.utils.toTable("a", ())
    assert t.a.anyNone() is False
    assert t.a.anyFalse() is False
    assert t.a.anyTrue() is False

    t = emzed.utils.toTable("a", (None, None))
    assert t.a.anyNone() is True
    assert t.a.anyFalse() is False
    assert t.a.anyTrue() is False


def test_new_apply(regtest):
    t = emzed.utils.toTable("a", (1, 2, None), type_=float)
    t.addColumn("b", t.a + 1.0, type_=float)

    def add(a, b):
        return a + b

    def any_none(a, b):
        return a is None or b is None

    t.addColumn("sum", t.apply(add, (t.a, t.b)))
    t.addColumn("b+1", t.apply(add, (1.0, t.b)))
    t.addColumn("a+3", t.apply(add, (t.a, 3.0)))
    t.addColumn("four", t.apply(add, (1.0, 3.0)))

    t.addColumn("n", (None, 1, 2), type_=int)
    t.addColumn("a_or_n_is_none", t.apply(any_none, (t.a, t.n), keep_nones=True), type_=bool)
    print(t, file=regtest)


def test_method_call(regtest):
    t = emzed.utils.toTable("a", ("1", "23", None))
    t.addColumn("l", t.a.callMethod("__len__"), type_=int)
    t.addColumn("x", t.a.callMethod("startswith", ("1",)), type_=bool)
    print(t, file=regtest)

    class Counter(object):

        def __init__(self):
            self.counter = 0

        def up(self):
            self.counter += 1

    cc = Counter()
    t.addColumn("cc", cc)
    t.cc.callMethod("up")

    assert cc.counter == 3

    t = t.filter(t.a.callMethod("__len__") > 1)
    t = t.filter(t.a.callMethod("startswith", ("2",)))
    print(t, file=regtest)


def test_relative_path_computation(regtest):

    def _test(a, b):
        print("from=", a, file=regtest)
        print("to=", b, file=regtest)
        result = relative_path(a, b)
        print("relative_path=", result, file=regtest)
        print(os.path.normpath(os.path.join(a, result)), file=regtest)
        print(file=regtest)

    _test("/a/b/c/", "/a/b/x/y/proxies/d.proxy")
    _test("/z/b/c/", "/a/b/x/y/proxies/d.proxy")
    _test("/a/b/c/d/e", "/a/b/c/d/proxies/d.proxy")
    _test("/", "/a/b/x/y/proxies/d.proxy")
    _test("/", "/d.proxy")
    _test("/a/", "/d.proxy")


def test_postfix_cleanup(regtest):

    t = emzed.utils.toTable("a", (1,), type_=int)
    t.addColumn("b", 2, type_=int)

    t2 = t[:]
    tn = t.join(t2, t.a == t2.a)

    print(tn, file=regtest)
    tn.cleanupPostfixes()
    print(tn, file=regtest)

    tn.dropColumns("b")
    tn.cleanupPostfixes()
    print(tn, file=regtest)


def test_overwrite(regtest):
    t1 = emzed.utils.toTable("a", (1,), type_=int)
    t2 = emzed.utils.toTable("a", (3, 4), type_=int)

    t1.overwrite(t2)
    assert t1.a.values == (3, 4)

    # test if no refs are introduced:
    t2.addRow([5])
    assert t1.a.values == (3, 4)

    t2 = emzed.utils.toTable("a", (), type_=int)
    t1.overwrite(t2)
    assert t1.a.values == ()

    t2 = emzed.utils.toTable("b", (1, ), type_=int)
    with pytest.raises(Exception):
        t1.overwrite(t2)

    t2 = emzed.utils.toTable("a", (1.0,), type_=float)
    with pytest.raises(Exception):
        t1.overwrite(t2)


def test_set_cell_value(regtest):

    t = emzed.utils.toTable("a", (0, 0, 0), type_=int)
    t.addColumn("b", t.a.apply(str), type_=str)
    t.addColumn("c", t.a.apply(float), type_=float)

    t0 = t.copy()

    t0.setCellValue(0, 0, 42)
    assert t0.getValues(t0.rows[0]).a == 42
    t0.setCellValue(1, 0, 42.1)
    assert t0.getValues(t0.rows[1]).a == 42
    t0.setCellValue(2, 0, "42")
    assert t0.getValues(t0.rows[2]).a == 42
    with pytest.raises(ValueError):
        t0.setCellValue(0, 0, "hello")

    t0.setCellValue(0, 1, 42)
    assert t0.getValues(t0.rows[0]).b == "42"
    t0.setCellValue(1, 1, 42.1)
    assert t0.getValues(t0.rows[1]).b == "42.1"
    t0.setCellValue(2, 1, "42")
    assert t0.getValues(t0.rows[2]).b == "42"

    t0 = t.copy()
    t0.setCellValue([0], 0, [42])
    print(t0, file=regtest)

    t0 = t.copy()
    t0.setCellValue(0, [0], [42])
    print(t0, file=regtest)

    t0 = t.copy()
    t0.setCellValue([0], [0], [[42]])
    print(t0, file=regtest)

    t0 = t.copy()
    t0.setCellValue([0], [0, 2], [[42, 43]])
    print(t0, file=regtest)

    t0 = t.copy()
    t0.setCellValue([0, 2], [0], [[42], [43]])
    print(t0, file=regtest)

    t0 = t.copy()
    t0.setCellValue([0, 2], [0, 2], [[42, 43], [11, 12]])
    print(t0, file=regtest)

    t0 = t.copy()
    t0.setCellValue([0, 2], 0, 1234)
    print(t0, file=regtest)


def test_selected_replacements(regtest):
    t = emzed.utils.toTable("a", (0, 0, 0), type_=int)
    t.addColumn("b", t.a.apply(str), type_=str)
    t.addColumn("c", t.a.apply(float), type_=float)
    print(t, file=regtest)

    t.replaceSelectedRows("a", 2, (0, 2))
    print(t, file=regtest)

    t.replaceSelectedRows("a", None, (0, 2))
    print(t, file=regtest)

    t.replaceSelectedRows("b", "2", (0, 2))
    print(t, file=regtest)
    t.replaceSelectedRows("b", None, (0, 2))
    print(t, file=regtest)

    t.replaceSelectedRows("c", 2.0, (0, 2))
    print(t, file=regtest)
    t.replaceSelectedRows("c", None, (0, 2))
    print(t, file=regtest)


def test_selected_col_values(regtest):
    t = emzed.utils.toTable("a", (0, 0, None), type_=int)
    t.addColumn("b", t.a.apply(str), type_=str)

    v = t.selectedRowValues("a", (0, 2))
    print(v, file=regtest)

    v = t.selectedRowValues("b", (0, 2))
    print(v, file=regtest)


def test_append(regtest):
    t = emzed.utils.toTable("a", (0, 0, None), type_=int)
    t0 = emzed.utils.toTable("b", (0, 0, None), type_=int)
    t.appendTable(t0)
    print(t, file=regtest)
