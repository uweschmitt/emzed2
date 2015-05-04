# encoding: utf-8

from emzed.core.patch_utils import replace, add
import os

_here = os.path.abspath(os.path.dirname(__file__))
_path_to_emzed_startup = os.path.join(_here, "startup.py")
_path_to_emzed_ipython_startup = os.path.join(_here, "ipython_startup.py")


def patch_spyderlib():

    patch_qt_version_check()

    patch_baseconfig()
    # patches default config values for first startup
    # including path to startup.py for "normal" python console:
    patch_userconfig()

    # the following patch must appear before patching Externalshell, as the
    # corresponding import of ExternalConsole implies import of baseshell. So
    # patching baseshell will not work, as it is registered in sys.modules in
    # unpatched version !

    # patches python path, so that external IPython shell loads patched
    # sitecustomize.py
    patch_baseshell()

    # patch dialogs for emzed specific types:
    patch_RemoteDictEditorTableView()
    patch_NamespaceBrowser()


def patch_RemoteDictEditorTableView():

    from spyderlib.widgets.dicteditor import (RemoteDictEditorTableView,
                                              BaseTableView)

    @replace(RemoteDictEditorTableView.edit_item, verbose=True)
    def patch(self):
        if self.remote_editing_enabled:
            index = self.currentIndex()
            if not index.isValid():
                return
            key = self.model.get_key(index)
            if (self.is_list(key) or self.is_dict(key)
                    or self.is_array(key) or self.is_image(key)):
                # If this is a remote dict editor, the following avoid
                # transfering large amount of data through the socket
                self.oedit(key)
            # START MOD EMZED
            elif self.is_peakmap(key) or self.is_table(key) or\
                    self.is_tablelist(key):
                self.oedit(key)
            # END MOD EMZED
            else:
                BaseTableView.edit_item(self)
        else:
            BaseTableView.edit_item(self)


def patch_NamespaceBrowser():

    from spyderlib.widgets.externalshell.monitor import communicate
    from spyderlib.widgets.externalshell.namespacebrowser import NamespaceBrowser

    @add(NamespaceBrowser, verbose=True)
    def is_peakmap(self, name):
        """Return True if variable is a PeakMap"""
        return communicate(self._get_sock(),
                           "isinstance(globals()['%s'], emzed.core.data_types.PeakMap)" % name)

    @add(NamespaceBrowser, verbose=True)
    def is_table(self, name):
        """Return True if variable is a PeakMap"""
        return communicate(self._get_sock(),
                           "isinstance(globals()['%s'], emzed.core.data_types.Table)" % name)

    @add(NamespaceBrowser, verbose=True)
    def is_tablelist(self, name):
        """Return True if variable is a PeakMap"""
        return communicate(self._get_sock(),
                           "isinstance(globals()['%s'], list) "
                           "and all(isinstance(li, emzed.core.data_types.Table)"
                           "        for li in globals()['%s'])" % (name, name))

    @replace(NamespaceBrowser.setup, verbose=True)
    def setup(self, *a, **kw):
        NamespaceBrowser._orig_setup(self, *a, **kw)
        self.editor.is_peakmap = self.is_peakmap
        self.editor.is_table = self.is_table
        self.editor.is_tablelist = self.is_tablelist

    @replace(NamespaceBrowser.import_data, verbose=True)
    def import_data(self, filenames=None):
        NamespaceBrowser._orig_import_data(self, filenames)
        self.save_button.setEnabled(self.filename is not None)

    @add(NamespaceBrowser, verbose=True)
    def get_remote_view_settings(self):
        """Return dict editor view settings for the remote process,
        but return None if this namespace browser is not visible (no need
        to refresh an invisible widget...)"""
        if self.is_visible and self.isVisible():
            return self.get_view_settings()


def patch_baseshell():

    # modifies assembly of PYTHONPATH before starting the external
    # shell in spyderlib\widgets\externalshell\pythonshell.py
    # so the sitecustomize will be loaded from patched_modules\
    # and not from spyderlib\widgets\externalshell\

    print "patch baseshell"

    import spyderlib.widgets.externalshell.baseshell as baseshell

    @replace(baseshell.add_pathlist_to_PYTHONPATH, verbose=True)
    def patched(env, pathlist, _here=_here):
        for i, p in enumerate(pathlist):
            # replace path to ../externalshell/ (which contains
            # sitecustomize.py) with path to patched_modules/
            # print >> fp, i, p
            if p.rstrip("/").endswith("externalshell"):
                pathlist[i] = _here
        baseshell._orig_add_pathlist_to_PYTHONPATH(env, pathlist)


def patch_userconfig():

    # patching the default settings for the first start is not easy,
    # as defaults are set in spyderlib.config during the first import
    # and the constructor of spyderlib.userconfig.UserConfig saves
    # them immediately.

    # this works:
    import spyderlib.userconfig

    @replace(spyderlib.userconfig.get_home_dir)
    def patched():
        """
        Return user home directory
        """
        import os.path as osp
        from spyderlib.utils import encoding
        for env_var in ('APPDATA', 'USERPROFILE', 'HOME', 'TMP'):
            # os.environ.get() returns a raw byte string which needs to be
            # decoded with the codec that the OS is using to represent environment
            # variables.
            path = encoding.to_unicode_from_fs(os.environ.get(env_var, ''))
            if osp.isdir(path):
                break
        if path:
            return path
        try:
            # expanduser() returns a raw byte string which needs to be
            # decoded with the codec that the OS is using to represent file paths.
            path = encoding.to_unicode_from_fs(osp.expanduser('~'))
            return path
        except:
            raise RuntimeError('Please define environment variable $HOME')

    from spyderlib.userconfig import UserConfig

    class MyConfig(UserConfig):

        # save this, else we get a recursion below
        __orig_base_class = UserConfig

        def __init__(self, name, defaults, *a, **kw):
            __my_defaults = {
                "console":
                            {"pythonstartup/default": False,
                             "pythonstartup/custom": True,
                             "pythonstartup": _path_to_emzed_startup,
                             "object_inspector": False,
                             "open_python_at_startup": False,
                             "open_ipython_at_startup": True,
                             "start_ipython_kernel_at_startup": False,
                             "ipython_options": "-q4thread -colors LightBG",
                             },

                # "ipython_console":
                # {
                # "open_ipython_at_startup"  : True,
                # "startup/run_file" : _path_to_emzed_ipython_startup,
                # "startup/use_run_file" : True,
                # },
                #
                "inspector":
                {"automatic_import": False,  # faster !
                 },
                "variable_explorer":
                {"remote_editing": True,
                 },
                "editor":
                # paranthesis closing is annoying
                {
                    "close_parentheses": False,
                    "outline_explorer": True,
                    "object_inspector": True,
                    "edge_line_column": 99,
                    },
            }
            for section, settings in defaults:
                override = __my_defaults.get(section)
                if override:
                    settings.update(override)

            # using UserConfig.__init__ would recurse here as we set UserConfig = MyConfig below !
            MyConfig.__orig_base_class.__init__(self, name, defaults, *a, **kw)

    import spyderlib.userconfig
    spyderlib.userconfig.UserConfig = MyConfig


def patch_qt_version_check():
    # spyderlib.requirements.check_qt in  2.1.X is broken for Qt4 verion 4.4.10 and above
    # this is fixed in the latest spyderlib versions, but we have to fix this because
    # we stick to spyderlib 2.1.3 with its integration of IPython 0.10.
    def check_qt():
        """Check Qt binding requirements"""
        print "this is the patched spyderlib.requirements.check_qt function"
        from distutils.version import LooseVersion
        qt_infos = dict(pyqt=("PyQt4", "4.4"), pyside=("PySide", "1.1.1"))
        try:
            from spyderlib import qt
            package_name, required_ver = qt_infos[qt.API]
            actual_ver = qt.__version__
            if LooseVersion(actual_ver) < LooseVersion(required_ver):
                show_warning("Please check Spyder installation requirements:\n"
                             "%s %s+ is required (found v%s)."
                             % (package_name, required_ver, actual_ver))
            print "Qt version", actual_ver, "passed version test"
        except ImportError:
            show_warning("Please check Spyder installation requirements:\n"
                         "%s %s+ (or %s %s+) is required."
                         % (qt_infos['pyqt']+qt_infos['pyside']))

    import spyderlib.requirements
    spyderlib.requirements.check_qt = check_qt


def patch_baseconfig():
    from spyderlib import baseconfig

    # Opening an IPYTHON shell does not use the configures startup.py
    # which we see in spyder.ini, but locate starup.py inside the
    # the directory where spyderlib.widgets.externalshell resides.
    # So we fool ExternalPythonShell in widgets/externalshell/pythonshell.py
    # by patching baseconfig.get_module_source_path:

    @replace(baseconfig.get_module_source_path, verbose=True)
    def patch(modname, basename=None):
        if modname == "spyderlib.widgets.externalshell"\
                and basename == "startup.py":
            return _path_to_emzed_startup
        return baseconfig._orig_get_module_source_path(modname, basename)
