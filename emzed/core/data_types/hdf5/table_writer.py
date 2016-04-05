import itertools

from tables import (open_file, UInt64Col, Int64Col, UInt32Col, Float64Col, BoolCol, Filters)

from store_manager import setup_manager


def append_to_hdf5(table, path):

    file_ = open_file(path, mode="w")
    filters = Filters(complib="blosc", complevel=9)

    store, fetch, finalize = setup(file_)


def to_hdf5(table, path):

    file_ = open_file(path, mode="w")
    filters = Filters(complib="blosc", complevel=9)

    store, fetch, finalize = setup(file_)

    meta_table = file_.create_table(file_.root, "meta_index",
                                    description=dict(index=UInt64Col()),
                                    filters=filters)

    missing_values = file_.create_table(file_.root, "missing_values",
                                        description=dict(row_index=UInt64Col(pos=0),
                                                         col_index=UInt64Col(pos=1)),
                                        filters=filters)

    def store_meta(what):
        meta_index = store(what)
        row = meta_table.row
        row["index"] = meta_index
        row.append()

    col_names = table.getColNames()
    col_types = table.getColTypes()
    col_formats = table.getColFormats()

    store_meta(table.meta)
    store_meta(col_names)
    store_meta(col_types)
    store_meta(col_formats)

    basic_type_map = {int: Int64Col, long: Int64Col, float: Float64Col, bool: BoolCol}

    description = {}
    for (pos, name, type_) in zip(itertools.count(), col_names, col_types):
        tables_type = basic_type_map.get(type_)
        if tables_type is None:
            tables_type = UInt32Col
        description[name] = tables_type(pos=pos)

    row_table = file_.create_table(file_.root, "rows", description=description,
                                   filters=filters)

    for row_index, row in enumerate(table.rows):
        hdf_row = row_table.row
        for col_index, value, name, type_ in zip(itertools.count(), row, col_names, col_types):
            if value is None:
                m_row = missing_values.row
                m_row["row_index"] = row_index
                m_row["col_index"] = col_index
                m_row.append()
            else:
                if type_ in basic_type_map:
                    hdf_row[name] = value
                else:
                    hdf_row[name] = store(value)
        hdf_row.append()

    finalize()
    meta_table.flush()
    missing_values.flush()
    row_table.flush()

    file_.close()


def main():
    import contextlib
    import time

    @contextlib.contextmanager
    def measure(title=""):
        if title:
            title = " " + title
        print("start%s" % title)
        started = time.time()
        yield
        needed = time.time() - started
        print("running%s needed %.2f seconds" % (title, needed))

    import emzed

    with measure("load pm"):
        pm = emzed.io.loadPeakMap("141208_pos001.mzXML")

    import copy
    # create modified copy
    pm2 = copy.deepcopy(pm)
    pm2.spectra = pm2.spectra[1:]

    pms = [pm, pm2]

    n = 10000
    integers = list(reversed(range(n)))
    for k in range(0, n, 10):
        integers[k] = None


    from numpy.random import randint, random as np_random
    import random

    tuples = [tuple(randint(0, 1000, size=10)) for _ in range(100)]

    with measure("create table"):
        t = emzed.utils.toTable("integers", integers, type_=int)
        t.addColumn("mzmin", t.apply(lambda: 100 + 900 * np_random() + np_random(), ()), type_=float)
        t.addColumn("mzmax", t.apply(lambda mzmin: mzmin + 0.1 * np_random(), (t.mzmin,)), type_=float)

        t.addColumn("rtmin", t.apply(lambda: 50 + 1000 * np_random(), ()), type_=float)
        t.addColumn("rtmax", t.apply(lambda rtmin: rtmin + 10 + 60 * np_random(), (t.rtmin,)), type_=float)
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
