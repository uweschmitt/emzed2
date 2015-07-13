# encoding: utf-8
from __future__ import print_function


import emzed


def test_0(path):
    from emzed.core.data_types.ms_types import PeakMapProxy
    pm = PeakMapProxy(path("data/SHORT_MS2_FILE.mzData"))
    # this will trigger loading:
    n = len(pm)
    assert n == 41


def test_1(path):
    pm = emzed.io.loadPeakMap(path("data/SHORT_MS2_FILE.mzData"))
    t = emzed.utils.toTable("id", (1, 2, 3), type_=int)
    t.addColumn("peakmap", pm, type_=object)
    t.store("without_comp.table", True)
    t.store("with_comp.table", True, peakmap_cache_folder=".")

    tn = emzed.io.loadTable("with_comp.table")
    pm = tn.peakmap.uniqueValue()
    assert len(pm) == 41



