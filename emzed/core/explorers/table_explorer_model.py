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


class DeleteRowAction(TableAction):

    actionName = "delete row"

    def __init__(self, model, rowIdx):
        super(DeleteRowAction, self).__init__(model, rowIdx=rowIdx)
        self.toview = dict(row=rowIdx)

    def do(self):
        self.beginDelete(self.rowIdx)
        table = self.model.table
        self.memory = table.rows[self.rowIdx][:]
        del table.rows[self.rowIdx]
        self.endDelete()
        return True

    def undo(self):
        super(DeleteRowAction, self).undo()
        table = self.model.table
        self.beginInsert(self.rowIdx)
        table.rows.insert(self.rowIdx, self.memory)
        self.endInsert()


class CloneRowAction(TableAction):

    actionName = "clone row"

    def __init__(self, model, rowIdx):
        super(CloneRowAction, self).__init__(model, rowIdx=rowIdx)
        self.toview = dict(row=rowIdx)

    def do(self):
        self.beginInsert(self.rowIdx + 1)
        table = self.model.table
        table.rows.insert(self.rowIdx + 1, table.rows[self.rowIdx][:])
        self.memory = True
        self.endInsert()
        return True

    def undo(self):
        super(CloneRowAction, self).undo()
        table = self.model.table
        self.beginDelete(self.rowIdx + 1)
        del table.rows[self.rowIdx + 1]
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
        self.memory = table.sortBy(colName, ascending)
        self.model.reset()
        return True

    def undo(self):
        super(SortTableAction, self).undo()
        table = self.model.table
        # calc inverse permuation:
        decorated = [(self.memory[i], i) for i in range(len(self.memory))]
        decorated.sort()
        invperm = [i for (_, i) in decorated]
        table._applyRowPermutation(invperm)
        self.model.reset()


class ChangeValueAction(TableAction):

    actionName = "change value"

    def __init__(self, model, idx, dataColIdx, value):
        super(ChangeValueAction, self).__init__(model, idx=idx,
                                                dataColIdx=dataColIdx,
                                                value=value)
        self.toview = dict(row=idx.row(), column=idx.column(), value=value)

    def do(self):
        table = self.model.table
        row = table.rows[self.idx.row()]
        self.memory = row[self.dataColIdx]
        if self.memory == self.value:
            return False
        row[self.dataColIdx] = self.value
        self.model.emit(
            SIGNAL("dataChanged(QModelIndex,QModelIndex,PyQt_PyObject)"),
            self.idx,
            self.idx,
            self)
        return True

    def undo(self):
        super(ChangeValueAction, self).undo()
        table = self.model.table
        table.rows[self.idx.row()][self.dataColIdx] = self.memory
        self.model.emit(
            SIGNAL("dataChanged(QModelIndex,QModelIndex,PyQt_PyObject)"),
            self.idx,
            self.idx,
            self)


class IntegrateAction(TableAction):

    actionName = "integrate"

    def __init__(self, model, idx, postfix, method, rtmin, rtmax):
        super(IntegrateAction, self).__init__(model, idx=idx, postfix=postfix,
                                              method=method, rtmin=rtmin,
                                              rtmax=rtmax, )
        self.toview = dict(rtmin=rtmin, rtmax=rtmax, method=method,
                           postfix=postfix)

    def do(self):
        # pyqtRemoveInputHook()
        integrator = dict(_algorithm_configs.peakIntegrators).get(self.method)
        table = self.model.table
        # returns Bunch which sublcasses dict
        args = table.getValues(table.rows[self.idx])
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
        self.memory = table.rows[self.idx][:]

        # write values to table
        row = table.rows[self.idx]
        table.setValue(row, "method" + postfix, self.method)
        table.setValue(row, "rtmin" + postfix, self.rtmin)
        table.setValue(row, "rtmax" + postfix, self.rtmax)
        table.setValue(row, "area" + postfix, area)
        table.setValue(row, "rmse" + postfix, rmse)
        table.setValue(row, "params" + postfix, params)
        # args = table.get(table.rows[self.idx], None)
        self.notifyGUI()
        return True

    def undo(self):
        super(IntegrateAction, self).undo()
        table = self.model.table
        table.setRow(self.idx, self.memory)
        table.resetInternals()
        self.notifyGUI()

    def notifyGUI(self):
        tl = self.model.createIndex(self.idx, 0)
        tr = self.model.createIndex(self.idx, self.model.columnCount() - 1)
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

    def __init__(self, table, parent):
        super(TableModel, self).__init__(parent)
        self.table = table
        self.parent = parent
        nc = len(self.table._colNames)
        indizesOfVisibleCols = (j for j in range(nc)
                                if self.table._colFormats[j] is not None)
        self.widgetColToDataCol = dict(enumerate(indizesOfVisibleCols))
        self.emptyActionStack()

        self.nonEditables = set()

    def addNonEditable(self, name):
        dataColIdx = self.table.getIndex(name)
        self.nonEditables.add(dataColIdx)

    def emptyActionStack(self):
        self.actions = []
        self.redoActions = []

    def getRow(self, idx):
        return self.table.getValues(self.table.rows[idx])

    def rowCount(self, index=QModelIndex()):
        return len(self.table)

    def columnCount(self, index=QModelIndex()):
        return len(self.widgetColToDataCol)

    def column_name(self, index):
        __, col = self.table_index(index)
        return self.table.getColNames()[col]

    def table_index(self, index):
        cidx = self.widgetColToDataCol[index.column()]
        return index.row(), cidx

    def cell_value(self, index):
        __, cidx = self.table_index(index)
        value = self.table.rows[index.row()][cidx]
        return value

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self.table)):
            return QVariant()
        cidx = self.widgetColToDataCol[index.column()]
        value = self.table.rows[index.row()][cidx]
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
        if index.isValid() and 0 <= index.row() < len(self.table):
            __, dataIdx = self.table_index(index)
            expectedType = self.table._colTypes[dataIdx]
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
            return self.runAction(ChangeValueAction, index, dataIdx, value)
        return False

    def runAction(self, clz, *a):
        action = clz(self, *a)
        done = action.do()
        if not done:
            return done
        self.actions.append(action)
        self.redoActions = []
        self.parent.updateMenubar()
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
            self.redoActions.append(action)
            self.parent.updateMenubar()

    def redoLastAction(self):
        if len(self.redoActions):
            action = self.redoActions.pop()
            action.do()
            self.actions.append(action)
            self.parent.updateMenubar()
            return

    def cloneRow(self, position):
        self.runAction(CloneRowAction, position)
        return True

    def removeRow(self, position):
        self.runAction(DeleteRowAction, position)
        return True

    def sort(self, colIdx, order=Qt.AscendingOrder):
        if len(self.widgetColToDataCol):
            dataColIdx = self.widgetColToDataCol[colIdx]
            self.runAction(SortTableAction, dataColIdx, colIdx, order)
            self.current_sort_idx = colIdx # dataColIdx

    def integrate(self, idx, postfix, method, rtmin, rtmax):
        self.runAction(IntegrateAction, postfix, idx, method, rtmin, rtmax)

    def eicColNames(self):
        return ["peakmap", "mzmin", "mzmax", "rtmin", "rtmax"]

    def hasFeatures(self):
        return self.checkForAny(*self.eicColNames())

    def integrationColNames(self):
        return ["area", "rmse", "method", "params"]

    def getIntegrationValues(self, rowIdx, p):
        get = lambda nn: self.table.getValue(self.table.rows[rowIdx], nn + p)
        return dict((nn + p, get(nn)) for nn in self.integrationColNames())

    def isIntegrated(self):
        return self.hasFeatures()\
            and self.checkForAny(*self.integrationColNames())

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

    def getSmoothedEics(self, rowIdx, rts):
        allsmoothed = []
        for p in self.table.supportedPostfixes(self.integrationColNames()):
            values = self.getIntegrationValues(rowIdx, p)
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

    def getPeakmaps(self, rowIdx):
        peakMaps = []
        for p in self.table.supportedPostfixes(["peakmap"]):
            pm = self.table.getValue(self.table.rows[rowIdx], "peakmap" + p)
            if pm is None:
                pm = PeakMap([])
            peakMaps.append(pm)
        return peakMaps

    def getLevelNSpectra(self, rowIdx, minLevel=2, maxLevel=999):
        spectra = []
        postfixes = []
        for p in self.table.supportedPostfixes(self.eicColNames()):
            values = self.table.getValues(self.table.rows[rowIdx])
            pm = values["peakmap" + p]
            rtmin = values["rtmin" + p]
            rtmax = values["rtmax" + p]
            if pm is not None and rtmin is not None and rtmax is not None:
                for spec in pm.levelNSpecs(minLevel, maxLevel):
                    if rtmin <= spec.rt <= rtmax:
                        spectra.append(spec)
                        postfixes.append(p)
        return postfixes, spectra

    def getEics(self, rowIdx):
        eics = []
        mzmins = []
        mzmaxs = []
        rtmins = []
        rtmaxs = []
        allrts = []
        for p in self.table.supportedPostfixes(self.eicColNames()):
            values = self.table.getValues(self.table.rows[rowIdx])
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
