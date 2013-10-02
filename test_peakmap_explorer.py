import emzed
import copy

pm = emzed.io.loadPeakMap(("tests/data/test.mzXML"))

pm2 = copy.deepcopy(pm)
pm2.meta["source"] = "distorted.mzXML"

for s in pm2.spectra:
    s.rt = s.rt + 0.005 * (s.rt - 30.5) **2
    s.peaks[:,0] += 0.01


tab = emzed.utils.toTable("name", ["subst1", "H2O"])
tab.addColumn("rtmin", [0, 20.0])
tab.addColumn("rtmax", [20, 30.0])
tab.addColumn("mzmin", [200, 0.0])
tab.addColumn("mzmax", [500, 999.0])
#tab = tab.join(tab, True)
#tab = emzed.utils.integrate(tab)
print emzed.gui.inspectPeakMap(pm, table=tab)
#emzed.gui.inspect(tab)
#emzed.gui.inspectChromatograms(pm)
