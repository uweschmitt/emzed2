# encoding: utf-8
from __future__ import print_function

from PyQt4 import QtCore, QtGui

from _filter_criteria_widget import _FilterCriteriaWidget


from fnmatch import fnmatch

from _choose_range import ChooseRange as _ChooseRange
from _choose_value import ChooseValue as _ChooseValue
from _string_filter import StringFilter as _StringFilter


class _ChooseNumberRange(_ChooseRange):

    INDICATE_CHANGE = QtCore.pyqtSignal(str)

    def __init__(self, name, table, min_=None, max_=None, parent=None):
        super(_ChooseNumberRange, self).__init__(parent)
        self.name = name
        self.table = table
        self.column_name.setText(self.name)
        if min_ is not None:
            self.lower_bound.setText(min_)
        if max_ is not None:
            self.upper_bound.setText(max_)

    def setupUi(self, parent):
        super(_ChooseNumberRange, self).setupUi(self)
        self.lower_bound.setMinimumWidth(40)
        self.upper_bound.setMinimumWidth(40)
        self.lower_bound.returnPressed.connect(self.return_pressed)
        self.upper_bound.returnPressed.connect(self.return_pressed)

    def return_pressed(self):
        self.INDICATE_CHANGE.emit(self.name)

    def update(self):
        pass


def range_filter(v1, v2):
    if v1 is None and v2 is None:
        return None

    def filter(v, v1=v1, v2=v2):
        if v is None:
            return False
        return (v1 is None or v1 <= v) and (v2 is None or v <= v2)
    return filter


class ChooseFloatRange(_ChooseNumberRange):

    def get_filter(self):
        v1 = str(self.lower_bound.text()).strip()
        v2 = str(self.upper_bound.text()).strip()
        try:
            v1 = float(v1) if v1 else None
        except Exception:
            v1 = None
        try:
            v2 = float(v2) if v2 else None
        except Exception:
            v2 = None
        return self.name, range_filter(v1, v2)


class ChooseIntRange(_ChooseNumberRange):

    def get_filter(self):
        v1 = str(self.lower_bound.text()).strip()
        v2 = str(self.upper_bound.text()).strip()
        try:
            v1 = int(v1) if v1 else None
        except Exception:
            v1 = None
        try:
            v2 = int(v2) if v2 else None
        except Exception:
            v2 = None
        return self.name, range_filter(v1, v2)


class ChooseTimeRange(_ChooseNumberRange):

    def __init__(self, name, table, min_=None, max_=None, parent=None):
        super(ChooseTimeRange, self).__init__(name, table, min_, max_, parent)
        self.column_name.setText("%s [m]" % self.name)

    def get_filter(self):
        v1 = str(self.lower_bound.text()).strip()
        v2 = str(self.upper_bound.text()).strip()
        v1 = v1.rstrip("m").rstrip()
        v2 = v2.rstrip("m").rstrip()
        try:
            v1 = 60.0 * float(v1) if v1 else None
        except Exception:
            v1 = None
        try:
            v2 = 60.0 * float(v2) if v2 else None
        except Exception:
            v2 = None
        return self.name, range_filter(v1, v2)


class ChooseValue(_ChooseValue):

    INDICATE_CHANGE = QtCore.pyqtSignal(str)

    def __init__(self, name, table, parent=None):
        super(ChooseValue, self).__init__(parent)
        self.name = name
        self.table = table
        self.column_name.setText(self.name)
        self.update()

    def setupUi(self, parent):
        super(ChooseValue, self).setupUi(self)
        self.values.currentIndexChanged.connect(self.choice_changed)

    def choice_changed(self, *a):
        self.INDICATE_CHANGE.emit(self.name)

    def get_filter(self):
        t = self.pure_values[self.values.currentIndex()]
        if t is None:
            return self.name, None
        if t == "-":
            t = None
        return self.name, lambda v: v == t

    def update(self):
        before = self.values.currentText()
        values = set(self.table.getColumn(self.name).values)
        values = sorted("-" if v is None else v for v in values)
        self.pure_values = [None] + values
        new_items = [u""] + map(unicode, values)

        # block emiting signals, because the setup / update of the values below would
        # trigger emitting a curretnIndexChanged signal !
        old_state = self.values.blockSignals(True)

        self.values.clear()
        self.values.addItems(new_items)
        if before in new_items:
            self.values.setCurrentIndex(new_items.index(before))

        # unblock:
        self.values.blockSignals(old_state)


class StringFilterPattern(_StringFilter):

    INDICATE_CHANGE = QtCore.pyqtSignal(str)

    def __init__(self, name, table, pattern=None, parent=None):
        super(StringFilterPattern, self).__init__(parent)
        self.name = name
        self.table = table
        self.column_name.setText(self.name)
        if pattern is not None:
            self.pattern.setText(pattern)

    def setupUi(self, parent):
        super(StringFilterPattern, self).setupUi(self)
        self.pattern.setMinimumWidth(40)
        self.pattern.returnPressed.connect(self.return_pressed)

    def return_pressed(self):
        self.INDICATE_CHANGE.emit(self.name)

    def get_filter(self, *a):
        pattern = unicode(self.pattern.text())
        if pattern == u"":
            return self.name, None
        return self.name, lambda v, pattern=pattern: v is not None and fnmatch(v, pattern)


class FilterCriteriaWidget(_FilterCriteriaWidget):

    LIMITS_CHANGED = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        super(FilterCriteriaWidget, self).__init__(parent)
        self._choosers = []

    def setup(self):
        self.setEnabled(False)

    def _addChooser(self, chooser):
        self._hlayout.addWidget(chooser)
        self._hlayout.setAlignment(chooser, QtCore.Qt.AlignTop)
        chooser.INDICATE_CHANGE.connect(self.value_commited)
        self._choosers.append(chooser)

    def value_commited(self, name):
        limits = {}
        for chooser in self._choosers:
            name, filter_function = chooser.get_filter()
            limits[name] = filter_function
        self.LIMITS_CHANGED.emit(limits)

    def configure(self, emzed_table):
        t = emzed_table
        for i, (fmt, name, type_) in enumerate(zip(t.getColFormats(),
                                                   t.getColNames(),
                                                   t.getColTypes())):
            if fmt is not None:
                ch = None
                col = t.getColumn(name)
                if type_ == float:
                    fmtter = t.colFormatters[i]
                    try:
                        txt = fmtter(0.0)
                    except Exception:
                        txt = ""
                    if txt.endswith("m"):
                        ch = ChooseTimeRange(name, t)
                    else:
                        ch = ChooseFloatRange(name, t)
                elif type_ in (bool, str, unicode, basestring, int):
                    distinct_values = sorted(set(col.values))
                    if len(distinct_values) <= 15:
                        ch = ChooseValue(name, t)
                    else:
                        if type_ == int:
                            ch = ChooseIntRange(name, t)
                        elif type_ in (str, unicode, basestring):
                            ch = StringFilterPattern(name, t)
                if ch is not None:
                    self._addChooser(ch)
        self._hlayout.addStretch(1)
        if not len(self._choosers):
            self.filters_enabled = False
            self.setVisible(False)
            return
        self.setEnabled(True)

    def hide_filters(self, names):
        for c in self._choosers:
            c.setVisible(c.name not in names)

    def update(self, name):
        for chooser in self._choosers:
            if chooser.name == name:
                chooser.update()


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    widget = FilterCriteriaWidget()
    widget.show()

    import emzed
    t = emzed.utils.toTable("a", (1,2, 3), type_=int)
    t.addColumn("b", (1, 2, 3), type_=float)
    t.addColumn("c", ("asdf", "asdf", "asdf"), type_=str)

    def dump(*a):
        print(a)

    widget.configure(t)
    widget.LIMITS_CHANGED.connect(print)

    widget.show()

    sys.exit(app.exec_())

