# encoding: utf-8
from __future__ import print_function

from _column_selection_dialog import ColumnMultiSelectDialog as _ColumnMultiSelectDialog

from PyQt4 import QtCore, QtGui


class ColumnMultiSelectDialog(_ColumnMultiSelectDialog):

    def __init__(self, names, states, n_shown=20, parent=None):
        super(ColumnMultiSelectDialog, self).__init__(parent)
        assert len(names) == len(states)

        n = len(names)
        oversize = n > n_shown
        self.model = model = QtGui.QStandardItemModel()

        for i, (name, state) in enumerate(zip(names, states)):
            print(i, name, state)
            item = QtGui.QStandardItem(name)
            check = QtCore.Qt.Checked if state else QtCore.Qt.Unchecked
            item.setCheckState(check)
            item.setCheckable(True)
            model.appendRow(item)

        list_ = self.column_names
        list_.setModel(model)

        if oversize:
            extra_w = list_.verticalScrollBar().sizeHint().width()
        else:
            extra_w = 0

        w = list_.sizeHintForColumn(0) + 2 * list_.frameWidth() + extra_w
        h = list_.sizeHintForRow(0) * n_shown + 2 * list_.frameWidth()
        list_.setFixedSize(w, h)

        self.setFixedSize(w, h + self.apply_button.height())





if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)


    names = ["abc" * i for i in range(10)]
    states = [len(n) % 2 == 0 for n in names]

    dlg = ColumnMultiSelectDialog(names, states, n_shown=5)
    dlg.exec_()



    """
    w = list.verticalScrollBar().sizeHint().width()
    list.setFixedSize(list.sizeHintForColumn(0) + 2 * list.frameWidth() + w, list.sizeHintForRow(0) * 6 + 2 * list.frameWidth())
    # layout.addWidget(list)
    dlg.setFixedSize(dlg.column_names.size())

    dlg.show()
    app.exec_()
    """
