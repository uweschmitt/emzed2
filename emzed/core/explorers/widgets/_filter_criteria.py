# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'filter_criteria.ui'
#
#      by: PyQt4 UI code generator 4.11.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_FilterCriteria(object):
    def setupUi(self, FilterCriteria):
        FilterCriteria.setObjectName(_fromUtf8("FilterCriteria"))
        FilterCriteria.resize(177, 114)
        self.verticalLayout = QtGui.QVBoxLayout(FilterCriteria)
        self.verticalLayout.setSpacing(1)
        self.verticalLayout.setMargin(3)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.groupBox = QtGui.QGroupBox(FilterCriteria)
        self.groupBox.setFlat(True)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.groupBox)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.verticalLayout.addWidget(self.groupBox)

        self.retranslateUi(FilterCriteria)
        QtCore.QMetaObject.connectSlotsByName(FilterCriteria)

    def retranslateUi(self, FilterCriteria):
        FilterCriteria.setWindowTitle(_translate("FilterCriteria", "Form", None))


class FilterCriteria(QtGui.QWidget, Ui_FilterCriteria):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QWidget.__init__(self, parent, f)

        self.setupUi(self)


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    FilterCriteria = QtGui.QWidget()
    ui = Ui_FilterCriteria()
    ui.setupUi(FilterCriteria)
    FilterCriteria.show()
    sys.exit(app.exec_())

