from base_integrator import BaseIntegrator
import numpy as np
import scipy.optimize as opt
import math

class AsymmetricGaussIntegrator(BaseIntegrator):

    def __init__(self, **kw):
        super(AsymmetricGaussIntegrator, self).__init__(kw)
        self.gtol = kw.get("gtol")

    def __str__(self):
        info = "default" if self.gtol is None else "%.2e" % self.gtol
        return "AsymmetricGaussIntegrator, gtol=%s" %  info

    @staticmethod
    def __fun_eval(param, rts):
        A, s1, s2, mu = param
        isleft = rts < mu
        svec = s2 + isleft * (s1-s2)
        rv = np.exp(-(rts-mu)**2 / svec )
        return A*rv

    @staticmethod
    def __err(param, rts, values):
        return AsymmetricGaussIntegrator.__fun_eval(param, rts) - values

    def integrator(self, allrts, fullchromatogram, rts, chromatogram):

        """ model is to fit  A * exp ( (x-mu)**2 / s(x) ), where

            s(x) = s1 if x < mu else s2

        """

        # estimate rt of max peak as first moment:
        mu = sum( ci*ri for (ci,ri) in zip(chromatogram, rts))
        mu /= sum( ci for ci in chromatogram)

        area1 = sum(ci for (ci,ri) in zip(chromatogram, rts) if ri<=mu)
        area2 = sum(ci for (ci,ri) in zip(chromatogram, rts) if ri>=mu)
        # fit impossible: eithor less than three peaks or no area left
        # or no area right to estimated max peak:
        if len(rts)<4 or area1 == 0 or area2 == 0:
            rmse = 1.0/math.sqrt(len(rts))*np.linalg.norm(chromatogram)
            return 0.0, rmse, (0.0, 1.0, 1.0, 0.0)

        imax = np.argmax(chromatogram)
        A = chromatogram[imax]

        # normalize second moment as a guess for sigma 1 (left side)
        var1 = sum( ci * (ri-mu)**2 for (ci,ri) in zip(chromatogram, rts) if ri<=mu)
        var1 /= area1

        # normalize second moment as a guess for sigma 2 (right side)
        var2 = sum( ci * (ri-mu)**2 for (ci,ri) in zip(chromatogram, rts) if ri>=mu)
        var2 /= area2
        s1 = var1 if var1>0.5 else 0.5
        s2 = var2 if var2>0.5 else 0.5
        if self.gtol is None:
            (A, s1, s2, mu), ok = opt.leastsq(AsymmetricGaussIntegrator.__err,
                                              (A, s1, s2, mu),
                                              maxfev = 0,
                                              args=(rts, chromatogram))
        else:
            (A, s1, s2, mu), ok = opt.leastsq(AsymmetricGaussIntegrator.__err,
                                              (A, s1, s2, mu),
                                              gtol = self.gtol,
                                              args=(rts, chromatogram))

        if ok not in [1,2,3,4, 5] or s1<0 or s2<0 : # failed
            area = np.nan
            rmse = np.nan
        else:
            smoothed = AsymmetricGaussIntegrator.__fun_eval( (A, s1, s2, mu), allrts)
            area = self.trapez(allrts, smoothed)
            rmse = 1/math.sqrt(len(allrts)) * np.linalg.norm(smoothed - fullchromatogram)

        return area, rmse, (A, s1, s2, mu)

    def getSmoothed(self, rtvalues, params):
        return rtvalues, AsymmetricGaussIntegrator.__fun_eval(params, np.array(rtvalues))
