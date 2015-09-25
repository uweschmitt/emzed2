
from ..core import batch_runner


class FD(batch_runner.BatchRunner):

    def process(self, path):
        from .. import io

        try:
            print "read ", path
            ds = io.loadPeakMap(path)
        except Exception, e:
            print e
            print "reading FAILED"
            return None

        table = self.det.process(ds)
        table.title = path

        print len(table), "features found"
        return table

    def write(self, result, destinationDir, path):
        import os.path
        basename, ext = os.path.splitext(os.path.basename(path))
        savePath = os.path.join(destinationDir, basename + ".csv")
        print "save to ", savePath
        result.storeCSV(savePath)


def runCentwave(pattern=None, destination=None, configid="std", **params):
    """runs centwave algorithm from xcms in batch mode

    - *pattern* is used for file globbing, eg "/data/experiment1/\*.mzML", allowed are
      files of type *.mzML*, *.mzXML* and *.mzData*.
    - *destination* is a target folder where the results are stored as *.csv* files
    - *configid* is a preconfiugred setting id, but following key pairs as *ppm=20* override this.

    Examples:

    - runCentwave()
        asks for source files and target directory
        asks for config if multiple algorithm_configs are defined

    - runCentwave(configid="std", ppm=17)
        uses confi with id *"std"*, overwrites ppm parameter with *ppm=17*.

    - runCentwave(ppm=13):
        asks for source files and target directory runs centwave with modified *ppm=13* parameter.

    - runCentwave(pattern):
        looks for map files matching pattern resulting csv files are stored next to input map file

    - runCentwave(pattern, mzDiff=0.003):
        looks for map files matching pattern resulting csv files are stored next to input map file
        runs centwave with modified mzDiff parameter

    - runCentwave(pattern, destination):
        looks for map files matching pattern resulting csv files are stored at destination directory

    - runCentwave(pattern, destination, ppm=17, peakwidth=(5,100) ):
        looks for map files matching pattern resulting csv files are stored at destination directory
        runs centwave with modified ppm and peakwidth parameters.

    :download:`Docs from XCMS library <../emzed/core/r_connect/centwave.txt>`
    """

    from .. import algorithm_configs
    from ..core.r_connect import CentwaveFeatureDetector

    class P(FD):

        def setup(self, config):
            self.det = CentwaveFeatureDetector(**config)

    return P(algorithm_configs.centwaveConfig, True).run(pattern, destination, configid, **params)


def runMatchedFilter(pattern=None, destination=None, configid="std", **params):
    """runs matched filters algorithm from *XCMS* in batch mode

    - *pattern* is a used for file globbing, eg "/data/experiment1/\*.mzML", allowed are
      files of type *.mzML*, *.mzXML* and *.mzData*.
    - *destination* is a target folder where the results are stored as *.csv* files
    - *configid* is a preconfiugred setting id, but following key pairs as *ppm=20* override this.

    Examples:

    - runMatchedFilter():
        asks for source files and target directory
        asks for config if multiple algorithm_configs are defined

    - runMatchedFilter(configid="std", ppm=17)
        uses config with id "std", overwrites ppm parameter
        with ppm=17.

    - runMatchedFilter(ppm=13):
        asks for source files and target directory
        runs matched filter with modified ppm=13 parameter.

    - runMatchedFilter(pattern):
        looks for map files matching pattern
        resulting csv files are stored next to input map file

    - runMatchedFilter(pattern, mzDiff=0.003):
        looks for map files matching pattern
        resulting csv files are stored next to input map file
        runs matched filter with modified mzDiff parameter

    - runMatchedFilter(pattern, destination):
        looks for map files matching pattern
        resulting csv files are stored at destination directory

    - runMatchedFilter(pattern, destination, ppm=17, peakwidth=(5,100) ):
        looks for map files matching pattern
        resulting csv files are stored at destination directory
        runs matched filter with modified ppm and peakwidth parameters.

    :download:`Docs from XCMS library <../emzed/core/r_connect/matched_filter.txt>`
    """

    from ..core.r_connect import MatchedFilterFeatureDetector
    from .. import algorithm_configs

    class P(FD):

        def setup(self, config):
            self.det = MatchedFilterFeatureDetector(**config)

    return P(algorithm_configs.matchedFilterConfig, True).run(pattern, destination, configid,
                                                              **params)


def runMetaboFeatureFinder(pattern=None, destination=None, configid="std", **params):
    """runs *MetaboFeatureFinding* from *OpenMS* in batch mode.

    - *pattern* is a used for file globbing, eg "/data/experiment1/\*.mzML", allowed are
      files of type *.mzML*, *.mzXML* and *.mzData*.
    - *destination* is a target folder where the results are stored as *.csv* files
    - *configid* is a preconfiugred setting id, but following key pairs as *ppm=20* override this.

    Examples:

    - runMetaboFeatureFinder():
        asks for source files and target directory
        asks for config if multiple algorithm_configs are defined

    - runMetaboFeatureFinder(configid="std", ffm_local_mz_range=0.01)
        uses config with id "std", overwrites *ffm_local_mz_range* parameter
        with value *0.01*

    - runMetaboFeatureFinder(ppm=13):
        asks for source files and target directory
        runs matched filter with modified ppm=13 parameter.

    - runMetaboFeatureFinder(pattern):
        looks for map files matching pattern
        resulting csv files are stored next to input map file

    - runMetaboFeatureFinder(pattern, mzDiff=0.003):
        looks for map files matching pattern
        resulting csv files are stored next to input map file
        runs matched filter with modified mzDiff parameter

    - runMetaboFeatureFinder(pattern, destination):
        looks for map files matching pattern
        resulting csv files are stored at destination directory

    - runMetaboFeatureFinder(pattern, destination, ppm=17, peakwidth=(5,100) ):
        looks for map files matching pattern
        resulting csv files are stored at destination directory
        runs matched filter with modified ppm and peakwidth parameters.

    For the available parameter settings see :py:func:`~emzed.ff.runMetaboFeatureFinder`.
    """

    from .. import algorithm_configs

    class P(FD):

        def __init__(self, *a, **kw):
            batch_runner.BatchRunner.__init__(self, *a, **kw)

        def process(self, path):
            from ..ff._metaboff import metaboFeatureFinder
            from .. import io

            try:
                print "read ", path
                ds = io.loadPeakMap(path)
            except Exception, e:
                print e
                print "reading FAILED"
                return None

            table = metaboFeatureFinder(ds, **self._ff_config)
            table.title = path

            print len(table), "features found"
            return table

        def setup(self, config):
            self._ff_config = config

    return P(algorithm_configs.metaboFFConfigs, True).run(pattern, destination, configid, **params)
