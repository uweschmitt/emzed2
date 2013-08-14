def runPeakPickerHiRes(pattern=None, destination=None, configid=None, **params):

    """
         runs peakPickerHiRes fron openMs in batch mode.
         input files are map files (mzXML, mxML, mzData),
         ouput files are mzML files, with extended file name.

         you can add modifications to the standard parameters, eg
         signal_to_noise, as named arguments.

         if you have multiple configs for the peakpicker, you can give an
         configid as defined in configs.py, or you are asked to choose
         a config.

         if you have a single config this one is used automatically

         examples:

              runPeakPickerHiRes():
                     asks for source files and target directory
                     asks for config if multiple configs are defined

              runPeakPickerHiRes(configid="std", signal_to_noise = 2.0)
                     uses config with id "std", overwrites signal_to_noise
                     parameter with signal_to_noise=2.0.

              runPeakPickerHiRes(signal_to_noise = 2.0)
                     asks for source files and target directory
                     runs peak picking with modified parameter.

              runPeakPickerHiRes(pattern):
                     looks for map files matching pattern
                     resulting mzML files are stored next to input map file

              runPeakPickerHiRes(pattern, signal_to_noise = 2.0)
                     looks for map files matching pattern
                     resulting mzML files are stored next to input map file
                     runs peak picking with modified parameter

              runPeakPickerHiRes(pattern, destination):
                     looks for map files matching pattern
                     resulting mzML files are stored at destination directory

              runPeakPickerHiRes(pattern, destination, signal_to_noise = 2.0)
                     looks for map files matching pattern
                     resulting csv files are stored at destination directory
                     runs peak picking with modified parameter

    """


    from _BatchRunner import BatchRunner
    import configs
    import ms
    import os.path
    import libms.PeakPicking

    class P(BatchRunner):

        def setup(self, config):
            self.pp = libms.PeakPicking.PeakPickerHiRes(**config)

        def process(self, path):

            try:
                print "read ", path
                pm = ms.loadPeakMap(path)
            except Exception, e:
                print e
                print "reading FAILED"
                return None

            picked = self.pp.pickPeakMap(pm, showProgress = True)
            return picked

        def write(self, result, destinationDir, path):
            basename, ext = os.path.splitext(os.path.basename(path))
            savePath = os.path.join(destinationDir, basename+"_centroided.mzML")
            print "save to ", savePath
            ms.storePeakMap(result, savePath)

    return P(configs.peakPickerHiResConfig, False).run(pattern, destination, configid, **params)
