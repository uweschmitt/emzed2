import base_integrator

class NoIntegration(base_integrator.BaseIntegrator):

    def __init__(self, *a, **kw):
        pass

    def setbaseMap(self, baseMap):
        pass

    def integrate(self, *a, **kw):
        return dict(area=None, rmse=None, params=None, eic=None, baseline=None)

    def getSmoothed(self, *a, **kw):
        """has to be implemented"""
        return [], []

    def integrator(self, *a):
        """has to be implemented"""
        pass
