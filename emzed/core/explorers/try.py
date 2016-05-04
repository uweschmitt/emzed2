# encoding: utf-8, division
from __future__ import print_function, division

from PyQt4.QtGui import *
from PyQt4.QtCore import *


import guidata
import time

app = guidata.qapplication()  # singleton !

def doit(app=app):
    print("run")
    time.sleep(2.0)
    print("run")
    app.quit()

ti = QTimer.singleShot(1000, doit)
print(ti)

app.exec_()



