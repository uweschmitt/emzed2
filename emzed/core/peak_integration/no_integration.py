import base_integrator

class NoIntegration(base_integrator.BaseIntegrator):

    def __init__(self, *a, **kw):
        pass

    def setbaseMap(self, baseMap):
        pass

    def integrate(self, *a, **kw):
        return dict(area=None, rmse=None, params=None)

    def _getSmoothed(self, *a, **kw):
        return [], []
