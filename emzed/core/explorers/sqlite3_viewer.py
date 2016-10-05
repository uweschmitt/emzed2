# encoding: utf-8

from __future__ import print_function

'''
###########################################################
##   A Demo Application showing the use of sqlite3     ##
##   and the QSqlTableModel    Class                    ##
##   written by rowinggolfer 24th Feb 2010              ##
##   version 0.1 and NOT YET WORKING!!                  ##
##   this work is in the public domain,                 ##
##   do with it as you please                           ##
###########################################################
'''

import sys
import cPickle
from PyQt4 import QtCore, QtGui  # , QtSql, Qt

from emzed.core.data_types.sqlite3_table_proxy import Sqlite3TableProxy


"""
todo:
    - sortieren
    - filtern
    + objects lesen
"""

STATE = QtCore.QByteArray.fromBase64('AAAA/wAAAAAAAAABAAAAAQAAAAAAAAAAEgAAAAEAAAAAAAAAAgAAAAMAAAAEAAAABQAAAAYAAAAHAAAACAAAAAkAAAAKAAAACwAAAAwAAAANAAAADgAAAA8AAAAQAAAAEQAAABIAAAABAAAAAAAAAAIAAAADAAAABAAAAAUAAAAGAAAABwAAAAgAAAAJAAAACgAAAAsAAAAMAAAADQAAAA4AAAAPAAAAEAAAABEAAAAAAAAAAAAABwgAAAASAQEBAAAAAAAAAAAAAAAAAGT/////AAAAhAAAAAAAAAADAAAAZAAAAAEAAAAAAAAAZAAAAAEAAAAAAAAGQAAAABAAAAAA')


class Sqlite3TableViewer(QtGui.QDialog):

    def __init__(self, path, config_id="default", parent=None):
        super(Sqlite3TableViewer, self).__init__(parent)
        self.model = Sqlite3Model(path)

        self.table = table = QtGui.QTableView()
        table.setModel(self.model)

        for i in range(self.model.columnCount(None)):
            table.setColumnHidden(i, i in self.model.always_invisible)

        table.horizontalHeader().sectionMoved.connect(self.update_config)
        table.horizontalHeader().setMovable(True)
        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(table)
        self.update_config()

    def update_config(self, *a):
        print(self.table.horizontalHeader().saveState().toBase64())


class Sqlite3Model(QtCore.QAbstractTableModel):

    def __init__(self, path, prefetch=100, parent=None):
        super(Sqlite3Model, self).__init__(parent)

        self.db_proxy = Sqlite3TableProxy(path)
        self.db_proxy.create_query()

        for attr in ("col_names", "col_types", "col_formats", "meta", "object_columns"):
            setattr(self, attr, getattr(self.db_proxy, attr))

        self.always_invisible = set(i for (i, f) in enumerate(self.col_formats) if f is None)

        self.prefetch = prefetch

        self.loaded_rows = []
        self.exhausted = False
        self.fetch_first_batch()

    def data(self, index, role):
        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        try:
            row = self.get_row(index.row())
        except IndexError:
            return QtCore.QVariant()
        ci = index.column()
        value = row[ci]
        if value is None:
            return "-"
        if self.col_names[ci] in self.object_columns:
            value = value.split("!", 1)[1]
        return value

    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        if orientation == QtCore.Qt.Horizontal:
            if section < len(self.col_names):
                return self.col_names[section]
            return QtCore.QVariant()
        return QtCore.QString("   ")

    def columnCount(self, index):
        return len(self.col_names)

    def fetch_first_batch(self):
        try:
            self.get_row(self.prefetch)
        except IndexError:
            pass

    def rowCount(self, index):
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

    #import sqlite3
    #conn = sqlite3.connect("peaks.db")
    app = QtGui.QApplication(sys.argv)

    dlg = Sqlite3TableViewer("../tests/data/features.db")
    dlg.exec_()
