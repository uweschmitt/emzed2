
def test_apply_with_nones():
    import emzed
    t = emzed.utils.toTable("a", [1, None])
    t.addColumn("b", t.a.apply(lambda v: 0 if v is None else v))
    assert t.b.values == (1, None)
    t.addColumn("c", t.a.apply(lambda v: 0 if v is None else v, filter_nones=False))
    assert t.c.values == (1, 0)

def test_insert_before_and_after():
    import emzed
    t = emzed.utils.toTable("b", [1])
    t.addColumn("d", [3], insertAfter="b")
    t.addColumn("a", [0], insertBefore="b")
    t.addColumn("c", [2], insertAfter="b")
    assert t.getColNames() == ["a", "b", "c", "d"]
    (a, b, c, d), = t.rows
    assert (a, b, c, d) == (0, 1, 2, 3)


def test_col_with_tuples():
    import emzed
    t = emzed.utils.toTable("b", [(1, 2)])
    import cStringIO
    fp = cStringIO.StringIO()
    t.print_(out=fp)
    out = fp.getvalue()
    lines = [l.strip() for l in out.split("\n")]
    assert lines[3] == "(1, 2)"


def test_evalsize_of_grouped_aggregate_values():
    import emzed
    # tests a bug fixed in commit 843144a
    t = emzed.utils.toTable("v", [1, 1, 2])
    assert (t.v.count.group_by(t.v) == 1).values == (False, False, True)


def test_grouped_aggregate_with_None_in_group():
    import emzed
    # tests a bug fixed in commit 843144a
    t = emzed.utils.toTable("v", [1, 1, 2, None])
    assert (t.v.count.group_by(t.v)).values == (2, 2 , 1, None)

def test_apply_to_empty_col():
    import emzed
    t = emzed.utils.toTable("b", (1,))
    t.addColumn("a", t.b.apply(lambda x: None))

def test_diff_time_setting():
    import emzed
    t = emzed.utils.toTable("rt", (20.2,), meta=dict(time_is_in_seconds=False))
    print repr(str(t))
    assert "\n20.2m" in str(t)

