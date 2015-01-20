import os

here = os.path.dirname(os.path.abspath(__file__))

import guidata
app = guidata.qapplication()

import emzed
pm = emzed.io.loadPeakMap(os.path.join(here, "..", "tests", "data", "test_mini.mzXML"))

print "TIME IS IN SECONDS"

t = emzed.utils.toTable("mzmin", range(0, 2000, 100), type_=float)
t.addColumn("mzmax", t.mzmin + 10.0)
t.addColumn("rtmin", range(10, 30), type_=float)
t.addColumn("rtmax", t.rtmin + 3)
t.addColumn("peakmap", pm)
t.addColumn("class", t.rtmin > 20)
t = emzed.utils.integrate(t)

print t.getColFormats()


t2 = emzed.utils.toTable("mzmin", range(0, 2000, 200), type_=float)
t2.addColumn("mzmax", t2.mzmin + 10.0)
t2.addColumn("rtmin", range(10, 30, 2), type_=float)
t2.addColumn("rtmax", t2.rtmin + 3)
t2.addColumn("peakmap", pm)

t2 = emzed.utils.integrate(t2)

emzed.gui.inspect((t, t2))



