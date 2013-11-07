from PyQt4.QtCore import *
from PyQt4.QtGui import *


class ImageDialog(QDialog):

    def __init__(self, binary_data, parent=None):
        super(ImageDialog, self).__init__(parent)

        self.setWindowFlags(Qt.Window)

        scene = QGraphicsScene()
        view = QGraphicsView(scene)
        pm = QPixmap()
        pm.loadFromData(binary_data)
        item = QGraphicsPixmapItem(pm)
        scene.addItem(item)
        layout = QVBoxLayout()
        layout.addWidget(view)
        self.setLayout(layout)


if __name__ == "__main__":

    app = QApplication([])

    dlg = ImageDialog("../tests/data/test.png")
    dlg.exec_()


