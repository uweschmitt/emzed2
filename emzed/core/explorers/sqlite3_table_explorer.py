# encoding: utf-8

from __future__ import print_function

import base64
from collections import defaultdict
import copy
import cPickle
import json
import os
import sys
from PyQt4 import QtCore, QtGui

from ..data_types.sqlite3_table_proxy import Sqlite3TableProxy
from ..data_types.table import _formatter
from ..config import folders

from .widgets.column_selection_dialog import ColumnMultiSelectDialog

from ._sqlite3_table_explorer import _Sqlite3TableExplorer
from .filter_dialog import FilterDialog


def std_font(bold=False):
    font = QtGui.QFont("Monospace")
    font.setStyleHint(QtGui.QFont.TypeWriter)
    font.setBold(bold)
    return font


def try_to_reactivate(choice_box, text):
    index = choice_box.findText(text)
    if index >= 0:
        choice_box.setCurrentIndex(index)
        return True
    choice_box.setCurrentIndex(0)
    return False



class ModifiedTableView(QtGui.QTableView):

    def showEvent(self, evt):
        pass
        # self.resizeColumnsToContents()
        # self.resizeColumnsToContents()
        # self.horizontalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)

    def keyPressEvent(self, evt):
        if evt.key() in (QtCore.Qt.Key_Up, QtCore.Qt.Key_Down):
            """automatically select full row if user uses cursor up/down keys
            """
            rows = set(idx.row() for idx in self.selectedIndexes())
            if rows:
                min_row = min(rows)
                max_row = max(rows)
                if evt.key() == QtCore.Qt.Key_Up:
                    row = min_row - 1
                else:
                    row = max_row + 1
                row = min(max(row, 0), self.model().rowCount() - 1)
                current_position = self.currentIndex()
                ix = self.model().index(row, current_position.column())
                self.selectRow(row)
                self.verticalHeader().sectionClicked.emit(row)
                self.setCurrentIndex(ix)
                # skip event handling:
                return
        return super(ModifiedTableView, self).keyPressEvent(evt)


class TableConfigHandler(object):

    """manages user specific settings on view as order of columns after drag drop.
    """

    def __init__(self, config_id, dialog):  # table_view, model):
        self.config_id = config_id
        self.dialog = dialog
        self.table_view = dialog.table_view
        self.model = dialog.model
        self.filter_dialog = dialog.filter_dialog

    def _read_config(self):
        f = folders.getEmzedFolder()
        config_path = os.path.join(f, "sqlite3_viewer_config.json")
        if os.path.exists(config_path):
            config = json.load(open(config_path, "r"))
        else:
            config = {}
        dd = defaultdict(dict)
        dd.update(config)
        return dd, config_path

    def _write_config(self, config, config_path):
        with open(config_path, "w") as fh:
            json.dump(config, fh)

    def update_config(self, *a):
        config, config_path = self._read_config()

        backup_config = copy.deepcopy(config)
        try:
            key = self.model.table_info_identifier()
            config[self.config_id][key] = self.get_state()
            self._write_config(config, config_path)
        except ValueError:
            # in case of json serialization error we keep old file, new and maybe partially written
            # file might be # corrupted:
            self._write_config(backup_config, config_path)

    def load_config(self):
        config, config_path = self._read_config()
        if self.config_id in config:
            key = self.model.table_info_identifier()
            value = config[self.config_id].get(key)
            if value is not None:
                valid = self.restore_state(value)
                if not valid:
                    # cleanup for old states
                    del config[self.config_id][key]
                    self._write_config(config, config_path)

    def get_state(self):
        tv = self.table_view
        header_state = str(tv.horizontalHeader().saveState().toBase64())
        n = self.model.columnCount()
        # string of 0/1 s:
        visible_column_state = "".join(str(int(tv.isColumnHidden(i))) for i in range(n))
        filter_dlg_state = base64.encodestring(cPickle.dumps(self.filter_dialog.get_state()))
        filter_expression = unicode(self.dialog.current_filter.toPlainText())

        sort_state = self.dialog.get_sort_state()
        return u"|".join([header_state, visible_column_state, filter_dlg_state, filter_expression,
                          sort_state])

    def restore_state(self, state):
        states = state.split("|")
        # state format might be outdated, so we check first if data structure is valid:
        if len(states) == 5:
            header_state, visible_column_state, filter_state, filter_expression, sort_state = states
            self.table_view.horizontalHeader().restoreState(
                QtCore.QByteArray.fromBase64(header_state))
            for i, c in enumerate(visible_column_state):
                self.table_view.setColumnHidden(i, c == "1")
            self.filter_dialog.set_state(cPickle.loads(base64.decodestring(filter_state)))
            self.dialog.set_filter_expression(filter_expression)
            self.dialog.set_sort_fields(sort_state)
            return True
        return False


class Sqlite3TableExplorer(_Sqlite3TableExplorer):

    def __init__(self, path, config_id="default", parent=None):
        super(Sqlite3TableExplorer, self).__init__(parent)
        self.model = Sqlite3Model(path)

        # patch table_view which is created in _Sqlite3TableExplorer:
        self.table_view.__class__ = ModifiedTableView
        self.table_view.setModel(self.model)

        self.filter_dialog = FilterDialog(self.model, self)
        self.filter_dialog.set_visible_columns(self.visible_flags())

        # only minimalistic view:
        self.plot_frame.setVisible(False)

        self.connect_signals()
        self.configure_dialog(config_id)
        self.set_styles()

    def configure_dialog(self, config_id):
        self.setup_widget_defaults()  # might be overridden by config handler
        self.update_sort_widgets()    # might be overridden by config handler
        self.config_handler = TableConfigHandler(config_id, self)
        self.config_handler.load_config()

    def setup_widget_defaults(self):
        for i in range(self.model.columnCount(None)):
            self.table_view.setColumnHidden(i, i in self.model.always_invisible)

    def update_sort_widgets(self):

        flags = self.visible_flags()

        if self.first_sort_field.count():
            first_col_name = self.first_sort_field.currentText()
            self.first_sort_field.clear()
        else:
            for name in self.model.col_names:
                if flags[name]:
                    first_col_name = name
                    break

        if self.second_sort_field.count():
            second_col_name = self.second_sort_field.currentText()
            self.second_sort_field.clear()
        else:
            second_col_name = ""

        self.second_sort_field.addItem("")
        for name, active in sorted(flags.items()):
            if active and name not in self.model.object_columns:
                self.first_sort_field.addItem(unicode(name))
                self.second_sort_field.addItem(unicode(name))

        ok = try_to_reactivate(self.first_sort_field, first_col_name)
        if not ok:
            self.first_sort_order.setCurrentIndex(0)
        ok = try_to_reactivate(self.second_sort_field, second_col_name)
        if not ok:
            self.second_sort_order.setCurrentIndex(0)

    def closeEvent(self, *a):
        self.config_handler.update_config()
        return super(Sqlite3TableExplorer, self).closeEvent(*a)

    def get_sort_state(self):
        f1_name = unicode(self.first_sort_field.currentText())
        f1_order = unicode(self.first_sort_order.currentText())
        f2_name = unicode(self.second_sort_field.currentText())
        f2_order = unicode(self.second_sort_order.currentText())
        return u",".join([f1_name, f1_order, f2_name, f2_order])

    def set_filter_expression(self, filter_expression):
        self.current_filter.setPlainText(filter_expression)
        # self.filter_expression_changed()

    def filter_expression_changed(self):
        self.model.update_filter(unicode(self.current_filter.toPlainText()))

    def set_sort_fields(self, state):
        fields = state.split(",")
        if len(fields) != 4:
            return
        f1_name, f1_order, f2_name, f2_order = fields
        if try_to_reactivate(self.first_sort_field, f1_name):
            try_to_reactivate(self.first_sort_order, f1_order)
        if try_to_reactivate(self.second_sort_field, f2_name):
            try_to_reactivate(self.second_sort_order, f2_order)

        self.sort_settings_changed()

    def visible_flags(self):
        flags = {}
        for (i, name) in enumerate(self.model.col_names):
            flags[name] = not self.table_view.isColumnHidden(i)
        return flags

    def connect_signals(self):
        self.visible_columns_button.clicked.connect(self.choose_visible_columns)
        self.filter_button.clicked.connect(self.set_filter)
        self.reset_filter_button.clicked.connect(self.reset_filter)
        self.current_filter.textChanged.connect(self.filter_expression_changed)
        self.first_sort_field.currentIndexChanged.connect(self.sort_settings_changed)
        self.first_sort_order.currentIndexChanged.connect(self.sort_settings_changed)
        self.second_sort_field.currentIndexChanged.connect(self.sort_settings_changed)
        self.second_sort_order.currentIndexChanged.connect(self.sort_settings_changed)

    def set_styles(self):
        self.table_view.setFont(std_font())
        self.table_view.horizontalHeader().setFont(std_font(bold=True))
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.horizontalHeader().setResizeMode(QtGui.QHeaderView.Interactive)
        self.table_view.horizontalHeader().setMovable(True)
        self.table_view.verticalHeader().setDefaultSectionSize(21)
        self.table_view.resizeColumnsToContents()
        self.table_view.horizontalHeader().resizeSections(QtGui.QHeaderView.ResizeToContents)

    def set_filter(self, *a):
        dlg = self.filter_dialog
        dlg.set_visible_columns(self.visible_flags())
        dlg.exec_()
        if dlg.expression is not None:
            msg = self.model.check_filter_expression(dlg.expression)
            if msg is not None:
                QtGui.QMessageBox.critical(self, "syntax error in filter expression", msg)
            else:
                # self.model.update_filter(dlg.expression)
                self.current_filter.setPlainText(dlg.expression)

    def reset_filter(self, *a):
        self.model.update_filter("")
        self.current_filter.setPlainText("")

    def choose_visible_columns(self, *a):
        col_names = self.model.col_names
        if not col_names:
            return

        flags = sorted(self.visible_flags().items())
        sorted_col_names, currently_visible = zip(*flags)  # unzip

        dlg = ColumnMultiSelectDialog(sorted_col_names, currently_visible)
        dlg.exec_()
        if dlg.column_settings is None:
            return
        for (name, __, v) in dlg.column_settings:
            i = col_names.index(name)
            self.table_view.setColumnHidden(i, not v)
        # self.config_handler.update_config()
        self.update_sort_widgets()

    def sort_settings_changed(self):
        field_1 = unicode(self.first_sort_field.currentText()).strip()
        field_1_asc = self.first_sort_order.currentText() == "asc"
        field_2 = unicode(self.second_sort_field.currentText()).strip()
        field_2_asc = self.second_sort_order.currentText() == "asc"

        if not field_2:
            sort_params = [(field_1, field_1_asc)]
        else:
            sort_params = [(field_1, field_1_asc), (field_2, field_2_asc)]

        self.model.update_sort_order(sort_params)


class Sqlite3Model(QtCore.QAbstractTableModel):

    def __init__(self, path, prefetch=100, parent=None):
        super(Sqlite3Model, self).__init__(parent)

        self.db_proxy = Sqlite3TableProxy(path)
        self.db_proxy.create_query()

        for attr in ("col_names", "col_types", "col_formats", "meta", "object_columns"):
            setattr(self, attr, getattr(self.db_proxy, attr))

        self.setup_compatibility_api()

        self.always_invisible = set(i for (i, f) in enumerate(self.col_formats) if f is None)

        self.prefetch = prefetch

        self.exhausted = False
        self.fetch_first_batch()

    def update_filter(self, expression):
        self.beginResetModel()
        try:
            if expression == "":
                self.db_proxy.reset_filter()
            else:
                self.db_proxy.set_filter(expression)
            self.db_proxy.create_query()
            self.fetch_first_batch()
        finally:
            self.endResetModel()

    def check_filter_expression(self, expression):
        return self.db_proxy.check_filter_expression(expression)

    def update_sort_order(self, params):
        self.beginResetModel()
        try:
            self.db_proxy.set_sort_order(params)
            self.db_proxy.create_query()
            self.fetch_first_batch()
        finally:
            self.endResetModel()

    def setup_compatibility_api(self):
        self.getColFormats = lambda: self.col_formats
        self.getColNames = lambda: self.col_names
        self.getColTypes = lambda: self.col_types
        self.colFormatters = [lambda x: _formatter(f)(x) for f in self.col_formats]

    def data(self, index, role):
        ci = index.column()
        ri = index.row()
        if role == QtCore.Qt.TextAlignmentRole:
            type_ = self.col_types[ci]
            if type_ in (int, float):
                return QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            else:
                return QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
        if role == QtCore.Qt.BackgroundRole:
            if ri % 2 == 0:
                return QtGui.QBrush(QtGui.QColor(255, 255, 255))
            if ri % 2 == 1:
                return QtGui.QBrush(QtGui.QColor(245, 245, 245))

        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        try:
            row = self.get_row(index.row())
        except IndexError:
            return QtCore.QVariant()
        value = row[ci]
        if value is None:
            return "-"
        if self.col_names[ci] in self.object_columns:
            value = value.split("!", 1)[1]
        format = self.col_formats[ci]
        return _formatter(format)(value)

    def table_info_identifier(self):
        id_ = "__".join(self.col_names)
        id_ += "!" + "__".join(map(str, self.col_types))
        id_ += "!" + "__".join(self.col_formats)
        return id_

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.TextAlignmentRole:
            return QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        if orientation == QtCore.Qt.Horizontal:
            if section < len(self.col_names):
                return self.col_names[section]
            return QtCore.QVariant()
        return QtCore.QString("> ")

    def columnCount(self, index=None):
        return len(self.col_names)

    def fetch_first_batch(self):
        self.exhausted = False
        self.loaded_rows = []
        try:
            self.get_row(self.prefetch)
        except IndexError:
            pass

    def rowCount(self, index=None):
        if self.exhausted:
            return len(self.loaded_rows)
        else:
            return len(self.loaded_rows) + 1

    def get_row(self, row_index):

        if self.exhausted:
            return self.loaded_rows[row_index]

        if row_index < len(self.loaded_rows):
            return self.loaded_rows[row_index]

        # not exhausted, so we try to fetch the next block:
        before = len(self.loaded_rows)
        new_rows = []
        for i in xrange(len(self.loaded_rows), row_index + 1):
            row = self.db_proxy.fetchone()
            if row is None:
                self.exhausted = True
                break
            new_rows.append(row)
        if new_rows:
            self.beginInsertRows(QtCore.QModelIndex(), before + 1, before + len(new_rows))
            self.loaded_rows.extend(new_rows)
            self.endInsertRows()
        if row_index < len(self.loaded_rows):
            return self.loaded_rows[row_index]
        raise IndexError()


if __name__ == "__main__":

    app = QtGui.QApplication(sys.argv)
    dlg = Sqlite3TableExplorer("../tests/data/features.db")
    dlg.exec_()
