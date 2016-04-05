# encoding: utf-8
from __future__ import print_function

import emzed
import copy

pm = emzed.io.loadPeakMap("peaks_for_ms2_extraction.mzXML")
for s in pm.spectra[:]:
    s.msLevel = 1
    sneu = copy.deepcopy(s)
    sneu.peaks = sneu.peaksInRange(150, 250)
    sneu.msLevel = 2
    pm.spectra.append(sneu)

print(pm.getMsLevels())

emzed.io.storePeakMap(pm, "di.mzXML")



