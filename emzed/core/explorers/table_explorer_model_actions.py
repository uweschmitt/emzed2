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
        rows_to_del = sorted(self.data_row_indices)
        table = self.model.table
        permutation = self.model.get_row_permutation()
        self.memory = (permutation, [(i, table.rows[i]) for i in rows_to_del])

        # right order matters: (realy ?)
        for row_to_del in reversed(rows_to_del):
            del table.rows[row_to_del]
            # update permutation: remove entry and decrement succeeding data_row values:
            for i, data_row in enumerate(permutation):
                if data_row > row_to_del:
                    permutation[i] -= 1
                if data_row == row_to_del:
                    to_del = i
            del permutation[to_del]
        self.model.set_row_permutation(permutation)

        table.resetInternals()
        return True

    def undo(self):
        super(DeleteRowsAction, self).undo()
        table = self.model.table
        permutation, saved_rows = self.memory
        self.model.set_row_permutation(permutation)
        for ix, row in saved_rows:
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
        permutation = self.model.get_row_permutation()
        self.memory = permutation[:]
        # shift successors
        for i, pi in enumerate(permutation):
            if pi > self.data_row_idx:
                permutation[i] += 1

        # new entry in permutation
        if self.widget_row_idx == len(permutation) - 1:
            permutation.append(self.data_row_idx + 1)
        else:
            permutation.insert(self.widget_row_idx + 1, self.data_row_idx + 1)

        self.model.set_row_permutation(permutation)

        # duplicate row in data
        table.rows.insert(self.data_row_idx + 1, table.rows[self.data_row_idx][:])
        table.resetInternals()
        return True

    def undo(self):
        super(CloneRowAction, self).undo()
        table = self.model.table
        self.model.set_row_permutation(self.memory)
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
        self.memory = self.model.get_row_permutation()
        permutation = table.sortPermutation(names, ascending)
        self.model.set_row_permutation(permutation)
        return True

    def undo(self):
        super(SortTableAction, self).undo()
        self.model.set_row_permutation(self.memory)


class ChangeAllValuesInColumnAction(TableAction):

    actionName = "change all values"

    def __init__(self, model, widget_col_index, data_row_indices, data_col_index, value):
        super(ChangeAllValuesInColumnAction, self).__init__(model,
                                                            widget_col_index=widget_col_index,
                                                            data_row_indices=data_row_indices,
                                                            data_col_index=data_col_index,
                                                            value=value)
        self.toview = dict(column=widget_col_index, value=value)

    def do(self):
        table = self.model.table
        name = table.getColNames()[self.data_col_index]
        self.memory = table.selectedRowValues(name, self.data_row_indices)

        self.model.beginResetModel()
        table.replaceSelectedRows(name, self.value, self.data_row_indices)
        self.model.endResetModel()
        return True

    def undo(self):
        super(ChangeAllValuesInColumnAction, self).undo()

        self.model.beginResetModel()
        self.model.table.setCellValue(self.data_row_indices, self.data_col_index, self.memory)
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
        table.setCellValue(self.row_idx, self.col_idx, self.value)
        self.model.emit(
            SIGNAL("dataChanged(QModelIndex,QModelIndex,PyQt_PyObject)"),
            self.idx,
            self.idx,
            self)
        return True

    def undo(self):
        super(ChangeValueAction, self).undo()
        table = self.model.table
        table.setCellValue(self.row_idx, self.col_idx, self.memory)
        self.model.emit(
            SIGNAL("dataChanged(QModelIndex,QModelIndex,PyQt_PyObject)"),
            self.idx,
            self.idx,
            self)


class IntegrateAction(TableAction):

    actionName = "integrate"

    def __init__(self, model, data_row_idx, postfix, method, rtmin, rtmax, widget_row):
        super(IntegrateAction, self).__init__(model,
                                              data_row_idx=data_row_idx,
                                              postfix=postfix,
                                              method=method,
                                              rtmin=rtmin,
                                              rtmax=rtmax,
                                              widget_row=widget_row)
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
            pm = args["peakmap" + postfix]
            integrator.setPeakMap(pm)

            # TODO: EIC wird wo und / oder wann gesetzt: vergleiche emzed und envipy !

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
            area = rmse = params = eic = baseline = None

        # var 'row' is a Bunch, so we have to get the row from direct access
        # to table.rows:
        self.memory = table.rows[self.data_row_idx][:]


        names = ("method", "rtmin", "rtmax", "area", "rmse", "params", "eic", "baseline")
        values = (self.method, self.rtmin, self.rtmax, area, rmse, params, eic, baseline)

        col_indices= []
        for name in names:
            idx = table.getIndex(name)
            col_indices.append(idx)

        row_indices = [self.data_row_idx]
        table.setCellValue(row_indices, col_indices, [values])
        self.notifyGUI()
        return True

    def undo(self):
        super(IntegrateAction, self).undo()
        table = self.model.table
        table.setRow(self.data_row_idx, self.memory)
        table.resetInternals()
        self.notifyGUI()

    def notifyGUI(self):
        print(self.widget_row)
        tl = self.model.createIndex(self.widget_row, 0)
        tr = self.model.createIndex(self.widget_row, self.model.columnCount() - 1)
        # this one updates plots
        self.model.emit(
            SIGNAL("dataChanged(QModelIndex,QModelIndex,PyQt_PyObject)"),
            tl,
            tr,
            self)
        # this one updates cells in table
        self.model.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"), tl, tr)
