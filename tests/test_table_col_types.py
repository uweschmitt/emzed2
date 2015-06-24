# encoding: utf-8
from __future__ import print_function


def test_0():

    from emzed.core.data_types.col_types import TimeSeries
    import datetime

    time_stamps = (datetime.datetime.now(),)
    values = (1,)

    print(TimeSeries(values, time_stamps).uniqueId())

    time_stamps = ("a", "b")
    values = (1.0, 2.0)
    print(TimeSeries(values, time_stamps).uniqueId())

    time_stamps = (10, 20)
    values = (1.0, 2.0)
    print(TimeSeries(values, time_stamps).uniqueId())
