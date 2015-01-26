# encoding: utf-8
from __future__ import print_function

import guidata

import emzed
from emzed.core.explorers import TableExplorer
from emzed.core.data_types import Table

from PyQt4.QtGui import *


class ModExplorer(TableExplorer):

    def __init__(self, table):
        super(ModExplorer, self).__init__([table], False)

    def create_additional_widgets(self):
        self.status = widget = QLineEdit("HI PRESS ME", parent=self)
        return widget

    def connect_additional_widgets(self, model):
        model.DATA_CHANGE.connect(self.data_changed)

    def data_changed(self, full_t, visible_t):
        print(full_t, visible_t)
        self.status.setText("%d / %d rows" % (len(full_t), len(visible_t)))




if __name__ == "__main__":
    t = emzed.utils.toTable("a", (1, 2, 3, None))
    app = guidata.qapplication()
    dlg = ModExplorer(t)
    dlg.raise_()
    dlg.exec_()
