#encoding: utf-8
from r_executor import RExecutor
from ..data_types.table  import fms as formatSeconds
from ..data_types.table_parser import TableParser
from ..data_types import PeakMap

import os, sys

from ..temp_file_utils import TemporaryDirectoryWithBackup
from pyopenms import FileHandler

from .. import config


def exchangeFolderAvailable():
    return config.folders.getExchangeSubFolder(None) is not None

class XCMSFeatureParser(TableParser):


    typeDefaults = dict( mz= float, mzmin= float, mzmax=float,
                      rt= float, rtmin= float, rtmax=float,
                      into= float, intb= float,
                      maxo= float, sn= float,
                      sample= int )

    formatDefaults = dict( mz= "%10.5f", mzmin= "%10.5f", mzmax= "%10.5f",
                           rt=  formatSeconds, rtmin=formatSeconds,
                           rtmax=formatSeconds, into= "", intb= "", intf="",
                           maxo= "", sn= "%.1e",
                           sample= "")



def install_xmcs_if_needed_statements():
    r_libs = RExecutor().getRLibsFolder().replace("\\", "\\\\")

    script = """
                if (require("xcms") == FALSE)
                {
                    source("http://bioconductor.org/biocLite.R")
                    biocLite("xcms", dep=T, lib="%s", destdir="%s", quiet=T)
                }
            """ % (r_libs, r_libs)

    return script


def checkIfxcmsIsInstalled():

    status = RExecutor().run_command(""" if (require("xcms") == FALSE) q(status=1); q(status=0); """)
    return status==1


def installXcmsIfNeeded():

    RExecutor().run_command(install_xmcs_if_needed_statements())


def lookForXcmsUpgrades():

    script = """
                 source("http://bioconductor.org/biocLite.R")
                 todo <- old.packages(repos=biocinstallRepos(), lib="%s", quiet=T)
                 q(status=length(todo))
             """ % RExecutor().getRLibsFolder().replace("\\", "\\\\")

    num = RExecutor().run_command(script)
    if not num:
        print "No update needed"
    else:
        print num, "updates found"


def doXcmsUpgrade():

    r_libs = RExecutor().getRLibsFolder().replace("\\", "\\\\")

    script = """
     source("http://bioconductor.org/biocLite.R")
     todo <- update.packages(repos=biocinstallRepos(), ask=FALSE, checkBuilt=TRUE, lib="%s", destdir="%s", quiet=T)
     q(status=length(todo))
    """ % (r_libs, r_libs)

    return RExecutor().run_command(script)


def _get_temp_peakmap(msLevel, peakMap):
    if msLevel is None:
        msLevels = peakMap.getMsLevels()
        if len(msLevels) > 1:
            raise Exception("multiple msLevels in peakmap "\
                            "please specify msLevel in config")
        msLevel = msLevels[0]

    temp_peakmap =  peakMap.extract(mslevelmin=msLevel, mslevelmax=msLevel)
    temp_peakmap.spectra.sort(key = lambda s: s.rt)
    return temp_peakmap


class CentwaveFeatureDetector(object):

    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "centwave.txt")

    __doc__ = """ CentwaveFeatureDetector

    usage:

           print CentwaveFeatureDetector.standardConfig

           detector = CentwaveFeatureDetector(param1=val1, ....)
           detector.process(peakmap)


    Docs from XCMS library:

    """

    __doc__ += "".join(file(path).readlines())
    __doc__ = unicode(__doc__, "utf-8")

    standardConfig = dict(   ppm=25,
                             peakwidth=(20,50),
                             prefilter=(3,100),
                             snthresh = 10,
                             integrate = 1,
                             mzdiff=-0.001,
                             noise=0,
                             mzCenterFun="wMean",
                             fitgauss=False,
                             msLevel=None,
                             verbose_columns = False )

    def __init__(self, **kw):

        #installXcmsIfNeeded()

        self.config = self.standardConfig.copy()
        self.config.update(kw)

    def process(self, peakMap):
        assert isinstance(peakMap, PeakMap)
        if len(peakMap) == 0:
            raise Exception("empty peakmap")

        temp_peakmap = _get_temp_peakmap(self.config.get("msLevel"), peakMap)

        with TemporaryDirectoryWithBackup() as td:

            temp_input = os.path.join(td, "input.mzData")
            temp_output = os.path.join(td, "output.csv")

            # needed for network shares:
            if sys.platform == "win32":
                temp_input = temp_input.replace("/","\\")

            FileHandler().storeExperiment(temp_input, temp_peakmap.toMSExperiment())

            dd = self.config.copy()
            dd["temp_input"] = temp_input
            dd["temp_output"] = temp_output
            dd["fitgauss"] = str(dd["fitgauss"]).upper()
            dd["verbose_columns"] = str(dd["verbose_columns"]).upper()


            script = install_xmcs_if_needed_statements() + """
                        library(xcms)
                        xs <- xcmsSet(%(temp_input)r, method="centWave",
                                          ppm=%(ppm)d,
                                          peakwidth=c%(peakwidth)r,
                                          prefilter=c%(prefilter)r,
                                          snthresh = %(snthresh)f,
                                          integrate= %(integrate)d,
                                          mzdiff   = %(mzdiff)f,
                                          noise    = %(noise)f,
                                          fitgauss = %(fitgauss)s,
                                          verbose.columns = %(verbose_columns)s,
                                          mzCenterFun = %(mzCenterFun)r
                                     )
                        write.table(xs@peaks, file=%(temp_output)r)
                        q(status=123)
                     """ % dd

            del dd["temp_input"]
            del dd["temp_output"]

            if RExecutor().run_command(script, td) != 123:
                raise Exception("R operation failed")

            # parse csv and shift rt related values to undo rt modifiaction
            # as described above
            table = XCMSFeatureParser.parse(file(temp_output).readlines())
            table.addConstantColumn("centwave_config", dd, dict, None)
            table.meta["generator"] = "xcms.centwave"
            decorate(table, temp_peakmap)
            return table

class MatchedFilterFeatureDetector(object):

    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "matched_filter.txt")

    __doc__ = """ MatchedFilterFeatureDetector

    usage:

           print MatchedFilterFeatureDetector.standardConfig

           detector = MatchedFilterFeatureDetector(param1=val1, ....)
           detector.process(peakmap)


    Docs from XCMS library:

    """

    __doc__ += "".join(file(path).readlines())
    __doc__ = unicode(__doc__, "utf-8")

    standardConfig = dict(   fwhm = 30,
                             sigma = 30/2.3548,
                             max_ = 5,
                             snthresh = 10,
                             step = 0.1,
                             steps = 2,
                             mzdiff = 0.8 - 2*2,
                             msLevel = None,
                             index = False )

    def __init__(self, **kw):
        #installXcmsIfNeeded()
        self.config = self.standardConfig.copy()
        self.config.update(kw)

    def process(self, peakMap):
        assert isinstance(peakMap, PeakMap)
        if len(peakMap) == 0:
            raise Exception("empty peakmap")

        temp_peakmap = _get_temp_peakmap(self.config.get("msLevel"), peakMap)
        minRt = peakMap.spectra[0].rt
        # matched filter  does not like rt <= 0, so we shift that rt starts
        # with 1.0: we have to undo this shift later when parsing the output of
        # xcms
        shift = minRt-1.0
        peakMap.shiftRt(-shift)

        with TemporaryDirectoryWithBackup() as td:

            temp_input = os.path.join(td, "input.mzData")
            temp_output = os.path.join(td, "output.csv")

            # needed for network shares:
            if sys.platform == "win32":
                temp_input = temp_input.replace("/","\\")

            FileHandler().storeExperiment(temp_input, peakMap.toMSExperiment())

            dd = self.config.copy()
            dd["temp_input"] = temp_input
            dd["temp_output"] = temp_output
            dd["index"] = str(dd["index"]).upper()

            script = install_xmcs_if_needed_statements() + """
                        library(xcms)
                        xs <- xcmsSet(%(temp_input)r, method="matchedFilter",
                                       fwhm = %(fwhm)f, sigma = %(sigma)f,
                                       max = %(max_)d,
                                       snthresh = %(snthresh)f,
                                       step = %(step)f, steps=%(steps)d,
                                       mzdiff = %(mzdiff)f,
                                       index = %(index)s,
                                       sleep=0
                                     )
                        write.table(xs@peaks, file=%(temp_output)r)
                        q(status=123)
                     """ % dd

            del dd["temp_input"]
            del dd["temp_output"]

            if RExecutor().run_command(script, td) != 123:
                raise Exception("R opreation failed")

            # parse csv and
            table = XCMSFeatureParser.parse(file(temp_output).readlines())
            table.addConstantColumn("matchedfilter_config", dd, dict, None)
            table.meta["generator"] = "xcms.matchedfilter"
            decorate(table, temp_peakmap)
            # undo shiftRt done above:
            table.rtmin += shift
            table.rtmax += shift
            table.rt += shift
            return table

def decorate(table, peakMap):
    table.addConstantColumn("peakmap", peakMap, object, None)
    src = peakMap.meta.get("source","")
    table.addConstantColumn("source", src, str, None)
    table.addConstantColumn("polarity", peakMap.polarity, str, None)
    table.addEnumeration()
    table.title = os.path.basename(src)
