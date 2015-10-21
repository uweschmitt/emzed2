# encoding: utf-8
from __future__ import print_function

from PyQt4 import QtGui, QtCore

from _integration_widget import _IntegrationWidget


class IntegrationWidget(_IntegrationWidget):

    TRIGGER_INTEGRATION = QtCore.pyqtSignal(str, str)

    def __init__(self, parent=None):
        super(IntegrationWidget, self).__init__(parent)
        self._setup()

    def _setup(self):
        self.setEnabled(False)
        self._compute_button.clicked.connect(self._button_pressed)

    def set_integration_methods(self, names):
        self._methods.clear()
        for name in names:
            self._methods.addItem(name)
        self.setEnabled(True)

    def set_postfixes(self, postfixes):
        self._postfixes.clear()
        for postfix in postfixes:
            self._postfixes.addItem(postfix)

        if len(postfixes) == 1:
            self._postfixes.setVisible(False)

    def _button_pressed(self):
        self.TRIGGER_INTEGRATION.emit(self._methods.currentText(), self._postfixes.currentText())


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)

    def dump(*a):
        print(a)

    widget = IntegrationWidget()
    widget.set_integration_methods(("emg", "trapez"))
    widget.TRIGGER_INTEGRATION.connect(dump)
    widget.show()
    sys.exit(app.exec_())

