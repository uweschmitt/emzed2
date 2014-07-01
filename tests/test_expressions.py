from emzed.core.data_types.expressions import Value, le, gt, lt, ge
import numpy as np

import emzed
from emzed.core.data_types import col_types
import os

def test_if_all_operators_are_defined():

    v1 = Value(1)
    v2 = Value(2)

    v3=v1+v2
    v4=v1-v2
    v5=v1*v2
    v6=v1/v2

    t1 = v1 <= v2
    t2 = v1 < v2
    t3 = v1 >= v2
    t4 = v1 > v2
    t5 = v1 == v2
    t6 = v1 != v2

    t7 = t1 & t2
    t8 = t1 | t2
    t9 = t1 ^ t2

    assert t9 is not  None

def test_efficient_comparators():

    a=np.arange(5)
    assert le(a,0.5)  == 0
    assert le(a,1)    == 1
    assert le(a,1.5)  == 1
    assert le(a,3.5)  == 3
    assert le(a,4.0)  == 4
    assert le(a,5.0)  == 4
    assert ge(a,-1)   == 0 
    assert ge(a,0)    == 0
    assert ge(a,0.5)  == 1
    assert ge(a,1)    == 1
    assert ge(a,1.5)  == 2
    assert ge(a,3.5)  == 4
    assert ge(a,4.0)  == 4
    assert ge(a,5.0)  == 5 
    assert lt(a,-1)   == -1
    assert lt(a,0)    == -1
    assert lt(a,0.5)  == 0
    assert lt(a,1)    == 0
    assert lt(a,1.5)  == 1
    assert lt(a,3.5)  == 3
    assert lt(a,4.0)  == 3
    assert lt(a,5.0)  == 4
    assert gt(a,-1)   == 0
    assert gt(a,0)    == 1
    assert gt(a,0.5)  == 1
    assert gt(a,1)    == 2
    assert gt(a,1.5)  == 2
    assert gt(a,3.5)  == 4
    assert gt(a,4.0)  == 5
    assert gt(a,5.0)  == 5


def test_load_binary():
    here = os.path.dirname(os.path.abspath(__file__))
    png_path = os.path.join(here, "data", "test.png")
    t = emzed.utils.toTable("path", [png_path])
    value, = t.path.loadFileFromPath().values
    assert isinstance(value, col_types.Blob)
    assert value.type_ == "PNG"
    assert len(value.data) > 0
    assert value.uniqueId() == "487cd4e56a15e16622dd2daa781324d57129b709c39ad95eb556e3e939aa40a4"


def test_logical_with_Nones_1():
    t = emzed.utils.toTable("a", [None, True, False])
    t.addColumn("b", [None, None, False])
    t.addColumn("a_and_b", t.a & t.b)
    t.addColumn("a_or_b", t.a | t.b)
    t.addColumn("a_xor_b", t.a ^ t.b)
    t.addColumn("not_a", ~t.a)

    assert t.a_and_b.values == (None, None, False)
    assert t.a_or_b.values == (None, True, False)
    assert t.a_xor_b.values == (None, None, False)
    assert t.not_a.values == (None, False, True)


def test_logical_with_Nones_2():
    t = emzed.utils.toTable("a", [None, True, False])
    t.addColumn("a_and_none", t.a & None)
    t.addColumn("a_or_none", t.a | None)
    t.addColumn("a_xor_none", t.a ^ None)
    t.addColumn("none_and_a", Value(None) & t.a)
    t.addColumn("none_or_a", Value(None) | t.a)
    t.addColumn("none_xor_a", Value(None) ^ t.a)

    assert t.a_and_none.values == (None, None, False)
    assert t.a_or_none.values == (None, True, None)
    assert t.a_xor_none.values == (None, None, None)
    assert t.none_and_a.values == t.a_and_none.values
    assert t.none_or_a.values == t.a_or_none.values
    assert t.none_xor_a.values == t.a_xor_none.values
