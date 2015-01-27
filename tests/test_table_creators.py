def test_pandas(regtest):
    import pandas
    from emzed.core.data_types import Table
    data = dict(a=[1, 2, 3], b=[1.0, 2.0, None], c=["a", "b", "c"], d=[1.0, 2.0, 3.0],
                e=[None, None, None])
    df = pandas.DataFrame(data, columns=sorted(data.keys()))
    t = Table.from_pandas(df, formats={"b": "%.2f", float: "%.1f", object: "%s", None: "%s"})

    t.print_()
    t.print_(out=regtest)


def test_np_array():
    import numpy as np
    import emzed
    a = np.array([[1, 2, "a"], [1.0, 3, "b"], [2.0, None, np.nan]])
    t = emzed.core.data_types.Table.from_numpy_array(a, ["a", "b", "c"], [float, int, str],
                                                     ["%.2f", "%d", "%s"])

    assert t.rows == [[1.0, 2, "a"], [1.0, 3, "b"], [2.0, None, None]]
