from emzed.core.data_types.expressions import Value, le, gt, lt, ge
import numpy as np

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
