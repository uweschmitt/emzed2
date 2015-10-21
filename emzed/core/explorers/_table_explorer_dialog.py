# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'table_explorer_dialog.ui'
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

class Ui__TableExporerDialog(object):
    def setupUi(self, _TableExporerDialog):
        _TableExporerDialog.setObjectName(_fromUtf8("_TableExporerDialog"))
        _TableExporerDialog.resize(777, 531)
        self.gridLayout = QtGui.QGridLayout(_TableExporerDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.mz_plotter = MzPlottingWidget(_TableExporerDialog)
        self.mz_plotter.setObjectName(_fromUtf8("mz_plotter"))
        self.gridLayout.addWidget(self.mz_plotter, 0, 2, 3, 1)
        self.eic_plotter = EicPlottingWidget(_TableExporerDialog)
        self.eic_plotter.setObjectName(_fromUtf8("eic_plotter"))
        self.gridLayout.addWidget(self.eic_plotter, 0, 0, 3, 1)
        self.choose_spectra_widget = ChooseSpectraWidget(_TableExporerDialog)
        self.choose_spectra_widget.setObjectName(_fromUtf8("choose_spectra_widget"))
        self.gridLayout.addWidget(self.choose_spectra_widget, 1, 1, 1, 1)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 2, 1, 1, 1)
        self.integration_widget = IntegrationWidget(_TableExporerDialog)
        self.integration_widget.setObjectName(_fromUtf8("integration_widget"))
        self.gridLayout.addWidget(self.integration_widget, 0, 1, 1, 1)
        self.tableView = QtGui.QTableView(_TableExporerDialog)
        self.tableView.setObjectName(_fromUtf8("tableView"))
        self.gridLayout.addWidget(self.tableView, 3, 0, 1, 3)

        self.retranslateUi(_TableExporerDialog)
        QtCore.QMetaObject.connectSlotsByName(_TableExporerDialog)

    def retranslateUi(self, _TableExporerDialog):
        _TableExporerDialog.setWindowTitle(_translate("_TableExporerDialog", "Dialog", None))

from widgets.integration_widget import IntegrationWidget
from eic_plotting_widget import EicPlottingWidget
from widgets.choose_spectra_widget import ChooseSpectraWidget
from mz_plotting_widget import MzPlottingWidget

class _TableExporerDialog(QtGui.QDialog, Ui__TableExporerDialog):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QDialog.__init__(self, parent, f)

        self.setupUi(self)


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    _TableExporerDialog = QtGui.QDialog()
    ui = Ui__TableExporerDialog()
    ui.setupUi(_TableExporerDialog)
    _TableExporerDialog.show()
    sys.exit(app.exec_())

