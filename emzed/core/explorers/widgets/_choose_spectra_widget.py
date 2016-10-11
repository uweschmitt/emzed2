# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'choose_spectra_widget.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
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
        _ChooseSpectraWidget.resize(160, 111)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(_ChooseSpectraWidget.sizePolicy().hasHeightForWidth())
        _ChooseSpectraWidget.setSizePolicy(sizePolicy)
        self.verticalLayout = QtGui.QVBoxLayout(_ChooseSpectraWidget)
        self.verticalLayout.setSizeConstraint(QtGui.QLayout.SetMinimumSize)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.frame = QtGui.QFrame(_ChooseSpectraWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setMinimumSize(QtCore.QSize(0, 100))
        self.frame.setFrameShape(QtGui.QFrame.NoFrame)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setObjectName(_fromUtf8("frame"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.frame)
        self.verticalLayout_2.setSizeConstraint(QtGui.QLayout.SetMinimumSize)
        self.verticalLayout_2.setMargin(5)
        self.verticalLayout_2.setSpacing(5)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self._label = QtGui.QLabel(self.frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._label.sizePolicy().hasHeightForWidth())
        self._label.setSizePolicy(sizePolicy)
        self._label.setObjectName(_fromUtf8("_label"))
        self.verticalLayout_2.addWidget(self._label)
        self._spectra = QtGui.QListWidget(self.frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._spectra.sizePolicy().hasHeightForWidth())
        self._spectra.setSizePolicy(sizePolicy)
        self._spectra.setMinimumSize(QtCore.QSize(0, 50))
        self._spectra.setMaximumSize(QtCore.QSize(150, 80))
        self._spectra.setObjectName(_fromUtf8("_spectra"))
        self.verticalLayout_2.addWidget(self._spectra)
        self.verticalLayout_2.setStretch(0, 1)
        self.verticalLayout_2.setStretch(1, 1)
        self.verticalLayout.addWidget(self.frame)
        spacerItem = QtGui.QSpacerItem(20, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.verticalLayout.setStretch(0, 1)

        self.retranslateUi(_ChooseSpectraWidget)
        QtCore.QMetaObject.connectSlotsByName(_ChooseSpectraWidget)

    def retranslateUi(self, _ChooseSpectraWidget):
        _ChooseSpectraWidget.setWindowTitle(_translate("_ChooseSpectraWidget", "Form", None))
        self._label.setText(_translate("_ChooseSpectraWidget", "Spectra", None))


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

