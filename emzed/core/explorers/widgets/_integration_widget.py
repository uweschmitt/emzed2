# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'integration_widget.ui'
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

class Ui__IntegrationWidget(object):
    def setupUi(self, _IntegrationWidget):
        _IntegrationWidget.setObjectName(_fromUtf8("_IntegrationWidget"))
        _IntegrationWidget.resize(225, 154)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(_IntegrationWidget.sizePolicy().hasHeightForWidth())
        _IntegrationWidget.setSizePolicy(sizePolicy)
        self.gridLayout = QtGui.QGridLayout(_IntegrationWidget)
        self.gridLayout.setMargin(0)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self._frame = QtGui.QFrame(_IntegrationWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._frame.sizePolicy().hasHeightForWidth())
        self._frame.setSizePolicy(sizePolicy)
        self._frame.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self._frame.setFrameShape(QtGui.QFrame.WinPanel)
        self._frame.setFrameShadow(QtGui.QFrame.Sunken)
        self._frame.setLineWidth(1)
        self._frame.setObjectName(_fromUtf8("_frame"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self._frame)
        self.verticalLayout_2.setMargin(5)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self._label = QtGui.QLabel(self._frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._label.sizePolicy().hasHeightForWidth())
        self._label.setSizePolicy(sizePolicy)
        self._label.setMaximumSize(QtCore.QSize(250, 16777215))
        self._label.setFocusPolicy(QtCore.Qt.NoFocus)
        self._label.setObjectName(_fromUtf8("_label"))
        self.verticalLayout_2.addWidget(self._label)
        self._methods = QtGui.QComboBox(self._frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._methods.sizePolicy().hasHeightForWidth())
        self._methods.setSizePolicy(sizePolicy)
        self._methods.setMaximumSize(QtCore.QSize(250, 16777215))
        self._methods.setFocusPolicy(QtCore.Qt.NoFocus)
        self._methods.setObjectName(_fromUtf8("_methods"))
        self.verticalLayout_2.addWidget(self._methods)
        self._postfixes = QtGui.QComboBox(self._frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._postfixes.sizePolicy().hasHeightForWidth())
        self._postfixes.setSizePolicy(sizePolicy)
        self._postfixes.setMaximumSize(QtCore.QSize(250, 16777215))
        self._postfixes.setFocusPolicy(QtCore.Qt.NoFocus)
        self._postfixes.setObjectName(_fromUtf8("_postfixes"))
        self.verticalLayout_2.addWidget(self._postfixes)
        self._compute_button = QtGui.QPushButton(self._frame)
        self._compute_button.setEnabled(True)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._compute_button.sizePolicy().hasHeightForWidth())
        self._compute_button.setSizePolicy(sizePolicy)
        self._compute_button.setMaximumSize(QtCore.QSize(250, 16777215))
        self._compute_button.setMouseTracking(False)
        self._compute_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self._compute_button.setObjectName(_fromUtf8("_compute_button"))
        self.verticalLayout_2.addWidget(self._compute_button)
        self.gridLayout.addWidget(self._frame, 0, 0, 1, 1)

        self.retranslateUi(_IntegrationWidget)
        QtCore.QMetaObject.connectSlotsByName(_IntegrationWidget)

    def retranslateUi(self, _IntegrationWidget):
        _IntegrationWidget.setWindowTitle(_translate("_IntegrationWidget", "Form", None))
        self._label.setText(_translate("_IntegrationWidget", "Peak area computation", None))
        self._compute_button.setText(_translate("_IntegrationWidget", "Update area", None))


class _IntegrationWidget(QtGui.QWidget, Ui__IntegrationWidget):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QWidget.__init__(self, parent, f)

        self.setupUi(self)


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    _IntegrationWidget = QtGui.QWidget()
    ui = Ui__IntegrationWidget()
    ui.setupUi(_IntegrationWidget)
    _IntegrationWidget.show()
    sys.exit(app.exec_())

