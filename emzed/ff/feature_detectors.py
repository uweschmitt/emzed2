# encoding:utf-8
from emzed.core.r_connect import CentwaveFeatureDetector
from emzed.core.r_connect import MatchedFilterFeatureDetector
from _metaboff import metaboFeatureFinder as runMetaboFeatureFinder


def runCentwave(pm, **kws):
    """runs centwave feature detector from *XCMS* on Peakmap *pm*.

    For parameters see
    :download:`Docs from XCMS library <../emzed/core/r_connect/centwave.txt>`

    """
    det = CentwaveFeatureDetector(**kws)
    return det.process(pm)


def runMatchedFilters(pm, **kws):
    """runs matched filters feature detector from *XCMS* on Peakmap *pm*.

    For parameters see
    :download:`Docs from XCMS library <../emzed/core/r_connect/matched_filter.txt>`

    """
    det = MatchedFilterFeatureDetector(**kws)
    return det.process(pm)
