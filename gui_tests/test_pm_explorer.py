import os

here = os.path.dirname(os.path.abspath(__file__))

import guidata
app = guidata.qapplication()

import emzed
pm = emzed.io.loadPeakMap(os.path.join(here, "di.mzXML"))
# pm = emzed.io.loadPeakMap(os.path.join(here, "..", "tests", "data", "test_mini.mzXML"))
emzed.gui.inspect(pm)

