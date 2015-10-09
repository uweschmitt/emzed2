# encoding: utf-8
from __future__ import print_function

from PyQt4 import QtCore, QtGui

from _spectra_selector import _SpectraSelector


class SpectraSelector(_SpectraSelector):

    MS_LEVEL_CHOSEN = QtCore.pyqtSignal(int)
    PRECURSOR_RANGE_CHANGED = QtCore.pyqtSignal(float, float)

    def __init__(self, parent=None):
        super(SpectraSelector, self).__init__(parent)
        self._setup()
        self.setEnabled(False)

    def _setup(self):
        self._ms_level.activated.connect(self._ms_level_chosen)
        self._precursor.activated.connect(self._precursor_chosen)
        self._precursor_min.editingFinished.connect(self._precursor_range_updated)
        self._precursor_max.editingFinished.connect(self._precursor_range_updated)
        self._precursor_min.setValidator(QtGui.QDoubleValidator())
        self._precursor_max.setValidator(QtGui.QDoubleValidator())

    def set_data(self, ms_levels, precursor_mz_values):
        self._ms_level.clear()
        for ms_level in ms_levels:
            self._ms_level.addItem(str(ms_level))

        self._precursor.clear()
        self._precursor.addItem("-use range-")
        for precursor_mz_value in precursor_mz_values:
            self._precursor.addItem("%.5f" % precursor_mz_value)
        self.setEnabled(True)

        self._ms_levels = ms_levels
        self._precursor_mz_values = precursor_mz_values
        self._ms_level_chosen(0)
        self._precursor_chosen(0)

    def _ms_level_chosen(self, idx):
        ms_level = self._ms_levels[idx]
        self._set_dependend_fields(ms_level)
        self.MS_LEVEL_CHOSEN.emit(ms_level)

    def _precursor_chosen(self, idx):
        if idx == 0:
            mz_min = min(self._precursor_mz_values)
            mz_max = max(self._precursor_mz_values)
        else:
            precursor_mz = self._precursor_mz_values[idx - 1]
            mz_min = precursor_mz - 0.01
            mz_max = precursor_mz + 0.01
        self.PRECURSOR_RANGE_CHANGED.emit(mz_min, mz_max)
        self._precursor_min.setText("%.5f" % mz_min)
        self._precursor_max.setText("%.5f" % mz_max)

    def _precursor_range_updated(self):
        try:
            mz_min = float(self._precursor_min.text())
            mz_max = float(self._precursor_max.text())
        except ValueError:
            return
        self.PRECURSOR_RANGE_CHANGED.emit(mz_min, mz_max)

    def _set_dependend_fields(self, ms_level):
        flag = ms_level > 1
        self._precursor.setEnabled(flag)
        self._precursor_min.setEnabled(flag)
        self._precursor_max.setEnabled(flag)


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
