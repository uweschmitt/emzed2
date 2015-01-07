import numpy as np


class BaseIntegrator(object):

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
            return dict(area=0.0, rmse=0.0, params=None)

        allrts, fullchrom = self.peakMap.chromatogram(mzmin, mzmax, None, None, msLevel)

        area, rmse, params = self.integrator(allrts, fullchrom, rts, chromatogram)

        return dict(area=area, rmse=rmse, params=params)

    def getSmoothed(self, *a):
        if hasattr(self, "_getSmoothed"):
            try:
                return self._getSmoothed(*a)
            except:
                # maybe overflow or something similar
                return None

        raise Exception("not implemented")

    def trapez(self, x, y):
        assert len(x)==len(y), "x, y have different length"

        x = np.array(x)
        y = np.array(y)

        dx = x[1:] - x[:-1]
        sy = 0.5*(y[1:] + y[:-1])
        return np.dot(dx, sy)


if __name__ == "__main__":

        pi = PeakIntegrator(None)
        x = [1,2,5,6,9]
        y = [1,2,1,4,-7]

        pi.trapez(x,y)
