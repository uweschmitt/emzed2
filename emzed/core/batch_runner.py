#encoding: utf-8

class BatchRunner(object):

    """ Base class for batch jobs on the file system.
        Uses template pattern
    """

    def __init__(self, config=None, collectResults = False):
        self.config = config
        self.collectResults = collectResults

    def setup(self, conf):
        """ setup processor with config conf if needed """
        raise NotImplementedError("you have to override this method")

    def process(self, path):
        """ process file denoted by path, returns result object """
        raise NotImplementedError("you have to override this method")

    def write(self, result, destinationDir, path):
        """ writes result to destinationDir. path is the path of the input file"""
        raise NotImplementedError("you have to override this method")

    def run(self, pattern=None, destination=None, configid=None, **params):

        import glob, os.path

        if pattern is None:
            from .. import gui
            files = gui.askForMultipleFiles(extensions=["mzXML", "mzData", "mzML"])
            if not files:
                print "aborted"
                return
            destination = gui.askForDirectory()
            if not destination:
                print "aborted"
                return
        else:
            files = glob.glob(pattern)

        if self.config is None:
            config = dict()
        else:
            if configid is not None:
                for id_, _, config in self.config:
                    if id_ == configid:
                        break
                else:
                    print "invalid configid %r" % configid
                    return

            elif len(self.config) > 1:
                from .. import gui
                config = gui.chooseConfig(self.config,  params)
            else:
                config = self.config[0][2]

            if config is None:
                return # dialog aborted
            config.update(params)

        self.setup(config)

        count = 0
        results = []
        for path in files:

            result = self.process(path)
            if result is None:
                continue

            if destination is None:
                destinationDir = os.path.dirname(path)
            else:
                destinationDir = destination
                try:
                    os.makedirs(destinationDir)
                except:
                    pass # verzeichnisse schon vorhanden

            self.write(result, destinationDir, path)
            if self.collectResults:
                results.append(result)
            count += 1

        print
        print "analyzed %d inputs" % count
        print
        if self.collectResults:
            return results
