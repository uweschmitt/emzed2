# encoding: utf-8
from __future__ import print_function

import emzed
import pytest


@pytest.fixture
def peaks(path):
    peaks = emzed.io.loadTable(path("data", "peaks_for_ms2_extraction.table"))

    # in order to reduce output for regtest:
    peaks.dropColumns("feature_id", "intensity", "quality", "fwhm", "z", "source")

    # additionally reduces output:
    return peaks.filter((peaks.id <= 6) | (peaks.id > 17))


@pytest.fixture
def peakmap(path):
    return emzed.io.loadPeakMap(path("data", "peaks_for_ms2_extraction.mzXML"))


def check(peaks, peakmap, regtest, mode):
    print(file=regtest)
    print("MODE=", mode, file=regtest)
    print(file=regtest)
    emzed.utils.attach_ms2_spectra(peaks, peakmap, mode=mode)

    def mz_range(spectra):
        mzs = [mz for s in spectra for mz in s.peaks[:, 0]]
        return max(mzs) - min(mzs)

    def energy(spectra):
        iis = [ii for s in spectra for ii in s.peaks[:, 1]]
        return sum(i * i for i in iis)

    peaks.addColumn("ms2_mz_range", peaks.spectra_ms2.apply(mz_range), type_=float)
    peaks.addColumn("ms2_energy", peaks.spectra_ms2.apply(energy), type_=float, format_="%.2e")
    peaks.addColumn("ms2_spec_count", peaks.spectra_ms2.apply(len), type_=int, format_="%d")
    peaks.setColFormat("spectra_ms2", None)

    print(peaks, file=regtest)


def test_mode_is_intersection(peaks, peakmap, regtest):
    check(peaks, peakmap, regtest, "intersection")


def test_mode_is_union(peaks, peakmap, regtest):
    check(peaks, peakmap, regtest, "union")


def test_mode_is_max_range(peaks, peakmap, regtest):
    check(peaks, peakmap, regtest, "max_range")


def test_mode_is_max_energy(peaks, peakmap, regtest):
    check(peaks, peakmap, regtest, "max_energy")


def test_mode_is_all(peaks, peakmap, regtest):
    check(peaks, peakmap, regtest, "all")
