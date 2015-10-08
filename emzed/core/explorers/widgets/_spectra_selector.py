# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'spectra_selector.ui'
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

class Ui_SpectraSelector(object):
    def setupUi(self, SpectraSelector):
        SpectraSelector.setObjectName(_fromUtf8("SpectraSelector"))
        SpectraSelector.resize(275, 118)
        self.horizontalLayout = QtGui.QHBoxLayout(SpectraSelector)
        self.horizontalLayout.setSpacing(-1)
        self.horizontalLayout.setMargin(0)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.frame = QtGui.QFrame(SpectraSelector)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setObjectName(_fromUtf8("frame"))
        self.gridLayout = QtGui.QGridLayout(self.frame)
        self.gridLayout.setHorizontalSpacing(10)
        self.gridLayout.setVerticalSpacing(5)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label_2 = QtGui.QLabel(self.frame)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.precursor = QtGui.QComboBox(self.frame)
        self.precursor.setObjectName(_fromUtf8("precursor"))
        self.gridLayout.addWidget(self.precursor, 1, 1, 1, 1)
        self.ms_level = QtGui.QComboBox(self.frame)
        self.ms_level.setObjectName(_fromUtf8("ms_level"))
        self.gridLayout.addWidget(self.ms_level, 0, 1, 1, 1)
        self.label = QtGui.QLabel(self.frame)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_3 = QtGui.QLabel(self.frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)
        self.precursor_max = QtGui.QLineEdit(self.frame)
        self.precursor_max.setObjectName(_fromUtf8("precursor_max"))
        self.gridLayout.addWidget(self.precursor_max, 3, 1, 1, 1)
        self.precursor_min = QtGui.QLineEdit(self.frame)
        self.precursor_min.setObjectName(_fromUtf8("precursor_min"))
        self.gridLayout.addWidget(self.precursor_min, 3, 0, 1, 1)
        self.horizontalLayout.addWidget(self.frame)

        self.retranslateUi(SpectraSelector)
        QtCore.QMetaObject.connectSlotsByName(SpectraSelector)

    def retranslateUi(self, SpectraSelector):
        SpectraSelector.setWindowTitle(_translate("SpectraSelector", "Form", None))
        self.label_2.setText(_translate("SpectraSelector", "Choose Precursor", None))
        self.label.setText(_translate("SpectraSelector", "Choose MS Level", None))
        self.label_3.setText(_translate("SpectraSelector", "m/z Range Precursor", None))


class SpectraSelector(QtGui.QWidget, Ui_SpectraSelector):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QWidget.__init__(self, parent, f)

        self.setupUi(self)


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    SpectraSelector = QtGui.QWidget()
    ui = Ui_SpectraSelector()
    ui.setupUi(SpectraSelector)
    SpectraSelector.show()
    sys.exit(app.exec_())

