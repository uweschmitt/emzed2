from PyQt4.Qt import QApplication
from PyQt4.QtCore import Qt, SIGNAL
from PyQt4.QtGui import QTableWidget, QTableWidgetItem

app = QApplication([])

item = QTableWidgetItem("")
item.setCheckState(Qt.Checked)
item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable)

tab = QTableWidget(2, 3)
tab.setHorizontalHeaderLabels(["ok", "value"])
tab.setItem(0, 0, item)

item = QTableWidgetItem("")
item.setCheckState(Qt.Checked)
item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable)
tab.setItem(1, 0, item)

item2 = QTableWidgetItem("1.0")
item2.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable)

tab.setItem(0, 1, item2)

def handler(ii):
    print ii

tab.connect(tab.verticalHeader(), SIGNAL("sectionClicked(int)"), handler)
tab.show()



