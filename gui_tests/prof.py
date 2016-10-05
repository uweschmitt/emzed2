# encoding: utf-8
from __future__ import print_function, division

from emzed.core.data_types import Hdf5TableProxy, to_hdf5
from emzed.core.data_types.hdf5_table_proxy import UfuncWrapper

from emzed.utils import toTable
import numpy as np

try:
    profile
except NameError:

    import functools
    import time

    def profile(function):

        @functools.wraps(function)
        def wrapped(*a, **kw):
            started = time.time()
            try:
                return function(*a, **kw)
            finally:
                print("%s needed %.2f seconds" % (function.__name__, time.time() - started))
        return wrapped


def test_perm():
    t = toTable("a", (1, 1, 2, 2, None), type_=int)
    t.addColumn("d", (4, 4, 2, 1, None), type_=str)
    to_hdf5(t, "abc.hdf5")

    prox = Hdf5TableProxy("abc.hdf5")

    t = prox.toTable()

    perm = prox.sortPermutation(("a", "d"), (True, True))
    print(t[perm])

    perm = prox.sortPermutation(("a", "d"), (False, True))
    print(t[perm])

    perm = prox.sortPermutation(("a", "d"), (True, False))
    print(t[perm])

    perm = prox.sortPermutation(("a", "d"), (False, False))
    print(t[perm])

    perm = prox.sortPermutation("a", True)
    print(perm)
    print(t[perm])

    perm = prox.sortPermutation("a", False)
    print(perm)
    print(t[perm])


def t():
    a = ["a", "bc", "d", "ef", "a", "b"] * 1000

    @profile
    def t0(a=a):
        for i in range(0, len(a), 3):
            a[i] = None

    @profile
    def t1(a=a):
        a = np.array(a, dtype=object)
        a[::3] = None

    t0()
    t1()

if 0:
    import time
    for name in ("test_1000000.hdf5", "test_100000.hdf5", "test_10000.hdf5"):
        prox = Hdf5TableProxy(name)
        started = time.time()
        prox.sortPermutation(("strings_0",))
        print(time.time() - started, "seconds for sorting strings_0, table size", len(prox))
        started = time.time()
        prox.sortPermutation(("strings_0",))
        print(time.time() - started, "seconds for sorting strings_0 again, table size", len(prox))
        print()
        started = time.time()
        prox.sortPermutation(("integers",))
        print(time.time() - started, "seconds for sorting integers, table size", len(prox))
        started = time.time()
        prox.sortPermutation(("integers",))
        print(time.time() - started, "seconds for sorting integers again, table size", len(prox))
        print()

else:
    #prox = Hdf5TableProxy("pm_only.hdf5")
    prox = Hdf5TableProxy("test_1000000.hdf5")
    print(len(prox))
    prox.info()
    v1 = "10"
    v2 = "10000"
    f = UfuncWrapper(lambda vec, v1=v1, v2=v2: np.logical_and(
        np.greater(v2, vec), np.greater(vec, v1)))
    import fnmatch
    f = np.vectorize(lambda s: s is not None and fnmatch.fnmatch(s, "target*"))
    f = np.vectorize(lambda s: s is not None and s.startswith("target"))

    @profile
    def run():
        prox.findMatchingRows([("target_id", f)])
        prox.findMatchingRows([("target_id", f)])
    run()

    # pm = prox.rows[0][6]
    #@profile
    def run():
        print(pm)
        pm.sample_peaks(1088.33622354351, 1367.6245046237466, 636.8035228441362, 636.8039141375544,
                        3000, 1)
        pm.chromatogram(636.8035228441362, 636.8039141375544, 1088.33622354351, 1367.6245046237466)
        # pm.sample_peaks(1112.8111908544108, 1241.240507095392, 157.43532418668036, 157.50834174873089, 3000, 1)
        #profile(pm.sample_peaks)(483, 1656, 357.97, 358.05, 1000, 1)
    # run()
