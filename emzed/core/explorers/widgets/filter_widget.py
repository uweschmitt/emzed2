# encoding: utf-8
from __future__ import print_function

from _filter_criteria import FilterCriteria as _FilterCriteria
from _choose_range import ChooseRange as _ChooseRange
from _choose_value import ChooseValue as _ChooseValue

from PyQt4 import QtCore, QtGui


class ChooseFloatRange(_ChooseRange):

    RANGE_CHANGED = QtCore.pyqtSignal(str, object, object)

    def __init__(self, name, min_=None, max_=None, parent=None):
        super(ChooseFloatRange, self).__init__(parent)
        self.name = name
        self.column_name.setText(self.name)
        if min_ is not None:
            self.lower_bound.setText(min_)
        if max_ is not None:
            self.upper_bound.setText(max_)

    def setupUi(self, parent):
        super(ChooseFloatRange, self).setupUi(self)
        self.lower_bound.setMinimumWidth(40)
        self.upper_bound.setMinimumWidth(40)
        self.lower_bound.returnPressed.connect(self.emit_limits)
        self.upper_bound.returnPressed.connect(self.emit_limits)

    def emit_limits(self):
        v1 = str(self.lower_bound.text()).strip()
        v2 = str(self.upper_bound.text()).strip()
        try:
            v1 = float(v1) if v1 else None
        except Exception:
            return
        try:
            v2 = float(v1) if v2 else None
        except Exception:
            return
        self.RANGE_CHANGED.emit(self.name, v1, v2)


class ChooseValue(_ChooseValue):

    RANGE_CHANGED = QtCore.pyqtSignal(str, object, object)

    def __init__(self, name, values, parent=None):
        super(ChooseValue, self).__init__(parent)
        self.name = name
        self.column_name.setText(self.name)
        self.values.addItems(values)

    def setupUi(self, parent):
        super(ChooseValue, self).setupUi(self)
        self.values.currentIndexChanged.connect(self.emit_limits)

    def emit_limits(self, *a):
        t = str(self.values.currentText())
        self.RANGE_CHANGED.emit(self.name, t, t)


class FilterCriteria(_FilterCriteria):

    LIMITS_CHANGED = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        self.limits = dict()
        super(FilterCriteria, self).__init__(parent)

    def addChooser(self, chooser):
        self.horizontalLayout.addWidget(chooser)
        self.horizontalLayout.setAlignment(chooser, QtCore.Qt.AlignTop)
        chooser.RANGE_CHANGED.connect(self.criteria_updated)
        chooser.emit_limits()

    def criteria_updated(self, name, min_, max_):
        self.limits[str(name)] = (min_, max_)
        self.LIMITS_CHANGED.emit(self.limits)
        print(self.limits)


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    fc = FilterCriteria()
    fc.addChooser(ChooseValue("pol", ("+", "-")))
    fc.addChooser(ChooseFloatRange("mz"))
    fc.show()
    sys.exit(app.exec_())
