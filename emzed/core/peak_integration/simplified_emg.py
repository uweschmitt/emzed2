from base_integrator import BaseIntegrator
import numpy as np
import scipy.optimize as opt
import math

class SimplifiedEMGIntegrator(BaseIntegrator):

    def __init__(self, **kw):
        super(SimplifiedEMGIntegrator, self).__init__(kw)
        self.xtol = kw.get("xtol")

    def __str__(self):
        info = "default" if self.xtol is None else "%.2e" % self.xtol
        return "SimplifiedEMGIntegrator, xtol=%s" %  info

    @staticmethod
    def __fun_eval(param, rts, sqrt_two_pi=math.sqrt(math.pi), sqrt_2=math.sqrt(2.0), exp=np.exp):
        h, z, w, s = param
        # avoid zero division
        if s*s==0.0: s=1e-6
        inner = w*w/2.0/s/s - (rts-z)/s
        # avoid overflow: may happen if __fun_eval is called with full
        # rtrange (getSmoothed...), and s is small:
        inner[inner>200] = 200
        nominator = np.exp(inner)
        # avoid zero division
        if w==0:
            w=1e-6
        denominator = 1 + exp(-2.4055/sqrt_2 * ((rts-z)/w - w/s))
        return h*w/s * sqrt_two_pi * nominator / denominator

    @staticmethod
    def __err(param, rts, values):
        return SimplifiedEMGIntegrator.__fun_eval(param, rts) - values

    def integrator(self, allrts, fullchromatogram, rts, chromatogram):

        """
             model is simplified EMG
        """

        if len(rts)<4:
            rmse = 1.0/math.sqrt(len(rts))*np.linalg.norm(chromatogram)
            return 0.0, rmse, (0.0, rts[0], 1.0, 0.0)

        imax = np.argmax(chromatogram)
        h = chromatogram[imax]
        z = rts[imax]
        w = s = 5.0
        rts = np.array(rts)

        param = (h, z, w, s)
        if self.xtol is None:
            param, ok = opt.leastsq(SimplifiedEMGIntegrator.__err, param, args=(rts, chromatogram),
                                    ftol=0.005)
        else:
            param, ok = opt.leastsq(SimplifiedEMGIntegrator.__err, param, args=(rts, chromatogram),
                                    xtol=self.xtol)
        h, z, w, s = param

        if ok not in [1,2,3,4] or w<=0: # failed
            area = 0.0
            rmse = 1.0/math.sqrt(len(rts))*np.linalg.norm(chromatogram)
            param = np.array((0., 0., 0., 0.)) # these params generate area=0
        else:
            smoothed = SimplifiedEMGIntegrator.__fun_eval(param, allrts)
            isnan = np.isnan(smoothed)
            if np.any(isnan):
                print isnan
            smoothed[isnan]=0.0
            area = self.trapez(allrts, smoothed)
            rmse = 1/math.sqrt(len(allrts)) * np.linalg.norm(smoothed - fullchromatogram)

        return area, rmse, param

    def getSmoothed(self, rtvalues, params):
        return rtvalues, SimplifiedEMGIntegrator.__fun_eval(params, np.array(rtvalues))
