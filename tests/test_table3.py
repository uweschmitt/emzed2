import emzed

def test_apply_with_nones():
    t = emzed.utils.toTable("a", [1, None])
    t.addColumn("b", t.a.apply(lambda v: 0 if v is None else v))
    assert t.b.values == (1, None)
    t.addColumn("c", t.a.apply(lambda v: 0 if v is None else v, filter_nones=False))
    assert t.c.values == (1, 0)

