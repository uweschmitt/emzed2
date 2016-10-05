# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'filter_dialog.ui'
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

class Ui_FilterDialog(object):
    def setupUi(self, FilterDialog):
        FilterDialog.setObjectName(_fromUtf8("FilterDialog"))
        FilterDialog.resize(480, 640)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(FilterDialog.sizePolicy().hasHeightForWidth())
        FilterDialog.setSizePolicy(sizePolicy)
        FilterDialog.setMinimumSize(QtCore.QSize(0, 0))
        self.verticalLayout = QtGui.QVBoxLayout(FilterDialog)
        self.verticalLayout.setMargin(5)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.frame = QtGui.QFrame(FilterDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setMinimumSize(QtCore.QSize(400, 0))
        self.frame.setObjectName(_fromUtf8("frame"))
        self.widgets = QtGui.QGridLayout(self.frame)
        self.widgets.setContentsMargins(0, 5, 3, 3)
        self.widgets.setSpacing(0)
        self.widgets.setObjectName(_fromUtf8("widgets"))
        self.groupBox = QtGui.QGroupBox(self.frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.groupBox.setTitle(_fromUtf8(""))
        self.groupBox.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.groupBox.setFlat(True)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.groupBox)
        self.horizontalLayout.setMargin(0)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.cancel_button = QtGui.QPushButton(self.groupBox)
        self.cancel_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.cancel_button.setObjectName(_fromUtf8("cancel_button"))
        self.horizontalLayout.addWidget(self.cancel_button)
        self.submit_button = QtGui.QPushButton(self.groupBox)
        self.submit_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.submit_button.setObjectName(_fromUtf8("submit_button"))
        self.horizontalLayout.addWidget(self.submit_button)
        self.widgets.addWidget(self.groupBox, 4, 0, 1, 1)
        self.expert_mode_box = QtGui.QGroupBox(self.frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.expert_mode_box.sizePolicy().hasHeightForWidth())
        self.expert_mode_box.setSizePolicy(sizePolicy)
        self.expert_mode_box.setFlat(True)
        self.expert_mode_box.setCheckable(True)
        self.expert_mode_box.setChecked(False)
        self.expert_mode_box.setObjectName(_fromUtf8("expert_mode_box"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.expert_mode_box)
        self.verticalLayout_2.setMargin(12)
        self.verticalLayout_2.setSpacing(1)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.filter_expression = QtGui.QPlainTextEdit(self.expert_mode_box)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.filter_expression.sizePolicy().hasHeightForWidth())
        self.filter_expression.setSizePolicy(sizePolicy)
        self.filter_expression.setMinimumSize(QtCore.QSize(0, 120))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Courier"))
        self.filter_expression.setFont(font)
        self.filter_expression.setFrameShape(QtGui.QFrame.NoFrame)
        self.filter_expression.setFrameShadow(QtGui.QFrame.Plain)
        self.filter_expression.setLineWidth(1)
        self.filter_expression.setObjectName(_fromUtf8("filter_expression"))
        self.verticalLayout_2.addWidget(self.filter_expression)
        self.widgets.addWidget(self.expert_mode_box, 1, 0, 1, 1)
        self.scrollArea = QtGui.QScrollArea(self.frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(5)
        sizePolicy.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy)
        self.scrollArea.setMinimumSize(QtCore.QSize(0, 0))
        self.scrollArea.setFrameShape(QtGui.QFrame.NoFrame)
        self.scrollArea.setFrameShadow(QtGui.QFrame.Plain)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidgetResizable(False)
        self.scrollArea.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
        self.scrollArea.setObjectName(_fromUtf8("scrollArea"))
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 397, 423))
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(5)
        sizePolicy.setHeightForWidth(self.scrollAreaWidgetContents.sizePolicy().hasHeightForWidth())
        self.scrollAreaWidgetContents.setSizePolicy(sizePolicy)
        self.scrollAreaWidgetContents.setObjectName(_fromUtf8("scrollAreaWidgetContents"))
        self.filters_layout = QtGui.QGridLayout(self.scrollAreaWidgetContents)
        self.filters_layout.setContentsMargins(10, 15, 10, 20)
        self.filters_layout.setHorizontalSpacing(5)
        self.filters_layout.setVerticalSpacing(7)
        self.filters_layout.setObjectName(_fromUtf8("filters_layout"))
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.widgets.addWidget(self.scrollArea, 0, 0, 1, 1)
        self.verticalLayout.addWidget(self.frame)

        self.retranslateUi(FilterDialog)
        QtCore.QObject.connect(self.expert_mode_box, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.scrollArea.setDisabled)
        QtCore.QMetaObject.connectSlotsByName(FilterDialog)

    def retranslateUi(self, FilterDialog):
        FilterDialog.setWindowTitle(_translate("FilterDialog", "Dialog", None))
        self.cancel_button.setText(_translate("FilterDialog", "Cancel", None))
        self.submit_button.setText(_translate("FilterDialog", "Submit", None))
        self.expert_mode_box.setTitle(_translate("FilterDialog", "expert mode", None))


class FilterDialog(QtGui.QDialog, Ui_FilterDialog):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QDialog.__init__(self, parent, f)

        self.setupUi(self)


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    FilterDialog = QtGui.QDialog()
    ui = Ui_FilterDialog()
    ui.setupUi(FilterDialog)
    FilterDialog.show()
    sys.exit(app.exec_())

