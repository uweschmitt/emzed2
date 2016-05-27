# encoding: utf-8
from __future__ import print_function


def test_0(regtest):

    from emzed.core.data_types.col_types import TimeSeries
    import datetime

    time_stamps = (datetime.datetime.fromordinal(1),)
    values = (1,)

    print(TimeSeries(time_stamps, values).uniqueId(), file=regtest)

    time_stamps = map(datetime.datetime.fromordinal, (1, 2))
    values = (1.0, 2.0)
    print(TimeSeries(time_stamps, values).uniqueId(), file=regtest)

    n = 100
    time_stamps = map(datetime.datetime.fromordinal, range(1000, 1000 + 10 * n, 10))
    values = range(n)

    print(TimeSeries(time_stamps, values).uniqueId(), file=regtest)

    ts0 = TimeSeries(time_stamps, values, blank_flags=[True] * n)
    for i in (1, 2, 3, 99, 100):
        tsi = TimeSeries(time_stamps[:-i], values[:-i], blank_flags=[True] * (n - i))
        assert ts0.continues(tsi)


def test_checked():
    from emzed.core.data_types.col_types import CheckState
    ch = CheckState(True)
    assert bool(ch) is True

    ch = CheckState(False)
    assert bool(ch) is False
