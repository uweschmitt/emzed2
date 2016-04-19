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
        StringFilter.resize(150, 44)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(StringFilter.sizePolicy().hasHeightForWidth())
        StringFilter.setSizePolicy(sizePolicy)
        StringFilter.setMaximumSize(QtCore.QSize(300, 16777215))
        self.verticalLayout = QtGui.QVBoxLayout(StringFilter)
        self.verticalLayout.setSpacing(1)
        self.verticalLayout.setMargin(3)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.column_name = QtGui.QLabel(StringFilter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.column_name.sizePolicy().hasHeightForWidth())
        self.column_name.setSizePolicy(sizePolicy)
        self.column_name.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.column_name.setObjectName(_fromUtf8("column_name"))
        self.verticalLayout.addWidget(self.column_name)
        self.pattern = QtGui.QLineEdit(StringFilter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pattern.sizePolicy().hasHeightForWidth())
        self.pattern.setSizePolicy(sizePolicy)
        self.pattern.setMinimumSize(QtCore.QSize(100, 0))
        self.pattern.setObjectName(_fromUtf8("pattern"))
        self.verticalLayout.addWidget(self.pattern)

        self.retranslateUi(StringFilter)
        QtCore.QMetaObject.connectSlotsByName(StringFilter)

    def retranslateUi(self, StringFilter):
        StringFilter.setWindowTitle(_translate("StringFilter", "Form", None))
        self.column_name.setText(_translate("StringFilter", "gtest", None))


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

