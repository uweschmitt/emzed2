# encoding: utf-8
from __future__ import print_function
import os

here = os.path.dirname(os.path.abspath(__file__))

import emzed

t = emzed.io.loadTable(os.path.join(here, "calibration_patterns.table"))
t.setColFormat("name", "%s")
t.replaceColumn("id", t.id.apply(str))
t.meta["hide_in_explorer"] = ("t", "isotope_id", "a")
ti = [t.copy() for _ in t]
t.addColumn("t", ti)
t.info()

t2 = t.copy()
emzed.gui.inspect([t, t2])

print(t.meta)
print(t2.meta)
