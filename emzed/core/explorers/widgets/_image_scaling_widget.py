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
    def setupUi(self, ImageScalingWidget):
        ImageScalingWidget.setObjectName(_fromUtf8("ImageScalingWidget"))
        ImageScalingWidget.resize(386, 106)
        self.gridLayout = QtGui.QGridLayout(ImageScalingWidget)
        self.gridLayout.setMargin(0)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.frame = QtGui.QFrame(ImageScalingWidget)
        self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setObjectName(_fromUtf8("frame"))
        self.gridLayout_2 = QtGui.QGridLayout(self.frame)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.label = QtGui.QLabel(self.frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout_2.addWidget(self.label, 0, 0, 1, 1)
        self.logarithmic_scale = QtGui.QCheckBox(self.frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.logarithmic_scale.sizePolicy().hasHeightForWidth())
        self.logarithmic_scale.setSizePolicy(sizePolicy)
        self.logarithmic_scale.setText(_fromUtf8(""))
        self.logarithmic_scale.setObjectName(_fromUtf8("logarithmic_scale"))
        self.gridLayout_2.addWidget(self.logarithmic_scale, 0, 1, 1, 1)
        self.label_2 = QtGui.QLabel(self.frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout_2.addWidget(self.label_2, 0, 2, 1, 1)
        self.gamma_slider = QtGui.QSlider(self.frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.gamma_slider.sizePolicy().hasHeightForWidth())
        self.gamma_slider.setSizePolicy(sizePolicy)
        self.gamma_slider.setMinimumSize(QtCore.QSize(50, 0))
        self.gamma_slider.setOrientation(QtCore.Qt.Horizontal)
        self.gamma_slider.setObjectName(_fromUtf8("gamma_slider"))
        self.gridLayout_2.addWidget(self.gamma_slider, 0, 3, 1, 1)
        self.label_3 = QtGui.QLabel(self.frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout_2.addWidget(self.label_3, 1, 0, 1, 1)
        self.imin_input = QtGui.QLineEdit(self.frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.imin_input.sizePolicy().hasHeightForWidth())
        self.imin_input.setSizePolicy(sizePolicy)
        self.imin_input.setMinimumSize(QtCore.QSize(50, 0))
        self.imin_input.setObjectName(_fromUtf8("imin_input"))
        self.gridLayout_2.addWidget(self.imin_input, 2, 0, 1, 1)
        self.imin_slider = QtGui.QSlider(self.frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.imin_slider.sizePolicy().hasHeightForWidth())
        self.imin_slider.setSizePolicy(sizePolicy)
        self.imin_slider.setMinimumSize(QtCore.QSize(50, 0))
        self.imin_slider.setOrientation(QtCore.Qt.Horizontal)
        self.imin_slider.setObjectName(_fromUtf8("imin_slider"))
        self.gridLayout_2.addWidget(self.imin_slider, 2, 1, 1, 1)
        self.imax_slider = QtGui.QSlider(self.frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.imax_slider.sizePolicy().hasHeightForWidth())
        self.imax_slider.setSizePolicy(sizePolicy)
        self.imax_slider.setMinimumSize(QtCore.QSize(50, 0))
        self.imax_slider.setOrientation(QtCore.Qt.Horizontal)
        self.imax_slider.setObjectName(_fromUtf8("imax_slider"))
        self.gridLayout_2.addWidget(self.imax_slider, 2, 2, 1, 1)
        self.imax_input = QtGui.QLineEdit(self.frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.imax_input.sizePolicy().hasHeightForWidth())
        self.imax_input.setSizePolicy(sizePolicy)
        self.imax_input.setMinimumSize(QtCore.QSize(50, 0))
        self.imax_input.setObjectName(_fromUtf8("imax_input"))
        self.gridLayout_2.addWidget(self.imax_input, 2, 3, 1, 1)
        self.gridLayout.addWidget(self.frame, 0, 0, 1, 1)

        self.retranslateUi(ImageScalingWidget)
        QtCore.QMetaObject.connectSlotsByName(ImageScalingWidget)

    def retranslateUi(self, ImageScalingWidget):
        ImageScalingWidget.setWindowTitle(_translate("ImageScalingWidget", "Form", None))
        self.label.setText(_translate("ImageScalingWidget", "Logarithmic Scale", None))
        self.label_2.setText(_translate("ImageScalingWidget", "Contrast", None))
        self.label_3.setText(_translate("ImageScalingWidget", "Intensity:", None))


class ImageScalingWidget(QtGui.QWidget, Ui_ImageScalingWidget):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QWidget.__init__(self, parent, f)

        self.setupUi(self)


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    ImageScalingWidget = QtGui.QWidget()
    ui = Ui_ImageScalingWidget()
    ui.setupUi(ImageScalingWidget)
    ImageScalingWidget.show()
    sys.exit(app.exec_())

