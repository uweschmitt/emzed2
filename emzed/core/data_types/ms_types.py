import pyopenms
import numpy as np
import os.path
import copy
import hashlib
from collections import defaultdict
import warnings

OPTIMIZATIONS_INSTALLED = False
try:
    import emzed_optimizations
    OPTIMIZATIONS_INSTALLED = True
except:
    pass


IS_PYOPENMS_2  = pyopenms.__version__.startswith("2.")


def deprecation(message):
    warnings.warn(message, UserWarning, stacklevel=2)


class Spectrum(object):

    """
    MS Spectrum Type
    """

    def __init__(self, peaks, rt, msLevel, polarity, precursors=None, meta=None):
        """Initialize instance

        - peaks
                       n x 2 matrix
                       first column: m/z values
                       second column: intensities
        - rt
                       float
                       retention time in seconds
        - msLevel
                       int
                       MSn level.
        - polarity
                       string of length 1
                       values: 0, + or -
        - precursors
                       list of floats
                       precursor m/z values if msLevel > 1
           """
        assert type(peaks) == np.ndarray, type(peaks)
        assert peaks.ndim == 2, "peaks has wrong dimension"
        assert peaks.shape[1] == 2, "peaks needs 2 columns"

        assert polarity in "0+-", "polarity must be +, - or 0"

        assert msLevel >= 1, "invalid msLevel"

        if precursors is None:
            precursors = []

        if meta is None:
            meta = dict()

        peaks = peaks[peaks[:, 1] > 0]  # remove zero intensities
        # sort resp. mz values:
        perm = np.argsort(peaks[:, 0])
        self.peaks = peaks[perm, :].astype(np.float32)
        self.rt = rt
        self.msLevel = msLevel
        self.polarity = polarity
        self.precursors = precursors
        self.meta = meta

    def __eq__(self, other):
        """Method to compare two instances of class Spectrum"""
        if self is other:
            return True
        return self.rt == other.rt and self.msLevel == other.msLevel \
            and self.precursors == other.precursors and self.polarity == other.polarity \
            and self.peaks.shape == other.peaks.shape and np.all(self.peaks == other.peaks)

    def __neq__(self, other):
        """Method to check if two instances of class Spectrum are *not* equal"""
        return not self.__eq__(other)

    def uniqueId(self):
        if "unique_id" not in self.meta:
            h = hashlib.sha256()
            h.update("%.6e" % self.rt)
            h.update(str(self.msLevel))
            # peaks.data is binary representation of numpy array peaks:
            h.update(str(self.peaks.data))
            h.update(str(self.polarity))
            for mz, ii in self.precursors:
                h.update("%.6e" % mz)
                h.update("%.6e" % ii)
            self.meta["unique_id"] = h.hexdigest()
        return self.meta["unique_id"]

    @classmethod
    def fromMSSpectrum(clz, mspec):
        """creates Spectrum from pyopenms.MSSpectrum"""
        assert type(mspec) == pyopenms.MSSpectrum, type(mspec)
        pcs = [(p.getMZ(), p.getIntensity()) for p in mspec.getPrecursors()]
        pol = {pyopenms.IonSource.Polarity.POLNULL: '0',
               pyopenms.IonSource.Polarity.POSITIVE: '+',
               pyopenms.IonSource.Polarity.NEGATIVE: '-'
               }.get(mspec.getInstrumentSettings().getPolarity())
        peaks = mspec.get_peaks()
        if IS_PYOPENMS_2:
            # signature changed in pyopenms
            mzs, iis = peaks
            peaks = np.vstack((mzs.flatten(), iis.flatten())).T
        res = clz(peaks, mspec.getRT(), mspec.getMSLevel(), pol, pcs)
        return res

    def __str__(self):
        """Return description of object as a string"""
        n = len(self)
        return "<Spectrum %#x with %d %s>" % (id(self), n, "peak" if n == 1 else "peaks")

    def __len__(self):
        """number of peaks in spectrum"""
        return self.peaks.shape[0]

    def __iter__(self):
        """Returns an iterator of the peaks of the Spectrum object"""
        return iter(self.peaks)

    def __getitem__(self, idx):
        return self.peaks[idx, :]

    def intensityInRange(self, mzmin, mzmax):
        """summed up intensities in given m/z range"""
        return self.peaksInRange(mzmin, mzmax)[:, 1].sum()

    def peaksInRange(self, mzmin=None, mzmax=None):
        """peaks in given m/z range as n x 2 matrix

           first column:   m/z values
           second column:  intenisities
        """
        mzs = None
        if mzmin is not None or mzmax is not None:
            mzs = self.peaks[:, 0]
        if mzmin is None and mzmax is None:
            raise Exception("no limits provided. need mzmin or mzmax")
        if mzmin is not None:
            imin = mzs.searchsorted(mzmin)
        else:
            imin = 0
        if mzmax is not None:
            imax = mzs.searchsorted(mzmax, side='right')
        else:
            # exclusive:
            imax = self.peaks.shape[0]
        return self.peaks[imin:imax]

    def mzRange(self):
        """returns pair min(mz), max(mz) for mz values in current spec.
           may return None, None if spec is empty !
        """
        return self.mzMin(), self.mzMax()

    def mzMin(self):
        """minimal m/z value in spectrum"""

        if len(self.peaks):
            return float(self.peaks[0, 0])
        return None

    def mzMax(self):
        """maximal m/z value in spectrum"""
        if len(self.peaks):
            return float(self.peaks[-1, 0])
        return None

    def maxIntensity(self):
        """maximal intensity in spectrum"""
        return float(self.peak[:, 1].max())

    def toMSSpectrum(self):
        """converts to pyopenms.MSSpectrum"""
        spec = pyopenms.MSSpectrum()
        spec.setRT(self.rt)
        spec.setMSLevel(self.msLevel)
        ins = spec.getInstrumentSettings()
        pol = {'0': pyopenms.IonSource.Polarity.POLNULL,
               '+': pyopenms.IonSource.Polarity.POSITIVE,
               '-': pyopenms.IonSource.Polarity.NEGATIVE}[self.polarity]
        ins.setPolarity(pol)
        spec.setInstrumentSettings(ins)
        oms_pcs = []
        for mz, I in self.precursors:
            p = pyopenms.Precursor()
            p.setMZ(mz)
            p.setIntensity(I)
            oms_pcs.append(p)
        spec.setPrecursors(oms_pcs)
        if IS_PYOPENMS_2:
            mz = self.peaks[:, 0]
            I = self.peaks[:, 1]
            spec.set_peaks((mz, I))
        else:
            spec.set_peaks(self.peaks)
        spec.updateRanges()
        return spec

    def __setstate__(self, state):
        self.__dict__ = state
        if not hasattr(self, "meta"):
            self.meta = dict()


class PeakMap(object):

    """
        This is the container object for spectra of type :py:class:`~.Spectrum`.
        Peakmaps can be loaded from .mzML, .mxXML or .mzData files,
        using :py:func:`~emzed.io.loadPeakMap`

        A PeakMap is a list of :py:class:`~.Spectrum` objects attached with
        meta data about its source.
    """

    def __init__(self, spectra, meta=None):
        """
            spectra : iterable (list, tuple, ...)  of objects of type
            :py:class:`~.Spectrum`

            meta    : dictionary of meta values
        """
        try:
            self.spectra = sorted(spectra, key=lambda spec: spec.rt)
        except:
            raise Exception("spectra param is not iterable")

        if meta is None:
            meta = dict()
        self.meta = meta
        polarities = set(spec.polarity for spec in spectra)
        if len(polarities) > 1:
            self.polarity = list(polarities)
        elif len(polarities) == 1:
            self.polarity = polarities.pop()
        else:
            self.polarity = None

    def __iter__(self):
        """Returns an iterator of the spectra of the PeakMap object"""
        return iter(self.spectra)

    def __getitem__(self, idx):
        return self.spectra[idx]

    def all_peaks(self, msLevel=1):
        return np.vstack((s.peaks for s in self.spectra if s.msLevel == msLevel))

    def filterIntensity(self, msLevel=None, minInt=None, maxInt=None):
        """creates new peakmap matching the given conditions. Using a single requirement
        as::

            pm.filterIntensity(
        """
        spectra = []
        for spec in self.spectra:
            if msLevel is not None and spec.msLevel != msLevel:
                continue
            peaks = spec.peaks
            if minInt is not None:
                peaks = peaks[peaks[:, 1] >= minInt]
            if maxInt is not None:
                peaks = peaks[peaks[:, 1] <= maxInt]
            spec = copy.deepcopy(spec)
            spec.peaks = peaks
            spectra.append(spec)

        return PeakMap(spectra, self.meta.copy())

    def extract(self, rtmin=None, rtmax=None, mzmin=None, mzmax=None, imin=None, imax=None,
                mslevelmin=None, mslevelmax=None):
        """ returns restricted Peakmap with given limits.
        Parameters with *None* value are not considered.

        Examples::

            pm.extract(rtmax = 12.5 * 60)
            pm.extract(rtmin = 12*60, rtmax = 12.5 * 60)
            pm.extract(rtmax = 12.5 * 60, mzmin = 100, mzmax = 200)
            pm.extract(rtmin = 12.5 * 60, mzmax = 200)
            pm.extract(mzmax = 200)

        \
        """

        spectra = copy.deepcopy(self.spectra)

        if mslevelmin is not None:
            spectra = [s for s in spectra if s.msLevel >= mslevelmin]
        if mslevelmax is not None:
            spectra = [s for s in spectra if s.msLevel <= mslevelmax]

        if rtmin:
            spectra = [s for s in spectra if rtmin <= s.rt]
        if rtmax:
            spectra = [s for s in spectra if rtmax >= s.rt]

        if mzmin is not None or mzmax is not None:
            for s in spectra:
                s.peaks = s.peaksInRange(mzmin, mzmax)

        if imin is not None or imax is not None:
            for s in spectra:
                if imin is not None:
                    s.peaks = s.peaks[s.peaks[:, 1] >= imin]
                if imax is not None:
                    s.peaks = s.peaks[s.peaks[:, 1] <= imax]

        spectra = [s for s in spectra if len(s.peaks)]

        return PeakMap(spectra, self.meta.copy())

    def representingMzPeak(self, mzmin, mzmax, rtmin, rtmax):
        """returns a weighted mean m/z value in given range.
           high intensities contribute with weight ln(I+1) to final m/z value
        """
        mzsum = wsum = 0
        for s in self.spectra:
            if rtmin <= s.rt <= rtmax:
                ix = (mzmin <= s.peaks[:, 0]) * (s.peaks[:, 0] <= mzmax)
                weights = np.log(s.peaks[ix, 1] + 1.0)
                wsum += np.sum(weights)
                mzsum += np.sum(s.peaks[ix, 0] * weights)
        if wsum > 0.0:
            return mzsum / wsum
        else:
            return None

    def getDominatingPeakmap(self):
        levels = self.getMsLevels()
        if levels == [1]:
            return self
        ms_level = min(levels)
        spectra = [copy.deepcopy(s) for s in self.spectra if s.msLevel == ms_level]
        for spec in spectra:
            spec.msLevel = 1
        return PeakMap(spectra, meta=self.meta.copy())

    def filter(self, condition):
        """ builds new peakmap where ``condition(s)`` is ``True`` for
            spectra ``s``
        """
        spectra = copy.deepcopy(self.spectra)
        return PeakMap([s for s in spectra if condition(s)], self.meta.copy())

    def specsInRange(self, rtmin, rtmax):
        """
        returns list of spectra with rt values in range ``rtmin...rtmax``
        """
        return [spec for spec in self.spectra if rtmin <= spec.rt <= rtmax]

    def levelNSpecsInRange(self, n, rtmin, rtmax):
        """
        returns lists level one spectra in peakmap
        """
        # rt values can be truncated/rounded from gui or other sources,
        # so wie dither the limits a bit, spaces in realistic rt values
        # are much higher thae 1e-2 seconds
        return [spec for spec in self.spectra if rtmin - 1e-2 <= spec.rt
                <= rtmax + 1e-2
                and spec.msLevel == n]

    def remove(self, mzmin, mzmax, rtmin=None, rtmax=None, msLevel=None):
        if not self.spectra:
            return
        if rtmin is None:
            rtmin = self.spectra[0].rt
        if rtmax is None:
            rtmax = self.spectra[-1].rt
        if msLevel is None:
            msLevel = min(self.getMsLevels())

        for s in self.spectra:
            if s.msLevel != msLevel:
                continue
            if rtmin <= s.rt <= rtmax:
                peaks = s.peaks
                cut_out = (s.peaks[:, 0] >= mzmin) & (s.peaks[:, 0] <= mzmax)
                s.peaks = peaks[~cut_out]

        self.spectra = [s for s in self.spectra if len(s.peaks)]

    def chromatogram(self, mzmin, mzmax, rtmin=None, rtmax=None, msLevel=None):
        """
        extracts chromatogram in given rt- and mz-window.
        returns a tuple ``(rts, intensities)`` where ``rts`` is a list of
        rt values (in seconds, as always)  and ``intensities`` is a
        list of same length containing the summed up peaks for each
        rt value.
        """
        if not self.spectra:
            return [], []
        if rtmin is None:
            rtmin = self.spectra[0].rt
        if rtmax is None:
            rtmax = self.spectra[-1].rt

        if msLevel is None:
            msLevel = min(self.getMsLevels())

        if OPTIMIZATIONS_INSTALLED:
            rts, iis = emzed_optimizations.chromatogram(self, mzmin, mzmax, rtmin, rtmax, msLevel)
            # fix bug in old version of emzed_optimizations:
            # fails if rtmin and rtmax are beyond max rt in peakmap !
            f = (rts >= rtmin) * (rts <= rtmax)
            return rts[f], iis[f]

        specs = self.levelNSpecsInRange(msLevel, rtmin, rtmax)

        rts = [s.rt for s in specs]
        intensities = [s.intensityInRange(mzmin, mzmax) for s in specs]
        return rts, intensities

    def getMsLevels(self):
        """returns list of ms levels in current peak map"""

        return sorted(set(spec.msLevel for spec in self.spectra))

    def msNPeaks(self, n, rtmin=None, rtmax=None):
        """return ms level n peaks in given range"""
        if rtmin is None:
            rtmin = self.spectra[0].rt
        if rtmax is None:
            rtmax = self.spectra[-1].rt
        specs = self.levelNSpecsInRange(n, rtmin, rtmax)
        # following vstack does not like empty sequence, so:
        if len(specs):
            peaks = np.vstack([s.peaks for s in specs])
            perm = np.argsort(peaks[:, 0])
            return peaks[perm, :]
        return np.zeros((0, 2), dtype=float)

    def allRts(self):
        """returns all rt values in peakmap"""
        return [spec.rt for spec in self.spectra]

    def levelOneRts(self):
        """returns rt values of all level one spectra in peakmap"""
        return [spec.rt for spec in self.spectra if spec.msLevel == 1]

    def levelNSpecs(self, minN, maxN=None):
        """returns list of spectra in given msLevel range"""

        if maxN is None:
            maxN = minN
        return [spec for spec in self.spectra if minN <= spec.msLevel <= maxN]

    def shiftRt(self, delta):
        """shifts all rt values by delta"""
        for spec in self.spectra:
            spec.rt += delta
        return self

    def mzRange(self, msLevel=1):
        """returns mz-range *(mzmin, mzmax)* of current peakmap """
        mzranges = [s.mzRange() for s in self.spectra if s.msLevel == msLevel]
        if len(mzranges) == 0:
            return (None, None)
        mzmin = min(mzmin for (mzmin, mzmax) in mzranges if mzmin is not None)
        mzmax = max(mzmax for (mzmin, mzmax) in mzranges if mzmax is not None)
        return (float(mzmin), float(mzmax))

    def rtRange(self):
        """ returns rt-range *(rtmin, tax)* of current peakmap """
        rtmin = min(s.rt for s in self.spectra) if len(self.spectra) else 1e300
        rtmax = max(s.rt for s in self.spectra) if len(self.spectra) else 1e300
        return rtmin, rtmax

    @classmethod
    def fromMSExperiment(clz, mse):
        """creates Spectrum from pyopenms.MSExperiment"""
        assert type(mse) == pyopenms.MSExperiment
        specs = [Spectrum.fromMSSpectrum(mse[i]) for i in range(mse.size())]
        meta = dict()
        meta["full_source"] = mse.getLoadedFilePath()
        meta["source"] = os.path.basename(meta.get("full_source"))
        return clz(specs, meta)

    def uniqueId(self):
        if "unique_id" not in self.meta:
            h = hashlib.sha256()
            for spec in self.spectra:
                h.update(spec.uniqueId())
            self.meta["unique_id"] = h.hexdigest()
        return self.meta["unique_id"]

    def __len__(self):
        """returns number of all spectra (all ms levels) in peakmap"""
        return len(self.spectra)

    def __str__(self):
        """Returns description of  PeakMap object as a string."""
        n = len(self)
        return "<PeakMap %#x with %d %s>" % (id(self), n, "spectrum" if n == 1 else "spectra")

    def toMSExperiment(self):
        """converts peakmap to pyopenms.MSExperiment"""
        exp = pyopenms.MSExperiment()

        if hasattr(exp, "push_back"):
            # pyopenms 1.10
            add_ = exp.push_back
        else:
            # pyopenms 1.11
            add_ = exp.addSpectrum
        for spec in self.spectra:
            add_(spec.toMSSpectrum())

        exp.updateRanges()
        exp.setLoadedFilePath(self.meta.get("source", ""))
        return exp

    def splitLevelN(self, msLevel, significant_digits_precursor=2):
        """splits peakmap to list of tuples. the first entry of a tuple is the precursor mass, the
        second one the corresponding peak map of spectra of level *msLevel*"""
        msn_spectra = defaultdict(list)
        for spectrum in self.spectra:
            if spectrum.msLevel == msLevel:
                spectrum = copy.deepcopy(spectrum)
                key = spectrum.precursors[0][0]
                if significant_digits_precursor is not None:
                    key = round(key, significant_digits_precursor)
                msn_spectra[key].append(spectrum)

        meta = self.meta.copy()
        return sorted([(key, PeakMap(values, meta=meta)) for (key, values) in msn_spectra.items()])
