# encoding: utf-8

import emzed
CallBack = emzed.core.CallBack


# first colum containts tables:
subtable = emzed.utils.toTable("t", (2, 3, 4, 6))
t = emzed.utils.toTable("number", (42, 4711, 666))
t.addColumn("table", subtable)


def show(row, parent):
    print "you clicked on row with values", row
    emzed.gui.inspect(row.table, modal=False, parent=parent)

def message(row, parent):
    row.number = 2
    print(row)
    # emzed.gui.showInformation("you clicked on row with number %d" % row.number)

# create three cells of type CallBack manually:
cb1 = CallBack("show subtable", show)
cb2 = CallBack("yo !?", message)

t.addColumn("buttons", [cb1, cb2, cb2])

emzed.gui.inspect(t)
