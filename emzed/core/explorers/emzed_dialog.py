import contextlib
import pkg_resources

from PyQt4.QtGui import QIcon, QImage, QPixmap, QDialog
from PyQt4.QtCore import Qt
import guidata


class EmzedDialog(QDialog):

    def __init__(self, *a, **kw):
        super(EmzedDialog, self).__init__(*a, **kw)
        data = pkg_resources.resource_string("emzed.workbench", "icon64.png")
        img = QImage()
        img.loadFromData(data)
        pixmap = QPixmap.fromImage(img)
        self.setWindowIcon(QIcon(pixmap))

    def processEvents(self):
        guidata.qapplication().processEvents()

    def setWaitCursor(self):
        self.setCursor(Qt.WaitCursor)

    def setArrowCursor(self):
        self.setCursor(Qt.ArrowCursor)

    @contextlib.contextmanager
    def execute_blocked(self, *a):
        self.setWaitCursor()
        for ai in a:
            ai.setEnabled(False)
        self.processEvents()
        yield
        self.setArrowCursor()
        for ai in a:
            ai.setEnabled(True)

