# encoding: utf-8
from __future__ import print_function

from _head import Form


from PyQt4.QtGui import *
from PyQt4.QtCore import Qt, QSize


class MyHeader(QHeaderView):

    def __init__(self, parent=None):
        super(MyHeader, self).__init__(Qt.Horizontal, parent)
        self.boxes = dict()
        self.sectionResized.connect(self.handle_section_resized)
        self.sectionMoved.connect(self.handle_section_moved)
        self.setMovable(1)

    def _set_geom(self, i):
        x, y = self.sectionViewportPosition(i), 0
        w, h = self.sectionSize(i), self.boxes[i].height()
        print(x, y, w, h)
        self.boxes[i].setGeometry(x, y + 10, w, h)

    def showEvent(self, e):
        for i in range(self.count()):
            if i not in self.boxes:
                self.boxes[i] = Form(self)
            self._set_geom(i)
            self.boxes[i].show()
        return super(MyHeader, self).showEvent(e)

    def sectionSizeFromContents(self, *a):
        widget = Form(self)
        widget.setVisible(0)
        h = widget.height() + 20
        w = widget.width() + 10
        return QSize(w, h)

    def handle_section_resized(self, i):
        for j in range(self.visualIndex(i), self.count()):
            logical = self.logicalIndex(j)
            self._set_geom(logical)

    def handle_section_moved(self, logical, old_idx, new_idx):
        for i in range(min(old_idx, new_idx), self.count()):
            logical = self.logicalIndex(i)
            self._set_geom(logical)
