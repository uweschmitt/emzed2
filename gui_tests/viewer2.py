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
from emzed.core.explorers.sqlite3_table_explorer import Sqlite3TableExplorer


if __name__ == "__main__":

    app = QtGui.QApplication(sys.argv)
    config = {
        "id": "default",
        "show_peaks": True
        }

    dlg = Sqlite3TableExplorer("peaks.db", config)
    dlg.exec_()
