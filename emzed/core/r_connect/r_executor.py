import os
import glob
import subprocess
import sys
import re
import tempfile
import pandas
import numpy
from ..data_types import Table

from .. import config

import patched_pyper as pyper

def find_r_exe():

    assert sys.platform == "win32"
    import _winreg
    pathToR = None
    for finder in [
        lambda: _path_from(_winreg.HKEY_CURRENT_USER),
        lambda: _path_from(_winreg.HKEY_LOCAL_MACHINE),
        lambda: os.environ.get("R_HOME"),
        _parse_path_variable,
    ]:
        try:
            pathToR = finder()
            if pathToR is not None:
                break
        except (KeyError, WindowsError):
            pass
    if pathToR is None:
        raise Exception("install dir of R not found, neither in registry, nor is R_HOME set.")

    found = glob.glob("%s/bin/x64/R.exe" % rHome)
    if not found:
        found = glob.glob("%s/bin/R.exe" % rHome)
        if not found:
            raise Exception("could not find R.exe")
    return found[0]

def _parse_path_variable():
    for path in os.environ.get("PATH", "").split(os.pathsep):
        # windows
        if os.path.exists(os.path.join(path, "R.exe")):
            print "Found R at", path
            return path
        # non windows:
        test = os.path.join(path, "R")
        if os.path.exists(test) and not os.path.isdir(test):
            return test
    return None

def _path_from(regsection):
    assert sys.platform == "win32"
    import _winreg
    key = _winreg.OpenKey(regsection, "Software\\R-core\\R")
    return _winreg.QueryValueEx(key, "InstallPath")[0]


class RInterpreter(object):

    """
    This class is the bridge to R. It creates a connection to a R process, it allows code
    execution and passes data to and from this process. For convinience R data.frame objects
    are converted to and from emzed Table objects.

    Example::

        >>> ip = emzed.r.RInterpreter()

        >>> ip.execute("a <- 3")
        >>> print ip.a
        3

        >>> ip.execute("tab <- data.frame(a=c(1, 2), b=c(2.1, 3))")
        >>> print ip.tab
        <emzed.core.data_types.table.Table object at 0x.......>

        >>> ip.tab.print_()
        a        b
        int      float
        ------   ------
        1        2.100000
        2        3.000000

        >>> print ip.get_raw("x")    # returns pandas DataFrame
           a    b
        1  1  2.1
        2  2  3.0

    """

    def __init__(self, dump_stdout=True, r_exe=None, **kw):
        """Starts a R process.

           In case of ``dump_stdout`` being ``True``, console output from R is imediatly
           dumped to the stdout of Python. This is helpful for long running scripts indicating
           their progress by printing status information, but may clutter the console,
           as lots of internal conversion operations are printed too.
        """
        if r_exe is None:
            if sys.platform == "win32":
                r_exe = find_r_exe()
            else:
                r_exe = "R"

        self.__dict__["session"] = pyper.R(RCMD=r_exe, dump_stdout=dump_stdout, **kw)

    def __dir__(self):
        """ avoid completion in IPython shell, as attributes are automatically looked up in
        overriden __getattr__ method
        """
        return ["execute", "get_df_as_table", "get_raw"]

    def execute(self, *cmds):
        """executes commands. Each command by be a multiline command. """
        for cmd in cmds:
            self.session(cmd)
        return self

    def get_df_as_table(self, name, title=None, meta=None, types=None, formats=None):
        """
        Transfers R data.frame object with name ``name`` to emzed Table object.
        For the remaining paramters see :py:meth:`~emzed.core.data_types.table.Table.from_pandas`
        """
        native = getattr(self.session, name)
        assert isinstance(native, pandas.DataFrame), "expected data frame, got %s" % type(native)
        return Table.from_pandas(native, title, meta, types, formats)

    def get_raw(self, name):
        """
        returns data.frame as pandas DataFrame, etc.
        no converstion to emzed Table data structure
        """
        return self.__getattr__(name, False)

    def __getattr__(self, name, convert_to_table=True):
        # IPython 0.10 does strange things for completion, so we circument them:
        if name == "trait_names" or name == "_getAttributeNames":
            return []
        # IPython 0.10 has an error for ip.execute("x <- data.frame()") as it tries to lookup
        # attribute 'execute("x <- data")', I think this is driven by the dot in "data.frame"
        if name.startswith("execute("):
            return []
        value = getattr(self.session, name)
        if convert_to_table and isinstance(value, pandas.DataFrame):
            return Table.from_pandas(value)
        return value

    def __setattr__(self, name, value):
        if isinstance(value, Table):
            value = value.to_pandas()
        setattr(self.session, name, value)


class _RExecutor(object):

    _patched_rlibs_folder = None

    # RExecutor is a singleton:
    _instance = None

    def __new__(cls, *args, **kwargs):

        if not cls._instance:
            cls._instance = super(RExecutor, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if sys.platform == "win32":
            rExe = RExecutor.findRExe()
            # import win32api
            self.rExe = rExe  # win32api.GetShortPathName(rExe)
        else:
            self.rExe = "R"

    @staticmethod
    def findRExe():

        assert sys.platform == "win32"
        import _winreg
        pathToR = None
        for finder in [
            lambda: RExecutor._path_from(_winreg.HKEY_CURRENT_USER),
            lambda: RExecutor._path_from(_winreg.HKEY_LOCAL_MACHINE),
            lambda: os.environ.get("R_HOME"),
            RExecutor._parse_path_variable,
        ]:
            try:
                pathToR = finder()
                if pathToR is not None:
                    break
            except (KeyError, WindowsError):
                pass
        if pathToR is None:
            raise Exception("install dir of R not found, neither in registry, nor is R_HOME set.")

        found = glob.glob("%s/bin/x64/R.exe" % rHome)
        if not found:
            found = glob.glob("%s/bin/R.exe" % rHome)
            if not found:
                raise Exception("could not find R.exe")
        return found[0]

    @staticmethod
    def _parse_path_variable():
        for path in os.environ.get("PATH", "").split(os.pathsep):
            # windows
            if os.path.exists(os.path.join(path, "R.exe")):
                print "Found R at", path
                return path
            # non windows:
            test = os.path.join(path, "R")
            if os.path.exists(test) and not os.path.isdir(test):
                return test
        return None

    @staticmethod
    def _path_from(regsection):
        assert sys.platform == "win32"
        import _winreg
        key = _winreg.OpenKey(regsection, "Software\\R-core\\R")
        return _winreg.QueryValueEx(key, "InstallPath")[0]

    def create_process(self, path):
        self.setup_r_libs_variable()
        with open(path, "r") as fp:
            # do not know why diff platforms behave differntly:
            if sys.platform == "win32":
                proc = subprocess.Popen(['%s' % self.rExe, '--vanilla', '--silent'],
                                        stdin=fp, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        bufsize=0, shell=True)
            else:
                proc = subprocess.Popen(['%s --vanilla --silent' % self.rExe],
                                        stdin=fp, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        bufsize=0, shell=True)
            while True:
                line_out = proc.stdout.readline().rstrip()
                yield line_out
                if not line_out:
                    break

            proc.wait()
            err = proc.stderr.read()
            yield err
            yield proc.returncode

    def run_script(self, path):
        proc = self.create_process(path)
        for rv in proc:
            if not rv:
                break
            print rv
        err = proc.next()
        rc = proc.next()
        print err
        return rc

    def get_r_version(self):
        if sys.platform == "win32":
            proc = subprocess.Popen(['%s' % self.rExe, '--version', '--vanilla', '--silent'],
                                    stderr=subprocess.PIPE,
                                    bufsize=0, shell=True)
            out, err = proc.communicate()
            answer = err
        else:
            proc = subprocess.Popen(['%s --version' % self.rExe],
                                    stdout=subprocess.PIPE,
                                    bufsize=0, shell=True)
            out, err = proc.communicate()
            answer = out
        match = re.search("version\s+(\d+\.\d+\.\d+)", answer)
        if not match:
            return None
        return match.groups(0)[0]

    def get_r_libs_folder(self):

        r_version = RExecutor().get_r_version()
        if r_version is None:
            subfolder = "r_libs"
        else:
            subfolder = "r_libs_%s" % r_version
        r_libs_folder = config.folders.getDataHomeSubFolder(subfolder)
        return r_libs_folder

    def setup_r_libs_variable(self):

        r_libs_folder = self.get_r_libs_folder()
        print "SET R_LIBS ENVIRONMENT VARIABLE TO", r_libs_folder
        if r_libs_folder is not None:
            r_libs = [path for path in os.environ.get("R_LIBS", "").split(os.pathsep) if path]
            if r_libs_folder not in r_libs:
                if not os.path.exists(r_libs_folder):
                    os.makedirs(r_libs_folder)
                r_libs.insert(0, r_libs_folder)
                os.environ["R_LIBS"] = os.pathsep.join(r_libs)

    def run_command(self, command):
        dir_ = tempfile.mkdtemp(prefix="emzed_r_script_")
        with open(os.path.join(dir_, "script.R"), "w") as fp:
            print >> fp, command
        fp.close()
        return self.run_script(fp.name)

    def start_command(self, command):
        """
        yields stdout line by line, empty line marks end of process, then stderr in one string
        and process return code as integer are yielded.
        """
        dir_ = tempfile.mkdtemp(prefix="emzed_r_script_")
        with open(os.path.join(dir_, "script.R"), "w") as fp:
            print >> fp, command
        fp.close()
        proc = self.create_process(fp.name)
        for answer in proc:
            yield answer
