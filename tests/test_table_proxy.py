# encoding: utf-8
from __future__ import print_function


def test_0():
    import emzed
    t = emzed.utils.toTable("a", (1,2,3), type_=int)
    t0 = t.buildEmptyClone()
    print(t)
    t2 = t.view((0,))
    t2.replaceColumn("a", 3)
    print(t2)
    print(t2.a.values)
    print(t)
    t0 += t2
    t0 += t2
    t0 += t
    print(t0)
