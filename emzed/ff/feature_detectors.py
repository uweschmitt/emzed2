#encoding:utf-8




def runCentwave(pm, **kws):
    from emzed.core.r_connect import CentwaveFeatureDetector
    det = CentwaveFeatureDetector(**kws)
    return det.process(pm)

def runMatchedFilters(pm, **kws):
    from emzed.core.r_connect import MatchedFilterFeatureDetector
    det = MatchedFilterFeatureDetector(**kws)
    return det.process(pm)

def runMetaboFeatureFinder(pm,**kws):
    from _metaboff import metaboFeatureFinder
    return metaboFeatureFinder(pm, **kws)
