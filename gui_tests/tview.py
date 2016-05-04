# encoding: utf-8, division
from __future__ import print_function, division

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys



my_array = [['00', '01', '02'],
            ['10', '11', '12'],
            ['20', '21', '22']]


from emzed.core.data_types.hdf5_table_proxy import Hdf5TableProxy

import emzed

def main():

    import os.path

    here = os.path.dirname(os.path.abspath(__file__))
    tproxy = Hdf5TableProxy(os.path.join(here, "test_100000.hdf5"))

    # tproxy.filter_("floats_0", 400, 450)
    #print("sort")
    #tproxy.sortBy(["floats_0"], [True])

    emzed.gui.inspect(tproxy)
    return

    app = QApplication(sys.argv)
    w = MyWindow(tproxy)
    w.show()
    sys.exit(app.exec_())


class MyWindow(QWidget):

    def __init__(self, tproxy, *args):
        QWidget.__init__(self, *args)

        tablemodel = MyTableModel(tproxy, self)
        tableview = QTableView()
        tableview.setModel(tablemodel)

        layout = QVBoxLayout(self)
        layout.addWidget(tableview)
        self.setLayout(layout)


class MyTableModel(QAbstractTableModel):

    def __init__(self, tproxy, parent=None, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self.tproxy = tproxy
        self.n_cols = len(tproxy[0])

    def rowCount(self, parent):
        return len(self.tproxy)

    def columnCount(self, parent):
        return self.n_cols

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()
        cell_value = self.tproxy[index.row()][index.column()]
        if cell_value is None:
            return "-"
        return str(cell_value)

if __name__ == "__main__":
    main()
