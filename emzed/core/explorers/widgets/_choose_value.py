# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'choose_value.ui'
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

class Ui_ChooseValue(object):
    def setupUi(self, ChooseValue):
        ChooseValue.setObjectName(_fromUtf8("ChooseValue"))
        ChooseValue.resize(211, 45)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ChooseValue.sizePolicy().hasHeightForWidth())
        ChooseValue.setSizePolicy(sizePolicy)
        ChooseValue.setMaximumSize(QtCore.QSize(300, 16777215))
        self.verticalLayout = QtGui.QVBoxLayout(ChooseValue)
        self.verticalLayout.setSpacing(1)
        self.verticalLayout.setMargin(3)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.column_name = QtGui.QLabel(ChooseValue)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.column_name.sizePolicy().hasHeightForWidth())
        self.column_name.setSizePolicy(sizePolicy)
        self.column_name.setAlignment(QtCore.Qt.AlignCenter)
        self.column_name.setObjectName(_fromUtf8("column_name"))
        self.verticalLayout.addWidget(self.column_name)
        self.values = QtGui.QComboBox(ChooseValue)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.values.sizePolicy().hasHeightForWidth())
        self.values.setSizePolicy(sizePolicy)
        self.values.setObjectName(_fromUtf8("values"))
        self.verticalLayout.addWidget(self.values)

        self.retranslateUi(ChooseValue)
        QtCore.QMetaObject.connectSlotsByName(ChooseValue)

    def retranslateUi(self, ChooseValue):
        ChooseValue.setWindowTitle(_translate("ChooseValue", "Form", None))


class ChooseValue(QtGui.QWidget, Ui_ChooseValue):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QWidget.__init__(self, parent, f)

        self.setupUi(self)


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    ChooseValue = QtGui.QWidget()
    ui = Ui_ChooseValue()
    ui.setupUi(ChooseValue)
    ChooseValue.show()
    sys.exit(app.exec_())

