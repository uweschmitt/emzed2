# encoding: utf-8
from __future__ import print_function

from PyQt4 import QtCore, QtGui

from _spectra_selector import SpectraSelector as _SpectraSelector


class SpectraSelector(_SpectraSelector):

    MS_LEVEL_CHOSEN = QtCore.pyqtSignal(int)
    PRECURSOR_RANGE_CHANGED = QtCore.pyqtSignal(float, float)

    def __init__(self, parent=None):
        super(SpectraSelector, self).__init__(parent)
        self.setup()
        self.setEnabled(False)

    def setup(self):
        self.ms_level.activated.connect(self.ms_level_chosen)
        self.precursor.activated.connect(self.precursor_chosen)
        self.precursor_min.editingFinished.connect(self.precursor_range_updated)
        self.precursor_max.editingFinished.connect(self.precursor_range_updated)

    def set_data(self, ms_levels, precursor_mz_values):
        self.ms_level.clear()
        for ms_level in ms_levels:
            self.ms_level.addItem(str(ms_level))

        self.precursor.clear()
        self.precursor.addItem("-use range-")
        for precursor_mz_value in precursor_mz_values:
            self.precursor.addItem("%.5f" % precursor_mz_value)
        self.setEnabled(True)

        self.ms_levels = ms_levels
        self.precursor_mz_values = precursor_mz_values
        self.ms_level_chosen(0)
        self.precursor_chosen(0)

    def ms_level_chosen(self, idx):
        ms_level = self.ms_levels[idx]
        self.set_dependend_fields(ms_level)
        self.MS_LEVEL_CHOSEN.emit(ms_level)

    def precursor_chosen(self, idx):
        if idx == 0:
            mz_min = min(self.precursor_mz_values)
            mz_max = max(self.precursor_mz_values)
        else:
            precursor_mz = self.precursor_mz_values[idx - 1]
            mz_min = precursor_mz - 0.01
            mz_max = precursor_mz + 0.01
        self.PRECURSOR_RANGE_CHANGED.emit(mz_min, mz_max)
        self.precursor_min.setText("%.5f" % mz_min)
        self.precursor_max.setText("%.5f" % mz_max)

    def precursor_range_updated(self):
        try:
            mz_min = float(self.precursor_min.text())
            mz_max = float(self.precursor_max.text())
        except ValueError:
            return
        self.PRECURSOR_RANGE_CHANGED.emit(mz_min, mz_max)

    def set_dependend_fields(self, ms_level):
        flag = ms_level > 1
        self.precursor.setEnabled(flag)
        self.precursor_min.setEnabled(flag)
        self.precursor_max.setEnabled(flag)


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    widget = SpectraSelector()
    widget.show()

    def dump(*a):
        print(a)

    widget.PRECURSOR_RANGE_CHANGED.connect(dump)
    widget.MS_LEVEL_CHOSEN.connect(dump)

    widget.set_data([1, 2], [100, 100.1, 100.3])

    sys.exit(app.exec_())
