from base_integrator import BaseIntegrator
import scipy.interpolate
import numpy as np

class SmoothedIntegrator(BaseIntegrator):


    def integrator(self, allrts, fullchromatogram, rts, chromatogram):

        usedrts, smoothed = self.smooth(allrts, rts, chromatogram)
        assert len(usedrts)==len(smoothed)

        area = self.trapez(usedrts, smoothed)

        # maybe the smoothed() call introduces rts not in self.allrts
        # so we interpolate the input to the usedrts in order to
        # get an estimation about the quality of the smoothing
        cinterpolator = scipy.interpolate.interp1d(allrts, fullchromatogram)
        newc = cinterpolator(usedrts)
        rmse = np.sqrt( np.sum( (newc-smoothed)**2) / len(smoothed))

        return area, rmse, (usedrts, smoothed)

    def getSmoothed(self, rtvalues, params):
        return params


class SGIntegrator(SmoothedIntegrator):

    def __init__(self, **kw):

        super(SGIntegrator, self).__init__(kw)

        order = kw.get("order")
        window_size = kw.get("window_size")

        if order is None or window_size is None:
            raise Exception("need arguments order and window_size")

        self.weights = self._savitzky_golay_coeff(window_size, order)

    def __str__(self):
        return "SGIntegrator (window_size=%(window_size)d, order=%(order)d)" % self.config

    def _savitzky_golay_coeff(self, window_size, order, deriv=0):
        """ from http://www.scipy.org/Cookbook/SavitzkyGolay """

        if window_size % 2 != 1 or window_size < 1:
            raise TypeError("window_size size must be a positive odd number")
        if window_size < order + 2:
            raise TypeError("window_size is too small for the polynomials order")
        order_range = range(order+1)
        half_window = (window_size -1) // 2
        # precompute coefficients
        b = np.mat([[k**i for i in order_range] for k in range(-half_window, half_window+1)])
        m = np.linalg.pinv(b).A[deriv]
        # pad the signal at the extremes with
        # values taken from the signal itself
        return m

    def _savitzky_golay_smooth(self, y, w):
        """ from http://www.scipy.org/Cookbook/SavitzkyGolay """

        half_window = len(w)/2
        firstvals = y[0] - np.abs( y[1:half_window+1][::-1] - y[0] )
        lastvals = y[-1] + np.abs(y[-half_window-1:-1][::-1] - y[-1])
        y = np.concatenate((firstvals, y, lastvals))
        return np.convolve( w, y, mode='valid')

    def smooth(self, allrts, rts, chromatogram):
        smoothed = self._savitzky_golay_smooth(chromatogram, self.weights)
        smoothed[smoothed<0]= 0  # clip negative values, result from some spikes
        missing = len(rts) - len(smoothed)
        if missing >0 : # pad zeros for very short eics
            smoothed = np.hstack( [ np.zeros( ( missing/2, )), smoothed,\
                                    np.zeros( (  missing - missing/2, )) ] )
        if missing <0 : # pad zeros for very short eics
            missing = - missing
            rts = np.hstack([rts[0]*np.ones( ( missing/2, )), rts,\
                             rts[-1]*np.ones( (  missing - missing/2, ))])
        return rts, smoothed
