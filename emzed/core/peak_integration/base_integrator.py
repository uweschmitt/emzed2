import numpy as np
import abc


class BaseIntegrator(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, config=None):
        self.config = config
        self.peakMap = None

    def setPeakMap(self, peakMap):
        self.peakMap = peakMap

    def integrate(self, mzmin, mzmax, rtmin, rtmax, msLevel=None):

        assert self.peakMap is not None, "call setPeakMap() before integrate()"

        if msLevel is None:
            msLevels = self.peakMap.getMsLevels()
            if len(msLevels) > 1:
                raise Exception("multiple ms levels, you must specify the level")
            msLevel = msLevels[0]

        spectra = [s for s in self.peakMap.spectra if s.msLevel == msLevel]
        self.allrts = sorted([spec.rt for spec in spectra])

        rts, chromatogram = self.peakMap.chromatogram(mzmin, mzmax, rtmin, rtmax, msLevel)
        if len(rts) == 0:
            return dict(area=0.0, rmse=0.0, params=None, eic=None, baseline=None)

        eic = self.peakMap.chromatogram(mzmin, mzmax)
        allrts, fullchrom = eic

        area, rmse, params = self.integrator(allrts, fullchrom, rts, chromatogram)
        baseline = self.getBaseline(rts, params)

        eic = [], []

        return dict(area=area, rmse=rmse, params=params, eic=eic, baseline=baseline)

    @abc.abstractmethod
    def integrator(self, allrts, fullchrom, rts, chrom):
        pass

    @abc.abstractmethod
    def getSmoothed(self, *a):
        pass

    def getBaseline(self, rtvalues, params):
        pass

    def trapez(self, x, y):
        """ needed by some sub classes """
        area = 0.5 * (np.dot(y[:-1], x[1:]) - np.dot(y[1:], x[:-1]) + x[-1] * y[-1] - x[0] * y[0])
        return area
