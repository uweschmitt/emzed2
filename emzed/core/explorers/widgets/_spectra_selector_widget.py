# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'spectra_selector_widget.ui'
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
    def setupUi(self, _SpectraSelectorWidget):
        _SpectraSelectorWidget.setObjectName(_fromUtf8("_SpectraSelectorWidget"))
        _SpectraSelectorWidget.setGeometry(QtCore.QRect(0, 0, 275, 118))
        self._horizontalLayout = QtGui.QHBoxLayout(_SpectraSelectorWidget)
        self._horizontalLayout.setSpacing(-1)
        self._horizontalLayout.setMargin(0)
        self._horizontalLayout.setObjectName(_fromUtf8("_horizontalLayout"))
        self._frame = QtGui.QFrame(_SpectraSelectorWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._frame.sizePolicy().hasHeightForWidth())
        self._frame.setSizePolicy(sizePolicy)
        self._frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self._frame.setFrameShadow(QtGui.QFrame.Raised)
        self._frame.setObjectName(_fromUtf8("_frame"))
        self._gridLayout = QtGui.QGridLayout(self._frame)
        self._gridLayout.setHorizontalSpacing(10)
        self._gridLayout.setVerticalSpacing(3)
        self._gridLayout.setObjectName(_fromUtf8("_gridLayout"))
        self._label_2 = QtGui.QLabel(self._frame)
        self._label_2.setObjectName(_fromUtf8("_label_2"))
        self._gridLayout.addWidget(self._label_2, 1, 0, 1, 1)
        self._precursor = QtGui.QComboBox(self._frame)
        self._precursor.setObjectName(_fromUtf8("_precursor"))
        self._gridLayout.addWidget(self._precursor, 1, 1, 1, 1)
        self._ms_level = QtGui.QComboBox(self._frame)
        self._ms_level.setObjectName(_fromUtf8("_ms_level"))
        self._gridLayout.addWidget(self._ms_level, 0, 1, 1, 1)
        self._label = QtGui.QLabel(self._frame)
        self._label.setObjectName(_fromUtf8("_label"))
        self._gridLayout.addWidget(self._label, 0, 0, 1, 1)
        self._label_3 = QtGui.QLabel(self._frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._label_3.sizePolicy().hasHeightForWidth())
        self._label_3.setSizePolicy(sizePolicy)
        self._label_3.setObjectName(_fromUtf8("_label_3"))
        self._gridLayout.addWidget(self._label_3, 2, 0, 1, 1)
        self._precursor_max = QtGui.QLineEdit(self._frame)
        self._precursor_max.setObjectName(_fromUtf8("_precursor_max"))
        self._gridLayout.addWidget(self._precursor_max, 3, 1, 1, 1)
        self._precursor_min = QtGui.QLineEdit(self._frame)
        self._precursor_min.setObjectName(_fromUtf8("_precursor_min"))
        self._gridLayout.addWidget(self._precursor_min, 3, 0, 1, 1)
        self._horizontalLayout.addWidget(self._frame)

        self.retranslateUi(_SpectraSelectorWidget)
        QtCore.QMetaObject.connectSlotsByName(_SpectraSelectorWidget)

    def retranslateUi(self, _SpectraSelectorWidget):
        _SpectraSelectorWidget.setWindowTitle(_translate("SpectraSelector", "Form", None))
        self._label_2.setText(_translate("SpectraSelector", "Choose Precursor", None))
        self._label.setText(_translate("SpectraSelector", "Choose MS Level", None))
        self._label_3.setText(_translate("SpectraSelector", "m/z Range Precursor", None))


class _SpectraSelectorWidget(QtGui.QWidget, Ui_SpectraSelector):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QWidget.__init__(self, parent, f)

        self.setupUi(self)


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    _SpectraSelectorWidget = QtGui.QWidget()
    ui = Ui_SpectraSelector()
    ui.setupUi(_SpectraSelectorWidget)
    _SpectraSelectorWidget.show()
    sys.exit(app.exec_())

