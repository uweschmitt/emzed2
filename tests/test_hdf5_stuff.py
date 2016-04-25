# encoding: utf-8, division
from __future__ import print_function, division

import os
import tempfile

from datetime import datetime

import numpy as np

from emzed.core.data_types import TimeSeries
from emzed.core.data_types.hdf5_table_writer import to_hdf5, append_to_hdf5, atomic_hdf5_writer
from emzed.core.data_types.hdf5_table_proxy import Hdf5TableProxy, ObjectProxy, PeakMapProxy
from emzed.core.data_types.ms_types import PeakMap, Spectrum

from emzed.core.data_types.hdf5.accessors import (Hdf5TableWriter, Hdf5TableAppender,
                                                  Hdf5TableReader)

from emzed.core.data_types.hdf5.stores import (BitMatrix,)


from emzed.utils import toTable

from pytest import fixture, raises, yield_fixture


@fixture()
def table():

    peaks_0 = np.arange(20.0).reshape(-1, 2)
    peaks_1 = np.arange(30.0).reshape(-1, 2)

    spec_0 = Spectrum(peaks_0[:], 30.0, 1, "+")
    spec_1 = Spectrum(peaks_1[:], 30.0, 2, "+", [(10, 1000)])
    spec_2 = Spectrum(peaks_1[:], 40.0, 1, "+")

    pm = PeakMap([spec_0, spec_1, spec_2])

    t0 = toTable("int", (None, 2, 3, 3, None), type_=int)
    t0.addColumn("float", (1.0, 2.0, 4.0, 3.0, None), type_=float)
    t0.addColumn("bool", (True, False, None, True, False), type_=bool)
    t0.addColumn("str", ("1", "2" * 100, None, "a", "b"), type_=str)
    t0.addColumn("object", ({1}, dict(a=2), None, (1,), [1, 2]), type_=object)
    t0.addColumn("peakmap", pm, type_=object)
    t0.addColumn("i1", [1, None, 2, None, 3], type_=int)
    t0.addColumn("i2", [None, 1, None, 2, None], type_=int)

    n = 10
    ts_0 = TimeSeries(map(datetime.fromordinal, range(1, n + 1)), range(n), "label1")
    ts_0.x[3] = None
    ts_0.y[3] = np.nan

    n = 10
    ts_1 = TimeSeries(map(datetime.fromordinal, range(1000,  n + 1000)),
                      range(1000, 1000 + n), "label2", [bool(i % 4) for i in range(n)])

    t0.addColumn("time_series", [ts_0, ts_0, ts_1, ts_1, None], type_=TimeSeries)

    t0.meta = {"a": "b"}
    return t0


@yield_fixture()
def tproxy(table):

    folder = tempfile.mkdtemp()
    path = os.path.join(folder, "t.hdf5")
    to_hdf5(table, path)

    tproxy = Hdf5TableProxy(path)
    yield tproxy
    tproxy.close()


def test_writer_appender_reader(table, tmpdir, regtest):

    path = tmpdir.join("test.hdf5").strpath
    writer = Hdf5TableWriter(path)
    writer.write_table(table)
    writer.close()

    appender = Hdf5TableAppender(path)
    appender.append_table(table)
    appender.append_table(table)
    appender.close()

    reader = Hdf5TableReader(path)
    assert len(reader) == 3 * len(table)
    rows = list(reader)

    # resolve proxies:
    rows = [[ci.load() if isinstance(ci, ObjectProxy) else ci for ci in row] for row in rows]

    # check if appending worked:
    assert rows[:5] == rows[5:10]
    assert rows[5:10] == rows[10:]

    for col in reader.col_names:
        print(reader.get_col_values(col), file=regtest)

    reader.close()


def test_hdf5_table_appender(table, tmpdir):
    path = tmpdir.join("test.hdf5").strpath
    to_hdf5(table, path)
    append_to_hdf5([table, table, table], path)


def test_atomic_hdf5_writer(table, tmpdir, regtest):
    path = tmpdir.join("test.hdf5").strpath
    with atomic_hdf5_writer(path) as add:
        add(table)
        table.replaceColumn("int", table.int + 10, type_=int)
        add(table)
        table.replaceColumn("int", table.int + 10, type_=int)
        add(table)
        table.replaceColumn("int", table.int + 10, type_=int)

    t = Hdf5TableProxy(path).toTable()
    print(t.int.values, file=regtest)


def test_round_trip(tproxy, table, regtest):
    # test roundtrip:
    t1 = tproxy.toTable()
    assert t1.uniqueId() == table.uniqueId()
    assert t1.meta == table.meta

    for pm0, pm1 in zip(t1.peakmap, table.peakmap):
        assert isinstance(pm0, PeakMapProxy)
        assert isinstance(pm1, PeakMap)
        rt0, ii0 = pm0.chromatogram(0, 1000, 0, 1000)   # fetch lazy
        rt1, ii1 = pm1.chromatogram(0, 1000, 0, 1000)   # data is in memory
        assert np.all(rt0 == rt1)
        assert np.all(ii0 == ii1)

    print(t1, file=regtest)
    return


def test_get_index(tproxy):

    # test getIndex method
    assert tproxy.getIndex("int") == 0
    assert tproxy.getIndex("object") == 4

    with raises(Exception):
        tproxy.getIndex("hih")


def test_row_attribute(tproxy, regtest):
    # test row attribute
    for row in tproxy.rows:
        print(row, file=regtest)


def test_row_write_cell(tproxy, regtest):
    # test row attribute
    tproxy.setCellValue(0, 0, 4711)

    t = tproxy.toTable()
    t.dropColumns("time_series", "object", "peakmap")
    print(t, file=regtest)

    # make sure that row 0 is cached, and test again:
    tproxy[0]
    tproxy.setCellValue(0, 0, 4712)
    t = tproxy.toTable()
    t.dropColumns("time_series", "object", "peakmap")
    print(t, file=regtest)

    tproxy.setCellValue(4, 0, 4713)
    t = tproxy.toTable()
    t.dropColumns("time_series", "object", "peakmap")
    print(t, file=regtest)

    tproxy.setCellValue(4, 0, None)
    t = tproxy.toTable()
    t.dropColumns("time_series", "object", "peakmap")
    print(t, file=regtest)

    tproxy.setCellValue(4, 0, 4713)
    t = tproxy.toTable()
    t.dropColumns("time_series", "object", "peakmap")
    print(t, file=regtest)

    tproxy.setCellValue(4, 0, None)
    t = tproxy.toTable()
    t.dropColumns("time_series", "object", "peakmap")
    print(t, file=regtest)

    tproxy.setCellValue(0, 3, "4713")
    t = tproxy.toTable()
    t.dropColumns("time_series", "object", "peakmap")
    print(t, file=regtest)

    tproxy.setCellValue(0, 3, None)
    t = tproxy.toTable()
    t.dropColumns("time_series", "object", "peakmap")
    print(t, file=regtest)


def test_sort_by(tproxy, regtest):
    # test sortBy
    perm = tproxy.sortPermutation("int", True)
    print(perm, file=regtest)
    print(tproxy.toTable()[perm], file=regtest)

    perm = tproxy.sortPermutation("int", False)
    print(perm, file=regtest)
    print(tproxy.toTable()[perm], file=regtest)

    perm = tproxy.sortPermutation(("int", "float"), (True, True))
    print(perm, file=regtest)
    print(tproxy.toTable()[perm], file=regtest)

    perm = tproxy.sortPermutation(("int", "float"), (True, False))
    print(perm, file=regtest)
    print(tproxy.toTable()[perm], file=regtest)


def test_replace_column(tproxy, regtest):

    tproxy.replaceColumn("int", 2)
    print(tproxy.toTable().extractColumns("int", "float", "bool", "str"), file=regtest)

    tproxy.replaceColumn("int", None)
    print(tproxy.toTable().extractColumns("int", "float", "bool", "str"), file=regtest)

    tproxy.replaceColumn("int", 1)
    print(tproxy.toTable().extractColumns("int", "float", "bool", "str"), file=regtest)

    tproxy.replaceColumn("int", 3)
    print(tproxy.toTable().extractColumns("int", "float", "bool", "str"), file=regtest)

    tproxy.replaceColumn("int", None)
    print(tproxy.toTable().extractColumns("int", "float", "bool", "str"), file=regtest)

    tproxy.replaceColumn("int", 3)
    print(tproxy.toTable().extractColumns("int", "float", "bool", "str"), file=regtest)


def test_replace_column_2(tproxy, regtest):
    tproxy.replaceColumn("str", "2")
    print(tproxy.toTable().extractColumns("int", "float", "bool", "str"), file=regtest)

    tproxy.replaceColumn("str", None)
    print(tproxy.toTable().extractColumns("int", "float", "bool", "str"), file=regtest)

    tproxy.replaceColumn("str", "1")
    print(tproxy.toTable().extractColumns("int", "float", "bool", "str"), file=regtest)

    tproxy.replaceColumn("str", "3")
    print(tproxy.toTable().extractColumns("int", "float", "bool", "str"), file=regtest)

    tproxy.replaceColumn("str", None)
    print(tproxy.toTable().extractColumns("int", "float", "bool", "str"), file=regtest)

    tproxy.replaceColumn("str", "3")
    print(tproxy.toTable().extractColumns("int", "float", "bool", "str"), file=regtest)


def test_replace_column_3(tproxy, regtest):

    tproxy.replaceSelectedRows("int", 2, range(5))
    print(tproxy.toTable().extractColumns("int", "float", "bool", "str"), file=regtest)

    tproxy.replaceSelectedRows("int", None, range(5))
    print(tproxy.toTable().extractColumns("int", "float", "bool", "str"), file=regtest)

    tproxy.replaceSelectedRows("int", 1, range(5))
    print(tproxy.toTable().extractColumns("int", "float", "bool", "str"), file=regtest)

    tproxy.replaceSelectedRows("int", 3, range(5))
    print(tproxy.toTable().extractColumns("int", "float", "bool", "str"), file=regtest)

    tproxy.replaceSelectedRows("int", None, range(5))
    print(tproxy.toTable().extractColumns("int", "float", "bool", "str"), file=regtest)

    tproxy.replaceSelectedRows("int", 3, range(5))
    print(tproxy.toTable().extractColumns("int", "float", "bool", "str"), file=regtest)


def test_selected_col_values(tproxy, regtest):
    for n in (1, 2, 3, 4, 5):
        v = tproxy.selectedRowValues("int", range(n))
        print(v, file=regtest)

    for n in (1, 2, 3, 4):
        v = tproxy.selectedRowValues("int", range(n, 5))
        print(v, file=regtest)


def test_ghost_table_forwarding(tproxy):
    assert tproxy.getValue(tproxy.rows[1], "int") == 2

    assert tproxy.supportedPostfixes("") == []


def test_version_2_26_0(path, regtest):
    t = Hdf5TableProxy(path("data/table_v_2_26_0.hdf5"))
    assert t.hdf5_meta == {'hdf5_table_version': (2, 26, 0)}

    # calling .toTable is the "lackmus" test if data reading worked:
    print(t.toTable(), file=regtest)


def test_bit_matrix(tmpdir):
    from tables import open_file
    for n in (11, 53):
        file_ = open_file(tmpdir.join("data.bin").strpath, "w")
        bm = BitMatrix(file_, "flags", n)
        bm.resize(5)
        for row in range(5):
            for col in range(n):
                bm.set_bit(row, col)
                print(row, col, bm.positions_in_col(col), end=" ")
                print(sorted(bm.positions_in_row(row)))
                assert row in bm.positions_in_col(col)
                assert col in bm.positions_in_row(row)
                bm.unset_bit(row, col)
        print()
        file_.close()

