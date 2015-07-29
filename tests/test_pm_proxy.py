# encoding: utf-8
from __future__ import print_function


import emzed


def test_0(path):
    from emzed.core.data_types.ms_types import PeakMapProxy
    pm = PeakMapProxy(path("data/SHORT_MS2_FILE.mzData"))
    # this will trigger loading:
    n = len(pm)
    assert n == 41


def test_1(path, tmpdir):
    from emzed.core.data_types.ms_types import PeakMapProxy
    pm = emzed.io.loadPeakMap(path("data/SHORT_MS2_FILE.mzData"))
    t = emzed.utils.toTable("id", (1, 2, 3), type_=int)
    t.addColumn("peakmap", pm, type_=object)
    t.store(tmpdir.join("without_comp.table").strpath, True)
    t.store(tmpdir.join("with_comp.table").strpath, True, True, peakmap_cache_folder=tmpdir.strpath)

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


def test_squeeze(path):

    from emzed.core.data_types.ms_types import PeakMapProxy
    pm = PeakMapProxy(path("data/SHORT_MS2_FILE.mzData"))
    # this will trigger loading:
    n = len(pm)
    assert n == 41
    assert isinstance(pm, PeakMapProxy)
    assert "spectra" in pm.__dict__

    pm.squeeze()
    assert "spectra" not in pm.__dict__
    assert len(pm) == 41  # triggers loading
    assert "spectra" in pm.__dict__
