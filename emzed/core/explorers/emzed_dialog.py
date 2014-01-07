from PyQt4.QtGui import QIcon, QImage, QPixmap, QDialog
import pkg_resources

class EmzedDialog(QDialog):

    def __init__(self, *a, **kw):
        super(EmzedDialog, self).__init__(*a, **kw)
        data = pkg_resources.resource_string("emzed.workbench", "icon64.png")
        img = QImage()
        img.loadFromData(data)
        pixmap = QPixmap.fromImage(img)
        self.setWindowIcon(QIcon(pixmap))
