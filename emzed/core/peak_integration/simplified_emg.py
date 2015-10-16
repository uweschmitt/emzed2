from base_integrator import BaseIntegrator
import numpy as np
import scipy.optimize as opt
import math


class SimplifiedEMGIntegrator(BaseIntegrator):

    def __init__(self, **kw):
        super(SimplifiedEMGIntegrator, self).__init__(kw)
        self.xtol = kw.get("xtol")
        self.fit_baseline = kw.get("fit_baseline")

    def __str__(self):
        info = "default" if self.xtol is None else "%.2e" % self.xtol
        return "SimplifiedEMGIntegrator, xtol=%s" % info

    @staticmethod
    def _fun_eval(param, rts, sqrt_two_pi=math.sqrt(math.pi), sqrt_2=math.sqrt(2.0), exp=np.exp):
        h, z, w, s = param
        # avoid zero division
        if s * s == 0.0:
            s = 1e-6
        inner = w * w / 2.0 / s / s - (rts - z) / s
        # avoid overflow: may happen if _fun_eval is called with full
        # rtrange (getSmoothed...), and s is small:
        inner[inner > 200] = 200
        nominator = np.exp(inner)
        # avoid zero division
        if w == 0:
            w = 1e-6
        denominator = 1 + exp(-2.4055 / sqrt_2 * ((rts - z) / w - w / s))
        return h * w / s * sqrt_two_pi * nominator / denominator

    @staticmethod
    def _fun_eval_baseline(param, rts):
        h, z, w, s, beta = param
        return SimplifiedEMGIntegrator._fun_eval((h, z, w, s), rts) + beta

    @staticmethod
    def _err(param, rts, values):
        return SimplifiedEMGIntegrator._fun_eval(param, rts) - values

    @staticmethod
    def _err_baseline(param, rts, values):
        return SimplifiedEMGIntegrator._fun_eval_baseline(param, rts) - values

    def integrator(self, allrts, fullchromatogram, rts, chromatogram):

        """
             model is simplified EMG
        """

        if len(rts)<4:
            rmse = 1.0/math.sqrt(len(rts))*np.linalg.norm(chromatogram)
            return 0.0, rmse, (0.0, rts[0], 1.0, 0.0)

        imax = np.argmax(chromatogram)
        h = chromatogram[imax] * 2
        z = rts[imax]
        w = 0.2
        s = 0.3
        rts = np.array(rts)

        param = (h, z, w, s)
        err = SimplifiedEMGIntegrator._err
        fun = SimplifiedEMGIntegrator._fun_eval

        # we use usual emg model as start model if fit with baseline is requested.

        if self.xtol is None:
            param, ok = opt.leastsq(err, param, args=(rts, chromatogram), ftol=0.005)
        else:
            param, ok = opt.leastsq(err, param, args=(rts, chromatogram), xtol=self.xtol)

        fitted_baseline = False
        if self.fit_baseline:
            # no we try to fit the model incl. baseline:
            h = param[0]
            param_bl = np.hstack((param, h / 2.0))  # start with max / 2. baseline
            err = SimplifiedEMGIntegrator._err_baseline
            if self.xtol is None:
                param_bl, ok_bl = opt.leastsq(err, param_bl, args=(rts, chromatogram), ftol=0.005)
            else:
                param_bl, ok_bl = opt.leastsq(err, param_bl, args=(rts, chromatogram), xtol=self.xtol)
            beta = param_bl[-1]
            if beta >= 0 and ok_bl:  # success:
                param = param_bl
                ok = ok_bl
                fun = SimplifiedEMGIntegrator._fun_eval_baseline
                fitted_baseline = True

        w = param[1]
        if ok not in [1, 2, 3, 4] or w <= 0:  # failed
            area = 0.0
            rmse = 1.0 / math.sqrt(len(rts)) * np.linalg.norm(chromatogram)
            param = np.zeros_like(param)
        else:
            smoothed = fun(param, allrts)
            fitted = fun(param, rts)
            isnan = np.isnan(smoothed)
            smoothed[isnan] = 0.0
            if fitted_baseline:
                beta = param[-1]
                ix = smoothed > beta
                sm_sel = smoothed[ix]
                rt_sel = allrts[ix]
                if len(rt_sel):
                    area = self.trapez(rt_sel, sm_sel) - (max(rt_sel) - min(rt_sel)) * beta
                else:
                    area = 0.0
            else:
                area = self.trapez(allrts, smoothed)
            rmse = 1 / math.sqrt(len(rts)) * np.linalg.norm(fitted - chromatogram)

        return area, rmse, param

    def getSmoothed(self, rtvalues, params):
        if len(params) == 5:
            fun = SimplifiedEMGIntegrator._fun_eval_baseline
        else:
            fun = SimplifiedEMGIntegrator._fun_eval
        return rtvalues, fun(params, np.array(rtvalues))

    def getBaseline(self, rtvalues, param):
        if len(param) == 5:
            return param[-1]
        return None
