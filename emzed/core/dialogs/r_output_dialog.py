from PyQt4.Qt import QApplication
from PyQt4.QtCore import Qt, SIGNAL, QThread
from PyQt4.QtGui import (QDialog, QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout, QCursor)

from ..r_connect.r_executor import RInterpreter


class ROutputDialog(QDialog):

    def __init__(self, command):
        super(ROutputDialog, self).__init__(None, Qt.Window)
        self.setWindowTitle("R output dialog")
        self.setWindowModality(Qt.WindowModal)
        self.setMinimumWidth(800)
        self.setMinimumHeight(500)
        self.setup_widgets()
        self.setup_layout()
        self.connect_signals()
        self.command = command

    def setup_widgets(self):
        self.stdout = QTextEdit(self)
        self.stdout.setReadOnly(1)
        scrb = self.stdout.verticalScrollBar()
        scrb.setValue(scrb.maximum())
        self.ok_button = QPushButton("Close")
        self.ok_button.setEnabled(False)

    def setup_layout(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.stdout)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        layout.addLayout(button_layout)

    def connect_signals(self):
        self.connect(self.ok_button, SIGNAL("pressed()"), self.accept)

    def showEvent(self, evt):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

        class WorkerThread(QThread):

            def run(self, command=self.command, stdout=self.stdout):
                raise Exception("depreciated, please adapt to new r interpreter")
                #RInterpreter().execute(command)
                proc = RExecutor().start_command(command)
                for line in proc:
                    stdout.append(line)
                    if not line:
                        break
                stderr = proc.next()
                stdout.append("\n" + stderr)
                return_code = proc.next()
                self.emit(SIGNAL("command_finished(int)"), return_code)

        self.t = WorkerThread()
        self.connect(self.t, SIGNAL("command_finished(int)"), self.command_finished)
        self.t.start()

    def command_finished(self, return_code):
        self.return_code = return_code
        self.ok_button.setEnabled(True)
        scrb = self.stdout.verticalScrollBar()
        scrb.setValue(scrb.maximum())
        QApplication.restoreOverrideCursor()


def main():
    app = QApplication([])
    dlg = ROutputDialog("""
                    source("http://bioconductor.org/biocLite.R")
                    todo <- old.packages(repos=biocinstallRepos())
                    todo <- old.packages(repos=biocinstallRepos())
                    todo <- old.packages(repos=biocinstallRepos())
                    q(status=length(todo))
    """)
    dlg.exec_()

if __name__ == "__main__":
    main()
