# encoding: latin-1

# keep namespace clean:

import guidata.dataset.datatypes as _dt
import guidata.dataset.dataitems as _di
import os
import types
import functools
import sys

from .. import version


def _linuxdefault(path):
    def wrapper(fun, path=path):
        @functools.wraps(fun)
        def new_fun():
            if sys.platform == "win32":
                return fun()
            else:
                return path
        return new_fun
    return wrapper


class _FolderLocations(object):

    @staticmethod
    def _query(subKey):
        import _winreg
        key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
                              "Software\\Microsoft\\Windows\\CurrentVersion"
                              "\\Explorer\\User Shell Folders")
        val, _ = _winreg.QueryValueEx(key, subKey)
        return _winreg.ExpandEnvironmentStrings(val)

    # order of decorators counts
    @staticmethod
    @_linuxdefault(os.environ.get("HOME"))
    def getDocumentFolder():
        return _FolderLocations._query("Personal")

    # order of decorators counts
    @staticmethod
    @_linuxdefault(os.environ.get("HOME"))
    def getAppDataFolder():
        return _FolderLocations._query("AppData")

    # order of decorators counts
    @staticmethod
    @_linuxdefault(os.environ.get("HOME"))
    def getLocalAppDataFolder():
        return _FolderLocations._query("Local AppData")

    @staticmethod
    def getEmzedFolder():
        if sys.platform == "win32":
            return os.path.join(_FolderLocations.getAppDataFolder(), "emzed2")
        else:
            return os.path.join(_FolderLocations.getAppDataFolder(), ".emzed2")

    @staticmethod
    def getDataHome():
        default = os.path.join(_FolderLocations.getDocumentFolder(), "emzed2_files")
        folder = global_config.get("emzed_files_folder")
        return folder or default

    @staticmethod
    def getDataHomeSubFolder(subfolder=None):
        data_home = _FolderLocations.getDataHome()
        if subfolder is not None:
            data_home = os.path.join(data_home, subfolder)
        return data_home

    @staticmethod
    def getExchangeSubFolder(subfolder=None):
        folder = global_config.get("exchange_folder")
        if folder:
            if subfolder is not None:
                folder = os.path.join(folder, subfolder)
            try:
                if not os.path.exists(folder):
                    os.makedirs(folder)
                os.stat(folder)
            except:
                # not reachable, may happen for network folders
                return None
            return folder
        # no global exchange folder set, use local folder instead:
        return None

    @staticmethod
    def getVersionedExchangeFolder():
        return _FolderLocations.getExchangeSubFolder(version.version)

folders = _FolderLocations


_is_expert = _dt.ValueProp(False)


def _apply_patch_for_allowing_empty_value(diretory_item):
    def check_value(self, value):
        if not value:
            return True
        return _di.DirectoryItem.check_value(self, value)
    # subclassing _di.DirectoryItem does not work as guidata does some lookup based
    # on "typc(xxx)" for DataItems. So we replace the corresponding method:
    diretory_item.check_value = types.MethodType(check_value, diretory_item, _di.DirectoryItem)


class _UserConfig(object):

    class Parameters(_dt.DataSet):

        """ EMZED CONFIGURATION DIALOG

        Please provide data requested below. You can open this dialog and modify data
        later running 'emzed.config.edit()'.
        """

        g1 = _dt.BeginGroup("User Settings")

        user_name = _di.StringItem("Full Name",
                                   notempty=True,
                                   default="",
                                   help="needed for submitting to package store")

        user_email = _di.StringItem("Email Adress",
                                    notempty=True,
                                    default="",
                                    help="needed for submitting to package store")

        user_url = _di.StringItem("Website URL",
                                  help="usefull when submitting to package store")

        project_home = _di.DirectoryItem("Folder for emzed projects",
                                         default="",
                                         help="here you can configure a folder in which emzed package projects "
                                         "will be created")
        _apply_patch_for_allowing_empty_value(project_home)

        _g1 = _dt.EndGroup("User Settings")

        g11 = _dt.BeginGroup("Folder Settings")

        exchange_folder = _di.DirectoryItem("Exchange Folder", default="",
                                            help="here you can configure a shared folder, see emezed "
                                            "installation guide on emzed website for more information")

        emzed_files_folder = _di.DirectoryItem("Emzed data files", default="",
                                            help="place for installing data files etc")


        _apply_patch_for_allowing_empty_value(exchange_folder)

        _g11 = _dt.EndGroup("Folder Settings")

        g2 = _dt.BeginGroup("Webservice Settings")

        metlin_token = _di.StringItem("Metlin SOAP Token",
                                      help="needed for metlin matching. you can request this "
                                      "token from metlins website")

        _g2 = _dt.EndGroup("Webservice Settings")

        g3 = _dt.BeginGroup("Emzed Store User Account")

        emzed_store_user = _di.StringItem("User Name",
                                          help="please request name and password from emzed google group")
        emzed_store_password = _di.StringItem("User Password",
                                              help="please request name and password from emzed google group")

        _g3 = _dt.EndGroup("Emzed Store Settings")

        g4 = _dt.BeginGroup("Emzed Store Expert Settings")
        enable_expert_settings = _di.BoolItem("Enable Settings",
                                              help="only check this box if you really know what you do !!!"
                                              ).set_prop("display", store=_is_expert)

        emzed_store_url = _di.StringItem("Emzed Store URL").set_prop("display",
                                                                     active=_is_expert)

        pypi_url = _di.StringItem("PyPi URL").set_prop("display",
                                                       active=_is_expert)
        pypi_index_url = _di.StringItem("PyPi Index URL").set_prop("display",
                                                       active=_is_expert)

        _g4 = _dt.EndGroup("Expert Settings")

        g5 = _dt.BeginGroup("Internal Settings")

        last_active_project = _di.StringItem(
            "Last active project").set_prop("display", active=False)

        _g5 = _dt.EndGroup("Internal Settings")

    def __init__(self, *a, **kw):
        self.parameters = _UserConfig.Parameters()

    def get(self, key, default=None):
        env_key = "EMZED_%s" % key.upper()
        if env_key in os.environ:
            val = os.environ.get(env_key, default)
        else:
            val = getattr(self.parameters, key, default)
        if isinstance(val, unicode):
            val = val.encode("latin-1")
        return val

    def set_(self, key, value):
        setattr(self.parameters, key, value)
        global global_config
        global_config = self

    def get_url(self, key):
        val = self.get(key)
        if val is not None:
            val = val.rstrip("/")
        return val

    def store(self, path=None):

        import os

        # path UserConfig for not writing to ~/.config/.none.ini as default:
        import guidata.userconfig
        __save = guidata.userconfig.UserConfig.__save
        try:
            guidata.userconfig.UserConfig.__save = lambda self: None
            if path is None:
                path = _UserConfig.config_file_path()
            cf = guidata.userconfig.UserConfig(dict())
            self.parameters.write_config(cf, "emzed2", "")
            dir_name = os.path.dirname(path)
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
            with open(path, "wt") as fp:
                cf.write(fp)
        finally:
            # undo patch
            guidata.userconfig.UserConfig.__save = __save

    def load(self, path=None):
        import os
        import guidata.userconfig
        cf = guidata.userconfig.UserConfig(dict())
        if path is None:
            path = _UserConfig.config_file_path()
        if os.path.exists(path):
            with open(path, "rt") as fp:
                try:
                    cf.readfp(fp)
                    self.parameters.read_config(cf, "emzed2", "")
                    return True
                except:
                    pass
        return False

    def check_fields(self):
        if sys.platform == "win32":
            if self.parameters.project_home.startswith("\\\\"):
                return (False, "UNC network pathes are not allowed for project home\n"
                               "Mount this UNC path as a drive and use this instead.")
        return True, ""

    def edit(self):
        import guidata
        from guidata.qt.QtGui import QMessageBox
        app = guidata.qapplication()
        while True:
            aborted = self.parameters.edit(size=(600, 800)) == 0
            if not aborted:
                ok, msg = self.check_fields()
                if not ok:
                    QMessageBox.warning(None, "Error", msg)
                    continue
                global global_config
                global_config = self
            break
        return aborted

    @staticmethod
    def config_file_path():
        return os.path.join(folders.getEmzedFolder(), "config_emzed2.ini")

    def set_defaults(self):
        self.parameters.emzed_store_url = ""
        self.parameters.pypi_url = "https://pypi.python.org/pypi"
        self.parameters.pypi_index_url = "https://pypi.python.org/simple"
        self.parameters.project_home = os.path.join(folders.getDataHome(), "emzed_projects")
        self.parameters.last_active_project = ""
        self.parameters.emzed_files_folder = os.path.join(_FolderLocations.getDocumentFolder(),
                                                          "emzed2_files")
        try:
            os.makedirs(self.parameters.project_home)
        except:
            pass

global_config = _UserConfig()
