import emzed.core
a = 42

import guidata.dataset.datatypes as dt
import guidata.dataset.dataitems as di


class Processing(dt.DataSet):
    """Example"""

    a = di.FloatItem("Parameter #1", default=2.3)
    b = di.IntItem("Parameter #2", min=0, max=10, default=5)
    c = di.StringItem("NAME")

#import PyQt4.QtGui
#import sys
#app = PyQt4.QtGui.QApplication(sys.argv)
p = Processing()
#x = p.edit()
