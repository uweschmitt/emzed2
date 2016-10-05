# encoding: utf-8
from __future__ import print_function, division, absolute_import

import operator

from PyQt4 import QtGui, QtCore

from ._filter_dialog import FilterDialog as _FilterDialog


class RangeFilter(object):

    def __init__(self, name, line_edit_min, line_edit_max):
        self.name = name
        self.line_edit_min = line_edit_min
        self.line_edit_max = line_edit_max

    def get_state(self):
        min_ = unicode(self.line_edit_min.text()).strip()
        max_ = unicode(self.line_edit_max.text()).strip()
        return min_, max_

    def set_state(self, state):
        try:
            min_, max_ = state
        except:
            return
        if isinstance(min_, unicode) and isinstance(max_, unicode):
            self.line_edit_min.setText(min_)
            self.line_edit_max.setText(max_)

    def expression(self):
        min_ = unicode(self.line_edit_min.text()).strip()
        max_ = unicode(self.line_edit_max.text()).strip()
        min_stmt = None
        max_stmt = None
        if max_:
            max_stmt = u"{name} <= {max}".format(name=self.name, max=max_)
        if min_:
            min_stmt = u"{min} <= {name}".format(name=self.name, min=min_)
        if min_ and max_:
            return u"{} AND {}".format(min_stmt, max_stmt)
        if min_:
            return min_stmt
        if max_:
            return max_stmt
        return None


class PatternFilter(object):

    def __init__(self, name, line_edit):
        self.name = name
        self.line_edit = line_edit

    def get_state(self):
        return unicode(self.line_edit.text()).strip()

    def set_state(self, state):
        if isinstance(state, unicode):
            pattern = state
            self.line_edit.setText(pattern)

    def expression(self):
        pattern = unicode(self.line_edit.text()).strip()
        if not pattern:
            return None
        if "*" in pattern or "?" in pattern:
            pattern = pattern.replace("_", "[_]").replace("?", "_").replace("*", "%")
            return u"{} LIKE '{}'".format(self.name, pattern)
        return u"{} = '{}'".format(self.name, pattern)


class ChoiceFilter(object):

    def __init__(self, name, combo_box, values):
        self.name = name
        self.combo_box = combo_box
        self.values = values

    def get_state(self):
        return unicode(self.combo_box.currentText())

    def set_state(self, state):
        if isinstance(state, unicode):
            text = state
            self.combo_box.setCurrentIndex(self.combo_box.findText(unicode(text)))

    def expression(self):
        """values might be bool etc, so just using label of selected item will not work"""
        choice = self.values[self.combo_box.currentIndex()]
        if not choice:
            return None
        if isinstance(choice, unicode):
            choice = u"'{}'".format(choice)
        elif isinstance(choice, bool):
            choice = "1" if choice else "0"
        return u"{} = {}".format(self.name, choice)


class Filters(list):

    def expression(self):
        expressions = [f.expression() for f in self]
        return u" AND ".join(s for s in expressions if s is not None)

    def get_state(self):
        return {f.name: f.get_state() for f in self}

    def set_state(self, states):
        for f in self:
            state = states.get(f.name)
            if state is not None:
                f.set_state(state)


class FilterDialog(_FilterDialog):

    def __init__(self, model, parent=None):
        super(FilterDialog, self).__init__(parent)

        self.model = model
        self.setup_filters()
        self.connect_signals()

    def connect_signals(self):
        self.cancel_button.clicked.connect(self.canceled)
        self.submit_button.clicked.connect(self.submitted)

    def canceled(self, *a):
        self.expression = None
        self.close()

    def submitted(self, *a):
        self.expression = unicode(self.filter_expression.toPlainText()).strip()
        self.close()

    def get_state(self):
        return (self.expert_mode_box.isChecked(),
                unicode(self.filter_expression.toPlainText()),
                self.filters.get_state())

    def set_state(self, state):
        try:
            mode, expression, filters = state
        except ValueError:
            return
        if mode in (True, False) and isinstance(expression, unicode):
            self.expert_mode_box.setChecked(mode)
            self.filter_expression.setPlainText(expression)
            self.filters.set_state(filters)

    def setup_filters(self):
        """
        TODO: FilterDialog mit allen Spalten ! Aber: abhänging von den indicators anzeigen !
        invalid fields: invalidieren !
        """
        self.filters = Filters()

        # sort by names:
        self.names_to_rows = {}
        col_names = self.model.col_names
        col_types = self.model.col_types
        i = 0
        for name, type_ in sorted(zip(col_names, col_types)):
            if type_ in (str, unicode, basestring):
                self.add_pattern(name)
            elif type_ in (bool,):
                self.add_choice(name, ["", True, False])
            elif type_ in (int, float, long):
                self.add_range(name)
            else:
                continue
            self.names_to_rows[name] = i
            i += 1

    def set_visible_columns(self, flags):

        for (name, row_index) in self.names_to_rows.items():
            row_visible = flags[name]
            for col_index in range(self.filters_layout.columnCount()):
                item = self.filters_layout.itemAtPosition(row_index, col_index)
                item.widget().setVisible(row_visible)

        sh = self.scrollAreaWidgetContents.minimumSizeHint()
        self.scrollAreaWidgetContents.resize(sh)

        sh = self.minimumSizeHint()
        self.setMaximumWidth(sh.width())
        self.resize(sh)

    def finalize_layout(self):
        v_spacer = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.filters_layout.addItem(v_spacer, len(self.filters), 1, 1, 1)

    def _set_policy(self, widget):
        sp = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sp.setHorizontalStretch(0)
        sp.setVerticalStretch(0)
        widget.setSizePolicy(sp)

    def _add_widget(self, widget, row_index, col_index, col_span=1):
        self.filters_layout.addWidget(widget, row_index, col_index, 1, col_span)

    def _label(self, text):
        label = QtGui.QLabel(text)
        self._set_policy(label)
        label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        return label

    def _line_edit(self, min_size):
        line_edit = QtGui.QLineEdit(self.scrollAreaWidgetContents)
        self._set_policy(line_edit)
        line_edit.setMinimumSize(QtCore.QSize(min_size, 0))
        line_edit.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self._set_policy(line_edit)
        line_edit.textEdited.connect(self.update_expression)
        return line_edit

    def add_label(self, name, row):
        label = self._label("%s: " % name)
        self._add_widget(label, row, 0)

    def add_range(self, name):

        ri = len(self.filters)
        self.add_label(name, ri)

        range_min = self._line_edit(50)
        self._add_widget(range_min, ri, 1)

        dots = self._label("...")
        dots.setMinimumSize(QtCore.QSize(20, 0))
        dots.setAlignment(QtCore.Qt.AlignCenter)
        self._add_widget(dots, ri, 2)

        range_max = self._line_edit(50)
        self._add_widget(range_max, ri, 3)

        self.filters.append(RangeFilter(name, range_min, range_max))

    def add_pattern(self, name):

        ri = len(self.filters)
        self.add_label(name, ri)

        pattern = self._line_edit(100)
        self._add_widget(pattern, ri, 1, col_span=3)

        self.filters.append(PatternFilter(name, pattern))

    def add_choice(self, name, values):

        ri = len(self.filters)
        self.add_label(name, ri)

        combo_box = QtGui.QComboBox(self.scrollAreaWidgetContents)
        for value in values:
            combo_box.addItem(unicode(value))
        self._set_policy(combo_box)
        combo_box.setMinimumSize(QtCore.QSize(100, 0))
        combo_box.setFrame(False)
        combo_box.currentIndexChanged.connect(self.update_expression)
        self._add_widget(combo_box, ri, 1, col_span=3)

        self.filters.append(ChoiceFilter(name, combo_box, values))

    def update_expression(self, *a):
        stmt = self.filters.expression()
        self.filter_expression.setPlainText(stmt)
