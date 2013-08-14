#encoding:utf-8

#from libms.RConnect import CentwaveFeatureDetector as _Centwave
#from libms.RConnect import MatchedFilterFeatureDetector as _MatchedFilters

from emzed.core.r_connect import CentwaveFeatureDetector as _Centwave
from emzed.core.r_connect import MatchedFilterFeatureDetector as _MatchedFilters

from _metabo import metaboFeatureFinder


def runCentwave(pm, **kws):
    det = _Centwave(**kws)
    return det.process(pm)

def runMatchedFilters(pm, **kws):
    det = _MatchedFilters(**kws)
    return det.process(pm)

def runMetaboFeatureFinder(pm,**kws):
    return metaboFeatureFinder(pm, **kws)
