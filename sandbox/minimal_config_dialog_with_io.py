import PyQt4.QtGui
import sys

app = PyQt4.QtGui.QApplication(sys.argv)
import guidata.dataset.datatypes as dt
import guidata.dataset.dataitems as di
import guidata.userconfig as ucf


class Processing(dt.DataSet):
    """Example"""

    g1 = dt.BeginGroup("g1")
    a = di.FloatItem("Parameter #1", default=2.3)
    b = di.IntItem("Parameter #2", min=0, max=10, default=5)
    c = di.StringItem("NAME")
    _g1 = dt.EndGroup("g1")

    g2 = dt.BeginGroup("g2")
    type = di.ChoiceItem("Processing algorithm",
                         ("type 1", "type 2", "type 3"))

    _g2 = dt.EndGroup("g2")

def save(fp, param):

    cf = ucf.UserConfig(dict())
    param.write_config(cf, "section", "option")
    cf.write(fp)

def load(fp, param):
    cf = ucf.UserConfig(dict())
    cf.read(fp)
    param.read_config(cf, "section", "option")


param = Processing()
param.edit()


import cStringIO
fp = cStringIO.StringIO()

save(fp, param)

print fp.getvalue()

fp.seek(0)
load(fp, param)

print param.to_string()
