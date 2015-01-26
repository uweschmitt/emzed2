# -*- coding: utf-8 -*-

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from ..data_types import PeakMap

import guidata

import os
import re

from ... import _algorithm_configs


def isUrl(what):
    return what.startswith("http://")


class TableAction(object):

    actionName = None

    def __init__(self, model, **kw):
        self.model = model
        self.args = kw
        self.__dict__.update(kw)
        self.memory = None

    def undo(self):
        assert self.memory is not None

    def beginDelete(self, idx, idx2=None):
        if idx2 is None:
            idx2 = idx
        self.model.beginRemoveRows(QModelIndex(), idx, idx2)

    def endDelete(self):
        self.model.endRemoveRows()

    def beginInsert(self, idx, idx2=None):
        if idx2 is None:
            idx2 = idx
        self.model.beginInsertRows(QModelIndex(), idx, idx2)

    def endInsert(self):
        self.model.endInsertRows()

    def __str__(self):
        args = ", ".join("%s: %s" % it for it in self.toview.items())
        return "%s(%s)" % (self.actionName, args)


class DeleteRowsAction(TableAction):

    actionName = "delete row"

    def __init__(self, model, widget_row_indices, data_row_indices):
        super(DeleteRowsAction, self).__init__(model, widget_row_indices=widget_row_indices,
                                               data_row_indices=data_row_indices)
        self.toview = dict(rows=widget_row_indices)

    def do(self):
        indices = sorted(self.data_row_indices)
        table = self.model.table
        self.memory = [(i, table.rows[i]) for i in indices]

        self.model.beginResetModel()
        for ix in reversed(indices):
            del table.rows[ix]

        table.resetInternals()
        self.model.endResetModel()
        return True

    def undo(self):
        super(DeleteRowsAction, self).undo()
        table = self.model.table
        self.model.beginResetModel()
        for ix, row in self.memory:
            table.rows.insert(ix, row[:])
        table.resetInternals()
        self.model.endResetModel()


class CloneRowAction(TableAction):

    actionName = "clone row"

    def __init__(self, model, widget_row_idx, data_row_idx):
        super(CloneRowAction, self).__init__(model, widget_row_idx=widget_row_idx,
                                             data_row_idx=data_row_idx)
        self.toview = dict(row=widget_row_idx)

    def do(self):
        self.beginInsert(self.widget_row_idx + 1)
        table = self.model.table
        table.rows.insert(self.data_row_idx + 1, table.rows[self.data_row_idx][:])
        table.resetInternals()
        self.memory = True
        self.endInsert()
        return True

    def undo(self):
        super(CloneRowAction, self).undo()
        table = self.model.table
        self.beginDelete(self.widget_row_idx + 1)
        del table.rows[self.data_row_idx + 1]
        table.resetInternals()
        self.endDelete()


class SortTableAction(TableAction):

    actionName = "sort table"

    def __init__(self, model, dataColIdx, colIdx, order):
        super(SortTableAction, self).__init__(model, dataColIdx=dataColIdx, colIdx=colIdx,
                                              order=order)
        self.toview = dict(sortByColumn=colIdx, ascending=(order == Qt.AscendingOrder))

    def do(self):
        table = self.model.table
        ascending = self.order == Qt.AscendingOrder
        colName = table._colNames[self.dataColIdx]
        # 'memory' is the permutation which sorted the table rows
        # sortBy returns this permutation:
        self.model.beginResetModel()
        self.memory = table.sortBy(colName, ascending)
        self.model.endResetModel()
        return True

    def undo(self):
        super(SortTableAction, self).undo()
        table = self.model.table
        # calc inverse permuation:
        decorated = [(self.memory[i], i) for i in range(len(self.memory))]
        decorated.sort()
        invperm = [i for (_, i) in decorated]
        self.model.beginResetModel()
        table._applyRowPermutation(invperm)
        self.model.endResetModel()


class ChangeValueAction(TableAction):

    actionName = "change value"

    def __init__(self, model, idx, row_idx, col_idx, value):
        super(ChangeValueAction, self).__init__(model,
                                                idx=idx,
                                                row_idx=row_idx,
                                                col_idx=col_idx,
                                                value=value)
        self.toview = dict(row=idx.row(), column=idx.column(), value=value)

    def do(self):
        table = self.model.table
        row = table.rows[self.row_idx]
        self.memory = row[self.col_idx]
        if self.memory == self.value:
            return False
        row[self.col_idx] = self.value
        table.resetInternals()
        self.model.emit(
            SIGNAL("dataChanged(QModelIndex,QModelIndex,PyQt_PyObject)"),
            self.idx,
            self.idx,
            self)
        return True

    def undo(self):
        super(ChangeValueAction, self).undo()
        table = self.model.table
        table.rows[self.row_idx][self.col_idx] = self.memory
        table.resetInternals()
        self.model.emit(
            SIGNAL("dataChanged(QModelIndex,QModelIndex,PyQt_PyObject)"),
            self.idx,
            self.idx,
            self)


class IntegrateAction(TableAction):

    actionName = "integrate"

    def __init__(self, model, data_row_idx, postfix, method, rtmin, rtmax, data_row_to_widget_row):
        super(IntegrateAction, self).__init__(model,
                                              data_row_idx=data_row_idx,
                                              postfix=postfix,
                                              method=method,
                                              rtmin=rtmin,
                                              rtmax=rtmax,
                                              data_row_to_widget_row=data_row_to_widget_row)
        self.toview = dict(rtmin=rtmin, rtmax=rtmax, method=method,
                           postfix=postfix)

    def do(self):
        # pyqtRemoveInputHook()
        integrator = dict(_algorithm_configs.peakIntegrators).get(self.method)
        table = self.model.table
        # returns Bunch which sublcasses dict
        args = table.getValues(table.rows[self.data_row_idx])
        postfix = self.postfix

        if integrator and all(args[f + postfix]
                              is not None
                              for f in ["mzmin", "mzmax", "rtmin", "rtmax", "peakmap"]):

            # TODO: restructure datatypes to avoid this dirty workaround
            # for ms 2 spectra:
            pm = args["peakmap" + postfix].getDominatingPeakmap()
            integrator.setPeakMap(pm)

            # integrate
            mzmin = args["mzmin" + postfix]
            mzmax = args["mzmax" + postfix]
            res = integrator.integrate(mzmin, mzmax, self.rtmin, self.rtmax, msLevel=None)

            area = res["area"]
            rmse = res["rmse"]
            params = res["params"]

        else:
            area = None
            rmse = None
            params = None

        # var 'row' is a Bunch, so we have to get the row from direct access
        # to table.rows:
        self.memory = table.rows[self.data_row_idx][:]

        # write values to table
        row = table.rows[self.data_row_idx]
        table.setValue(row, "method" + postfix, self.method)
        table.setValue(row, "rtmin" + postfix, self.rtmin)
        table.setValue(row, "rtmax" + postfix, self.rtmax)
        table.setValue(row, "area" + postfix, area)
        table.setValue(row, "rmse" + postfix, rmse)
        table.setValue(row, "params" + postfix, params)
        self.notifyGUI()
        return True

    def undo(self):
        super(IntegrateAction, self).undo()
        table = self.model.table
        table.setRow(self.data_row_idx, self.memory)
        table.resetInternals()
        self.notifyGUI()

    def notifyGUI(self):
        idx_view = self.data_row_to_widget_row[self.data_row_idx]
        tl = self.model.createIndex(idx_view, 0)
        tr = self.model.createIndex(idx_view, self.model.columnCount() - 1)
        # this one updates plots
        self.model.emit(
            SIGNAL("dataChanged(QModelIndex,QModelIndex,PyQt_PyObject)"),
            tl,
            tr,
            self)
        # this one updates cells in table
        self.model.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"), tl, tr)



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
            if colType in [int, float, str]:
                if shown.strip().endswith("m"):
                    return shown
                try:
                    colType(shown)
                    return shown
                except:
                    if colType == float:
                        return "-" if value is None else "%.4f" % value
                    return str(value)
            return str(value)
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
        if isUrl(str(self.data(index))):
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
                # QVariant -> QString -> str + strip:
                value = str(value.toString()).strip()
                # minutes ?
                if re.match("^((\d+m)|(\d*.\d+m))$", value):
                    value = 60.0 * float(value[:-1])
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
            return str(self.actions[-1])
        return None

    def infoRedoAction(self):
        if len(self.redoActions):
            return str(self.redoActions[-1])
        return None

    def undoLastAction(self):
        if len(self.actions):
            action = self.actions.pop()
            action.undo()
            self.update_visible_rows_for_given_limits()
            self.redoActions.append(action)
            self.view.updateMenubar()

    def redoLastAction(self):
        if len(self.redoActions):
            action = self.redoActions.pop()
            action.do()
            self.update_visible_rows_for_given_limits()
            self.actions.append(action)
            self.view.updateMenubar()
            return

    def cloneRow(self, widget_row_idx):
        data_row_idx = self.widgetRowToDataRow[widget_row_idx]
        self.runAction(CloneRowAction, widget_row_idx, data_row_idx)
        self.update_visible_rows_for_given_limits()
        return True

    def removeRows(self, widget_row_indices):
        data_row_indices = [self.widgetRowToDataRow[ix] for ix in widget_row_indices]
        self.runAction(DeleteRowsAction, widget_row_indices, data_row_indices)
        self.update_visible_rows_for_given_limits()
        return True

    def removeRow(self, *a):
        raise RuntimeError("obsolte method, use removeRows instead")

    def sort(self, colIdx, order=Qt.AscendingOrder):
        if len(self.widgetColToDataCol):
            dataColIdx = self.widgetColToDataCol[colIdx]
            self.runAction(SortTableAction, dataColIdx, colIdx, order)
            self.current_sort_col_idx = colIdx
            self.update_visible_rows_for_given_limits()

    def integrate(self, data_row_idx, postfix, method, rtmin, rtmax):
        self.runAction(IntegrateAction, postfix, data_row_idx, method, rtmin, rtmax,
                       self.dataRowtoWidgetRow)
        self.update_visible_rows_for_given_limits()

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
        look_for = str(look_for).strip()
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
        self.runAction(DeleteRowsAction, [], delete_data_rows)
        self.update_visible_rows_for_given_limits()
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


