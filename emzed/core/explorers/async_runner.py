# encoding: utf-8, division
from __future__ import print_function, division

import random
import time

from PyQt4.QtCore import (QThread, Qt, pyqtSignal, QString, QTimer)


class Worker(QThread):

    finished = pyqtSignal()
    error = pyqtSignal(QString)
    message = pyqtSignal(QString)
    result = pyqtSignal(object)

    def __init__(self, f, args):
        super(Worker, self).__init__()
        self.f = f
        self.args = args
        self.setObjectName("%s_%s" % (str(time.time()), random.random()))

    def run(self):
        try:
            self.message.emit("run %s %s" % (self.f.__name__, self.args))
            result = self.f(*self.args)
            self.result.emit(result)
            self.message.emit("emitted %s" % result)
        except Exception:
            import traceback
            e = traceback.format_exc()
            self.error.emit(e)
        finally:
            self.finished.emit()


class AsyncRunner(object):

    def __init__(self, parent=None, reporter=None):
        self.workers = {}
        self.parent = parent
        self.reporter = reporter

    def run_async_chained(self, functions, first_args):

        def start(i, args):
            if i >= len(functions):
                return None
            f = functions[i]

            def call_back(result):
                start(i + 1, (result,))
            self.run_async(f, args, call_back=call_back)

        start(0, first_args)

    def _setup_worker(self, function, args, call_back):

        worker = Worker(function, args)
        worker.error.connect(print)
        if self.reporter is not None:
            worker.message.connect(self.reporter)
        if call_back is not None:
            worker.result.connect(call_back)

        # we keep references, else the objects would get killed when the method
        # is finished, which crashs the application:
        key = str(worker.objectName())
        self.workers[key] = worker

        def remove_reference():
            worker = self.workers[key]
            while worker.isRunning():
                time.sleep(.001)
            del self.workers[key]

        worker.finished.connect(remove_reference)
        return worker

    def _schedule_waiting_cursor(self, worker, blocked):
        # if the worker runs more than 500 msec we set the cursor to WaitCursor,
        def set_waiting_cursor(worker=worker, blocked=blocked, parent=self.parent):
            try:
                if worker is not None and worker.isRunning():
                    parent.setCursor(Qt.WaitCursor)
                    if blocked:
                        parent.setEnabled(False)
            except RuntimeError:
                # happens if underlying c++ object is already killed
                pass

        def reset_cursor(parent=self.parent):
            print("reset cursor + unblock gui")
            parent.setCursor(Qt.ArrowCursor)
            parent.setEnabled(True)

        worker.finished.connect(reset_cursor)
        QTimer.singleShot(200, set_waiting_cursor)

    def run_async(self, function, args, call_back=None, blocked=False):

        worker = self._setup_worker(function, args, call_back)
        if self.parent is not None:
            self._schedule_waiting_cursor(worker, blocked)

        worker.start()
