# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'filter_criteria_widget.ui'
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

class Ui__FilterCriteriaWidget(object):
    def setupUi(self, _FilterCriteriaWidget):
        _FilterCriteriaWidget.setObjectName(_fromUtf8("_FilterCriteriaWidget"))
        _FilterCriteriaWidget.resize(291, 200)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(_FilterCriteriaWidget.sizePolicy().hasHeightForWidth())
        _FilterCriteriaWidget.setSizePolicy(sizePolicy)
        _FilterCriteriaWidget.setMinimumSize(QtCore.QSize(100, 0))
        self._verticalLayout = QtGui.QVBoxLayout(_FilterCriteriaWidget)
        self._verticalLayout.setSpacing(1)
        self._verticalLayout.setMargin(3)
        self._verticalLayout.setObjectName(_fromUtf8("_verticalLayout"))
        self._scrollArea = QtGui.QScrollArea(_FilterCriteriaWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._scrollArea.sizePolicy().hasHeightForWidth())
        self._scrollArea.setSizePolicy(sizePolicy)
        self._scrollArea.setMinimumSize(QtCore.QSize(0, 90))
        self._scrollArea.setFrameShape(QtGui.QFrame.NoFrame)
        self._scrollArea.setFrameShadow(QtGui.QFrame.Plain)
        self._scrollArea.setLineWidth(0)
        self._scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._scrollArea.setWidgetResizable(True)
        self._scrollArea.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self._scrollArea.setObjectName(_fromUtf8("_scrollArea"))
        self._widgets = QtGui.QWidget()
        self._widgets.setGeometry(QtCore.QRect(0, 0, 285, 194))
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._widgets.sizePolicy().hasHeightForWidth())
        self._widgets.setSizePolicy(sizePolicy)
        self._widgets.setObjectName(_fromUtf8("_widgets"))
        self._hlayout = QtGui.QHBoxLayout(self._widgets)
        self._hlayout.setMargin(0)
        self._hlayout.setObjectName(_fromUtf8("_hlayout"))
        self._scrollArea.setWidget(self._widgets)
        self._verticalLayout.addWidget(self._scrollArea)

        self.retranslateUi(_FilterCriteriaWidget)
        QtCore.QMetaObject.connectSlotsByName(_FilterCriteriaWidget)

    def retranslateUi(self, _FilterCriteriaWidget):
        _FilterCriteriaWidget.setWindowTitle(_translate("_FilterCriteriaWidget", "Form", None))


class _FilterCriteriaWidget(QtGui.QWidget, Ui__FilterCriteriaWidget):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QWidget.__init__(self, parent, f)

        self.setupUi(self)


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    _FilterCriteriaWidget = QtGui.QWidget()
    ui = Ui__FilterCriteriaWidget()
    ui.setupUi(_FilterCriteriaWidget)
    _FilterCriteriaWidget.show()
    sys.exit(app.exec_())

