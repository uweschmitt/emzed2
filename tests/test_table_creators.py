def test_pandas():
    import pandas
    import cStringIO
    from emzed.core.data_types import Table
    data = dict(a=[1, 2, 3], b=[1.0, 2.0, None], c=["a", "b", "c"], d=[1.0, 2.0, 3.0],
                e=[None, None, None])
    df = pandas.DataFrame(data, columns=sorted(data.keys()))
    t = Table.from_pandas(df, formats={"b": "%.2f", float: "%.1f", object: "%s"})
    out = cStringIO.StringIO()

    t.print_()
    t.print_(out=out)
    lines = out.getvalue().split("\n")

    assert len(lines) == 7
    assert lines[0].strip() == "a        b        c        d        e"
    assert lines[1].strip() == "int      float    str      float    object"
    assert lines[2].strip() == "------   ------   ------   ------   ------"
    assert lines[3].strip() == "1        1.00     a        1.0      -"
    assert lines[4].strip() == "2        2.00     b        2.0      -"
    assert lines[5].strip() == "3        -        c        3.0      -"


def test_np_array():
    import numpy as np
    import emzed
    a = np.array([[1, 2, "a"], [1.0, 3, "b"], [2.0, None, np.nan]])
    t = emzed.core.data_types.Table.from_numpy_array(a, ["a", "b", "c"], [float, int, str],
                                                     ["%.2f", "%d", "%s"])

    assert t.rows == [[1.0, 2, "a"], [1.0, 3, "b"], [2.0, None, None]]
