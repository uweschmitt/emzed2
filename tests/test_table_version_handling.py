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
