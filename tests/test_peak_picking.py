import emzed.core.peak_picking
import emzed.io

def testPeakPicking(path):
    pp = emzed.core.peak_picking.PeakPickerHiRes()
    ds = emzed.io.loadPeakMap(path("data/gauss_data.mzML"))
    ds2 = pp.pickPeakMap(ds)
    assert len(ds) == len(ds2)
    assert ds2.spectra[0].peaks.shape == (9570, 2)
