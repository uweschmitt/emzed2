from tempfile import mkdtemp
from shutil   import rmtree, copytree
import os

class TemporaryDirectoryWithBackup(object):

    def __init__(self, keep=False):
        self.keep = keep

    def __enter__(self):
        self.d = mkdtemp()
        return self.d

    def __exit__(self, a, b, c):

        backupdir = "logs/last_temp_dir"
        rmtree(backupdir, ignore_errors = True) # might not exist
        try:
            copytree(self.d, backupdir)
            print "backuped logs to", os.path.abspath(backupdir)
        except:
            pass # sometimes copytree fails

        if not self.keep:
            try:
                rmtree(self.d)
            except:
                pass # sometimes rmtree fails
