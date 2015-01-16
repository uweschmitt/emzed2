import os

here = os.path.dirname(os.path.abspath(__file__))

import guidata
app = guidata.qapplication()

import emzed
pm = emzed.io.loadPeakMap(os.path.join(here, "..", "tests", "data", "test_mini.mzXML"))

print "TIME IS IN SECONDS"

t = emzed.utils.toTable("mzmin", (0.0, 300.0))
t.addColumn("mzmax", (1000.0, 400.0))
t.addColumn("rtmin", (0.0, 24.0))
t.addColumn("rtmax", (1000.0, 36.0))
t.addColumn("peakmap", (pm, pm))
t = emzed.utils.integrate(t)

emzed.gui.inspect(t)

print "TIME IS IN MINUTES"
t = emzed.utils.toTable("mzmin", (0.0, 300.0), meta=dict(time_is_in_seconds=False))
t.addColumn("mzmax", (1000.0, 400.0))
t.addColumn("rtmin", (0.0, 24.0 / 60.0))
t.addColumn("rtmax", (1000.0, 36.0 / 60.0))
t.addColumn("peakmap", (pm, pm))

t = emzed.utils.integrate(t)

emzed.gui.inspect(t)



