# encoding: utf-8
from __future__ import print_function

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from ... import algorithm_configs


class TableAction(object):

    actionName = None

    def __init__(self, model, **kw):
        self.model = model
        self.args = kw
        self.__dict__.update(kw)
        self.memory = None

    def undo(self):
        pass

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

        for ix in reversed(indices):
            del table.rows[ix]

        table.resetInternals()
        return True

    def undo(self):
        super(DeleteRowsAction, self).undo()
        table = self.model.table
        for ix, row in self.memory:
            table.rows.insert(ix, row[:])
        table.resetInternals()


class CloneRowAction(TableAction):

    actionName = "clone row"

    def __init__(self, model, widget_row_idx, data_row_idx):
        super(CloneRowAction, self).__init__(model, widget_row_idx=widget_row_idx,
                                             data_row_idx=data_row_idx)
        self.toview = dict(row=widget_row_idx)

    def do(self):
        table = self.model.table
        table.rows.insert(self.data_row_idx + 1, table.rows[self.data_row_idx][:])
        table.resetInternals()
        self.memory = True
        return True

    def undo(self):
        super(CloneRowAction, self).undo()
        table = self.model.table
        del table.rows[self.data_row_idx + 1]
        table.resetInternals()


class SortTableAction(TableAction):

    actionName = "sort table"

    def __init__(self, model, sort_data):
        super(SortTableAction, self).__init__(model, sort_data=sort_data)
        self.toview = dict(sortByColumn=sort_data)

    def do(self):
        table = self.model.table
        names, ascending = zip(*self.sort_data)
        self.memory = table.sortBy(names, ascending)
        return True

    def undo(self):
        super(SortTableAction, self).undo()
        table = self.model.table
        # calc inverse permuation:
        decorated = [(self.memory[i], i) for i in range(len(self.memory))]
        decorated.sort()
        invperm = [i for (_, i) in decorated]
        table._applyRowPermutation(invperm)


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
        integrator = dict(algorithm_configs.peakIntegrators).get(self.method)
        table = self.model.table
        # returns Bunch which sublcasses dict
        args = table.getValues(table.rows[self.data_row_idx])
        postfix = self.postfix

        if integrator and all(args[f + postfix] is not None
                              for f in ["mzmin", "mzmax", "rtmin", "rtmax", "peakmap"]):

            # TODO: restructure datatypes to avoid this dirty workaround
            # for ms 2 spectra:
            pm = args["peakmap" + postfix].getDominatingPeakmap()
            integrator.setPeakMap(pm)

            # integrate
            mzmin = args["mzmin" + postfix]
            mzmax = args["mzmax" + postfix]
            res = integrator.integrate(mzmin, mzmax, self.rtmin, self.rtmax, msLevel=None)

            area = res.get("area")
            rmse = res.get("rmse")
            params = res.get("params")
            eic = res.get("eic")
            baseline = res.get("baseline")

        else:
            area = None
            rmse = None
            params = None
            eic = None
            baseline = None

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
        table.setValue(row, "eic" + postfix, eic)
        table.setValue(row, "baseline" + postfix, baseline)
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


