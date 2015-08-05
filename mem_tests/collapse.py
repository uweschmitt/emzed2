# encoding: utf-8
from __future__ import print_function

import emzed

try:
    profile
except:
    def profile(fun):
        return fun

@profile
def test():
    m = 1000
    n = 50

    t = emzed.utils.toTable("id", range(m))
    for ni in range(n):
        name = chr(ord("a") + ni)
        t.addColumn(name, m * (5 * name,), type_=str)

    tn = t.collapse("id")

    tn = t.collapse("id", efficient=True)

    import time
    time.sleep(1.0)  # to make sure that memory mesaurement does not lack behind


test()

