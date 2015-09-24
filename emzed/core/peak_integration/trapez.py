from base_integrator import BaseIntegrator
import numpy as np


class TrapezIntegrator(BaseIntegrator):

    def __str__(self):
        return "TrapezIntegrator()"

    def integrator(self, allrts, fullchromatogram, rts, chromatogram):

        if len(rts) == 2:
            area = 0.5 * (chromatogram[0] + chromatogram[1]) * (rts[1] - rts[0])
            return area, 0.0, (rts, chromatogram)

        if len(rts) == 1:
            return 0.0, 0.0, (rts, chromatogram)

        area = self.trapez(rts, chromatogram)
        return area, 0.0, (rts, chromatogram)

    def getSmoothed(self, rtvalues, params):
        return params


class TrapezIntegratorWithBaseline(BaseIntegrator):

    def __str__(self):
        return "TrapezIntegratorWithBaseline()"

    def integrator(self, allrts, fullchromatogram, rts, chromatogram):

        baseline = min(chromatogram)
        basearea = baseline * (max(rts) - min(rts))

        if len(rts) == 2:
            area = 0.5 * (chromatogram[0] + chromatogram[1]) * (rts[1] - rts[0]) - basearea
            return area, 0.0, (rts, chromatogram, baseline)

        if len(rts) == 1:
            return 0.0, 0.0, (rts, chromatogram, baseline)

        area = self.trapez(rts, chromatogram) - basearea
        return area, 0.0, (rts, chromatogram, baseline)

    def getSmoothed(self, rtvalues, params):
        return params[:2]

    def getBaseline(self, rtvalues, params):
        return params[-1]

