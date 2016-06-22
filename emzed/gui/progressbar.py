# encoding: utf-8
from __future__ import print_function, division, absolute_import

from contextlib import contextmanager
import time

import guidata
from PyQt4.QtGui import QProgressDialog


@contextmanager
def ProgressBar(n_steps, label="", allow_cancel=False, parent=None):
    """
    Progressbar context manager for showing progress of workflow to user. Example::

        with emzed.gui.ProgressBar(n_steps=100, allow_cancel=True) as handler:
            for i in range(100):

                # we simulate work of step i

                # we update progressbar
                handler.update(i, "step %03d" % i)

                # we can check if user pressed "Cancel" button and stop our "workflow":
                if handler.is_canceled():
                    break
    """

    app = guidata.qapplication()
    dlg = QProgressDialog(parent)
    dlg.setLabelText(label)
    dlg.setAutoClose(False)
    dlg.setAutoReset(False)
    if allow_cancel:
        dlg.setCancelButtonText("Cancel")
    dlg.setMaximum(n_steps)

    class ProgressBarHandler(object):

        def __init__(self, n_steps, dlg):
            self._dlg = dlg
            self._n_steps = n_steps
            self._n = 0
            self._canceled = False
            dlg.canceled.connect(self._set_canceled)
            dlg.setValue(0)

        def _set_canceled(self):
            self._canceled = True
            dlg.close()

        def update(self, n, message=None):
            app.processEvents()
            self._n = n
            dlg.setValue(n + 1)
            if message is not None:
                dlg.setLabelText(message)
            dlg.update()
            app.processEvents()

        def is_canceled(self):
            return self._canceled

    dlg.activateWindow()
    dlg.show()
    dlg.raise_()
    app.processEvents()

    handler = ProgressBarHandler(n_steps, dlg)
    yield handler

    dlg.close()
