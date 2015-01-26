# encoding: utf-8


import emzed
CallBack = emzed.core.CallBack


subtable = emzed.utils.toTable("t", (2, 3, 4, 6))

t = emzed.utils.toTable("number", (1, 2, 3))
t.addColumn("table", subtable)


def show(row, parent):
    emzed.gui.inspect(row.table, modal=False, parent=parent)

# all cells in column are the same:
t.addColumn("button_1", CallBack("press me", show))

# create three cells of type CallBack manually:

cb1 = CallBack("hi", show)
cb2 = CallBack("yo", show)
cb3 = CallBack("whats up", show)

t.addColumn("button_2", [cb1, cb2, cb3])

# create three cells of type CallBack by computation using t.number.apply:


def create_call_back(i):
    return CallBack("press me %d" % i, show)

t.addColumn("button_3", t.number.apply(create_call_back))

emzed.gui.inspect(t)
