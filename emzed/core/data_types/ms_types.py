import pyopenms
import numpy as np
import os.path
import sys
import time
import copy
import hashlib
from collections import defaultdict
import warnings
import weakref
import zlib

from emzed_optimizations.sample import sample_peaks

OPTIMIZATIONS_INSTALLED = False
try:
    import emzed_optimizations
    OPTIMIZATIONS_INSTALLED = True
except ImportError:
    pass

IS_PYOPENMS_2 = pyopenms.__version__.startswith("2.")


def deprecation(message):
    warnings.warn(message, UserWarning, stacklevel=2)


class NDArrayProxy(np.ndarray):

    """works like a regular array but calls a call back function (if provided) in case of
    writing. Used in Spectrum class so that cached uniqued id can be invalidated.

    for details how this class is implemented see
    http://docs.scipy.org/doc/numpy-1.9.2/user/basics.subclassing.html
    """

    def __new__(cls, input_array):
        obj = np.asarray(input_array).view(cls)
        return obj

    def patch_modification_callback(self, callback):
        self._modification_callback = callback

    def __array_finalize__(self, obj):
        if obj is None:
            return
        self._modification_callback = getattr(obj, '_modification_callback', None)

    def wrap(special_method_name):
        def inner(self, *a, **kw):
            if self._modification_callback is not None:
                self._modification_callback()
            return getattr(np.ndarray, special_method_name)(self, *a, **kw)
        return inner

    __setitem__ = wrap("__setitem__")
    __iadd__ = wrap("__iadd__")
    __iand__ = wrap("__iand__")
    __idiv__ = wrap("__idiv__")
    __ifloordiv__ = wrap("__ifloordiv__")
    __itruediv__ = wrap("__itruediv__")
    __ilshift__ = wrap("__ilshift__")
    __imod__ = wrap("__imod__")
    __imul__ = wrap("__imul__")
    __ior__ = wrap("__ior__")
    __ipow__ = wrap("__ipow__")
    __irshift__ = wrap("__irshift__")
    __isub__ = wrap("__isub__")
    __itruediv__ = wrap("__itruediv__")
    __ixor__ = wrap("__ixor__")


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

        assert isinstance(peaks, (np.ndarray, NDArrayProxy))
        assert peaks.ndim == 2, "peaks has wrong dimension"
        assert peaks.shape[1] == 2, "peaks needs 2 columns"

        assert peaks.dtype in (np.float64,)

        assert polarity in "0+-", "polarity must be +, - or 0"

        assert msLevel >= 1, "invalid msLevel"

        if precursors is None:
            precursors = []

        if meta is None:
            meta = dict()

        peaks = peaks[peaks[:, 1] > 0]  # remove zero intensities
        # sort resp. mz values:
        perm = np.argsort(peaks[:, 0])

        self._setup_peaks(peaks[perm, :])

        self._rt = rt
        self._msLevel = msLevel
        self._polarity = polarity
        self._precursors = precursors

        self.meta = meta
        self._parent = None

    def _setup_peaks(self, peaks):
        self.peaks = NDArrayProxy(peaks)
        self.peaks.patch_modification_callback(self._invalidate_unique_id)

    def _invalidate_unique_id(self):
        if "unique_id" in self.meta:
            del self.meta["unique_id"]
            if self._parent is not None:
                parent = self._parent()
                if parent is not None and "unique_id" in parent.meta:
                    del parent.meta["unique_id"]

    def register_parent(self, parent):
        self._parent = weakref.ref(parent)

    def _create_prop(name):
        lname = "_" + name

        def getter(self):
            return getattr(self, lname)

        def setter(self, value):
            if "unique_id" in self.meta:
                del self.meta["unique_id"]
                if self._parent is not None:
                    parent = self._parent()
                    if parent is not None and "unique_id" in parent.meta:
                        del parent.meta["unique_id"]
            setattr(self, lname, value)
        return property(getter, setter)

    rt = _create_prop("rt")
    msLevel = _create_prop("msLevel")
    polarity = _create_prop("polarity")
    precursors = _create_prop("precursors")

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
            h.update(str(self.peaks.tostring()))
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
            peaks = np.vstack((mzs.flatten(), iis.flatten())).T.astype(np.float64)
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
        return float(self.peaks[:, 1].max())

    @staticmethod
    def compute_alignments(spectra, mz_tolerance):
        """takes a list of spectra and groups peaks given mz_tolerance.
        it returns a list of lists. every inner list specifies the alignment of one input
        spectrum to its follower in the list.
        One assignment is a list of tuples, where the first entry is a peak index from the first
        list, the second entry is the index of a peak from the second spectrum.

        For example:

            if you run this method with a list or tuple of three spectra (s0, s1, s2) the return
            values will be [align_0_to_1, align_1_to_2]

            an alignment is a list [(i0, j0), (i1, j1),  ...]

            so that s0.peaks[i0, :] is assigned to s1.peaks[j0, :] and so on.
        """
        aligner = pyopenms.SpectrumAlignment()
        alignment = []
        conf = aligner.getDefaults()
        conf_d = conf.asDict()
        conf_d["is_relative_tolerance"] = "false"  # "true" not implemented yet !
        conf_d["tolerance"] = mz_tolerance
        conf.update(conf_d)
        aligner.setParameters(conf)

        openms_spectra = [s.toMSSpectrum() for s in spectra]

        # create pairwise alignments
        alignments = []
        for s0, s1 in zip(openms_spectra, openms_spectra[1:]):
            alignment = []
            aligner.getSpectrumAlignment(alignment, s0, s1)
            alignments.append(alignment)

        return alignments

    def compute_alignment(self, other, mz_tolerance):
        assert isinstance(other, Spectrum), "need spectrum as argument"

        aligner = pyopenms.SpectrumAlignment()
        alignment = []
        conf = aligner.getDefaults()
        conf_d = conf.asDict()
        conf_d["is_relative_tolerance"] = "false"  # "true" not implemented yet !
        conf_d["tolerance"] = mz_tolerance
        conf.update(conf_d)
        aligner.setParameters(conf)

        s0 = self.toMSSpectrum()
        s1 = other.toMSSpectrum()

        alignment = []
        aligner.getSpectrumAlignment(alignment, s0, s1)
        return alignment

    def cosine_distance(self, other, mz_tolerance, top_n=10, min_matches=10,
                        consider_precursor_shift=False):
        """computes the cosine distance of *self* and *other*.

        *top_n* is the number of most intense peaks which should be used for alignment.
        *min_matches*: if there are less than *min_matches* matches the cosine distance will be 0.0

        *weight_for_precursor_shift*: for ms2 spectra the parameter *weight_for_precursor_shift*
        stirs advanced matching. in this mode the mz values of the peaks of *other* are shifted
        by the precursor difference of *self* and *other* and an additional cosine distance is
        computed. the final result is a weighted sum of "cosine_ms_level_0" and
        "cosine_ms_level_1", where the weight 0.0 only considers the match on ms1 level, a value
        of 1.0 only considers match on ms2 level and 0.5 computes an average of the cosine
        distances on both levels.
        """

        assert isinstance(other, Spectrum), "need spectrum as argument"

        if not consider_precursor_shift:
            al = self.compute_alignment(other, mz_tolerance)
            if len(al) >= min_matches:
                peaks_self = sorted([self.peaks[i, 1] for (i, j) in al])[:top_n]
                # fill up with zeros
                peaks_self += [0.0] * (top_n - len(peaks_self))
                peaks_self = np.array(peaks_self, dtype=np.float64)
                peaks_self /= np.linalg.norm(peaks_self)

                peaks_other = sorted([other.peaks[j, 1] for (i, j) in al])[:top_n]
                # fill up with zeros
                peaks_other += [0.0] * (top_n - len(peaks_other))
                peaks_other = np.array(peaks_other, dtype=np.float64)
                peaks_other /= np.linalg.norm(peaks_other)

                cos_dist = np.dot(peaks_self, peaks_other)
                return cos_dist
        else:
            assert len(self.precursors) > 0, "no precursor given"
            assert len(other.precursors) > 0, "no precursor given"

            mz_pc_self = self.precursors[0][0]
            mz_pc_other = other.precursors[0][0]
            shift = mz_pc_other - mz_pc_self
            peaks_shifted = np.vstack((other.peaks[:, 0] - shift, other.peaks[:, 1])).T
            other_shifted = Spectrum(peaks_shifted, other.rt, other.msLevel, other.polarity)

            al = self.compute_alignment(other_shifted, mz_tolerance)
            if len(al) >= min_matches:

                peaks_self = sorted([self.peaks[i, 1] for (i, j) in al])[:top_n]
                # fill up with zeros
                peaks_self += [0.0] * (top_n - len(peaks_self))
                peaks_self = np.array(peaks_self, dtype=np.float64)
                peaks_self /= np.linalg.norm(peaks_self)

                peaks_other = sorted([other.peaks[j, 1] for (i, j) in al])[:top_n]
                # fill up with zeros
                peaks_other += [0.0] * (top_n - len(peaks_other))
                peaks_other = np.array(peaks_other, dtype=np.float64)
                peaks_other /= np.linalg.norm(peaks_other)

                cos_dist_shifted = np.dot(peaks_self, peaks_other)
                return cos_dist_shifted

        return 0.0

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

    @staticmethod
    def _fix_for_unpickling_older_files(state):
        for attribute_name in ("rt", "msLevel", "polarity", "precursors"):
            if attribute_name in state:
                state["_%s" % attribute_name] = state.pop(attribute_name)
        if "meta" not in state:
            state["meta"] = {}
        state["peaks"] = NDArrayProxy(state["peaks"].astype(np.float64))
        return state

    def __getstate__(self):
        return (self.meta, self.rt, self.msLevel, self.polarity, self.precursors,
                np.asarray(self.peaks))

    def __setstate__(self, state):
        if isinstance(state, dict):
            state = self._fix_for_unpickling_older_files(state)
            self.__dict__.update(state)
            self._setup_peaks(self.peaks)
        else:
            self._parent = None
            self.meta = state[0]
            # here we have properties which access self.meta, this why we first set
            # selt.meta (no property) and then the following properties:
            self.rt, self.msLevel, self.polarity, self.precursors, peaks = state[1:]
            self.meta = state[0]
            self._setup_peaks(peaks)


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
        self.spectra = sorted(spectra, key=lambda spec: spec.rt)

        if meta is None:
            meta = dict()
        self.meta = meta

        # accepting the unique id from another peakmap is dangerous, eg if we uwe
        # the extract method, so we delete the cached value:
        self.meta.pop("unique_id", None)

        polarities = set(spec.polarity for spec in self.spectra)
        if len(polarities) > 1:
            self.polarity = list(polarities)
        elif len(polarities) == 1:
            self.polarity = polarities.pop()
        else:
            self.polarity = None

    @property
    def spectra(self):
        return self._spectra

    @spectra.setter
    def spectra(self, spectra):
        self._spectra = tuple(spectra)
        for s in self._spectra:
            s.register_parent(self)

    @staticmethod
    def _fix_for_unpickling_older_files(state):
        if "spectra" in state:
            state["_spectra"] = tuple(state.pop("spectra"))
        return state

    def __setstate__(self, state):
        state = self._fix_for_unpickling_older_files(state)
        self.__dict__.update(state)
        for s in self._spectra:
            s.register_parent(self)

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
            spectra = (s for s in spectra if s.msLevel >= mslevelmin)
        if mslevelmax is not None:
            spectra = (s for s in spectra if s.msLevel <= mslevelmax)

        if rtmin:
            spectra = (s for s in spectra if rtmin <= s.rt)
        if rtmax:
            spectra = (s for s in spectra if rtmax >= s.rt)

        spectra = list(spectra)
        if mzmin is not None or mzmax is not None:
            for s in spectra:
                s.peaks = s.peaksInRange(mzmin, mzmax)

        if imin is not None or imax is not None:
            for s in spectra:
                if imin is not None:
                    s.peaks = s.peaks[s.peaks[:, 1] >= imin]
                if imax is not None:
                    s.peaks = s.peaks[s.peaks[:, 1] <= imax]

        spectra = (s for s in spectra if len(s.peaks))

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
            return float(mzsum / wsum)
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
        return PeakMap((s for s in spectra if condition(s)), self.meta.copy())

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

        self.spectra = tuple(s for s in self.spectra if len(s.peaks))

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
        return np.zeros((0, 2), dtype=np.float64)

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

        m = self.meta.copy()
        if "unique_id" in m:
            del m["unique_id"]

        return sorted([(k, PeakMap(v, meta=m.copy())) for (k, v) in msn_spectra.items()])

    @staticmethod
    def load(path):
        # open-ms returns empty peakmap if file not exists, so we
        # check ourselves:
        if not os.path.exists(path):
            raise Exception("file %s does not exist" % path)
        if not os.path.isfile(path):
            raise Exception("path %s is not a file" % path)

        experiment = pyopenms.MSExperiment()
        fh = pyopenms.FileHandler()
        if sys.platform == "win32":
            path = path.replace("/", "\\")  # needed for network shares
        fh.loadExperiment(path, experiment)
        return PeakMap.fromMSExperiment(experiment)

    def store(self, path):
        if sys.platform == "win32":
            path = path.replace("/", "\\")  # needed for network shares

        experiment = self.toMSExperiment()
        fh = pyopenms.FileHandler()
        fh.storeExperiment(path, experiment)

    def dump_as_pickle(self, fp_or_path):
        import dill
        if isinstance(fp_or_path, basestring):
            if sys.platform == "win32":
                fp_or_path = fp_or_path.replace("/", "\\")  # needed for network shares

            # atomic write:
            folder = os.path.dirname(fp_or_path)
            if not os.path.exists(folder):
                os.makedirs(folder)
            with open(fp_or_path + ".incomplete", "wb") as fp:
                fp.write(zlib.compress(dill.dumps(self), 9))
                fp.flush()
                os.fsync(fp.fileno())
            if os.path.exists(fp_or_path):
                os.remove(fp_or_path)
            for attempt in range(10):
                try:
                    os.rename(fp_or_path + ".incomplete", fp_or_path)
                    break
                except EnvironmentError:
                    time.sleep(.1)
            return
        dill.dump(self, fp_or_path)

    @staticmethod
    def load_as_pickle(path):
        import dill
        if not isinstance(path, basestring):
            raise ValueError("load_as_pickle needs path as argument, you provided %r" % path)
        if sys.platform == "win32":
            path = path.replace("/", "\\")  # needed for network shares
        try:
            fp = open(path, "rb")
        except IOError:
            raise IOError("failed to open %s for reading" % path)
        try:
            data = fp.read()
            try:
                uncompressed = zlib.decompress(data)
            except zlib.error:
                raise IOError("compressed data in %s is invalid, file might be corrupted" % path)
            try:
                pm = dill.loads(uncompressed)
            except Exception:
                raise IOError("unpickling of data %s failed, file might be corrupted" % path)
            return pm
        finally:
            fp.close()

    def squeeze(self):
        """only supported for peakmap proxies to save space if possible"""
        pass

    def cleaned(self):
        """ removes empty spectra """
        spectra = [s for s in self.spectra if len(s.peaks) > 0]
        meta = self.meta.copy()
        if "unique_id" in meta:
            del meta["unique_id"]
        return PeakMap(spectra, meta=meta)

    def sample_peaks(self, rtmin, rtmax, mzmin, mzmax, n_bins, ms_level):
        """
        creates binned spectrum from given range. returns matrix with two columns,
        the first column corresponds to the mz bins and the second to the max intensity per bin.
        is used for plotting spectra on different zoom levels
        """
        assert n_bins > 0
        assert ms_level > 0
        if rtmin >= rtmax or mzmin >= mzmax:
            return np.zeros((n_bins, 2), dtype=np.float64)
        peaks = sample_peaks(self, rtmin, rtmax, mzmin, mzmax, n_bins, ms_level)
        return peaks

    def get_rts(self, msLevel=1):
        return [s.rt for s in self.spectra if s.msLevel == msLevel]


class PeakMapProxy(PeakMap):

    def __init__(self, path, meta=None):
        self._path = path
        self._loaded = False
        self.meta = meta if meta is not None else {}

    def uniqueId(self):
        if "unique_id" in self.meta:
            return self.meta["unique_id"]
        return super(PeakMapProxy, self).uniqueId()

    def __getattr__(self, name):
        if name == "_spectra" and not self._loaded:
            ext = os.path.splitext(self._path)[1].upper()
            if ext in (".MZML", ".MZXML", ".MZDATA"):
                pm = PeakMap.load(self._path)
            else:
                pm = PeakMap.load_as_pickle(self._path)
            self.__dict__.update(vars(pm))
            self._loaded = True
            return self.spectra
        elif name == "meta":
            self.meta = {}
            return self.meta
        raise AttributeError("unknown attribute %s" % name)

    def __getstate__(self):
        return (self._path, self.meta)

    def __setstate__(self, dd):
        self._path, self.meta = dd
        self._loaded = False

    def squeeze(self):
        self._loaded = False
        if "_spectra" in self.__dict__:  # use of 'hasattr' would trigger 'getattr' and load data !
            del self._spectra

    def store(self, path):
        """overrides path from PeakMap class because this method would trigger loading the
        peakmap, altough it is already on disk"""
        if not os.path.exists(path):
            self.dump_as_pickle(path)
