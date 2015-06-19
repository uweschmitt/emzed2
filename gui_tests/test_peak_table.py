import os

here = os.path.dirname(os.path.abspath(__file__))

import guidata
app = guidata.qapplication()

import emzed
import datetime
import math

pm = emzed.io.loadPeakMap(os.path.join(here, "..", "tests", "data", "test_mini.mzXML"))

TimeSeries = emzed.core.data_types.TimeSeries

print "TIME IS IN SECONDS"



t = emzed.utils.toTable("mzmin", range(0, 2000, 100), type_=float)

tsi = []
for i in range(len(t)):
    x = range(10 + i) + [None, None] + range(10 + i, 20 + i)
    y = [100 + 100 * math.sin(0.3 * (xi + i)) if xi is not None else None for xi in x]
    x = [None if xi is None else datetime.datetime(2015, 1 + xi / 20, 1 + xi % 20)  for xi in x]
    ts = TimeSeries(x,y)
    tsi.append(ts)


t.addColumn("mzmax", t.mzmin + 10.0)
t.addColumn("rtmin", range(10, 30), type_=float)
t.addColumn("rtmax", t.rtmin + 3)
t.addColumn("peakmap", pm)
t.addColumn("class", t.rtmin > 20)
t = emzed.utils.integrate(t)
# t.dropColumns("peakmap", "rtmin")
t.addEnumeration()
t.addColumn("f", t.id / 3)
t.addColumn("time_series", tsi, format_="%s", type_=TimeSeries)

print t.getColFormats()


t2 = emzed.utils.toTable("mzmin", range(0, 2000, 200), type_=float)
t2.addColumn("mzmax", t2.mzmin + 10.0)
t2.addColumn("rtmin", range(10, 30, 2), type_=float)
t2.addColumn("rtmax", t2.rtmin + 3)
t2.addColumn("mz", 0.5 * (t2.mzmin + t2.mzmax))
t2.dropColumns("mzmin", "mzmax")
t2.addColumn("peakmap", pm)

# t2 = emzed.utils.integrate(t2)

emzed.gui.inspect((t, t2))



