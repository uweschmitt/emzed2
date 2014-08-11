import pdb
import os
import datetime
import traceback
import glob
import sys
import pandas
from ..data_types import Table


import patched_pyper as pyper


def find_r_exe_on_windows():

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

    found = glob.glob("%s/bin/x64/R.exe" % pathToR)
    if not found:
        found = glob.glob("%s/bin/R.exe" % pathToR)
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

        >>> print ip.tab
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

    def __init__(self, dump_stdout=True, r_exe=None, do_log=False, **kw):
        """Starts a R process.

           In case of ``dump_stdout`` being ``True``, console output from R is imediatly
           dumped to the stdout of Python. This is helpful for long running scripts indicating
           their progress by printing status information, but may clutter the console,
           as lots of internal conversion operations are printed too.
        """
        if r_exe is None:
            if sys.platform == "win32":
                r_exe = find_r_exe_on_windows()
            else:
                r_exe = "R"

        fh = open("log_last_use_emzed_r_bridge.txt", "a") if do_log else None
        self.__dict__["fh"] = fh

        try:
            if do_log:
                print >> fh, "\n# start subprocess %s at %s" % (r_exe, datetime.datetime.now())
            session = pyper.R(RCMD=r_exe, dump_stdout=dump_stdout, **kw)
        except:
            print >> fh, "\n# failure"
            traceback.print_exc(file=fh)
            fh.close()
            raise Exception("could not start R, is R installed ?")
        self.__dict__["session"] = session

    def __dir__(self):
        """ avoid completion in IPython shell, as attributes are automatically looked up in
        overriden __getattr__ method
        """
        return ["execute", "get_df_as_table", "get_raw"]

    def execute(self, *cmds):
        """executes commands. Each command by be a multiline command. """
        if self.fh is not None:
            print >> self.fh, "#", datetime.datetime.now()
        for cmd in cmds:
            if self.fh is not None:
                print >> self.fh, cmd
            self.session(cmd)

        if self.fh is not None:
            print >> self.fh, "#", 60 * "="
        return self

    def execute_file(self, path):
        """execute r scripts described by path

           if path is only a file name the directory of the calling functions __file__ is used
           for looking up the r script.
           use "./abc.r" notation if you want to get script from the current working directory.
        """

        if os.path.dirname(path) == "":   # only file name
            import inspect
            calling_file = inspect.stack()[1][0].f_globals.get("__file__")
            if calling_file is not None:
                path = os.path.join(os.path.dirname(os.path.abspath(calling_file)), path)
        if self.fh is not None:
            print >> self.fh, "#", datetime.datetime.now()
            print >> self.fh, "# execute", path
        with open(path, "r") as fp:
            cmd = fp.read()
            if self.fh is not None:
                print >> self.fh, cmd
            self.session(cmd)
        if self.fh is not None:
            print >> self.fh, "#", 60 * "="
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
        if hasattr(self, session):
            value = getattr(self.session, name)
            if convert_to_table and isinstance(value, pandas.DataFrame):
                return Table.from_pandas(value)
            return value

    def __setattr__(self, name, value):
        if isinstance(value, Table):
            value = value.to_pandas()
        setattr(self.session, name, value)
