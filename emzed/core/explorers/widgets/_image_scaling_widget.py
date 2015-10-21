# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'image_scaling_widget.ui'
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

class Ui_ImageScalingWidget(object):
    def setupUi(self, _ImageScalingWidget):
        _ImageScalingWidget.setObjectName(_fromUtf8("_ImageScalingWidget"))
        _ImageScalingWidget.setGeometry(QtCore.QRect(0, 0, 389, 92))
        self.gridLayout = QtGui.QGridLayout(_ImageScalingWidget)
        self.gridLayout.setMargin(0)
        self.gridLayout.setVerticalSpacing(3)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self._frame = QtGui.QFrame(_ImageScalingWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._frame.sizePolicy().hasHeightForWidth())
        self._frame.setSizePolicy(sizePolicy)
        self._frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self._frame.setFrameShadow(QtGui.QFrame.Raised)
        self._frame.setObjectName(_fromUtf8("_frame"))
        self._gridLayout_2 = QtGui.QGridLayout(self._frame)
        self._gridLayout_2.setVerticalSpacing(3)
        self._gridLayout_2.setObjectName(_fromUtf8("_gridLayout_2"))
        self._label = QtGui.QLabel(self._frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._label.sizePolicy().hasHeightForWidth())
        self._label.setSizePolicy(sizePolicy)
        self._label.setObjectName(_fromUtf8("_label"))
        self._gridLayout_2.addWidget(self._label, 0, 0, 1, 1)
        self._logarithmic_scale = QtGui.QCheckBox(self._frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._logarithmic_scale.sizePolicy().hasHeightForWidth())
        self._logarithmic_scale.setSizePolicy(sizePolicy)
        self._logarithmic_scale.setText(_fromUtf8(""))
        self._logarithmic_scale.setObjectName(_fromUtf8("_logarithmic_scale"))
        self._gridLayout_2.addWidget(self._logarithmic_scale, 0, 1, 1, 1)
        self._label_2 = QtGui.QLabel(self._frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._label_2.sizePolicy().hasHeightForWidth())
        self._label_2.setSizePolicy(sizePolicy)
        self._label_2.setObjectName(_fromUtf8("_label_2"))
        self._gridLayout_2.addWidget(self._label_2, 0, 2, 1, 1)
        self._gamma_slider = QtGui.QSlider(self._frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._gamma_slider.sizePolicy().hasHeightForWidth())
        self._gamma_slider.setSizePolicy(sizePolicy)
        self._gamma_slider.setMinimumSize(QtCore.QSize(50, 0))
        self._gamma_slider.setOrientation(QtCore.Qt.Horizontal)
        self._gamma_slider.setObjectName(_fromUtf8("_gamma_slider"))
        self._gridLayout_2.addWidget(self._gamma_slider, 0, 3, 1, 1)
        self._label_3 = QtGui.QLabel(self._frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._label_3.sizePolicy().hasHeightForWidth())
        self._label_3.setSizePolicy(sizePolicy)
        self._label_3.setObjectName(_fromUtf8("_label_3"))
        self._gridLayout_2.addWidget(self._label_3, 1, 0, 1, 1)
        self._imin_input = QtGui.QLineEdit(self._frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._imin_input.sizePolicy().hasHeightForWidth())
        self._imin_input.setSizePolicy(sizePolicy)
        self._imin_input.setMinimumSize(QtCore.QSize(50, 0))
        self._imin_input.setObjectName(_fromUtf8("_imin_input"))
        self._gridLayout_2.addWidget(self._imin_input, 2, 0, 1, 1)
        self._imin_slider = QtGui.QSlider(self._frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._imin_slider.sizePolicy().hasHeightForWidth())
        self._imin_slider.setSizePolicy(sizePolicy)
        self._imin_slider.setMinimumSize(QtCore.QSize(50, 0))
        self._imin_slider.setOrientation(QtCore.Qt.Horizontal)
        self._imin_slider.setObjectName(_fromUtf8("_imin_slider"))
        self._gridLayout_2.addWidget(self._imin_slider, 2, 1, 1, 1)
        self._imax_slider = QtGui.QSlider(self._frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._imax_slider.sizePolicy().hasHeightForWidth())
        self._imax_slider.setSizePolicy(sizePolicy)
        self._imax_slider.setMinimumSize(QtCore.QSize(50, 0))
        self._imax_slider.setOrientation(QtCore.Qt.Horizontal)
        self._imax_slider.setObjectName(_fromUtf8("_imax_slider"))
        self._gridLayout_2.addWidget(self._imax_slider, 2, 2, 1, 1)
        self._imax_input = QtGui.QLineEdit(self._frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._imax_input.sizePolicy().hasHeightForWidth())
        self._imax_input.setSizePolicy(sizePolicy)
        self._imax_input.setMinimumSize(QtCore.QSize(50, 0))
        self._imax_input.setObjectName(_fromUtf8("_imax_input"))
        self._gridLayout_2.addWidget(self._imax_input, 2, 3, 1, 1)
        self.gridLayout.addWidget(self._frame, 0, 0, 1, 1)

        self.retranslateUi(_ImageScalingWidget)
        QtCore.QMetaObject.connectSlotsByName(_ImageScalingWidget)

    def retranslateUi(self, _ImageScalingWidget):
        _ImageScalingWidget.setWindowTitle(_translate("ImageScalingWidget", "Form", None))
        self._label.setText(_translate("ImageScalingWidget", "Logarithmic Scale", None))
        self._label_2.setText(_translate("ImageScalingWidget", "Contrast", None))
        self._label_3.setText(_translate("ImageScalingWidget", "Intensity:", None))


class _ImageScalingWidget(QtGui.QWidget, Ui_ImageScalingWidget):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QWidget.__init__(self, parent, f)

        self.setupUi(self)


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    _ImageScalingWidget = QtGui.QWidget()
    ui = Ui_ImageScalingWidget()
    ui.setupUi(_ImageScalingWidget)
    _ImageScalingWidget.show()
    sys.exit(app.exec_())

