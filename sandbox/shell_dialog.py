from PyQt4.Qt import QApplication
from PyQt4.QtCore import Qt, SIGNAL, QProcess
from PyQt4.QtGui import (QTableWidget, QTableWidgetItem, QDialog, QTextEdit, QPushButton,
                         QVBoxLayout, QHBoxLayout)

import subprocess

class UpdateDialog(QDialog):

    def __init__(self, parent, style):
        super(UpdateDialog, self).__init__(parent, style)
        self.setWindowTitle("emzed updates")
        self.setMinimumWidth(600)
        self.setup_widgets()
        self.setup_layout()
        self.connect_signals()

    def setup_widgets(self):
        self.info = QTextEdit(self)
        self.info.setReadOnly(1)
        self.updates = QTableWidget(0, 3)
        self.updates.setHorizontalHeaderLabels(["updater", "info", "do_update ?"])
        self.ok_button = QPushButton("OK")

    def setup_layout(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.info)
        layout.addWidget(self.updates)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        layout.addLayout(button_layout)

    def connect_signals(self):
        self.connect(self.ok_button, SIGNAL("pressed()"), self.ok_button_pressed)

    def ok_button_pressed(self):
        self.info.append("hi")
        self.add_update_info("updater", "info")
        proc = subprocess.Popen("ping -c 3 teamkarcher.de", shell=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, bufsize=0)
        while True:
            print 1
            line = proc.stdout.readline()
            line = line.rstrip()
            self.info.append(line)
            QApplication.processEvents()
            if not line:
                break
        line2 = proc.stderr.readline()
        line2 = line2.rstrip()
        self.info.append("err=%s" % line2)
        print proc.wait()



    def _item(self, content, is_checkable):
        item = QTableWidgetItem(content)
        if is_checkable:
            item.setCheckState(Qt.Unchecked)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable)
        return item

    def add_update_info(self, name, info):
        i = self.updates.rowCount()
        self.updates.insertRow(i)
        self.updates.setItem(i, 0, self._item(name, False))
        self.updates.setItem(i, 1, self._item(info, False))
        self.updates.setItem(i, 2, self._item("", True))
        self.updates.repaint()

if __name__ == "__main__":
    app = QApplication([])
    dlg = UpdateDialog(None, Qt.Window)
    dlg.exec_()



