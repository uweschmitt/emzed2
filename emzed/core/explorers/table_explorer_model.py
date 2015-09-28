# -*- coding: utf-8 -*-

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from ..data_types import PeakMap, TimeSeries
from ..data_types.table import create_row_class

import guidata

import hashlib
import os
import re
from datetime import datetime

from ... import algorithm_configs


from .table_explorer_model_actions import *

from ..config import folders


def isUrl(what):
    return what.startswith("http://") or what.startswith("https://")


class TableModel(QAbstractTableModel):

    LIGHT_BLUE = QColor(200, 200, 255)
    WHITE = QColor(255, 255, 255)

    DATA_CHANGE = pyqtSignal(object, object)
    SORT_TRIGGERED = pyqtSignal(str, bool)
 
    def __init__(self, table, view):
        parent = view
        super(TableModel, self).__init__(parent)
        self.table = table
        self.view = view
        nc = len(self.table._colNames)
        self.indizesOfVisibleCols = [j for j in range(nc) if self.table._colFormats[j] is not None]
        self.widgetColToDataCol = dict(enumerate(self.indizesOfVisibleCols))
        nr = len(table)
        self.widgetRowToDataRow = dict(zip(range(nr), range(nr)))
        self.dataRowToWidgetRow = dict(zip(range(nr), range(nr)))
        self.emptyActionStack()

        self.nonEditables = set()

        self.last_limits = None
        self.setFiltersEnabled(False)

        self.selected_data_rows = []
        self.counter_for_calls_to_sort = 0
        self.load_preset_hidden_column_names()

    def set_selected_data_rows(self, widget_rows):
        self.selected_data_rows = self.transform_row_idx_widget_to_model(widget_rows)

    def setFiltersEnabled(self, flag):
        self.filters_enabled = flag
        self.update_visible_rows_for_given_limits()

    def addNonEditable(self, name):
        dataColIdx = self.table.getIndex(name)
        self.nonEditables.add(dataColIdx)

    def emptyActionStack(self):
        self.actions = []
        self.redoActions = []

    def getRow(self, idx):
        r = self.widgetRowToDataRow[idx]
        return self.table.getValues(self.table.rows[r])

    def rowCount(self, index=QModelIndex()):
        return len(self.widgetRowToDataRow)

    def columnCount(self, index=QModelIndex()):
        return len(self.widgetColToDataCol)

    def column_name(self, index):
        __, col = self.table_index(index)
        return self.table.getColNames()[col]

    def table_index(self, index):
        cidx = self.widgetColToDataCol[index.column()]
        ridx = self.widgetRowToDataRow[index.row()]
        return ridx, cidx

    def cell_value(self, index):
        ridx, cidx = self.table_index(index)
        value = self.table.rows[ridx][cidx]
        return value

    def row(self, index):
        ridx, cidx = self.table_index(index)
        row = create_row_class(self.table)(self.table.rows[ridx])
        return row

    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        ridx, cidx = self.table_index(index)
        if not (0 <= index.row() < self.rowCount()):
            return QVariant()
        value = self.table.rows[ridx][cidx]
        fmter = self.table.colFormatters[cidx]

        if isinstance(value, datetime):
            fmt = self.table.getColFormats()[cidx]
            if fmt in ("%r", "%s"):
                shown = value.strftime(self.DATE_FORMAT)
            else:
                try:
                    shown = fmter(value)
                except:
                    shown = value.strftime(self.DATE_FORMAT)
            if role in (Qt.DisplayRole, Qt.EditRole):
                return shown
        else:
            shown = fmter(value)

        if role == Qt.DisplayRole:
            return shown
        if role == Qt.EditRole:
            colType = self.table._colTypes[cidx]
            if colType in (int, float, str, unicode):
                if shown.strip().endswith("m"):
                    return shown
                try:
                    colType(shown)
                    return shown
                except:
                    if colType == float:
                        return "-" if value is None else "%.4f" % value
                    return unicode(value) if value is not None else "-"
            return unicode(value) if value is not None else "-"
        if role == Qt.FontRole:
            content = self.data(index)
            if isUrl(content):
                font = QFont(super(TableModel, self).data(index, Qt.DisplayRole))
                font.setUnderline(True)
                return font

        return QVariant()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()
        if orientation == Qt.Horizontal:
            dataIdx = self.widgetColToDataCol[section]
            return str(self.table._colNames[dataIdx])
        # vertical header:
        return QString("   ")

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        default = super(TableModel, self).flags(index)
        # urls are not editable
        if isUrl(self.data(index)):
            return default
        if self.widgetColToDataCol[index.column()] in self.nonEditables:
            return default
        return Qt.ItemFlags(default | Qt.ItemIsEditable)

    def setData(self, index, value, role=Qt.EditRole):
        assert isinstance(value, QVariant)
        ridx, cidx = self.table_index(index)
        if index.isValid() and 0 <= index.row() < self.rowCount():
            expectedType = self.table._colTypes[cidx]
            if value.toString().trimmed() == "-":
                value = None
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

    def runAction(self, clz, *a):
        action = clz(self, *a)
        done = action.do()
        if not done:
            return done
        self.actions.append(action)
        self.redoActions = []
        self.view.updateMenubar()
        return done

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
            self.update_visible_rows_for_given_limits(force_reset=True)  # does endResetModel
            self.redoActions.append(action)
            self.view.updateMenubar()

    def redoLastAction(self):
        if len(self.redoActions):
            action = self.redoActions.pop()
            self.beginResetModel()
            action.do()
            self.update_visible_rows_for_given_limits(force_reset=True)  # does endResetModel
            self.actions.append(action)
            self.view.updateMenubar()
            return

    def cloneRow(self, widget_row_idx):
        data_row_idx = self.widgetRowToDataRow[widget_row_idx]
        self.beginResetModel()
        self.runAction(CloneRowAction, widget_row_idx, data_row_idx)
        self.update_visible_rows_for_given_limits()  # does endResetModel
        return True

    def removeRows(self, widget_row_indices):
        data_row_indices = self.transform_row_idx_widget_to_model(widget_row_indices)
        self.beginResetModel()
        self.runAction(DeleteRowsAction, widget_row_indices, data_row_indices)
        self.update_visible_rows_for_given_limits()  # does endResetModel
        return True

    def removeRow(self, *a):
        raise RuntimeError("obsolte method, use removeRows instead")

    def sort(self, colIdx, order=Qt.AscendingOrder):
        # the counter is a dirty hack: during startup of table explorer the sort method is
        # called twice automatically, so the original order of the table is not maintained
        # in the view when the explorer windows shows up.
        # we count the calls ignore the first two calls. then sorting is only done if
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
        cn = self.table._colNames
        data_cols = [(name, order.startswith("asc")) for (name, order) in sort_data]
        self.beginResetModel()
        self.runAction(SortTableAction, data_cols)
        self.update_visible_rows_for_given_limits(force_reset=True)  # does endResetModel

    def integrate(self, data_row_idx, postfix, method, rtmin, rtmax):
        self.beginResetModel()
        self.runAction(IntegrateAction, postfix, data_row_idx, method, rtmin, rtmax,
                       self.dataRowToWidgetRow)
        self.update_visible_rows_for_given_limits(force_reset=False)  # does endResetModel

    def eicColNames(self):
        return ["peakmap", "mzmin", "mzmax", "rtmin", "rtmax"]

    def hasFeatures(self):
        return self.checkForAny(*self.eicColNames())

    def hasEIC(self):
        return self.checkForAny("eic")

    def hasTimeSeries(self):
        return any(t is TimeSeries for t in self.table.getColTypes())

    def hasExtraSpectra(self):
        return any(n.startswith("spectra") for n in self.table.getColNames())

    def integrationColNames(self):
        return ["area", "rmse", "method", "params", "baseline"]

    def getIntegrationValues(self, data_row_idx, p):
        get = lambda nn: self.table.getValue(self.table.rows[data_row_idx], nn + p)
        return dict((nn + p, get(nn)) for nn in self.integrationColNames())

    def isIntegrated(self):
        return self.hasFeatures() and self.checkForAny(*self.integrationColNames())

    def checkForAny(self, *names):
        """
        checks if names appear at least once as prefixes in current colNames
        """
        return len(self.table.supportedPostfixes(names)) > 0

    def setNonEditable(self, colBaseName, group):
        for postfix in self.table.supportedPostfixes(group):
            if self.table.hasColumns(colBaseName + postfix):
                self.addNonEditable(colBaseName + postfix)

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
            if method is not None:
                # data is a tuple with two onedim numpy arrays:
                data = integrator.getSmoothed(rts, params)
                # baslein is a numerical value or None
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
        ts = []
        cols = [i for (i, t) in enumerate(self.table.getColTypes()) if t is TimeSeries]
        row = self.table.rows[data_row_idx]
        return [row[c] for c in cols]

    def getExtraSpectra(self, data_row_idx):
        spectra = []
        postfixes = []
        for p in self.table.supportedPostfixes(("spectra",)):
            values = self.table.getValues(self.table.rows[data_row_idx])
            specs = values["spectra" + p]
            spectra.append(specs)
            postfixes.append(p)
        return postfixes, spectra

    def extractEICs(self, data_row_idx):
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
                chromo = pm.chromatogram(mzmin, mzmax)
                mzmins.append(mzmin)
                mzmaxs.append(mzmax)
                rtmins.append(rtmin)
                rtmaxs.append(rtmax)
            eics.append(chromo)
            allrts.extend(chromo[0])
        if not mzmins:
            return eics, 0, 0, 0, 0, sorted(allrts)
        return eics, min(mzmins), max(mzmaxs), min(rtmins), max(rtmaxs),\
            sorted(allrts)

    def rows_with_same_value(self, col_name, widget_row_idx):
        t = self.table
        data_row_idx = self.widgetRowToDataRow[widget_row_idx]
        selected_value = t.getValue(t.rows[data_row_idx], col_name)
        selected_data_rows = [i for i, row in enumerate(t.rows)
                              if t.getValue(row, col_name) == selected_value]
        # view might be filtered, so only select what we can see:
        selected_data_rows = [i for i in selected_data_rows if i in self.dataRowToWidgetRow]
        return self.transform_row_idx_model_to_widget(selected_data_rows)

    def transform_row_idx_widget_to_model(self, row_idxs):
        return [self.widgetRowToDataRow[i] for i in row_idxs]

    def transform_row_idx_model_to_widget(self, row_idxs):
        return [self.dataRowToWidgetRow[i] for i in row_idxs]

    def getEICs(self, data_row_idx):
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
        return eics, min(rtmins) if rtmins else None, max(rtmaxs) if rtmaxs else rtmax, sorted(allrts)

    def remove_filtered(self):
        to_delete = sorted(self.widgetRowToDataRow.keys())  # sort for nicer undo/redo description
        self.removeRows(to_delete)

    def restrict_to_filtered(self):
        shown_data_rows = self.widgetRowToDataRow.values()
        delete_data_rows = set(range(len(self.table))) - set(shown_data_rows)
        self.beginResetModel()
        self.runAction(DeleteRowsAction, [], delete_data_rows)
        self.update_visible_rows_for_given_limits()  # does endResetModel
        return True

    def limits_changed(self, limits):
        self.last_limits = limits
        self.update_visible_rows_for_given_limits()

    def update_visible_rows_for_given_limits(self, force_reset=False):
        if self.filters_enabled is False:
            limits = {}
        else:
            if self.last_limits is None:
                limits = {}
            else:
                limits = self.last_limits

        t = self.table
        all_rows_to_remain = set(range(len(t)))

        for name, filter_function in limits.items():

            if filter_function is None:
                continue

            col_idx = t.getIndex(name)
            rows_to_remain = set()
            for j, row in enumerate(t):
                match = filter_function(row[col_idx])
                if match:
                    rows_to_remain.add(j)
            all_rows_to_remain = all_rows_to_remain.intersection(rows_to_remain)

        widget_row_to_data_row = {}
        data_row_to_widget_row = {}
        for view_idx, row_idx in enumerate(sorted(all_rows_to_remain)):
            widget_row_to_data_row[view_idx] = row_idx
            data_row_to_widget_row[row_idx] = view_idx

        if force_reset or widget_row_to_data_row != self.widgetRowToDataRow:
            # only reset view if something changed

            self.beginResetModel()
            self.widgetRowToDataRow = dict()
            self.dataRowToWidgetRow = dict()
            self.widgetRowToDataRow = widget_row_to_data_row
            self.dataRowToWidgetRow = data_row_to_widget_row
            self.endResetModel()
            self.emit_data_change()

    def emit_data_change(self):
        visible_table = self.table[self.widgetRowToDataRow.values()]
        self.DATA_CHANGE.emit(self.table, visible_table)

    def extract_visible_table(self):
        row_idxs = [didx for (widx, didx) in sorted(self.widgetRowToDataRow.items())]
        return self.table[row_idxs]

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
            dd = {}
            names = self.table.getColNames()
            try:
                with open(path, "r") as fp:
                    for line in fp:
                        i, name = line.strip().split()
                        if name in names:
                            dd[int(i)] = names.index(name)
                self.beginResetModel()
                self.widgetColToDataCol = dd
                self.endResetModel()
            except (IOError, ValueError), e:
                print(str(e))

    def hide_columns(self, names_to_hide):
        names = self.table.getColNames()
        col_indices = []
        for ix in self.indizesOfVisibleCols:
            name = names[ix]
            if name not in names_to_hide:
                col_indices.append(ix)
        self._set_visible_cols(col_indices)
