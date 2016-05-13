# encoding: utf-8, division
from __future__ import print_function, division

from collections import defaultdict
import itertools
import time

from .helpers import timethis


from PyQt4.QtCore import (QObject, QThread, Qt, pyqtSignal, pyqtSlot, QString, QTimer)


class Worker(QObject):

    finished = pyqtSignal()
    error = pyqtSignal(QString)
    result = pyqtSignal(object)

    def __init__(self, f, args):
        super(Worker, self).__init__()
        self.f = f
        self.args = args

    @pyqtSlot()
    def process(self):
        try:
            result = self.f(*self.args)
            self.result.emit(result)
        except Exception:
            import traceback
            e = traceback.format_exc()
            self.error.emit(e)
        finally:
            self.finished.emit()


class AsyncRunner(object):

    def __init__(self, parent):
        self.workers = defaultdict(list)
        self.parent = parent

    def run_async_chained(self, functions, first_args):

        def start(i, args):
            if i >= len(functions):
                return None
            f = functions[i]

            def call_back(result):
                start(i + 1, (result,))
            self.run_async(f, args, call_back=call_back)

        start(0, first_args)

    def _kill_running_workers(self, id_):
        for i, (thread, worker) in enumerate(self.workers[id_]):
            try:
                if thread.isRunning():
                    timethis(thread.quit)()
                    try:
                        del self.workers[id_][i]
                    except IndexError:
                        pass
            except RuntimeError:
                # happens if underlying c++ object is already killed
                pass

    def _setup_worker_and_move_to_new_thread(self, id_, function, args, call_back):

        thread = QThread()
        worker = Worker(function, args)
        worker.moveToThread(thread)
        thread.started.connect(worker.process)
        worker.error.connect(print)
        worker.finished.connect(thread.quit)
        worker.finished.connect(thread.deleteLater)
        thread.finished.connect(worker.deleteLater)
        if call_back is not None:
            worker.result.connect(call_back)

        # we keep references, else the objects would get killed when the method
        # is finished, which crashs the application:
        self.workers[id_].append((thread, worker))

        return worker, thread

    def _schedule_waiting_cursor(self, thread, blocked):
        # if the worker runs more than 500 msec we set the cursor to WaitCursor,
        def set_waiting_cursor(thread=thread, blocked=blocked, parent=self.parent):
            try:
                if thread is not None and thread.isRunning():
                    parent.setCursor(Qt.WaitCursor)
                    if blocked:
                        parent.setEnabled(False)
            except RuntimeError:
                # happens if underlying c++ object is already killed
                pass

        def reset_cursor(thread=thread, parent=self.parent):
            print("reset cursor + unblock gui")
            parent.setCursor(Qt.ArrowCursor)
            parent.setEnabled(True)

        thread.finished.connect(reset_cursor)
        QTimer.singleShot(200, set_waiting_cursor)

    def _setup_thread_cleanup(self, id_, thread):

        def remove(workers=self.workers, id_=id_, thread=thread, self=self):
            while True:
                try:
                    # sometimes the c++ object already died, then we get
                    # RuntimeError: wrapped C/C++ object of type QThread has been deleted
                    running = thread.isRunning()
                except RuntimeError:
                    running = False
                if not running:
                    break
                time.sleep(.01)

            for i, (t, w) in itertools.izip(itertools.count(), self.workers[id_]):
                if t is thread:
                    try:
                        del workers[id_][i]
                    except IndexError:
                        pass  # might happen in race situations.

        thread.finished.connect(remove)

    def run_async(self, function, args, id_=None, only_one_worker=False, call_back=None,
                  blocked=False):

        if only_one_worker:
            self._kill_running_workers(id_)

        worker, thread = self._setup_worker_and_move_to_new_thread(id_, function, args, call_back)
        self._setup_thread_cleanup(id_, thread)
        self._schedule_waiting_cursor(thread, blocked)

        thread.start()


if __name__ == "__main__":
    import  guidata
    app = guidata.qapplication()  # singleton !

    def f(x):
        return x + 1

    def g(x):
        print("got ", x)
        app.quit()

    runner = AsyncRunner()
    runner.run_async_chained((f, f,f,f,f,g), (0,))

    app.exec_()

