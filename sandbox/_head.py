# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'head.ui'
#
# Created: Fri Jan 16 17:13:20 2015
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

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName(_fromUtf8("Form"))
        Form.resize(200, 100)
        self.verticalLayout = QtGui.QVBoxLayout(Form)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.column_name = QtGui.QLabel(Form)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.column_name.sizePolicy().hasHeightForWidth())
        self.column_name.setSizePolicy(sizePolicy)
        self.column_name.setObjectName(_fromUtf8("column_name"))
        self.verticalLayout.addWidget(self.column_name)
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label_lower_bound = QtGui.QLabel(Form)
        self.label_lower_bound.setObjectName(_fromUtf8("label_lower_bound"))
        self.gridLayout.addWidget(self.label_lower_bound, 0, 0, 1, 1)
        self.label_upper_bound = QtGui.QLabel(Form)
        self.label_upper_bound.setObjectName(_fromUtf8("label_upper_bound"))
        self.gridLayout.addWidget(self.label_upper_bound, 1, 0, 1, 1)
        self.lower_bound = QtGui.QLineEdit(Form)
        self.lower_bound.setObjectName(_fromUtf8("lower_bound"))
        self.gridLayout.addWidget(self.lower_bound, 0, 1, 1, 1)
        self.upper_bound = QtGui.QLineEdit(Form)
        self.upper_bound.setObjectName(_fromUtf8("upper_bound"))
        self.gridLayout.addWidget(self.upper_bound, 1, 1, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(_translate("Form", "Form", None))
        self.column_name.setText(_translate("Form", "adsf", "asdfadsfdsf"))
        self.label_lower_bound.setText(_translate("Form", ">=", None))
        self.label_upper_bound.setText(_translate("Form", "<=", None))


class Form(QtGui.QWidget, Ui_Form):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QWidget.__init__(self, parent, f)

        self.setupUi(self)


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    Form = QtGui.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())

