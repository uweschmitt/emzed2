import pyopenms
from ..data_types import PeakMap

class PeakPickerHiRes(object):

    standardConfig = dict(ms1_only="false", signal_to_noise = 1.0)

    def __init__(self, **modified_config):
        self.pp = pyopenms.PeakPickerHiRes()
        params = self.pp.getParameters()
        config = self.standardConfig
        config.update(modified_config)
        params.update(config)
        self.pp.setParameters(params)

    def pickPeakMap(self, pm, showProgress=False):
        assert isinstance(pm, PeakMap)
        eout = pyopenms.MSExperiment()
        if showProgress:
            self.pp.setLogType(pyopenms.LogType.CMD)
        else:
            self.pp.setLogType(pyopenms.LogType.NONE)
        self.pp.pickExperiment(pm.toMSExperiment(), eout)
        return PeakMap.fromMSExperiment(eout)

