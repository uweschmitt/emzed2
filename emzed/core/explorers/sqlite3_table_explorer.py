# encoding: utf-8

from __future__ import print_function

import base64
from collections import defaultdict, OrderedDict
import copy
import cPickle
import json
import os
import sys
from PyQt4 import QtCore, QtGui

from ..config import folders

from .widgets.column_selection_dialog import ColumnMultiSelectDialog

from ._sqlite3_table_explorer import _Sqlite3TableExplorer
from .sqlite3_table_explorer_model import Sqlite3Model
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
        self.resizeColumnsToContents()
        self.horizontalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)

    def keyPressEvent(self, evt):
        if evt.key() in (QtCore.Qt.Key_Up, QtCore.Qt.Key_Down):
            """automatically select full row if user uses cursor up/down keys
            """
            modifiers = QtGui.QApplication.keyboardModifiers()
            allowed = (QtCore.Qt.NoModifier, QtCore.Qt.KeypadModifier)
            if modifiers in allowed:
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

    def __init__(self, config_id, dialog):
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

    def __init__(self, path, config, parent=None):
        super(Sqlite3TableExplorer, self).__init__(parent)
        self.model = Sqlite3Model(path)

        # patch table_view which is created in _Sqlite3TableExplorer:
        self.table_view.__class__ = ModifiedTableView
        self.table_view.setModel(self.model)

        self.filter_dialog = FilterDialog(self.model, self)
        self.filter_dialog.set_visible_columns(self.visible_flags())

        # only minimalistic view:
        self.show_peaks = config.get("show_peaks", False) and self.model.has_peaks
        self.plot_frame.setVisible(self.show_peaks)
        self.eic_plotter.setMinimumSize(100, 100)
        self.mz_plotter.setMinimumSize(100, 100)
        self.eic_plotter.VIEW_RANGE_CHANGE_FINISHED.connect(self.rt_range_changed)
        self.eic_plotter.BACKSPACE_PRESSED.connect(self.plot_chromatograms)
        self.eic_plotter.enable_range(True)

        self.connect_signals()
        self.configure_dialog(config.get("id", "default"))
        self.set_styles()

    def configure_dialog(self, config_id):
        self.setup_widget_defaults()  # might be overridden by config handler
        self.update_sort_widgets()    # might be overridden by config handler
        self.config_handler = TableConfigHandler(config_id, self)
        self.config_handler.load_config()

    def setup_widget_defaults(self):
        for i in range(self.model.columnCount(None)):
            self.table_view.setColumnHidden(i, i in self.model.always_invisible)

    def _disable_signals_from_sort_widgets(self):
        self.first_sort_field.blockSignals(True)
        self.first_sort_order.blockSignals(True)
        self.second_sort_field.blockSignals(True)
        self.second_sort_order.blockSignals(True)

    def _enable_signals_from_sort_widgets(self):
        self.first_sort_field.blockSignals(False)
        self.first_sort_order.blockSignals(False)
        self.second_sort_field.blockSignals(False)
        self.second_sort_order.blockSignals(False)

    def update_sort_widgets(self):

        flags = self.visible_flags()
        self._disable_signals_from_sort_widgets()

        try:
            if self.first_sort_field.count():
                first_col_name = self.first_sort_field.currentText()
                self.first_sort_field.clear()
            else:
                # first visible column_name:
                first_col_name = (name for name, flag in flags.items() if flag).next()

            if self.second_sort_field.count():
                second_col_name = self.second_sort_field.currentText()
                self.second_sort_field.clear()
            else:
                second_col_name = ""

            self.second_sort_field.addItem("")
            for name, active in flags.items():
                if active and name not in self.model.object_columns:
                    self.first_sort_field.addItem(unicode(name))
                    self.second_sort_field.addItem(unicode(name))

        finally:
            self._enable_signals_from_sort_widgets()

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

    def filter_expression_changed(self):
        self.model.update_filter(unicode(self.current_filter.toPlainText()))

    def set_sort_fields(self, state):
        fields = state.split(",")
        if len(fields) != 4:
            return
        f1_name, f1_order, f2_name, f2_order = fields
        self._disable_signals_from_sort_widgets()
        try:

            if try_to_reactivate(self.first_sort_field, f1_name):
                try_to_reactivate(self.first_sort_order, f1_order)
            if try_to_reactivate(self.second_sort_field, f2_name):
                try_to_reactivate(self.second_sort_order, f2_order)
        finally:
            self._enable_signals_from_sort_widgets()
        self.sort_settings_changed()

    def visible_flags(self):
        flags = OrderedDict()
        for (i, name) in enumerate(self.model.col_names):
            flags[name] = not self.table_view.isColumnHidden(i)
        return flags

    def connect_signals(self):
        self.table_view.selectionModel().selectionChanged.connect(self.handle_activated)
        self.visible_columns_button.clicked.connect(self.choose_visible_columns)
        self.filter_button.clicked.connect(self.set_filter)
        self.reset_filter_button.clicked.connect(self.reset_filter)
        self.current_filter.textChanged.connect(self.filter_expression_changed)
        self.first_sort_field.currentIndexChanged.connect(self.sort_settings_changed)
        self.first_sort_order.currentIndexChanged.connect(self.sort_settings_changed)
        self.second_sort_field.currentIndexChanged.connect(self.sort_settings_changed)
        self.second_sort_order.currentIndexChanged.connect(self.sort_settings_changed)

    def handle_activated(self, new, before):
        if self.show_peaks:
            self.plot_chromatograms()
            self.eic_plotter.replot()

    def selected_rows(self):
        return set(idx.row() for idx in self.table_view.selectionModel().selectedRows())

    def rt_range_changed(self, rtmin, rtmax):
        # eventhandler, rtmin, rtmax are in seconds
        __, __, imin, imax = self.eic_plotter.get_limits()
        eics, __, __ = self._compute_chromatograms(rtmin / 60.0, rtmax / 60.0)
        if not eics:
            return

        self.eic_plotter.del_all_items()
        self.eic_plotter.add_eics(eics)
        self.eic_plotter.set_intensity_axis_limits(imin, imax)
        self.eic_plotter.add_range_item()
        self.eic_plotter.replot()

    def _selected_rt_limits(self):
        row_indices = self.selected_rows()
        return self.model.values("rtmin", row_indices), self.model.values("rtmax", row_indices)

    def _compute_chromatograms(self, rtmin=None, rtmax=None):
        eics = []
        rt_bounds = []
        for row in self.selected_rows():
            rts, intensities, label = self.model.get_chromatogram(row, rtmin=rtmin, rtmax=rtmax)
            if len(rts):
                rts = rts * 60
                rt_bounds.append(min(rts))
                rt_bounds.append(max(rts))
                eics.append((rts, intensities))
        if eics:
            return eics, min(rt_bounds), max(rt_bounds)
        else:
            return [], None, None

    def plot_chromatograms(self):
        rtmins, rtmaxs = self._selected_rt_limits()
        if not rtmins:
            return

        rtmin, rtmax = min(rtmins), max(rtmaxs)
        rtmin_w = rtmin - (rtmax - rtmin) * 0.2
        rtmax_w = rtmax + (rtmax - rtmin) * 0.2

        eics, overall_rtmin, overall_rtmax = self._compute_chromatograms(rtmin_w, rtmax_w)
        if not eics:
            return

        self.eic_plotter.del_all_items()
        self.eic_plotter.add_eics(eics)
        self.eic_plotter.set_range_selection_limits(rtmin * 60, rtmax * 60)
        self.eic_plotter.set_rt_axis_limits(rtmin_w * 60, rtmax_w * 60)
        self.eic_plotter.replot()

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
                self.current_filter.setPlainText(dlg.expression)

    def reset_filter(self, *a):
        self.model.update_filter("")
        self.current_filter.setPlainText("")

    def choose_visible_columns(self, *a):
        col_names = self.model.col_names
        if not col_names:
            return

        flags = self.visible_flags().items()
        sorted_col_names, currently_visible = zip(*flags)  # unzip

        dlg = ColumnMultiSelectDialog(sorted_col_names, currently_visible)
        dlg.exec_()
        if dlg.column_settings is None:
            return
        for (name, __, v) in dlg.column_settings:
            i = col_names.index(name)
            self.table_view.setColumnHidden(i, not v)
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



if __name__ == "__main__":

    app = QtGui.QApplication(sys.argv)
    dlg = Sqlite3TableExplorer("../tests/data/features.db")
    dlg.exec_()
