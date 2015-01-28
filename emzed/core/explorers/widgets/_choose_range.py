# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'choose_range.ui'
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

class Ui_ChooseRange(object):
    def setupUi(self, ChooseRange):
        ChooseRange.setObjectName(_fromUtf8("ChooseRange"))
        ChooseRange.resize(143, 70)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ChooseRange.sizePolicy().hasHeightForWidth())
        ChooseRange.setSizePolicy(sizePolicy)
        ChooseRange.setMaximumSize(QtCore.QSize(200, 16777215))
        self.gridLayout = QtGui.QGridLayout(ChooseRange)
        self.gridLayout.setMargin(3)
        self.gridLayout.setSpacing(3)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label_upper_bound = QtGui.QLabel(ChooseRange)
        self.label_upper_bound.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_upper_bound.setObjectName(_fromUtf8("label_upper_bound"))
        self.gridLayout.addWidget(self.label_upper_bound, 2, 0, 1, 1)
        self.upper_bound = QtGui.QLineEdit(ChooseRange)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.upper_bound.sizePolicy().hasHeightForWidth())
        self.upper_bound.setSizePolicy(sizePolicy)
        self.upper_bound.setMinimumSize(QtCore.QSize(100, 0))
        self.upper_bound.setObjectName(_fromUtf8("upper_bound"))
        self.gridLayout.addWidget(self.upper_bound, 2, 2, 1, 3)
        self.label_lower_bound = QtGui.QLabel(ChooseRange)
        self.label_lower_bound.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_lower_bound.setObjectName(_fromUtf8("label_lower_bound"))
        self.gridLayout.addWidget(self.label_lower_bound, 1, 0, 1, 1)
        self.lower_bound = QtGui.QLineEdit(ChooseRange)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lower_bound.sizePolicy().hasHeightForWidth())
        self.lower_bound.setSizePolicy(sizePolicy)
        self.lower_bound.setMinimumSize(QtCore.QSize(100, 0))
        self.lower_bound.setObjectName(_fromUtf8("lower_bound"))
        self.gridLayout.addWidget(self.lower_bound, 1, 2, 1, 3)
        self.column_name = QtGui.QLabel(ChooseRange)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.column_name.sizePolicy().hasHeightForWidth())
        self.column_name.setSizePolicy(sizePolicy)
        self.column_name.setAlignment(QtCore.Qt.AlignCenter)
        self.column_name.setObjectName(_fromUtf8("column_name"))
        self.gridLayout.addWidget(self.column_name, 0, 2, 1, 1)

        self.retranslateUi(ChooseRange)
        QtCore.QMetaObject.connectSlotsByName(ChooseRange)
        ChooseRange.setTabOrder(self.lower_bound, self.upper_bound)

    def retranslateUi(self, ChooseRange):
        ChooseRange.setWindowTitle(_translate("ChooseRange", "Form", None))
        self.label_upper_bound.setText(_translate("ChooseRange", "max:", None))
        self.label_lower_bound.setText(_translate("ChooseRange", "min:", None))


class ChooseRange(QtGui.QWidget, Ui_ChooseRange):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QWidget.__init__(self, parent, f)

        self.setupUi(self)


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    ChooseRange = QtGui.QWidget()
    ui = Ui_ChooseRange()
    ui.setupUi(ChooseRange)
    ChooseRange.show()
    sys.exit(app.exec_())

