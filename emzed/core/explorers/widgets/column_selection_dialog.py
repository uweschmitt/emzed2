# encoding: utf-8
from __future__ import print_function

from _column_selection_dialog import ColumnMultiSelectDialog as _ColumnMultiSelectDialog

from PyQt4 import QtCore, QtGui


class ColumnMultiSelectDialog(_ColumnMultiSelectDialog):

    def __init__(self, names, states, n_shown=20, parent=None):
        super(ColumnMultiSelectDialog, self).__init__(parent)
        assert len(names) == len(states)
        self.setup(names, states, n_shown)
        self.column_settings = None

    def setup(self, names, states, n_shown):

        n = len(names)
        n_shown = min(n_shown, n)
        oversize = n > n_shown
        self.model = model = QtGui.QStandardItemModel(self)

        for i, (name, state) in enumerate(zip(names, states)):
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


        w_buttons = self.apply_button.sizeHint().width() + self.cancel_button.sizeHint().width()
        w_list = list_.sizeHintForColumn(0) + 2 * list_.frameWidth() + extra_w
        w = max(w_list, w_buttons)
        h = list_.sizeHintForRow(0) * n_shown + 2 * list_.frameWidth()
        list_.setFixedSize(w, h)

        self.setFixedSize(w, h + self.apply_button.height())

        self.apply_button.clicked.connect(self.apply_button_clicked)
        self.cancel_button.clicked.connect(self.cancel_button_clicked)

    def cancel_button_clicked(self, __):
        self.done(1)

    def apply_button_clicked(self, __):
        self.column_settings = []
        for row_idx in range(self.model.rowCount()):
            item = self.model.item(row_idx, 0)
            self.column_settings.append((str(item.text()), row_idx, item.checkState() == QtCore.Qt.Checked))
        self.done(0)


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)

    names = ["abc" * 1 for i in range(10)]
    states = [len(n) % 2 == 0 for n in names]

    dlg = ColumnMultiSelectDialog(names, states, n_shown=5)
    dlg.exec_()
    print(dlg.result)
