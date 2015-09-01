# encoding: utf-8
from __future__ import print_function
import pdb

import emzed
from emzed.core.data_types import Spectrum

import numpy as np

def test_0():

    ii = np.linspace(1000.0, 2000.0, 21)
    mzs = np.linspace(100.0, 1100.0, 21)

    peaks = np.vstack((mzs, ii)).T
    spec = Spectrum(peaks, rt=100.0, msLevel=1, polarity="+")
    assert (1.0 - 1e-3) <= spec.cosine_distance(spec, 0.001) <= 1.0 + 1e-3

    # enforce only 10 matches
    mzs[10:] = 0.0
    peaks = np.vstack((mzs, ii)).T
    other = Spectrum(peaks, rt=100.0, msLevel=1, polarity="+")
    assert (1.0 - 1e-3) <= spec.cosine_distance(other, 0.001) <= 1.0 + 1e-3

    # enforce only 5 matches
    mzs[5:] = 0.0
    peaks = np.vstack((mzs, ii)).T
    other = Spectrum(peaks, rt=100.0, msLevel=1, polarity="+")
    assert (0.0 - 1e-3) <= spec.cosine_distance(other, 0.001, min_matches=10) <= 0.0 + 1e-3

    ii = np.linspace(1000.0, 2000.0, 21)
    mzs = np.linspace(100.0, 1100.0, 21) + 800.0
    peaks = np.vstack((mzs, ii)).T
    other = Spectrum(peaks, rt=100.0, msLevel=1, polarity="+")
    assert (0.99963 - 1e-3) <= spec.cosine_distance(other, 0.001, min_matches=5) <= 0.99963 + 1e-3

    ii = np.linspace(1000.0, 2000.0, 21)
    mzs = np.linspace(100.0, 1100.0, 21) + 200
    peaks = np.vstack((mzs, ii)).T
    s1 = Spectrum(peaks, rt=1.0, msLevel=2, polarity="+", precursors=[(10.0, 1000)])
    s2 = Spectrum(peaks, rt=1.0, msLevel=2, polarity="+", precursors=[(210.0, 1000)])

    assert abs(s1.cosine_distance(s2, 0.001, consider_precursor_shift=True) - 0.99986) < 1e-3
