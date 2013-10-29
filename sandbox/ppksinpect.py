import numpy as np
import emzed
import pylab

def cleanup_shoulders(pm, rtmin, rtmax, mzmin, mzmax):

    pmsub = pm.extract(rtmin, rtmax, mzmin, mzmax)

    maxi = [np.max(s.peaks[:,1]) for s in pmsub.spectra]

    i0 = np.argmax(np.max(s.peaks[:, 1]) for s in pmsub.spectra)
    imax = np.max(pmsub.spectra[i0].peaks[:,1])
    imax = max(np.max(s.peaks[:, 1]) for s in pmsub.spectra)
    i1 = np.argmax(pmsub.spectra[i0].peaks[:,1])
    fkrit = 0.02 * imax

    colors = "rgbkyc"

    for i, s in enumerate(pmsub.spectra):
        s = pmsub.spectra[i]
        peaks = s.peaks
        peaks = peaks[peaks[:, 1] <= fkrit]
        if not len(peaks):
            continue
        imax = np.max(peaks[:, 1])
        mz = peaks[:, 0]
        ii = peaks[:, 1] / imax


tab = emzed.io.loadTable("shoulders_table_with_chromos.table")
#emzed.gui.inspectPeakMap(tab.peakmap.uniqueValue())
pm = tab.peakmap.uniqueValue()

windows = [(25.45, 26.09, 292.937, 293.435),
           (25.48, 26.04, 294.117, 294.256),
           (25.45, 25.92, 329.121, 329.194),
           (16.55, 17.43, 245.985, 246.189)][1:2]

for rtmin, rtmax, mzmin, mzmax in windows:
    cleanup_shoulders(pm, rtmin, rtmax, mzmin, mzmax)



