# encoding: utf-8, division
from __future__ import print_function, division

from collections import defaultdict
import itertools

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

    def print_error(self, e):
        print(e)

    def run_async_chained(self, functions, first_args):

        def start(i, args):
            if i >= len(functions):
                return None
            f = functions[i]
            def call_back(result):
                start(i + 1, (result,))
            self.run_async(f, args, call_back=call_back)

        start(0, first_args)

    def run_async(self, function, args, id_=None, only_one_worker=False, call_back=None,
                  blocked=False):

        if only_one_worker:
            for i, (thread, worker) in enumerate(self.workers[id_]):
                if thread.isRunning():
                    timethis(thread.quit)()
                    try:
                        del self.workers[id_][i]
                    except IndexError:
                        pass

        thread = QThread()
        worker = Worker(function, args)
        worker.moveToThread(thread)
        worker.error.connect(self.print_error)
        thread.started.connect(worker.process)
        worker.finished.connect(thread.quit)
        worker.finished.connect(thread.deleteLater)
        thread.finished.connect(worker.deleteLater)

        def unblock():
            self.parent.setCursor(Qt.ArrowCursor)

        thread.finished.connect(unblock)

        def set_waiting_cursor():
            self.parent.setCursor(Qt.WaitCursor)

        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(set_waiting_cursor)

        thread.finished.connect(timer.stop)
        timer.start(200)

        if call_back is not None:
            worker.result.connect(call_back)

        # we keep references, else the objects would get killed when the method
        # is finished, which crashs the application:
        self.workers[id_].append((thread, worker))

        def remove(workers=self.workers, id_=id_, thread=thread):
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

