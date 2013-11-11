import emzed
t = emzed.io.loadTable("shoulders_table_integrated.table")
print len(t)

t = t.filter(t.area > 5e4)
t.dropColumns("id")
t.addEnumeration()

import sys
ids = map(int, sys.argv[1:])

subt = t.filter(t.id.isIn(ids))
print len(subt)

ti = subt.splitBy("id")
t0 = ti[0]
for tii in ti[1:]:
    t0 = t0.join(tii)


emzed.io.storeTable(subt, "peaks_separate.table", True)
emzed.io.storeTable(t0, "peaks_joined.table", True)

emzed.gui.inspect([subt, t0, t])

p = t.peakmap.uniqueValue()
emzed.gui.inspectPeakMap(p, table=subt)
