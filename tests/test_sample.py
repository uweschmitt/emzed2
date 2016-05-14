from __future__ import print_function

import cPickle
import os

import numpy as np
import emzed
from emzed_optimizations import chromatogram, sample_image, sample_peaks, sample_peaks_from_lists

do_profile = False
try:
    profile
    do_profile = True
except:
    profile = lambda x: x


pms = []
def _load():
    # we doent want to import emzed here for avoiding
    # circular dependencies, so we fake objects
    # from emzed.core.data_types.ms_types for testing:
    if not pms:
        here = os.path.dirname(__file__)
        pms.append(emzed.io.loadPeakMap(os.path.join(here, "data", "test_mini.mzXML")))
    return pms[0]



@profile
def test_chromatogram():

    pm = _load()

    rtmin = pm.spectra[0].rt
    rtmax = pm.spectra[-1].rt
    mzmin = min(min(s.peaks[:, 0]) for s in pm.spectra)
    mzmax = max(max(s.peaks[:, 0]) for s in pm.spectra)


    rts, chromo = chromatogram(pm, 0, 0, 0, 0, 1)
    assert len(rts) == 0
    assert len(chromo) == 0

    rts, chromo = chromatogram(pm, 0, 10000, 0, 10000, 2)
    assert len(rts) == 0
    assert len(chromo) == 0

    rts, chromo = chromatogram(pm, 0, 1000, rtmin, rtmin, 1)
    assert len(rts) == 1
    assert len(chromo) == 1

    rts, chromo = chromatogram(pm, 0, 1000, rtmax, rtmax, 1)
    assert len(rts) == 1
    assert len(chromo) == 1

    rts, chromo = chromatogram(pm, mzmin - 1e-5, mzmin - 1e-5, rtmin, rtmax, 1)
    assert len(rts) == 2540
    assert len(chromo) == 2540
    assert sum(chromo) == 0.0

    rts, chromo = chromatogram(pm, mzmax + 1e-5, mzmax + 1e-5, rtmin, rtmax, 1)
    assert len(rts) == 2540
    assert len(chromo) == 2540
    assert sum(chromo) == 0.0

    rts, chromo = chromatogram(pm, 0, 1000, 41, 41.5, 1)
    assert len(rts) == 34
    assert len(chromo) == 34

    assert abs(rts[0] -  41.00279998779) < 1e-4, rts[0]
    assert abs(chromo[0] - 33628524.55078125) < 1e-2, chromo[0]

    rts, chromo = chromatogram(pm, 0, 1000, 41, 3000, 1)
    assert len(rts) == 216
    assert len(chromo) == 216

    assert abs(rts[215] - 44.89799880) < 1e-5, rts[215]
    assert abs(chromo[215] - 309048.935241) < 1e-2, chromo[215]

    rts, chromo = chromatogram(pm, 0, 1000, rtmax + 10, rtmax + 20, 1)
    assert len(rts) == 0
    assert len(chromo) == 0


def py_sample(pm, rtmin, rtmax, mzmin, mzmax, w, h):
    rtmin = float(rtmin)
    rtmax = float(rtmax)
    mzmin = float(mzmin)
    mzmax = float(mzmax)
    img = np.zeros((h, w), dtype=np.float64)
    for s in pm.spectra:
        if s.rt < rtmin:
            continue
        if s.rt > rtmax:
            continue
        if s.msLevel != 1:
            continue
        x_bin = int((s.rt - rtmin) / (rtmax - rtmin) * (w - 1))

        peaks = s.peaks
        ix = (peaks[:, 0] >= mzmin) & (peaks[:, 0] <= mzmax)
        mzs = peaks[ix, 0]
        iis = peaks[ix, 1]
        mz_bin = np.floor((mzs - mzmin) / (mzmax - mzmin) * (h - 1)).astype(int)
        upd = np.bincount(mz_bin, iis)
        i1 = max(mz_bin) + 1
        img[:i1, x_bin] = img[:i1, x_bin] + upd

    return img


@profile
def test_sample():
    pm = _load()

    t0 = 41.0
    m0 = 202.0

    pm, rtmin, rtmax, mzmin, mzmax, w, h = (pm, t0, t0 + 300.0, m0, m0 + 500, 200, 400)
    img_optim = sample_image(pm, rtmin, rtmax, mzmin, mzmax, w, h)
    img_py = py_sample(pm, rtmin, rtmax, mzmin, mzmax, w, h)

    diff = np.max(np.abs(img_optim - img_py))
    assert diff == 0.0, diff


@profile
def test_sample_peaks():
    pm = _load()
    rtmin = pm.spectra[0].rt
    rtmax = pm.spectra[-1].rt
    mzmin = min(min(s.peaks[:, 0]) for s in pm.spectra)
    mzmax = max(max(s.peaks[:, 0]) for s in pm.spectra)

    res = sample_peaks(pm, rtmin, rtmax, mzmin, mzmax, 1)
    assert res is not None
    assert res.shape == (1, 2)

    res = sample_peaks(pm, rtmin, rtmax, mzmin, mzmax, 10000)
    assert res is not None
    assert res.shape == (9876, 2)

    s0 = pm.spectra[0]
    pm.spectra = [s0]
    res = sample_peaks(pm, rtmin, rtmax, mzmin, mzmax, 10000)
    assert res is not None
    assert res.shape == (76, 2), res.shape
    dist = np.linalg.norm(res[0:2, :] - pm.spectra[0].peaks[0:2, :])
    assert dist == 0.0


@profile
def test_sample_peaks_from_lists(regtest):
    pm = _load()
    rtmin = pm.spectra[0].rt
    rtmax = pm.spectra[-1].rt
    mzmin = min(min(s.peaks[:, 0]) for s in pm.spectra)
    mzmax = max(max(s.peaks[:, 0]) for s in pm.spectra)

    mz_list = [s.peaks[:, 0] for s in pm.spectra]
    ii_list = [s.peaks[:, 1].astype(np.float32) for s in pm.spectra]

    res = sample_peaks_from_lists(mz_list, ii_list, mzmin, mzmax, 10000)
    assert res is not None
    assert res.shape == (76, 2)
    print(res, file=regtest)


if do_profile:
    test_sample_peaks()
    test_sample()
    test_chromatogram()
