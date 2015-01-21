# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'string_filter.ui'
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

class Ui_StringFilter(object):
    def setupUi(self, StringFilter):
        StringFilter.setObjectName(_fromUtf8("StringFilter"))
        StringFilter.resize(159, 46)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(StringFilter.sizePolicy().hasHeightForWidth())
        StringFilter.setSizePolicy(sizePolicy)
        StringFilter.setMaximumSize(QtCore.QSize(200, 16777215))
        self.gridLayout = QtGui.QGridLayout(StringFilter)
        self.gridLayout.setMargin(3)
        self.gridLayout.setSpacing(3)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.column_name = QtGui.QLabel(StringFilter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.column_name.sizePolicy().hasHeightForWidth())
        self.column_name.setSizePolicy(sizePolicy)
        self.column_name.setAlignment(QtCore.Qt.AlignCenter)
        self.column_name.setObjectName(_fromUtf8("column_name"))
        self.gridLayout.addWidget(self.column_name, 0, 2, 1, 1)
        self.label_pattern = QtGui.QLabel(StringFilter)
        self.label_pattern.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_pattern.setObjectName(_fromUtf8("label_pattern"))
        self.gridLayout.addWidget(self.label_pattern, 1, 0, 1, 1)
        self.pattern = QtGui.QLineEdit(StringFilter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pattern.sizePolicy().hasHeightForWidth())
        self.pattern.setSizePolicy(sizePolicy)
        self.pattern.setMinimumSize(QtCore.QSize(100, 0))
        self.pattern.setObjectName(_fromUtf8("pattern"))
        self.gridLayout.addWidget(self.pattern, 1, 2, 1, 2)

        self.retranslateUi(StringFilter)
        QtCore.QMetaObject.connectSlotsByName(StringFilter)

    def retranslateUi(self, StringFilter):
        StringFilter.setWindowTitle(_translate("StringFilter", "Form", None))
        self.label_pattern.setText(_translate("StringFilter", "pattern:", None))


class StringFilter(QtGui.QWidget, Ui_StringFilter):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QWidget.__init__(self, parent, f)

        self.setupUi(self)


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    StringFilter = QtGui.QWidget()
    ui = Ui_StringFilter()
    ui.setupUi(StringFilter)
    StringFilter.show()
    sys.exit(app.exec_())

