from  emzed.io import loadTable


def test_2_0_2(path):
    t = loadTable(path("data/table_version_2_0_2.table"))
    assert t.version == (2, 0, 2)


def test_2_7_5(path):
    """
    in 2.7.5 we switched from cPickle to dill for serialization
    """
    t = loadTable(path("data/table_version_2_7_5.table"))
    assert t.version == (2, 7, 5)


def test_1_3_2(path):
    """
    the internal version of emzed 1.3.8 did not change since 1.3.2 so the "table version"
    is 1.3.2, although the file was created using emzed 1.3.8
    """
    t = loadTable(path("data/table_version_1_3_2.table"))
    assert t is not None
    # no version attribute in emzed 1.3.2 !!!
    # assert t.version == "1.3.2"


def test_1_3_8(path):
    """
    the internal version of emzed 1.3.8 did not change since 1.3.2 so the "table version"
    is 1.3.2, although the file was created using emzed 1.3.8
    """
    t = loadTable(path("data/table_version_1_3_8.table"))
    assert t.version == "1.3.2"


def test_2_7_5_table_with_peakmap(path):
    """the table under test had originally attributes rt, polarity, msLevel and peaks
    which are now "proxied" (see impl. Spectrum class).
    We check if this conversion worked.
    """

    from emzed.core.data_types.ms_types import NDArrayProxy

    t = loadTable(path("data/features.table"))
    assert t.version == (2, 7, 5)

    pm = t.peakmap.uniqueValue()
    spec = pm.spectra[0]

    for att in ("rt", "polarity", "msLevel", "precursors"):
        assert hasattr(spec, "_" + att)

    assert isinstance(spec.peaks, NDArrayProxy)

