# encoding: utf-8
from __future__ import print_function, division, absolute_import

from . import base_integrator

class SumIntegrator(base_integrator.BaseIntegrator):

    def __str__(self):
        return "SumIntegrator()"

    def integrator(self, allrts, fullchromatogram, rts, chromatogram):
        if len(rts) == 0:
            return None, None, (rts, chromatogram)
        return sum(chromatogram), 0.0, (rts, chromatogram)

    def getSmoothed(self, *a, **kw):
        return [], []
