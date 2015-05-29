# encoding: utf-8
from __future__ import print_function

def test_0():
    from emzed.core.data_types.col_types import TimeSeries
    import datetime


    time_stamps = (datetime.datetime.now(),)
    values = (1,)

    print(TimeSeries(values, time_stamps).uniqueId())
    print(TimeSeries(values, time_stamps).time_stamps_as_strings())

    time_stamps = ("a", "b")
    values = (1.0, 2.0)
    print(TimeSeries(values, time_stamps).uniqueId())
    print(TimeSeries(values, time_stamps).time_stamps_as_strings())

    time_stamps = (10, 20)
    values = (1.0, 2.0)
    print(TimeSeries(values, time_stamps).uniqueId())
    print(TimeSeries(values, time_stamps).time_stamps_as_strings())


"""
todo:
    - TimeSeries in table und schauen obs klappt (vorlage: Blob )
    - was ist mit ausgabe ?

    - minimal table mit TimeSeries
    - plot dialog aufbohren !
    - profiles: gap filling !? (peaks können dooppelt auftauche !), evtl einfach deaktivieren
    - clustering
    - alles im viewer !
    - workflow

    - identitiy normalization

    - edit step im tool !

    - ms/ms analysis step (incl: marker column)

"""
