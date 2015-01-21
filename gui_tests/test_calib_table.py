# encoding: utf-8
from __future__ import print_function
import os

here = os.path.dirname(os.path.abspath(__file__))

import emzed

t = emzed.io.loadTable(os.path.join(here, "calibration_patterns.table"))
print(t.id.values)
t.replaceColumn("id", t.id.apply(str))
ti = [t.copy() for _ in t]
t.addColumn("t", ti)
emzed.gui.inspect(t)
