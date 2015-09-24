# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'column_selection_dialog.ui'
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

class Ui_ColumnMultiSelectDialog(object):
    def setupUi(self, ColumnMultiSelectDialog):
        ColumnMultiSelectDialog.setObjectName(_fromUtf8("ColumnMultiSelectDialog"))
        ColumnMultiSelectDialog.resize(150, 110)
        ColumnMultiSelectDialog.setMinimumSize(QtCore.QSize(150, 110))
        ColumnMultiSelectDialog.setSizeGripEnabled(False)
        self.verticalLayout = QtGui.QVBoxLayout(ColumnMultiSelectDialog)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setSizeConstraint(QtGui.QLayout.SetDefaultConstraint)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.column_names = QtGui.QListView(ColumnMultiSelectDialog)
        self.column_names.setMinimumSize(QtCore.QSize(150, 0))
        self.column_names.setFocusPolicy(QtCore.Qt.NoFocus)
        self.column_names.setViewMode(QtGui.QListView.ListMode)
        self.column_names.setObjectName(_fromUtf8("column_names"))
        self.verticalLayout.addWidget(self.column_names)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSpacing(3)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.apply_button = QtGui.QPushButton(ColumnMultiSelectDialog)
        self.apply_button.setAutoDefault(False)
        self.apply_button.setObjectName(_fromUtf8("apply_button"))
        self.horizontalLayout.addWidget(self.apply_button)
        self.cancel_button = QtGui.QPushButton(ColumnMultiSelectDialog)
        self.cancel_button.setAutoDefault(False)
        self.cancel_button.setObjectName(_fromUtf8("cancel_button"))
        self.horizontalLayout.addWidget(self.cancel_button)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(ColumnMultiSelectDialog)
        QtCore.QMetaObject.connectSlotsByName(ColumnMultiSelectDialog)

    def retranslateUi(self, ColumnMultiSelectDialog):
        ColumnMultiSelectDialog.setWindowTitle(_translate("ColumnMultiSelectDialog", "Select Columns", None))
        self.apply_button.setText(_translate("ColumnMultiSelectDialog", "Apply", None))
        self.cancel_button.setText(_translate("ColumnMultiSelectDialog", "Cancel", None))


class ColumnMultiSelectDialog(QtGui.QDialog, Ui_ColumnMultiSelectDialog):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QDialog.__init__(self, parent, f)

        self.setupUi(self)


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    ColumnMultiSelectDialog = QtGui.QDialog()
    ui = Ui_ColumnMultiSelectDialog()
    ui.setupUi(ColumnMultiSelectDialog)
    ColumnMultiSelectDialog.show()
    sys.exit(app.exec_())

