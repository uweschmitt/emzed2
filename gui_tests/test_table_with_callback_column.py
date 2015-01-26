# encoding: utf-8


import emzed
CallBack = emzed.core.CallBack


def show(row, parent):
    expl = emzed.core.explorers.TableExplorer([row.table], False, parent=parent)
    expl.raise_()
    expl.show()

t = emzed.utils.toTable("a", (1, 2, 3))
t2 = emzed.utils.toTable("t", (2, 3, 4, 6))

t.addColumn("table", t2)

t.addColumn("job", t.a.apply(lambda v: CallBack("press me %d" % v, show)))

print(t)
emzed.gui.inspect(t)
