import os

here = os.path.dirname(os.path.abspath(__file__))

import guidata
app = guidata.qapplication()

import emzed

t = emzed.utils.toTable("rtmin", (0, 1000), type_=float)
t.addColumn("rtmax", t.rtmin + 3000, type_=float)
t.addColumn("mzmin", (0, 100), type_=float)
t.addColumn("mzmax", (100, 1000), type_=float)
print(t)

pm = emzed.io.loadPeakMap(os.path.join(here, "di.mzXML"))
pm2 = emzed.io.loadPeakMap(os.path.join(here, "..", "tests", "data", "test_mini.mzXML"))

emzed.gui.inspect(pm, table=t)


