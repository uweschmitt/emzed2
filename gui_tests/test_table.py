import guidata
app = guidata.qapplication()

import emzed



t = emzed.utils.toTable("rt", (10.0, 20.0))
t.addColumn("rtmax", t.rt + 1.0)
t.addColumn("invisible", t.rt + 1.0, format_=None)
print emzed.gui.inspect(t)
