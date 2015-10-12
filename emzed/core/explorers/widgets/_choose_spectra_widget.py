# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'choose_spectra_widget.ui'
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

class Ui__ChooseSpectraWidget(object):
    def setupUi(self, _ChooseSpectraWidget):
        _ChooseSpectraWidget.setObjectName(_fromUtf8("_ChooseSpectraWidget"))
        _ChooseSpectraWidget.resize(238, 307)
        _ChooseSpectraWidget.setMaximumSize(QtCore.QSize(250, 16777215))
        self.verticalLayout = QtGui.QVBoxLayout(_ChooseSpectraWidget)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.frame = QtGui.QFrame(_ChooseSpectraWidget)
        self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setObjectName(_fromUtf8("frame"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.frame)
        self.verticalLayout_2.setMargin(5)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self._label = QtGui.QLabel(self.frame)
        self._label.setObjectName(_fromUtf8("_label"))
        self.verticalLayout_2.addWidget(self._label)
        self._spectra = QtGui.QListWidget(self.frame)
        self._spectra.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self._spectra.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self._spectra.setObjectName(_fromUtf8("_spectra"))
        self.verticalLayout_2.addWidget(self._spectra)
        self.verticalLayout.addWidget(self.frame)

        self.retranslateUi(_ChooseSpectraWidget)
        QtCore.QMetaObject.connectSlotsByName(_ChooseSpectraWidget)

    def retranslateUi(self, _ChooseSpectraWidget):
        _ChooseSpectraWidget.setWindowTitle(_translate("_ChooseSpectraWidget", "Form", None))
        self._label.setText(_translate("_ChooseSpectraWidget", "Spectra:", None))


class _ChooseSpectraWidget(QtGui.QWidget, Ui__ChooseSpectraWidget):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QWidget.__init__(self, parent, f)

        self.setupUi(self)


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    _ChooseSpectraWidget = QtGui.QWidget()
    ui = Ui__ChooseSpectraWidget()
    ui.setupUi(_ChooseSpectraWidget)
    _ChooseSpectraWidget.show()
    sys.exit(app.exec_())

