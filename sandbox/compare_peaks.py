import emzed
t = emzed.io.loadTable("shoulders_table_integrated.table")
print len(t)

t.sortBy("mz", ascending=True)
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

emzed.gui.inspect(t0)
