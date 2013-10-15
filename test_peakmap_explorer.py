import emzed
import copy

pm = emzed.io.loadPeakMap(("tests/data/test.mzXML"))
pm2 = emzed.io.loadPeakMap(("tests/data/test_mini.mzXML"))


tab = emzed.utils.toTable("name", ["subst1", "H2O"])
tab.addColumn("rtmin", [0, 20.0])
tab.addColumn("rtmax", [20, 30.0])
tab.addColumn("mzmin", [200, 0.0])
tab.addColumn("mzmax", [500, 999.0])
#tab = tab.join(tab, True)
#tab = emzed.utils.integrate(tab)
print emzed.gui.inspectPeakMap(pm, table=tab)
#print emzed.gui.inspectPeakMap(pm2, pm,  table=tab)
#emzed.gui.inspect(tab)
#emzed.gui.inspectChromatograms(pm)
