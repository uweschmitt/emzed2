# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'view_range_widget.ui'
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

class Ui__ViewRangeWidget(object):
    def setupUi(self, _ViewRangeWidget):
        _ViewRangeWidget.setObjectName(_fromUtf8("_ViewRangeWidget"))
        _ViewRangeWidget.resize(387, 138)
        self._gridLayout = QtGui.QGridLayout(_ViewRangeWidget)
        self._gridLayout.setMargin(0)
        self._gridLayout.setObjectName(_fromUtf8("_gridLayout"))
        self._frame = QtGui.QFrame(_ViewRangeWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._frame.sizePolicy().hasHeightForWidth())
        self._frame.setSizePolicy(sizePolicy)
        self._frame.setMinimumSize(QtCore.QSize(387, 0))
        self._frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self._frame.setFrameShadow(QtGui.QFrame.Raised)
        self._frame.setObjectName(_fromUtf8("_frame"))
        self._gridLayout_2 = QtGui.QGridLayout(self._frame)
        self._gridLayout_2.setMargin(5)
        self._gridLayout_2.setVerticalSpacing(3)
        self._gridLayout_2.setObjectName(_fromUtf8("_gridLayout_2"))
        self._label = QtGui.QLabel(self._frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._label.sizePolicy().hasHeightForWidth())
        self._label.setSizePolicy(sizePolicy)
        self._label.setMinimumSize(QtCore.QSize(371, 0))
        self._label.setBaseSize(QtCore.QSize(0, 0))
        self._label.setObjectName(_fromUtf8("_label"))
        self._gridLayout_2.addWidget(self._label, 0, 0, 1, 2)
        self._rt_min = QtGui.QLineEdit(self._frame)
        self._rt_min.setMinimumSize(QtCore.QSize(181, 0))
        self._rt_min.setText(_fromUtf8(""))
        self._rt_min.setObjectName(_fromUtf8("_rt_min"))
        self._gridLayout_2.addWidget(self._rt_min, 1, 0, 1, 1)
        self._rt_max = QtGui.QLineEdit(self._frame)
        self._rt_max.setMinimumSize(QtCore.QSize(180, 0))
        self._rt_max.setText(_fromUtf8(""))
        self._rt_max.setObjectName(_fromUtf8("_rt_max"))
        self._gridLayout_2.addWidget(self._rt_max, 1, 1, 1, 1)
        self._label_2 = QtGui.QLabel(self._frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._label_2.sizePolicy().hasHeightForWidth())
        self._label_2.setSizePolicy(sizePolicy)
        self._label_2.setMinimumSize(QtCore.QSize(181, 0))
        self._label_2.setObjectName(_fromUtf8("_label_2"))
        self._gridLayout_2.addWidget(self._label_2, 2, 0, 1, 1)
        self._use_ppm = QtGui.QCheckBox(self._frame)
        self._use_ppm.setMinimumSize(QtCore.QSize(191, 0))
        self._use_ppm.setObjectName(_fromUtf8("_use_ppm"))
        self._gridLayout_2.addWidget(self._use_ppm, 2, 1, 1, 1)
        self._mz_center = QtGui.QLineEdit(self._frame)
        self._mz_center.setMinimumSize(QtCore.QSize(181, 0))
        self._mz_center.setText(_fromUtf8(""))
        self._mz_center.setObjectName(_fromUtf8("_mz_center"))
        self._gridLayout_2.addWidget(self._mz_center, 3, 0, 1, 1)
        self._mz_width = QtGui.QLineEdit(self._frame)
        self._mz_width.setMinimumSize(QtCore.QSize(180, 0))
        self._mz_width.setText(_fromUtf8(""))
        self._mz_width.setObjectName(_fromUtf8("_mz_width"))
        self._gridLayout_2.addWidget(self._mz_width, 3, 1, 1, 1)
        self._label_4 = QtGui.QLabel(self._frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._label_4.sizePolicy().hasHeightForWidth())
        self._label_4.setSizePolicy(sizePolicy)
        self._label_4.setMinimumSize(QtCore.QSize(181, 0))
        self._label_4.setObjectName(_fromUtf8("_label_4"))
        self._gridLayout_2.addWidget(self._label_4, 4, 0, 1, 1)
        self._mz_min = QtGui.QLineEdit(self._frame)
        self._mz_min.setMinimumSize(QtCore.QSize(181, 0))
        self._mz_min.setText(_fromUtf8(""))
        self._mz_min.setObjectName(_fromUtf8("_mz_min"))
        self._gridLayout_2.addWidget(self._mz_min, 5, 0, 1, 1)
        self._mz_max = QtGui.QLineEdit(self._frame)
        self._mz_max.setMinimumSize(QtCore.QSize(180, 0))
        self._mz_max.setText(_fromUtf8(""))
        self._mz_max.setObjectName(_fromUtf8("_mz_max"))
        self._gridLayout_2.addWidget(self._mz_max, 5, 1, 1, 1)
        self._gridLayout.addWidget(self._frame, 3, 1, 1, 1)

        self.retranslateUi(_ViewRangeWidget)
        QtCore.QMetaObject.connectSlotsByName(_ViewRangeWidget)

    def retranslateUi(self, _ViewRangeWidget):
        _ViewRangeWidget.setWindowTitle(_translate("_ViewRangeWidget", "Form", None))
        self._label.setText(_translate("_ViewRangeWidget", "Retention time range [minutes]", None))
        self._label_2.setText(_translate("_ViewRangeWidget", "m/z center and half width", None))
        self._use_ppm.setText(_translate("_ViewRangeWidget", "use ppm ?", None))
        self._label_4.setText(_translate("_ViewRangeWidget", "m/z range", None))


class _ViewRangeWidget(QtGui.QWidget, Ui__ViewRangeWidget):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QWidget.__init__(self, parent, f)

        self.setupUi(self)


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    _ViewRangeWidget = QtGui.QWidget()
    ui = Ui__ViewRangeWidget()
    ui.setupUi(_ViewRangeWidget)
    _ViewRangeWidget.show()
    sys.exit(app.exec_())

