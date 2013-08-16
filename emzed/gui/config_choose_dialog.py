from PyQt4.QtCore import *
from PyQt4.QtGui import *

from   helpers import *


class ConfigChooseDialog(QDialog):

    def __init__(self, configs, params, parent=None):
        super(ConfigChooseDialog, self).__init__(parent)

        self.setWindowFlags(Qt.Window)
        self.setWindowTitle("Choose Config")

        self.configs = configs
        self.params  = params

        self.tw = QTableWidget()
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tw.setSizePolicy(sizePolicy)
        self.setupLayout()
        self.populate()

        self.setSizePolicy(sizePolicy)
        self.setSizeGripEnabled(True)
        self.setMinimumWidth(widthOfTableWidget(self.tw))

        self.result = None

        self.connect(self.tw, SIGNAL("cellClicked(int,int)"), self.clicked)
        self.connect(self.tw.verticalHeader(), SIGNAL("sectionClicked(int)"), self.rowClicked)


    @protect_signal_handler
    def rowClicked(self, row):
        self.result = self.configs[row][2]
        self.result.update(self.params)
        self.accept()

    @protect_signal_handler
    def clicked(self, row, col):
        self.rowClicked(row)


    def setupLayout(self):
        vlayout = QVBoxLayout()
        self.setLayout(vlayout)
        vlayout.addWidget(self.tw)

    def populate(self):
        self.tw.clear()
        self.tw.setSortingEnabled(False)

        self.tw.setRowCount(len(self.configs))

        self.tw.horizontalHeader().setStretchLastSection(True)
        #self.tw.horizontalHeader().setResizeMode(QHeaderView.Stretch)

        paramnames = set(self.params.keys())
        for id_, description, params in self.configs:
            paramnames.update(params.keys())

        paramnames=list(paramnames)
        headers = ["Id", "Description" ] + [ p+"*" if p in self.params.keys() else p for p in paramnames ]

        self.tw.setColumnCount(len(headers))
        self.tw.setHorizontalHeaderLabels(headers)

        for i, (id_, description, cfg) in enumerate(self.configs):

            self.tw.setItem(i, 0,  QTableWidgetItem(id_))
            self.tw.setItem(i, 1,  QTableWidgetItem(description))

            fields = dict( (k, cfg.get(k) ) for k in paramnames )
            fields.update(self.params)

            for j, key in enumerate(paramnames):
                self.tw.setItem(i, 2+j, QTableWidgetItem(str(fields.get(key))))

        self.tw.setSortingEnabled(True)






