import pyopenms
import numpy as np
import os.path
import copy
from   collections import defaultdict
import warnings

def deprecation(message):
    warnings.warn(message, UserWarning, stacklevel=2)

class Spectrum(object):

    """
        MS Spectrum Type
    """

    def __init__(self, peaks, rt, msLevel, polarity, precursors=None):
        """
           peaks:      n x 2 matrix
                       first column: m/z values
                       second column: intensities

           rt:         float
                       retention time in seconds

           msLevel:    int
                       MSn level.

           polarity:   string of length 1
                       values: 0, + or -

           precursors: list of floats
                       precursor m/z values if msLevel > 1

           """
        assert type(peaks) == np.ndarray, type(peaks)
        assert peaks.ndim == 2, "peaks has wrong dimension"
        assert peaks.shape[1] == 2, "peaks needs 2 columns"

        assert polarity in "0+-", "polarity must be +, - or 0"

        assert msLevel >= 1, "invalid msLevel"

        if precursors is None:
            precursors = []

        # level=1 -> no precursors
        if msLevel == 1:
            assert not precursors, "conflict: level 1 spec has precursors"

        self.rt = rt
        self.msLevel = msLevel
        self.precursors = precursors
        self.polarity = polarity
        peaks = peaks[peaks[:,1]>0] # remove zero intensities
        # sort resp. mz values:
        perm = np.argsort(peaks[:,0])
        self.peaks = peaks[perm,:]

    @classmethod
    def fromMSSpectrum(clz, mspec):
        """creates Spectrum from pyopenms.MSSpectrum"""
        assert type(mspec) == pyopenms.MSSpectrum, type(mspec)
        pcs = [ (p.getMZ(), p.getIntensity()) for p in mspec.getPrecursors()]
        pol = { pyopenms.IonSource.Polarity.POLNULL: '0',
                pyopenms.IonSource.Polarity.POSITIVE: '+',
                pyopenms.IonSource.Polarity.NEGATIVE: '-'
              }.get(mspec.getInstrumentSettings().getPolarity())
        res = clz(mspec.get_peaks(), mspec.getRT(),
                  mspec.getMSLevel(), pol, pcs)
        return res

    def __len__(self):
        """number of peaks in spectrum"""
        return self.peaks.shape[0]


    def __iter__(self):
        return iter(self.peaks)

    def intensityInRange(self, mzmin, mzmax):
        """summed up intensities in given m/z range"""
        return self.peaksInRange(mzmin, mzmax)[:,1].sum()

    def peaksInRange(self, mzmin=None, mzmax=None):
        """peaks in given m/z range as n x 2 matrix

           first column:   m/z values
           second column:  intenisities
        """
        mzs = None
        if mzmin is not None or mzmax is not None:
            mzs = self.peaks[:,0]
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
            return float(self.peaks[:,0].min())
        return None

    def mzMax(self):
        """maximal m/z value in spectrum"""
        if len(self.peaks):
            return float(self.peaks[:,0].max())
        return None

    def maxIntensity(self):
        """maximal intensity in spectrum"""
        return float(self.peak[:,1].max())

    def toMSSpectrum(self):
        """converts to pyopenms.MSSpectrum"""
        spec = pyopenms.MSSpectrum()
        spec.setRT(self.rt)
        spec.setMSLevel(self.msLevel)
        ins = spec.getInstrumentSettings()
        pol = { '0' : pyopenms.IonSource.Polarity.POLNULL,
                '+' : pyopenms.IonSource.Polarity.POSITIVE,
                '-' : pyopenms.IonSource.Polarity.NEGATIVE}[self.polarity]
        ins.setPolarity(pol)
        spec.setInstrumentSettings(ins)
        oms_pcs = []
        for mz, I in self.precursors:
            p = pyopenms.Precursor()
            p.setMZ(mz)
            p.setIntensity(I)
            oms_pcs.append(p)
        spec.setPrecursors(oms_pcs)
        spec.set_peaks(self.peaks)
        return spec

class PeakMap(object):
    """
        This is the container object for spectra of type :ref:Spectrum.
        Peakmaps can be loaded from .mzML, .mxXML or .mzData files,
        using :py:func:`~ms.loadPeakMap`

        A PeakMap is a list of :ref:Spectrum objects attached with
        meta data about its source.
    """


    def __init__(self, spectra, meta=dict()):
        """
            spectra : iterable (list, tuple, ...)  of objects of type
            :py:class:`~.Spectrum`

            meta    : dictionary of meta values
        """
        try:
            self.spectra = sorted(spectra, key = lambda spec : spec.rt)
        except:
            raise Exception("spectra param is not iterable")


        self.meta = meta
        polarities = set(spec.polarity for spec in spectra)
        if len(polarities) > 1:
            print
            print "INCONSISTENT POLARITIES"
            for i, s in enumerate(spectra):
                print "%7.2fm : %s" % (s.rt/60.0, s.polarity),
                if i%5==4:
                    print
            print
        elif len(polarities)==1:
            self.polarity = polarities.pop()
        else:
            self.polarity = None

    def extract(self, rtmin=None, rtmax=None, mzmin=None, mzmax=None,
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
            spectra = [ s for s in spectra if rtmin <= s.rt ]
        if rtmax:
            spectra = [ s for s in spectra if rtmax >= s.rt ]

        if mzmin is not None or mzmax is not None:
            for s in spectra:
                s.peaks = s.peaksInRange(mzmin, mzmax)

        return PeakMap(spectra, self.meta.copy())

    def representingMzPeak(self, mzmin, mzmax, rtmin, rtmax):
        """returns a weighted mean m/z value in given range.
           high intensities contribute with weight ln(I+1) to final m/z value
        """
        mzsum = wsum = 0
        for s in self.spectra:
            if rtmin <= s.rt <= rtmax:
                ix = (mzmin <= s.peaks[:,0]) * (s.peaks[:,0] <= mzmax)
                weights = np.log(s.peaks[ix,1] + 1.0)
                wsum += np.sum(weights)
                mzsum += np.sum(s.peaks[ix,0]*weights)
        if wsum > 0.0:
            return mzsum / wsum
        else:
            return None

    def getDominatingPeakmap(self):
        levels = self.getMsLevels()
        if len(levels) > 1 or 1 in levels:
            return self
        spectra = copy.copy(self.spectra)
        for spec in spectra:
            spec.msLevel = 1
        return PeakMap(spectra, meta=self.meta.copy())

    def filter(self, condition):
        """ builds new peakmap where ``condition(s)`` is ``True`` for
            spectra ``s``
        """
        return PeakMap([s for s in self.spectra if condition(s)], self.meta)

    def specsInRange(self, rtmin, rtmax):
        """
        returns list of spectra with rt values in range ``rtmin...rtmax``
        """
        return [spec for spec in self.spectra if rtmin <= spec.rt <= rtmax]

    def levelOneSpecsInRange(self, rtmin, rtmax):
        """
        returns lists level one spectra in peakmap
        """
        deprecation("WARNING: method is levelOneSpecsInRange is depreciated, "\
              "please use PeakMap.levelNSpecsInRange instead")
        return self.levelNSpecsInRange(1, rtmin, rtmax)

    def levelNSpecsInRange(self, n, rtmin, rtmax):
        """
        returns lists level one spectra in peakmap
        """
        # rt values can be truncated/rounded from gui or other sources,
        # so wie dither the limits a bit, spaces in realistic rt values
        # are much higher thae 1e-2 seconds
        return [spec for spec in self.spectra if rtmin-1e-2 <= spec.rt \
                                                            <= rtmax+1e-2
                                             and spec.msLevel == n]

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

        specs = self.levelNSpecsInRange(msLevel, rtmin, rtmax)

        rts = [s.rt for s in specs]
        intensities = [s.intensityInRange(mzmin, mzmax) for s in specs]
        return rts, intensities

    def getMsLevels(self):
        """returns list of ms levels in current peak map"""

        return sorted(set(spec.msLevel for spec in self.spectra))

    def ms1Peaks(self, rtmin=None, rtmax=None):
        deprecation("WARNING: ms1Peaks method is depreciated, please use "\
              "PeakMap.msNPeaks instead")
        return self.msNPeaks(1, rtmin, rtmax)

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
            perm = np.argsort(peaks[:,0])
            return peaks[perm,:]
        return np.zeros((0,2), dtype=float)

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

    def mzRange(self):
        """returns mz-range *(mzmin, mzmax)* of current peakmap """

        mzranges = [s.mzRange() for s in self.spectra]
        mzmin = min(mzmin for (mzmin, mzmax) in mzranges if mzmin is not None)
        mzmax = max(mzmax for (mzmin, mzmax) in mzranges if mzmax is not None)
        return float(mzmin), float(mzmax)

    def rtRange(self):
        """ returns rt-range *(rtmin, tax)* of current peakmap """
        rtmin = min(s.rt for s in self.spectra) if len(self.spectra) else 1e300
        rtmax = max(s.rt for s in self.spectra) if len(self.spectra) else 1e300
        return rtmin, rtmax

    @classmethod
    def fromMSExperiment(clz, mse):
        """creates Spectrum from pyopenms.MSExperiment"""
        assert type(mse) == pyopenms.MSExperiment
        specs = [ Spectrum.fromMSSpectrum(mse[i]) for i in range(mse.size()) ]
        meta = dict()
        meta["full_source"] = mse.getLoadedFilePath()
        meta["source"] = os.path.basename(meta.get("full_source"))
        return clz(specs, meta)

    def __len__(self):
        """returns number of all spectra (all ms levels) in peakmap"""
        return len(self.spectra)

    def toMSExperiment(self):
        """converts peakmap to pyopenms.MSExperiment"""
        exp = pyopenms.MSExperiment()
        for spec in self.spectra:
            exp.push_back(spec.toMSSpectrum())
        exp.updateRanges()
        exp.setLoadedFilePath(self.meta.get("source",""))
        return exp

    def splitLevelN(self, msLevel, significant_digits_precursor=2):
        """splits peakmapt to dictionary of lists of spectra.
           key of dictionary is precursor m/z rounded to
           significant_digits_precursor
        """
        ms2_spectra = defaultdict(list)
        for spectrum in self.spectra:
            if spectrum.msLevel==msLevel:
                spectrum = copy.copy(spectrum)
                key = round(spectrum.precursors[0][0],
                            significant_digits_precursor)
                ms2_spectra[key].append(spectrum)

        return [(key, PeakMap(values, meta=self.meta.copy())) \
                        for (key, values) in ms2_spectra.items()]
