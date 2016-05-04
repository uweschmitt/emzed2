# encoding: utf-8, division
from __future__ import print_function, division

def test_0():
    import emzed
    import tables

    assert hasattr(tables.array.Array._interpret_indexing, "patched")
    assert tables.array.Array._interpret_indexing.patched is True
