# -*- coding: utf-8 -*-

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from ..data_types import PeakMap

import guidata

import os
import re

from ... import _algorithm_configs


from .table_explorer_model_actions import *


def isUrl(what):
    return what.startswith("http://")



class TableModel(QAbstractTableModel):

    LIGHT_BLUE = QColor(200, 200, 255)
    WHITE = QColor(255, 255, 255)

    DATA_CHANGE = pyqtSignal(object, object)

    def __init__(self, table, view):
        parent = view
        super(TableModel, self).__init__(parent)
        self.table = table
        self.view = view
        nc = len(self.table._colNames)
        self.indizesOfVisibleCols = [j for j in range(nc)
                                     if self.table._colFormats[j] is not None]
        self.widgetColToDataCol = dict(enumerate(self.indizesOfVisibleCols))
        nr = len(table)
        self.widgetRowToDataRow = dict(zip(range(nr), range(nr)))
        self.emptyActionStack()

        self.nonEditables = set()

        self.last_limits = None
        self.setFiltersEnabled(False)

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
        return self.table.getValues(self.table.rows[ridx])

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        ridx, cidx = self.table_index(index)
        if not (0 <= index.row() < self.rowCount()):
            return QVariant()
        value = self.table.rows[ridx][cidx]
        shown = self.table.colFormatters[cidx](value)
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
                    return unicode(value)
            return unicode(value)
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
            return self.table._colNames[dataIdx]
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
            self.update_visible_rows_for_given_limits()  # does endResetModel
            self.redoActions.append(action)
            self.view.updateMenubar()

    def redoLastAction(self):
        if len(self.redoActions):
            action = self.redoActions.pop()
            self.beginResetModel()
            action.do()
            self.update_visible_rows_for_given_limits()  # does endResetModel
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
        data_row_indices = [self.widgetRowToDataRow[ix] for ix in widget_row_indices]
        self.beginResetModel()
        self.runAction(DeleteRowsAction, widget_row_indices, data_row_indices)
        self.update_visible_rows_for_given_limits()  # does endResetModel
        return True

    def removeRow(self, *a):
        raise RuntimeError("obsolte method, use removeRows instead")

    def sort(self, colIdx, order=Qt.AscendingOrder):
        if len(self.widgetColToDataCol):
            dataColIdx = self.widgetColToDataCol[colIdx]
            self.beginResetModel()
            self.runAction(SortTableAction, dataColIdx, colIdx, order)
            self.current_sort_col_idx = colIdx
            self.update_visible_rows_for_given_limits()  # does endResetModel

    def integrate(self, data_row_idx, postfix, method, rtmin, rtmax):
        self.beginResetModel()
        self.runAction(IntegrateAction, postfix, data_row_idx, method, rtmin, rtmax,
                       self.dataRowtoWidgetRow)
        self.update_visible_rows_for_given_limits()  # does endResetModel

    def eicColNames(self):
        return ["peakmap", "mzmin", "mzmax", "rtmin", "rtmax"]

    def hasFeatures(self):
        return self.checkForAny(*self.eicColNames())

    def integrationColNames(self):
        return ["area", "rmse", "method", "params"]

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
        if self.hasFeatures():
            title += " rt_aligned=%s" % table.meta.get("rt_aligned", "False")
            title += " mz_aligned=%s" % table.meta.get("mz_aligned", "False")
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

    def getSmoothedEics(self, data_row_idx, rts):
        allsmoothed = []
        for p in self.table.supportedPostfixes(self.integrationColNames()):
            values = self.getIntegrationValues(data_row_idx, p)
            method = values["method" + p]
            params = values["params" + p]
            integrator = dict(_algorithm_configs.peakIntegrators).get(method)
            data = ([], [])
            if method is not None:
                try:
                    data = integrator.getSmoothed(rts, params)
                except:
                    # maybe overflow or something like this
                    pass
            allsmoothed.append(data)
        return allsmoothed

    def getPeakmaps(self, data_row_idx):
        peakMaps = []
        for p in self.table.supportedPostfixes(["peakmap"]):
            pm = self.table.getValue(self.table.rows[data_row_idx], "peakmap" + p)
            if pm is None:
                pm = PeakMap([])
            peakMaps.append(pm)
        return peakMaps

    def getLevelNSpectra(self, data_row_idx, minLevel=2, maxLevel=999):
        spectra = []
        postfixes = []
        for p in self.table.supportedPostfixes(self.eicColNames()):
            values = self.table.getValues(self.table.rows[data_row_idx])
            pm = values["peakmap" + p]
            rtmin = values["rtmin" + p]
            rtmax = values["rtmax" + p]
            if pm is not None and rtmin is not None and rtmax is not None:
                for spec in pm.levelNSpecs(minLevel, maxLevel):
                    if rtmin <= spec.rt <= rtmax:
                        spectra.append(spec)
                        postfixes.append(p)
        return postfixes, spectra

    def getEics(self, data_row_idx):
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

    def update_visible_rows_for_given_limits(self):
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

        self.beginResetModel()
        self.widgetRowToDataRow = dict()
        self.dataRowtoWidgetRow = dict()
        for view_idx, row_idx in enumerate(sorted(all_rows_to_remain)):
            self.widgetRowToDataRow[view_idx] = row_idx
            self.dataRowtoWidgetRow[row_idx] = view_idx
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

    def set_visilbe_cols(self, col_indices):
        self.beginResetModel()
        self.widgetColToDataCol = dict(enumerate(col_indices))
        self.endResetModel()

    def set_visilbe_cols_by_names(self, col_names):
        indices = [self.table.getIndex(name) for name in col_names]
        self.set_visilbe_cols(indices)


