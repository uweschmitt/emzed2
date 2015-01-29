import base_integrator

class MaxIntegrator(base_integrator.BaseIntegrator):

    def __str__(self):
        return "MaxIntegrator()"

    def integrator(self, allrts, fullchromatogram, rts, chromatogram):
        if len(rts) == 0:
            return None, None, (rts, chromatogram)
        return max(chromatogram), 0.0, (rts, chromatogram)

    def getSmoothed(self, *a, **kw):
        return [], []
