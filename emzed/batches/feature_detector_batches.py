
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
        savePath = os.path.join(destinationDir, basename+".csv")
        print "save to ", savePath
        result.storeCSV(savePath)



def runCentwave(pattern=None, destination=None, configid="std", **params):

    """
    runs centwave algorithm from xcms in batch mode.
    input files are map files (mzXML, mxML, mzData),
    ouput files are csv files

    you can add modifications to the standard parameters, eg ppm,
    as named arguments.

    if you have multiple configs for centwave, you can give an
    configid as defined in _algorithm_configs.py, or you are asked to choose
    a config.

    if you have a single config this one is used automatically

    examples:

        runCentwave():
                asks for source files and target directory
                asks for config if multiple algorithm_configs are defined

        runCentwave(configid="std", ppm=17)
                uses config with id "std", overwrites ppm parameter
                with ppm=17.

        runCentwave(ppm=13):
                asks for source files and target directory
                runs centwave with modified ppm=13 parameter.

        runCentwave(pattern):
                looks for map files matching pattern
                resulting csv files are stored next to input map file

        runCentwave(pattern, mzDiff=0.003):
                looks for map files matching pattern
                resulting csv files are stored next to input map file
                runs centwave with modified mzDiff parameter

        runCentwave(pattern, destination):
                looks for map files matching pattern
                resulting csv files are stored at destination directory

        runCentwave(pattern, destination, ppm=17, peakwidth=(5,100) ):
                looks for map files matching pattern
                resulting csv files are stored at destination directory
                runs centwave with modified ppm and peakwidth parameters.

    """

    from .. import _algorithm_configs
    from ..core.r_connect import CentwaveFeatureDetector

    class P(FD):

        def setup(self, config):
            self.det = CentwaveFeatureDetector(**config)

    return P(_algorithm_configs.centwaveConfig, True).run(pattern, destination, configid, **params)

from ..core import r_connect as __rconnect
runCentwave.__doc__ += __rconnect.CentwaveFeatureDetector.__doc__

def runMatchedFilter(pattern=None, destination=None, configid="std", **params):

    """
         runs matched filters algorithm from xcms in batch mode.
         input files are map files (mzXML, mzML, mzData),
         output files are csv files

         you can add modifications to the standard parameters, eg ppm,
         as named arguments.

         if you have multiple configs for matched filter, you can give an
         configid as defined in algorithm_configs.py, or you are asked to choose
         a config.

         if you have a single config this one is used automatically

         examples:

              runMatchedFilter():
                     asks for source files and target directory
                     asks for config if multiple algorithm_configs are defined

              runMatchedFilter(configid="std", ppm=17)
                     uses config with id "std", overwrites ppm parameter
                     with ppm=17.

              runMatchedFilter(ppm=13):
                     asks for source files and target directory
                     runs matched filter with modified ppm=13 parameter.

              runMatchedFilter(pattern):
                     looks for map files matching pattern
                     resulting csv files are stored next to input map file

              runMatchedFilter(pattern, mzDiff=0.003):
                     looks for map files matching pattern
                     resulting csv files are stored next to input map file
                     runs matched filter with modified mzDiff parameter

              runMatchedFilter(pattern, destination):
                     looks for map files matching pattern
                     resulting csv files are stored at destination directory

              runMatchedFilter(pattern, destination, ppm=17, peakwidth=(5,100) ):
                     looks for map files matching pattern
                     resulting csv files are stored at destination directory
                     runs matched filter with modified ppm and peakwidth parameters.

    """

    from ..core.r_connect import MatchedFilterFeatureDetector
    from .. import _algorithm_configs

    class P(FD):

        def setup(self, config):
            self.det = MatchedFilterFeatureDetector(**config)

    return P(_algorithm_configs.matchedFilterConfig, True).run(pattern, destination, configid, **params)

runMatchedFilter.__doc__ += __rconnect.MatchedFilterFeatureDetector.__doc__




def runMetaboFeatureFinder(pattern=None, destination=None, configid="std", **params):

    """
         runs matched filters algorithm from xcms in batch mode.
         input files are map files (mzXML, mzML, mzData),
         output files are csv files

         you can add modifications to the standard parameters, eg ppm,
         as named arguments.

         if you have multiple configs for matched filter, you can give an
         configid as defined in _algorithm_configs.py, or you are asked to choose
         a config.

         if you have a single config this one is used automatically

         examples:

              runMatchedFilter():
                     asks for source files and target directory
                     asks for config if multiple algorithm_configs are defined

              runMatchedFilter(configid="std", ppm=17)
                     uses config with id "std", overwrites ppm parameter
                     with ppm=17.

              runMatchedFilter(ppm=13):
                     asks for source files and target directory
                     runs matched filter with modified ppm=13 parameter.

              runMatchedFilter(pattern):
                     looks for map files matching pattern
                     resulting csv files are stored next to input map file

              runMatchedFilter(pattern, mzDiff=0.003):
                     looks for map files matching pattern
                     resulting csv files are stored next to input map file
                     runs matched filter with modified mzDiff parameter

              runMatchedFilter(pattern, destination):
                     looks for map files matching pattern
                     resulting csv files are stored at destination directory

              runMatchedFilter(pattern, destination, ppm=17, peakwidth=(5,100) ):
                     looks for map files matching pattern
                     resulting csv files are stored at destination directory
                     runs matched filter with modified ppm and peakwidth parameters.

    """

    from .. import _algorithm_configs

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

    return P(_algorithm_configs.metaboFFConfigs, True).run(pattern, destination, configid, **params)

