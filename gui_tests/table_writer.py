import emzed
import copy
from numpy.random import randint, random as np_random
import random
import contextlib
import time


from emzed.core.data_types.hdf5_table_writer import to_hdf5


def main():

    @contextlib.contextmanager
    def measure(title=""):
        if title:
            title = " " + title
        print("start%s" % title)
        started = time.time()
        yield
        needed = time.time() - started
        print("running%s needed %.2f seconds" % (title, needed))

    with measure("load pm"):
        pm = emzed.io.loadPeakMap("141208_pos001.mzXML")

    # create modified copy
    pm2 = copy.deepcopy(pm)
    pm2.spectra = pm2.spectra[1:]

    pms = [pm, pm2]

    n = 10000
    integers = list(reversed(range(n)))
    for k in range(0, n, 10):
        integers[k] = None

    tuples = [tuple(randint(0, 1000, size=10)) for _ in range(100)]

    with measure("create table"):
        t = emzed.utils.toTable("integers", integers, type_=int)
        t.addColumn(
            "mzmin", t.apply(lambda: 100 + 900 * np_random() + np_random(), ()), type_=float)
        t.addColumn(
            "mzmax", t.apply(lambda mzmin: mzmin + 0.1 * np_random(), (t.mzmin,)), type_=float)

        t.addColumn("rtmin", t.apply(lambda: 50 + 1000 * np_random(), ()), type_=float)
        t.addColumn(
            "rtmax", t.apply(lambda rtmin: rtmin + 10 + 60 * np_random(), (t.rtmin,)), type_=float)
        t.addColumn("peakmap", t.apply(lambda: random.choice(pms), ()), type_=object)

        for i in range(30):
            t.addColumn("floats_%d" % i, t.integers + 1.1, type_=float)
            t.addColumn("strings_%d" % i, t.integers.apply(str) * (i % 3), type_=str)
            t.addColumn("tuples_%d" % i, t.apply(lambda: random.choice(tuples), ()), type_=object)
            t.addColumn("peakmaps_%d" % i, pms[i % 2], type_=object)

    with measure("write hdf5 table with %d rows and %d cols" % t.shape):
        to_hdf5(t, "test.hdf5")

if __name__ == "__main__":
    main()
