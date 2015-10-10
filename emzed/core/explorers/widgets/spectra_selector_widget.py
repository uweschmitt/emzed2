# encoding: utf-8
from __future__ import print_function

from PyQt4 import QtCore, QtGui

from _spectra_selector_widget import _SpectraSelectorWidget


class SpectraSelectorWidget(_SpectraSelectorWidget):

    MS_LEVEL_CHOSEN = QtCore.pyqtSignal(int)
    PRECURSOR_RANGE_CHANGED = QtCore.pyqtSignal(float, float)
    SELECTION_CHANGED = QtCore.pyqtSignal(int, float, float)

    def __init__(self, parent=None):
        super(SpectraSelectorWidget, self).__init__(parent)
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
        self._ms_level = None
        self._mz_range = None
        self._ms_level_chosen(0)
        self._precursor_chosen(0)

    def _ms_level_chosen(self, idx):
        self._ms_level = self._ms_levels[idx]
        self._set_dependend_fields()
        self.MS_LEVEL_CHOSEN.emit(self._ms_level)
        if self._mz_range is not None:
            self.SELECTION_CHANGED.emit(self._ms_level, *self._mz_range)

    def _precursor_chosen(self, idx):
        if not self._precursor_mz_values:
            return
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
        self._mz_range = (mz_min, mz_max)
        if self._ms_level is not None:
            self.SELECTION_CHANGED.emit(self._ms_level, mz_min, mz_max)

    def _precursor_range_updated(self):
        try:
            mz_min = float(self._precursor_min.text())
            mz_max = float(self._precursor_max.text())
        except ValueError:
            return
        self.PRECURSOR_RANGE_CHANGED.emit(mz_min, mz_max)
        self._mz_range = (mz_min, mz_max)
        if self._ms_level is not None:
            self.SELECTION_CHANGED.emit(self._ms_level, mz_min, mz_max)

    def _set_dependend_fields(self):
        not_ms_1 = self._ms_level > 1
        self._precursor.setEnabled(not_ms_1)
        self._precursor_min.setEnabled(not_ms_1)
        self._precursor_max.setEnabled(not_ms_1)


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    widget = SpectraSelectorWidget()
    widget.show()

    def dump(*a):
        print(a)

    widget.PRECURSOR_RANGE_CHANGED.connect(dump)
    widget.MS_LEVEL_CHOSEN.connect(dump)

    widget.set_data([1, 2], [100, 100.1, 100.3])

    sys.exit(app.exec_())
