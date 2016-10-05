# encoding: utf-8
from __future__ import print_function


import os
import shutil

import pytest

import emzed


def test_0(path):
    from emzed.core.data_types.ms_types import PeakMapProxy
    pm = PeakMapProxy(path("data/SHORT_MS2_FILE.mzData"))
    # this will trigger loading:
    n = len(pm)
    assert n == 41


@pytest.fixture
def t(path):
    pm = emzed.io.loadPeakMap(path("data/SHORT_MS2_FILE.mzData"))
    t = emzed.utils.toTable("id", (1, 2, 3), type_=int)
    t.addColumn("peakmap", pm, type_=object)
    return t


def test_1(tmpdir, t):
    from emzed.core.data_types.ms_types import PeakMapProxy

    p1 = tmpdir.join("without_comp.table").strpath
    t.store(p1, True, True)
    p2 = tmpdir.join("with_comp.table").strpath
    t.store(p2, True, True, tmpdir.strpath)

    # compression by peakmap proxy should be factor 30 or better in this particular case:
    s1 = os.stat(p1).st_size
    s2 = os.stat(p2).st_size
    assert s1 > 30 * s2, (s1, s2, 30 * s2)

    assert isinstance(t.peakmap.uniqueValue(), PeakMapProxy)
    assert not t.peakmap.uniqueValue()._loaded
    assert t.peakmap.uniqueValue().uniqueId() is not None    # must not trigger loading !
    assert not t.peakmap.uniqueValue()._loaded

    tn = emzed.io.loadTable(tmpdir.join("with_comp.table").strpath)
    pm = tn.peakmap.uniqueValue()
    assert t.peakmap.uniqueValue().uniqueId() is not None    # must not trigger loading !
    assert not tn.peakmap.uniqueValue()._loaded
    assert len(pm) == 41  # triggers loading
    assert tn.peakmap.uniqueValue()._loaded

    emzed.io.storeTable(t, tmpdir.join("with_comp_2.table").strpath, True, True, tmpdir.strpath)

    tn = emzed.io.loadTable(tmpdir.join("with_comp_2.table").strpath)
    pm = tn.peakmap.uniqueValue()
    assert isinstance(pm, PeakMapProxy)
    assert t.peakmap.uniqueValue().uniqueId() is not None    # must not trigger loading !
    assert not tn.peakmap.uniqueValue()._loaded
    assert len(pm) == 41  # triggers loading
    assert tn.peakmap.uniqueValue()._loaded


def test_2(path, tmpdir, regtest):

    # same folder as table for peakmaps:

    from emzed.core.data_types import Table

    pm = emzed.io.loadPeakMap(path("data/SHORT_MS2_FILE.mzData"))
    t = emzed.utils.toTable("id", (1, 2, 3), type_=int)
    t.addColumn("peakmap", pm, type_=object)

    p2 = tmpdir.join("with_comp.table").strpath

    t.store(p2, True, True, ".")

    # chekc if pm proxy is next ot
    file_names = [p.basename for p in tmpdir.listdir()]
    print(file_names, file=regtest)

    # force loading of data:.
    print(len(t.peakmap.values[0]), file=regtest)
    s1 = os.stat(p2).st_size
    assert s1 < 1000
    t = Table.load(p2)
    print(len(t.peakmap.values[0]), file=regtest)

    subfolder = tmpdir.join("subfolder")
    os.makedirs(subfolder.strpath)
    for p in file_names:
        shutil.move(tmpdir.join(p).strpath, subfolder.strpath)

    t2 = Table.load(subfolder.join("with_comp.table").strpath)
    print(t2, file=regtest)
    print(len(t2.peakmap.values[0]), file=regtest)
    print(t2, file=regtest)


def test_3(path, tmpdir, regtest):

    # relative path for peakmaps:

    from emzed.core.data_types import Table

    pm = emzed.io.loadPeakMap(path("data/SHORT_MS2_FILE.mzData"))
    t = emzed.utils.toTable("id", (1, 2, 3), type_=int)
    t.addColumn("peakmap", pm, type_=object)

    folder = tmpdir.join("subfolder")
    folder.mkdir()

    p2 = folder.join("with_comp.table").strpath
    t.store(p2, True, True, "..")

    for p in tmpdir.listdir():
        # full path varies because the folder is a tmp dir:
        print(p.basename, file=regtest)

    t2 = Table.load(p2)
    # this triggers loading:
    t2.peakmap[0].chromatogram(0, 10, 0, 10)

    t2.peakmap[0]._path == p.strpath

    # now we move and check if proxy still works:
    moved = folder.join("..").join("moved")
    shutil.move(folder.strpath, moved.strpath)

    t2 = Table.load(moved.join("with_comp.table").strpath)
    t2.peakmap[0].chromatogram(0, 10, 0, 10)


def test_squeeze(path):

    from emzed.core.data_types.ms_types import PeakMapProxy
    pm = PeakMapProxy(path("data/SHORT_MS2_FILE.mzData"))
    # this will trigger loading:
    n = len(pm)
    assert n == 41
    assert isinstance(pm, PeakMapProxy)
    assert "_spectra" in pm.__dict__

    pm.squeeze()
    assert "_spectra" not in pm.__dict__
    assert len(pm) == 41  # triggers loading
    assert "_spectra" in pm.__dict__


def test_as_pickle(path, tmpdir):
    from emzed.core.data_types.ms_types import PeakMapProxy, PeakMap
    pm = PeakMapProxy(path("data/SHORT_MS2_FILE.mzData"))
    print(pm)
    path = tmpdir.join("pm.pickle").strpath
    pm.dump_as_pickle(path)
    pm = PeakMap.load_as_pickle(path)
    print(pm)
