def runPeakPickerHiRes(pattern=None, destination=None, configid=None, **params):
    """ import runPeakPickerHiRes.
    runs peakPickerHiRes from openMs in batch mode.
    - input files are map files (mzXML, mxML, mzData),
    - ouput files are mzML files, with extended file name.
    - *pattern* is
    - *destination* is the path of the output file
    - *configid* is

    You can add modifications to the standard parameters, e. g.
    *signal_to_noise*, as named arguments.

    If you have multiple configs for the peakpicker, you can give an
    configid as defined in algorithm_configs.py, or you are asked to choose
    a config.

    If you have a single config this one is used automatically.

    Examples:

    - runPeakPickerHiRes()
       asks for source files and target directory
       asks for config if multiple algorithm_configs are defined

    - runPeakPickerHiRes(configid="std", signal_to_noise = 2.0)
       uses config with id "std", overwrites signal_to_noise
       parameter with signal_to_noise=2.0.

    - runPeakPickerHiRes(signal_to_noise = 2.0)
       asks for source files and target directory
       runs peak picking with modified parameter.

    - runPeakPickerHiRes(pattern)
       looks for map files matching pattern
       resulting mzML files are stored next to input map file

    - runPeakPickerHiRes(pattern, signal_to_noise = 2.0)
       looks for map files matching pattern
       resulting mzML files are stored next to input map file
       runs peak picking with modified parameter

    - runPeakPickerHiRes(pattern, destination)
       looks for map files matching pattern
       resulting mzML files are stored at destination directory

    - runPeakPickerHiRes(pattern, destination, signal_to_noise = 2.0)
       looks for map files matching pattern
       resulting csv files are stored at destination directory
       runs peak picking with modified parameter
    """

    from ..core.batch_runner import BatchRunner
    from .. import algorithm_configs
    from .. import io
    import os.path
    from ..core import peak_picking

    class P(BatchRunner):

        def setup(self, config):
            self.pp = peak_picking.PeakPickerHiRes(**config)

        def process(self, path):

            try:
                print "read ", path
                pm = io.loadPeakMap(path)
            except Exception, e:
                print e
                print "reading FAILED"
                return None

            picked = self.pp.pickPeakMap(pm, showProgress=True)
            return picked

        def write(self, result, destinationDir, path):
            basename, ext = os.path.splitext(os.path.basename(path))
            savePath = os.path.join(destinationDir, basename + "_centroided.mzML")
            print "save to ", savePath
            io.storePeakMap(result, savePath)

    return P(algorithm_configs.peakPickerHiResConfig, False).run(pattern, destination, configid, **params)
