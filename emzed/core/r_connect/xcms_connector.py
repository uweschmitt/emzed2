# encoding: utf-8
from ..data_types.table import fms as formatSeconds
from ..data_types import PeakMap

from ..dialogs.r_output_dialog import ROutputDialog

import os
import sys
import shutil
import time
import glob
import tempfile

from pyopenms import FileHandler

from pkg_resources import resource_string

from .. import update_handling, config

from r_executor import RInterpreter


def _get_r_version():
    interp = RInterpreter()
    version = interp.version
    return "%s.%s" % (version["major"], version["minor"])


def get_r_version():
    if not hasattr(_get_r_version, "cached_value"):
        r_version = _get_r_version()
        _get_r_version.cached_value = r_version
    return _get_r_version.cached_value


def setup_r_libs_variable():
    subfolder = "r_libs_%s" % get_r_version()
    r_libs_folder = config.folders.getDataHomeSubFolder(subfolder)
    r_libs = [path for path in os.environ.get("R_LIBS", "").split(os.pathsep) if path]
    if r_libs_folder not in r_libs:
        if not os.path.exists(r_libs_folder):
            os.makedirs(r_libs_folder)
        r_libs.insert(0, r_libs_folder)
        os.environ["R_LIBS"] = os.pathsep.join(r_libs)


def execute(*cmds):
    setup_r_libs_variable()
    interp = RInterpreter(dump_stdout=True)
    interp.execute(*cmds)
    return interp


def is_xcms_installed():
    return execute("""status <- require("xcms")""").status


class XCMSUpdateImpl(update_handling.AbstractUpdaterImpl):

    @staticmethod
    def get_id():
        return "xcms_updater"

    def get_update_time_delta_in_seconds(self):
        days = 1
        return days * 24 * 60 * 60

    def get_rlibs_sub_folder(self):
        r_version = get_r_version()
        if r_version is None:
            subfolder = "r_libs"
        else:
            subfolder = "r_libs_%s" % r_version
        return subfolder

    def get_local_rlibs_folder(self):
        subfolder = self.get_rlibs_sub_folder()
        folder = os.path.join(self.data_home, subfolder)
        return folder

    def get_rlibs_exchange_folder(self, exchange_folder):
        subfolder = self.get_rlibs_sub_folder()
        folder = os.path.join(exchange_folder, subfolder)
        return folder

    def _update_info_script(self):
        script = """
                    source("http://bioconductor.org/biocLite.R")
                    todo <- old.packages(repos=biocinstallRepos(), lib="%s")
                    num_to_update = length(todo)
                """ % self.get_local_rlibs_folder().replace("\\", "\\\\")
        return script

    def query_update_info(self, limit):
        #from PyQt4.QtCore import pyqtRemoveInputHook
        #import pdb
        #pyqtRemoveInputHook()
        #pdb.set_trace()
        if not is_xcms_installed():
            return "not installed yet", True
        script = self._update_info_script()

        num_to_update = execute(script).num_to_update
        if not num_to_update:
            return "no update found", False
        else:
            return "updates for %d packages found" % num_to_update, True

    def _do_update_with_gui(self, limit):
        local_folder = self.get_local_rlibs_folder().replace("\\", "\\\\")
        if not is_xcms_installed():
            script = """source("http://bioconductor.org/biocLite.R")
                        biocLite("xcms", dep=T, lib="%s", destdir="%s", quiet=T)
                        """ % (local_folder, local_folder)
        else:
            script = """
                source("http://bioconductor.org/biocLite.R")
                todo <- update.packages(repos=biocinstallRepos(), ask=FALSE, checkBuilt=TRUE,
                                        lib="%s", destdir="%s", quiet=T)
                """ % (local_folder, local_folder)
        assert False, "not tested yet, must be adapted to pyper"
        execute(script)
        dlg = ROutputDialog(script)
        dlg.exec_()

    def do_update(self, limit):
        local_folder = self.get_local_rlibs_folder().replace("\\", "\\\\")
        if not is_xcms_installed():
            script = """source("http://bioconductor.org/biocLite.R")
                        biocLite("xcms", dep=T, lib="%s", destdir="%s", quiet=T)
                        """ % (local_folder, local_folder)
        else:
            script = """
                source("http://bioconductor.org/biocLite.R")
                todo <- update.packages(repos=biocinstallRepos(), ask=FALSE, checkBuilt=TRUE,
                                        lib="%s", destdir="%s", quiet=T)
            """ % (local_folder, local_folder)
        execute(script)

    def upload_to_exchange_folder(self, exchange_folder):
        local_folder = self.get_local_rlibs_folder()
        r_libs_exchange_folder = self.get_rlibs_exchange_folder(exchange_folder)
        # maybe we have a race condition from other userse so we upload first to a unique # folder:
        first_destination_folder = r_libs_exchange_folder + "_%017d" % int(100000 * time.time())
        shutil.copytree(local_folder, first_destination_folder)
        try:
            shutil.rmtree(r_libs_exchange_folder)
        except:
            pass

        existing = glob.glob(r_libs_exchange_folder + "_*")
        latest = sorted(existing)[-1]
        os.rename(latest, r_libs_exchange_folder)

    def touch_data_home_files(self):
        local_folder = self.get_local_rlibs_folder()
        os.utime(local_folder, None)

    def check_for_newer_version_on_exchange_folder(self, exchange_folder):
        local_folder = self.get_local_rlibs_folder()
        exchange_folder = self.get_rlibs_exchange_folder(exchange_folder)
        if not os.path.exists(exchange_folder):
            return False
        return os.stat(local_folder).st_mtime < os.stat(exchange_folder).st_mtime

    def update_from_exchange_folder(self, exchange_folder):
        local_folder = self.get_local_rlibs_folder()
        exchange_folder = self.get_rlibs_exchange_folder(exchange_folder)
        shutil.rmtree(local_folder)
        shutil.copytree(exchange_folder, local_folder)


def _register_xcms_updater(data_home=None):

    from ..config import folders
    if data_home is None:
        data_home = folders.getDataHome()
    updater = update_handling.Updater(XCMSUpdateImpl(), data_home)
    update_handling.registry.register(updater)


def _get_temp_peakmap(msLevel, peakMap):
    if msLevel is None:
        msLevels = peakMap.getMsLevels()
        if len(msLevels) > 1:
            raise Exception("multiple msLevels in peakmap "
                            "please specify msLevel in config")
        msLevel = msLevels[0]

    temp_peakmap = peakMap.extract(mslevelmin=msLevel, mslevelmax=msLevel)
    temp_peakmap.spectra.sort(key=lambda s: s.rt)
    return temp_peakmap


class CentwaveFeatureDetector(object):

 __doc__ = """
 *CentwaveFeatureDetector*:
  Usage:
          print CentwaveFeatureDetector.standardConfig

          detector = CentwaveFeatureDetector(param1=val1, ....)
          detector.process(peakmap)


 :download:`Docs from XCMS library <../emzed/core/r_connect/centwave.txt>`
 """

 #__doc__ += resource_string("emzed.core.r_connect", "centwave.txt")
 #__doc__ = unicode(__doc__, "utf-8")

 standardConfig = dict(ppm=25,
                       peakwidth=(20, 50),
                       prefilter=(3, 100),
                       snthresh = 10,
                       integrate = 1,
                       mzdiff=-0.001,
                       noise=0,
                       mzCenterFun="wMean",
                       fitgauss=False,
                       msLevel=None,
                       verbose_columns = False)

 def __init__(self, **kw):

     if not is_xcms_installed():
         raise Exception("XCMS not installed yet")

     self.config = self.standardConfig.copy()
     self.config.update(kw)

 def process(self, peakMap):
     assert isinstance(peakMap, PeakMap)
     if len(peakMap) == 0:
         raise Exception("empty peakmap")

     temp_peakmap = _get_temp_peakmap(self.config.get("msLevel"), peakMap)

     td = tempfile.mkdtemp(prefix="emzed_r_script_centwave_")

     temp_input = os.path.join(td, "input.mzData")
     temp_output = os.path.join(td, "output.csv")

     # needed for network shares:
     if sys.platform == "win32":
         temp_input = temp_input.replace("/", "\\")

     FileHandler().storeExperiment(temp_input, temp_peakmap.toMSExperiment())

     dd = self.config.copy()
     dd["temp_input"] = temp_input
     dd["temp_output"] = temp_output
     dd["fitgauss"] = str(dd["fitgauss"]).upper()
     dd["verbose_columns"] = str(dd["verbose_columns"]).upper()

     script = """
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
                 print(xs@peaks)
                 peaks <- data.frame(xs@peaks)
                 """ % dd

     del dd["temp_input"]
     del dd["temp_output"]

     table = execute(script).get_df_as_table("peaks",
                               types=dict(mz=float, mzmin=float, mzmax=float,
                                          rt=float, rtmin=float, ftmax=float,
                                          into=float, intb=float, maxo=float,
                                          sn=float, sample=int),
                               formats=dict(mz="%10.5f", mzmin="%10.5f", mzmax="%10.5f",
                                            rt=formatSeconds, rtmin=formatSeconds,
                                            rtmax=formatSeconds,
                                            into="%.2e", intb="%.2e", maxo="%.2e",
                                            sn="%.2e", peakmap="%s")
                               )

     table.addConstantColumn("centwave_config", dd, dict, None)
     table.meta["generator"] = "xcms.centwave"
     decorate(table, temp_peakmap)
     return table


class MatchedFilterFeatureDetector(object):

 __doc__ = """
 *MatchedFilterFeatureDetector*:
  Usage:
        print MatchedFilterFeatureDetector.standardConfig

        detector = MatchedFilterFeatureDetector(param1=val1, ....)
        detector.process(peakmap)

 :download:`Docs from XCMS library <../emzed/core/r_connect/matched_filter.txt>`
 """

 standardConfig = dict(fwhm=30,
                       sigma=30 / 2.3548,
                       max_=5,
                       snthresh=10,
                       step=0.1,
                       steps=2,
                       mzdiff=0.8 - 2 * 2,
                       msLevel=None,
                       index=False)

 def __init__(self, **kw):
     if not is_xcms_installed():
         raise Exception("XCMS not installed yet")
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
     shift = minRt - 1.0
     peakMap.shiftRt(-shift)

     td = tempfile.mkdtemp(prefix="emzed_r_script_matched_filter_")

     temp_input = os.path.join(td, "input.mzData")
     temp_output = os.path.join(td, "output.csv")

     # needed for network shares:
     if sys.platform == "win32":
         temp_input = temp_input.replace("/", "\\")

     FileHandler().storeExperiment(temp_input, peakMap.toMSExperiment())

     dd = self.config.copy()
     dd["temp_input"] = temp_input
     dd["temp_output"] = temp_output
     dd["index"] = str(dd["index"]).upper()

     script = """
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
                 peaks <- data.frame(xs@peaks)
                 """ % dd

     del dd["temp_input"]
     del dd["temp_output"]

     table = execute(script).get_df_as_table("peaks",
                               types=dict(mz=float, mzmin=float, mzmax=float,
                                          rt=float, rtmin=float, ftmax=float,
                                          into=float, intf=float, maxo=float,
                                          maxf=float, i=int,
                                          sn=float, sample=int),
                               formats=dict(mz="%10.5f", mzmin="%10.5f", mzmax="%10.5f",
                                            rt=formatSeconds, rtmin=formatSeconds,
                                            rtmax=formatSeconds,
                                            into="%.2e", intf="%.2e", maxo="%.2e",
                                            maxf="%.2e", sn="%.2e")
                               )

     # parse csv and
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
    src = peakMap.meta.get("source", "")
    table.addConstantColumn("source", src, str, None)
    table.addConstantColumn("polarity", peakMap.polarity, str, None)
    table.addEnumeration()
    table.title = os.path.basename(src)
