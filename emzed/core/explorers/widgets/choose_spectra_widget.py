# encoding: utf-8
from __future__ import print_function

from PyQt4 import QtCore, QtGui

from _choose_spectra_widget import _ChooseSpectraWidget


class ChooseSpectraWidget(_ChooseSpectraWidget):

    SELECTION_CHANGED = QtCore.pyqtSignal(list)

    def __init__(self, parent=None):
        super(ChooseSpectraWidget, self).__init__(parent)
        self._setup()

    def _setup(self):
        self._spectra.itemSelectionChanged.connect(self._selection_changed)
        self.setEnabled(False)

    def _selection_changed(self):
        row_indices = [item.row() for item in self._spectra.selectedIndexes()]
        self.SELECTION_CHANGED.emit(row_indices)

    def set_spectra(self, names):
        self._spectra.clear()
        for name in names:
            self._spectra.addItem(name)
        self.setEnabled(True)


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    def dump(*a):
        print(*a)

    widget = ChooseSpectraWidget()
    widget.set_spectra(("ms", "ms/ms"))
    widget.SELECTION_CHANGED.connect(dump)
    widget.show()
    sys.exit(app.exec_())
