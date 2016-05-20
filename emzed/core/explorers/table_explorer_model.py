# -*- coding: utf-8 -*-

from datetime import datetime
import hashlib
import os
import re

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import guidata

from ..data_types import PeakMap, CheckState
from ..data_types.table import create_row_class
from ..data_types.hdf5_table_proxy import Hdf5TableProxy, ObjectProxy

from ... import algorithm_configs

from .table_explorer_model_actions import *

from ..config import folders

from .helpers import timethis


def isUrl(what):
    what = unicode(what)
    return what.startswith(u"http://") or what.startswith(u"https://")


class TableModel(QAbstractTableModel):

    LIGHT_BLUE = QColor(200, 200, 255)
    WHITE = QColor(255, 255, 255)

    VISIBLE_ROWS_CHANGE = pyqtSignal(int, int)
    SORT_TRIGGERED = pyqtSignal(str, bool)
    ACTION_LIST_CHANGED = pyqtSignal(object, object)

    def __init__(self, table, parent):
        super(TableModel, self).__init__(parent)
        self.table = table
        self.parent = parent
        # self.view_widget = view_widget
        nc = len(self.table._colNames)
        self.indizesOfVisibleCols = [j for j in range(nc) if self.table._colFormats[j] is not None]
        self.widgetColToDataCol = dict(enumerate(self.indizesOfVisibleCols))
        nr = len(table)

        self.row_permutation = range(nr)
        self.visible_rows = set(range(nr))
        self.update_row_view()

        self.emptyActionStack()

        self.last_filters = None
        self.setFiltersEnabled(False)

        self.selected_data_rows = []
        self.counter_for_calls_to_sort = 0
        self.load_preset_hidden_column_names()

    def set_row_permutation(self, permutation):
        self.row_permutation = list(permutation)

    def get_row_permutation(self):
        return self.row_permutation

    def update_row_view(self):
        self.widgetRowToDataRow = [row_idx for row_idx in self.row_permutation if row_idx in
                                   self.visible_rows]
        self.dataRowToWidgetRow = {row: i for (i, row) in enumerate(self.widgetRowToDataRow)}

    def set_selected_widget_rows(self, widget_rows):
        self.selected_data_rows = self.transform_row_idx_widget_to_model(widget_rows)

    def setFiltersEnabled(self, flag):
        self.filters_enabled = flag
        self.update_visible_rows_for_given_limits()

    def emptyActionStack(self):
        self.actions = []
        self.redoActions = []

    def rowCount(self, index=QModelIndex()):
        return len(self.widgetRowToDataRow)

    def columnCount(self, index=QModelIndex()):
        return len(self.widgetColToDataCol)

    def column_name(self, index):
        if isinstance(index, (int, long)):
            col = self.widgetColToDataCol[index]
        else:
            __, col = self.table_index(index)
        return self.table.getColNames()[col]

    def column_type(self, index):
        if isinstance(index, (int, long)):
            col = self.widgetColToDataCol[index]
        else:
            __, col = self.table_index(index)
        return self.table.getColTypes()[col]

    def table_index(self, index):
        cidx = self.widgetColToDataCol[index.column()]
        ridx = self.widgetRowToDataRow[index.row()]
        return ridx, cidx

    def cell_value(self, index):
        ridx, cidx = self.table_index(index)
        value = self.table.rows[ridx][cidx]
        return value

    def set_all(self, widget_col_index, value):
        data_col_index = self.widgetColToDataCol[widget_col_index]
        data_row_indices = self.widgetRowToDataRow
        done = self.runAction(ChangeAllValuesInColumnAction, widget_col_index, data_row_indices,
                              data_col_index, value)
        if done:
            self.update_visible_rows_for_given_limits()
        return done

    def row(self, index):
        ridx, cidx = self.table_index(index)
        row = create_row_class(self.table)(self.table.rows[ridx])
        return row

    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def font(self, index):
        content = self.data(index, Qt.DisplayRole)
        if isUrl(content):
            font = QFont(super(TableModel, self).data(index, Qt.DisplayRole))
            font.setUnderline(True)
            return font
        return QVariant()

    def check_state_data(self, index, role):
        if role == Qt.CheckStateRole:
            value = self.cell_value(index)
            if value is None:
                return QVariant()
            return Qt.Checked if value else Qt.Unchecked
        elif role == Qt.DisplayRole:
            return QString("")
        return QVariant()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()

        if role == Qt.FontRole:
            return self.font(index)

        if self.column_type(index) is CheckState:
            return self.check_state_data(index, role)

        if role != Qt.DisplayRole:
            return QVariant()

        value = self.cell_value(index)
        if isinstance(value, ObjectProxy):
            value = value.load()

        ridx, cidx = self.table_index(index)
        fmter = self.table.colFormatters[cidx]

        if isinstance(value, datetime):
            fmt = self.table.getColFormats()[cidx]
            if fmt in ("%r", "%s"):
                shown = value.strftime(self.DATE_FORMAT)
            else:
                try:
                    shown = fmter(value)
                except Exception:
                    shown = value.strftime(self.DATE_FORMAT)
        else:
            shown = fmter(value)
        return QString(shown)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()
        if orientation == Qt.Horizontal:
            dataIdx = self.widgetColToDataCol[section]
            return str(self.table._colNames[dataIdx])
        # vertical header:
        return QString("   ")

    def runAction(self, clz, *a):
        action = clz(self, *a)
        done = action.do()
        if not done:
            return done
        self.actions.append(action)
        self.redoActions = []
        self.emit_updated_actions()
        return done

    def emit_updated_actions(self):
        last_action = unicode(self.actions[-1]) if self.actions else None
        last_redo_action = unicode(self.redoActions[-1]) if self.redoActions else None
        self.ACTION_LIST_CHANGED.emit(last_action, last_redo_action)

    def infoLastAction(self):
        if len(self.actions):
            return unicode(self.actions[-1])
        return None

    def infoRedoAction(self):
        if len(self.redoActions):
            return unicode(self.redoActions[-1])
        return None

    def undoLastAction(self):
        if len(self.actions):
            action = self.actions.pop()
            self.beginResetModel()
            action.undo()
            self.update_visible_rows_for_given_limits()  # does endResetModel
            self.redoActions.append(action)
            self.emit_updated_actions()

    def redoLastAction(self):
        if len(self.redoActions):
            action = self.redoActions.pop()
            self.beginResetModel()
            action.do()
            self.update_visible_rows_for_given_limits()  # does endResetModel
            self.actions.append(action)
            self.emit_updated_actions()
            return

    def sort(self, colIdx, order=Qt.AscendingOrder):
        # the counter is a dirty hack: during startup of table explorer the sort method is
        # called twice automatically, so the original order of the table is not maintained
        # in the view when the explorer windows shows up.
        # we count the calls ignore the first two calls. after that sorting is only done if
        # the user clicks to a column heading.
        # this is a dirty hack but I cound not find out why sort() is called twice.
        # the first call is triggered by setSortingEnabled() in the table view, the origin
        # of the second call is unclear.
        self.counter_for_calls_to_sort += 1
        if self.counter_for_calls_to_sort > 2:
            if len(self.widgetColToDataCol):
                dataColIdx = self.widgetColToDataCol[colIdx]
                name = self.table._colNames[dataColIdx]
                self.sort_by([(name, "asc" if order == Qt.AscendingOrder else "desc")])
                self.SORT_TRIGGERED.emit(name, order == Qt.AscendingOrder)

    def widget_col(self, col_name):
        data_col_idx = self.table._colNames.index(col_name)
        for widget_col, data_col in self.widgetColToDataCol.items():
            if data_col == data_col_idx:
                return widget_col

    def sort_by(self, sort_data):
        data_cols = [(name, order.startswith("asc")) for (name, order) in sort_data]
        self.runAction(SortTableAction, data_cols)
        self.update_visible_rows_for_given_limits(force_reset=True)

    def eicColNames(self):
        return ["peakmap", "mzmin", "mzmax", "rtmin", "rtmax"]

    def hasFeatures(self):
        return self.checkForAny(*self.eicColNames())

    def hasEIC(self):
        return self.checkForAny("eic")

    def hasTimeSeries(self):
        return self.checkForAny("time_series")

    def hasSpectra(self):
        return any(n.startswith("spectra") for n in self.table.getColNames())

    def integrationColNames(self):
        return ["area", "rmse", "method", "params", "baseline"]

    def getIntegrationValues(self, data_row_idx, p):
        def get(nn):
            value = self.table.getValue(self.table.rows[data_row_idx], nn + p)
            return value
        return dict((nn + p, get(nn)) for nn in self.integrationColNames())

    def isIntegrated(self):
        return self.hasFeatures() and self.checkForAny(*self.integrationColNames())

    def checkForAny(self, *names):
        """
        checks if names appear at least once as prefixes in current colNames
        """
        return len(self.table.supportedPostfixes(names)) > 0

    def getTitle(self):
        table = self.table
        if table.title:
            title = table.title
        else:
            title = os.path.basename(table.meta.get("source", ""))
        return title

    def getShownColumnName(self, col_idx):
        """ lookup name of visible column #col_idx """
        data_col_idx = self.widgetColToDataCol[col_idx]
        return self.table.getColNames()[data_col_idx]

    def lookup(self, look_for, col_name):
        look_for = unicode(look_for).strip()
        ix = self.table.getIndex(col_name)
        formatter = self.table.colFormatters[ix]
        for row, value in enumerate(getattr(self.table, col_name)):
            if formatter(value).strip() == look_for:
                return row
        return None

    def getFittedPeakshapes(self, data_row_idx, rts):
        shapes = []
        for p in self.table.supportedPostfixes(self.integrationColNames()):
            values = self.getIntegrationValues(data_row_idx, p)
            method = values["method" + p]
            params = values["params" + p]
            integrator = dict(algorithm_configs.peakIntegrators).get(method)
            if method is not None and params is not None and integrator is not None:
                # data is a tuple with two onedim numpy arrays:
                data = integrator.getSmoothed(rts, params)
                # baseline is a numerical value or None
                baseline = integrator.getBaseline(rts, params)
            else:
                data = baseline = None
            shapes.append((data, baseline))
        return shapes

    def getPeakmaps(self, data_row_idx):
        peakMaps = []
        for p in self.table.supportedPostfixes(["peakmap"]):
            pm = self.table.getValue(self.table.rows[data_row_idx], "peakmap" + p)
            if pm is None:
                pm = PeakMap([])
            peakMaps.append(pm)
        return peakMaps

    def getEICWindows(self, data_row_idx):
        windows = []
        for p in self.table.supportedPostfixes(["rtmin", "rtmax", "mzmin", "mzmax"]):
            rtmin = self.table.getValue(self.table.rows[data_row_idx], "rtmin" + p)
            rtmax = self.table.getValue(self.table.rows[data_row_idx], "rtmax" + p)
            mzmin = self.table.getValue(self.table.rows[data_row_idx], "mzmin" + p)
            mzmax = self.table.getValue(self.table.rows[data_row_idx], "mzmax" + p)
            if all((rtmin is not None, rtmax is not None, mzmin is not None, mzmax is not None)):
                windows.append((rtmin, rtmax, mzmin, mzmax))
        return windows

    def getTimeSeries(self, data_row_idx):
        time_series = []
        for p in self.table.supportedPostfixes(["time_series",]):
            ts = self.table.getValue(self.table.rows[data_row_idx], "time_series" + p)
            time_series.append(ts)
        return time_series

    def getMS2Spectra(self, data_row_idx):
        spectra = []
        postfixes = []
        for p in self.table.supportedPostfixes(("spectra_ms2",)):
            values = self.table.getValues(self.table.rows[data_row_idx])
            specs = values["spectra_ms2" + p]
            spectra.append(specs)
            postfixes.append(p)
        return postfixes, spectra

    def numbersOfEicsPerRow(self):
        return len(self.table.supportedPostfixes(self.eicColNames()))

    def __len__(self):
        return len(self.widgetRowToDataRow)

    def computeEics(self, data_row_idx):
        eics = []
        mzmins = []
        mzmaxs = []
        rtmins = []
        rtmaxs = []
        allrts = []
        for p in self.table.supportedPostfixes(self.eicColNames()):
            values = self.table.getValues(self.table.rows[data_row_idx])
            pm = values["peakmap" + p]
            mzmin = values["mzmin" + p]
            mzmax = values["mzmax" + p]
            rtmin = values["rtmin" + p]
            rtmax = values["rtmax" + p]
            if mzmin is None or mzmax is None or rtmin is None or rtmax is None:
                chromo = [], []
            else:
                chromo = pm.chromatogram(mzmin, mzmax, rtmin, rtmax)
                mzmins.append(mzmin)
                mzmaxs.append(mzmax)
                rtmins.append(rtmin)
                rtmaxs.append(rtmax)
            eics.append(chromo)
            allrts.extend(chromo[0])
        if not mzmins:
            return eics, 0, 0, 0, 0, sorted(allrts)
        return eics, min(rtmins), max(rtmaxs),\
            sorted(allrts)

    def rows_with_same_value(self, col_name, widget_row_idx):
        data_row_idx = self.widgetRowToDataRow[widget_row_idx]
        selected_value = timethis(self.table.getValue)(self.table.rows[data_row_idx], col_name)

        def equals(value):
            return value == selected_value

        selected_data_rows = timethis(self.table.findMatchingRows)([(col_name, equals)])
        selected_data_rows = [r for r in selected_data_rows if r in self.visible_rows]
        return [self.dataRowToWidgetRow[i] for i in selected_data_rows]

    def transform_row_idx_widget_to_model(self, row_idxs):
        return [self.widgetRowToDataRow[i] for i in row_idxs]

    def getEics(self, data_row_idx):
        eics = []
        rtmins = []
        rtmaxs = []
        allrts = []
        for p in self.table.supportedPostfixes(["eic"]):
            values = self.table.getValues(self.table.rows[data_row_idx])
            rtmin = values.get("rtmin" + p)   # might be missing in table
            rtmax = values.get("rtmax" + p)   # might be missing in table
            eic = values["eic" + p]           # must be there !
            if eic is not None:
                eics.append(eic)
                rts, iis = eic
                if rtmin is not None:
                    rtmins.append(rtmin)
                else:
                    rtmins.append(min(rts))
                if rtmax is not None:
                    rtmaxs.append(rtmax)
                else:
                    rtmaxs.append(max(rts))
                allrts.extend(rts)
        return eics, min(rtmins) if rtmins else None, max(rtmaxs) if rtmaxs else None, sorted(allrts)

    def remove_filtered(self):
        to_delete = range(len(self.widgetRowToDataRow))
        self.removeRows(to_delete)

    def limits_changed(self, filters):
        self.last_filters = filters
        self.update_visible_rows_for_given_limits()

    def update_visible_rows_for_given_limits(self, force_reset=False):
        if self.filters_enabled is False:
            filters = {}
        else:
            if self.last_filters is None:
                filters = {}
            else:
                filters = self.last_filters

        visible_rows = self.table.findMatchingRows(filters.items())

        if force_reset or visible_rows != self.visible_rows:
            self.visible_rows = visible_rows
            self.beginResetModel()
            self.update_row_view()
            self.endResetModel()
            self.emit_visible_rows_change()

    def emit_visible_rows_change(self):
        n_visible = len(self.widgetRowToDataRow)
        self.VISIBLE_ROWS_CHANGE.emit(len(self.table), n_visible)

    def store_table_as_csv(self, path):
        self.table.storeCSV(path, as_printed=True, row_indices=self.widgetRowToDataRow)

    def columnames_with_visibility(self):
        avail = self.indizesOfVisibleCols
        names = [self.table.getColNames()[i] for i in avail]
        visible = [i in self.widgetColToDataCol.values() for i in avail]
        return names, visible

    def visible_column_names(self):
        avail = self.indizesOfVisibleCols
        names = [self.table.getColNames()[i] for i in avail]
        return names

    def _set_visible_cols(self, col_indices):
        self.beginResetModel()
        self.widgetColToDataCol = dict(enumerate(col_indices))
        self.endResetModel()

    def _settings_path(self):
        folder = folders.getEmzedFolder()
        digest = hashlib.md5()
        for name in self.table.getColNames():
            digest.update(name)
        file_name = "table_view_setting_%s.txt" % digest.hexdigest()
        path = os.path.join(folder, file_name)
        return path

    def save_preset_hidden_column_names(self):
        path = self._settings_path()
        names = self.table.getColNames()
        try:
            with open(path, "w") as fp:
                for i, j in self.widgetColToDataCol.items():
                    print >> fp, i, names[j]
        except IOError, e:
            print str(e)

    def load_preset_hidden_column_names(self):
        path = self._settings_path()
        if os.path.exists(path):
            shown = set()
            dd = {}
            names = self.table.getColNames()
            try:
                with open(path, "r") as fp:
                    for line in fp:
                        i, name = line.strip().split()
                        if name in names:
                            dd[int(i)] = names.index(name)
                            shown.add(name)
                self.beginResetModel()
                self.widgetColToDataCol = dd
                self.endResetModel()
            except (IOError, ValueError), e:
                print(str(e))
            return shown

    def hide_columns(self, names_to_hide):
        names = self.table.getColNames()
        col_indices = []
        for ix in self.indizesOfVisibleCols:
            name = names[ix]
            if name not in names_to_hide:
                col_indices.append(ix)
        self._set_visible_cols(col_indices)

    def implements(self, method_name):
        return hasattr(self, method_name)

    @staticmethod
    def table_model_for(table, parent=None):
        if isinstance(table, Hdf5TableProxy):
            return MutableTableModel(table, parent)
        else:
            return MutableTableModel(table, parent)


class MutableTableModel(TableModel):

    def __init__(self, table, parent):
        super(MutableTableModel, self).__init__(table, parent)
        self.nonEditables = set()

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.EditRole:
            shown = super(MutableTableModel, self).data(index, Qt.DisplayRole)
            print(repr(shown))
            return unicode(shown)
        else:
            return super(MutableTableModel, self).data(index, role)

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        default = super(TableModel, self).flags(index)
        # urls are not editable
        if isUrl(self.data(index)):
            return default
        if self.widgetColToDataCol[index.column()] in self.nonEditables:
            return default
        if self.column_type(index) is CheckState:
            value = self.cell_value(index)
            if value is None:
                return Qt.ItemFlags(default)
            else:
                return Qt.ItemFlags(default | Qt.ItemIsEditable | Qt.ItemIsUserCheckable)
        else:
            return Qt.ItemFlags(default | Qt.ItemIsEditable) #  | Qt.ItemIsUserCheckable)

    def setData(self, index, value, role=Qt.EditRole):
        ridx, cidx = self.table_index(index)
        if index.isValid() and 0 <= index.row() < self.rowCount():
            expectedType = self.table._colTypes[cidx]
            if value.toString().trimmed() == "-":
                value = None
            elif expectedType is CheckState:
                value = (value == Qt.Checked)
            elif expectedType != object:
                # QVariant -> QString -> unicode + strip:
                value = unicode(value.toString()).strip()
                # floating point number + "m for minutes ?
                if re.match("^((\d+m)|(\d*.\d+m))$", value):
                    try:
                        value = 60.0 * float(value[:-1])
                    except Exception:
                        guidata.qapplication().beep()
                        return False
                if expectedType == datetime:
                    try:
                        value = datetime.strptime(value, self.DATE_FORMAT)
                    except Exception:
                        guidata.qapplication().beep()
                        return False
                elif expectedType == bool:
                    if value.lower() in ("true", "false"):
                        value = (value.lower() == "true")
                    else:
                        guidata.qapplication().beep()
                        return False
                else:
                    try:
                        value = expectedType(value)
                    except Exception:
                        guidata.qapplication().beep()
                        return False
            done = self.runAction(ChangeValueAction, index, ridx, cidx, value)
            if done:
                self.update_visible_rows_for_given_limits()
            return done
        return False

    def addNonEditable(self, name):
        dataColIdx = self.table.getIndex(name)
        self.nonEditables.add(dataColIdx)

    def cloneRow(self, widget_row_idx):
        data_row_idx = self.widgetRowToDataRow[widget_row_idx]
        self.beginInsertRows(QModelIndex(), widget_row_idx, widget_row_idx)
        self.runAction(CloneRowAction, widget_row_idx, data_row_idx)
        self.endInsertRows()
        self.update_visible_rows_for_given_limits()  # does endResetModel
        return True

    def removeRows(self, widget_row_indices):
        data_row_indices = self.transform_row_idx_widget_to_model(widget_row_indices)
        mini = min(widget_row_indices)
        maxi = max(widget_row_indices)
        self.beginRemoveRows(QModelIndex(), mini, maxi)
        self.runAction(DeleteRowsAction, widget_row_indices, data_row_indices)
        self.endRemoveRows()
        self.update_visible_rows_for_given_limits()  # does endResetModel
        return True

    def integrate(self, data_row_idx, postfix, method, rtmin, rtmax):
        for widget_row_idx, ridx in enumerate(self.widgetRowToDataRow):
            if data_row_idx == ridx:
                break
        else:
            raise Exception("this should never happen !")

        self.runAction(IntegrateAction, data_row_idx, postfix, method, rtmin, rtmax,
                       widget_row_idx)
        self.dataChanged.emit(self.index(widget_row_idx, 0),
                              self.index(widget_row_idx, self.columnCount() - 1))
        self.update_visible_rows_for_given_limits()

    def setNonEditable(self, colBaseName, group):
        for postfix in self.table.supportedPostfixes(group):
            if self.table.hasColumns(colBaseName + postfix):
                self.addNonEditable(colBaseName + postfix)

    def restrict_to_filtered(self):
        shown_data_rows = self.widgetRowToDataRow
        delete_data_rows = set(range(len(self.table))) - set(shown_data_rows)
        self.runAction(DeleteRowsAction, [], delete_data_rows)
        self.update_visible_rows_for_given_limits()
        return True
