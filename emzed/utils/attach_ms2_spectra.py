from __future__ import print_function

import emzed

from emzed.core.data_types import Spectrum

import pyopenms
import numpy as np
import sklearn.cluster
from collections import Counter, defaultdict
import sys


class LookupMS2(object):

    """fast lookup of spectra for given peak limits. uses binning + dictionary
    for fast lookup.
    """

    def __init__(self, spectra, dmz=0.01, drt=10):
        self.bins = defaultdict(list)
        self.dmz = dmz
        self.drt = drt
        number = 0
        last_n = 0
        print("build lookup table: ", end="")
        for i, spec in enumerate(spectra):
            n = int(10.0 * i / len(spectra))
            if n != last_n:
                print("%d%%" % (10 * n + 10), end=" ")
                sys.stdout.flush()
                last_n = n
            if spec.msLevel == 2 and spec.precursors:
                rt = spec.rt
                mz = spec.precursors[0][0]
                i0 = int(mz / dmz)
                j0 = int(rt / drt)
                self.bins[i0, j0].append((number, mz, rt, spec))
                number += 1
        print()

    def find_spectra(self, mzmin, mzmax, rtmin, rtmax):
        i0min = int(mzmin / self.dmz)
        i0max = int(mzmax / self.dmz)
        j0min = int(rtmin / self.drt)
        j0max = int(rtmax / self.drt)
        found = []
        seen = set()
        for i0 in range(i0min - 1, i0max + 2):
            for j0 in range(j0min - 1, j0max + 2):
                for (number, mz, rt, spec) in self.bins[i0, j0]:
                    if number in seen:
                        continue
                    if mzmin <= mz <= mzmax and rtmin <= rt <= rtmax:
                        seen.add(number)
                        found.append(spec)
        return found


def _botton_up_common(alignments):
    # find common peaks from botton to up
    # the indices in the result list realte to the last spectrum
    common = []
    for alignment in alignments:
        if not common:
            js = [j for (i, j) in alignment]
        else:
            js = [j for (i, j) in alignment if i in common]
        common = js
    return common


def _determine_scaling_factors(mz_vecs, intensity_vecs, alignments, common):

    # now we know common peaks and collect mz values top to bottom:
    n = len(mz_vecs)
    intensities = []

    # common relates to the last spectrum, so we start with this and collect
    # the common peaks:
    for i in range(n - 1, 0, -1):
        if not common:
            break
        iiv = intensity_vecs[i]
        intensities.append([iiv[ii] for ii in common])
        # adapt common for spectrum in next iteration:
        alignment = alignments[i - 1]
        common = [_i for (_i, _j) in alignment if _j in common]
    else:
        iiv = intensity_vecs[0]
        intensities.append([iiv[ii] for ii in common])

    if not intensities:
        return None

    # we collected in reverse order, this is we slice with stepsize -1:
    intensities = np.vstack(intensities)[::-1]

    median_ii = np.median(intensities, axis=0)
    scalings = np.median(intensities / median_ii, axis=1)

    return scalings


def _final_spectrum(peaks, spectra):
    rt = np.mean([s.rt for s in spectra])
    msLevel = 2
    polarity = spectra[0].polarity

    # precursor_mz = np.mean([mz for s in spectra for (mz, ii) in s.precursors])
    # precursor_ii = np.mean([ii for s in spectra for (mz, ii) in s.precursors])
    # precursors = [(precursor_mz, precursor_ii)]
    precursors = [p for spec in spectra for p in spec.precursors]
    return Spectrum(np.vstack(peaks), rt, msLevel, polarity, precursors)


def _merge(spectra, mz_tolerance=1.3e-3, only_common_peaks=False, verbose=True):
    """merges a list of spectra to one spetrum.

    *mz_tolerance*        : binning size for grouping peaks.

    *only_common_peaks*: if this value is true the resulting spectrum
                         only consists of dominant peaks which are present
                         in every input spectrum

    *verbose*: print diagnosis messages if this value is True
    """

    if not spectra:
        return None

    if len(spectra) == 1:
        return spectra[0]

    alignments = Spectrum.compute_alignments(spectra, mz_tolerance)
    common = _botton_up_common(alignments)

    mz_vecs = [s.peaks[:, 0] for s in spectra]
    intensity_vecs = [s.peaks[:, 1] for s in spectra]

    if only_common_peaks:
        mz_last = mz_vecs[-1]
        ii_last = intensity_vecs[-1]
        peaks = [(mz_last[i], ii_last[i]) for i in common]
        return _final_spectrum(peaks, spectra)

    scalings = _determine_scaling_factors(mz_vecs, intensity_vecs, alignments, common)
    if scalings is not None:
        peaks = _overlay(mz_vecs, intensity_vecs, scalings, mz_tolerance, verbose, len(common))
    else:
        peaks = [np.empty((0, 2))]
    return _final_spectrum(peaks, spectra)


def _overlay(mz_vecs, intensity_vecs, scalings, mz_tolerance, verbose, n):

    data_mz = []
    data_ii = []
    for mzv, iiv, scaling in zip(mz_vecs, intensity_vecs,  scalings):
        for mzi, iii in zip(mzv, iiv):
            data_mz.append(mzi)
            data_ii.append(iii / scaling)

    data_mz = np.array(data_mz).reshape(-1, 1)
    data_ii = np.array(data_ii).reshape(-1, 1)

    labels = sklearn.cluster.MeanShift(seeds=data_mz, bandwidth=mz_tolerance).fit_predict(data_mz)

    cc = Counter(labels)
    label_common_peaks = set(l for l in labels if cc[l] == len(scalings))

    if verbose:
        print("diagnosis message:")
        print("   number of clusters in common peaks   :", len(label_common_peaks))
        print("   number of common peaks from alignment:", n)
        print("both numbers should be approx equal if mz_tolerance parameter is chosen right")

    peaks = []
    for l in set(labels):
        mz = np.mean(data_mz[labels == l])
        ii = np.mean(data_ii[labels == l])
        peaks.append((mz, ii))

    peaks.sort()
    return peaks


def overlay_spectra(spectra, mode="union", mz_tolerance=1.3e-3, verbose=True):
    """merge a list of spectra to one single spectrum.

    - allowed modes are 'union' and 'intersection'.
    - mz_tolerance is absolute in Dalton, used to group peaks from different spectra
    - verbose=True gives extra debugging messages which might help to adjust mz_tolerance.
    """
    assert mode in ("union", "intersection"), "invalid value for mode parameter"
    only_common_peaks = (mode == "intersection")
    return _merge(spectra, only_common_peaks=only_common_peaks,
                  mz_tolerance=mz_tolerance, verbose=verbose)


def _merge_spectra(spectra, mode, mz_tolerance, verbose):
    """merge a list of spectra. allowed modes are 'max_range', 'max_energy', 'union',
    'intersection' and 'all'
    """
    if not spectra:
        return None
    if mode == "max_range":
        spectrum = max(spectra, key=lambda s: (max(s.peaks[:, 0]) - min(s.peaks[:, 0])))
        spectra = [spectrum]
    elif mode == "max_energy":
        spectrum = max(spectra, key=lambda s: sum(s.peaks[:, 1] ** 2))
        spectra = [spectrum]
    elif mode in ("union", "intersection"):
        only_common_peaks = (mode == "intersection")
        ms2_spec = _merge(spectra, only_common_peaks=only_common_peaks,
                          mz_tolerance=mz_tolerance, verbose=verbose)
        spectra = [ms2_spec]
    elif mode == "all":
        pass  # this i
    else:
        raise ValueError("mode is not allowed")
    return spectra

def attach_ms2_spectra(peak_table, peak_map, mode="union", mz_tolerance=1.3e-3, verbose=True):
    """takes *peak_table* with columns "id", "rtmin", "rtmax", "mzmin", "mzmax" and "peakmap"
    and extracts the ms2 spectra for these peaks.

    the *peak_table* is modified in place, an extra column "ms2_spectra" is added.
    the content of such a cell in the table is always a list of spectra. for modes "union"
    and "intersection" this list contains one single spectrum.

    modes:
        - "all": extracts a list of ms2 spectra per peak
        - "max_range": extracts spec with widest m/z range
        - "max_energy": extrats spec with maximal energy
        - "union": merges all ms2 spectra from one peak to one spectrum containing all peaks
        - "intersection": merges all ms2 spectra from one peak to one spectrum containing peaks which appear in all ms2 spectra.


    *mz_tolerance*: only needed for modes "union" and "intersection".

    *verbose*: prints some diagnosis messages for testing if mz_tolerance parameter fits,
               you shoud set this parameter to True if you are not sure if mz_tolerance
               fits to your machines resolution.
    """

    assert mode in ("all", "max_range", "max_energy", "union", "intersection")

    peak_table.ensureColNames(("id", "rtmin", "rtmax", "mzmin", "mzmax"))
    assert "spectra_ms2" not in peak_table.getColNames()

    lookup = LookupMS2(peak_map)

    all_spectra = []
    last_n = 0
    num_spectra = []
    infos = []
    for i, row in enumerate(peak_table):
        n = int(10.0 * i / len(peak_table))
        if n != last_n:
            print("%d%%" % (10 * n + 10), end=" ")
            sys.stdout.flush()
            if verbose:
                print()  # else we mix other output with this counting output in one line
            last_n = n
        ms2_spectra = lookup.find_spectra(row.mzmin, row.mzmax, row.rtmin, row.rtmax)
        num_spectra.append(len(ms2_spectra))
        merged_spectra = _merge_spectra(ms2_spectra, mode, mz_tolerance, verbose)

        empty_result = merged_spectra is None or not any(len(s.peaks) for s in merged_spectra)
        if ms2_spectra and empty_result:
            infos.append("%s(failed)" % mode)
        else:
            infos.append(mode)
        all_spectra.append(merged_spectra)
    peak_table.addColumn("spectra_ms2", all_spectra, type_=list)
    peak_table.addColumn("num_spectra_ms2", num_spectra, type_=int)
    peak_table.addColumn("ms2_extraction_info", infos, type_=str)
    num_ms2_added = peak_table.spectra_ms2.countNotNone()
    print()
    if num_ms2_added == 0:
        print("*" * 80)
        print("WARNING: all values in the spectra columns are None")
        print("*" * 80)
    else:
        print("added ms2 spectra to %d peaks out of %d" % (num_ms2_added, len(peak_table)))
    print()


def test():
    """

    TODO:
        tests
    """

    t = emzed.io.loadTable("/Users/uweschmitt/Projects/eawag_workflows/src/sandbox/ms1ms2.table")
    ds = t.peakmap.uniqueValue()
    ds = emzed.io.loadPeakMap("/Users/uweschmitt/Projects/eawag_workflows/src/sandbox/ms1ms2.mzXML")
    import time
    started = time.time()
    attach_ms2_spectra(t, ds, verbose=False)
    print(time.time() - started)
    print(t)

if __name__ == "__main__":
    test()

