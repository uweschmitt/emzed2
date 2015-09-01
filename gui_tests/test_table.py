import guidata
app = guidata.qapplication()

import emzed



t = emzed.utils.toTable("rt", (10.0, 20.0))
print emzed.gui.inspect(t)
