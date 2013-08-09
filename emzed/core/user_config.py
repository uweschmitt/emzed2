import os, sys
import ConfigParser
import functools

from .. import version


class _GlobalConfig(object):

    def __init__(self):
        emzedFolder = getEmzedFolder()
        if not os.path.exists(emzedFolder):
            os.makedirs(emzedFolder)
        self.configFilePath=os.path.join(emzedFolder, "global.ini")
        if not os.path.exists(self.configFilePath):
            self.exchangeFolder = None
            self.metlinToken = None
            self.editConfig()
        else:
            p = ConfigParser.ConfigParser()
            p.readfp(open(self.configFilePath))
            self.exchangeFolder = p.get("DEFAULT", "exchange_folder")
            if p.has_option("DEFAULT", "metlin_token"):
                self.metlinToken = p.get("DEFAULT", "metlin_token")
            else:
                self.metlinToken = None
                self.editConfig()

    def getExchangeFolder(self):
        return self.exchangeFolder

    def getMetlinToken(self):
        return self.metlinToken

    def setMetlinToken(self, token):
        self.metlinToken = token
        self.saveConfig()

    def editConfig(self):
        import guidata

        app = guidata.qapplication() # singleton !

        import guidata.dataset.datatypes as dt
        import guidata.dataset.dataitems as di

        def check_value(self, value):
            if not isinstance(value, self.type):
                return False
            if str(value).strip()=="":
                return True
            return di.DirectoryItem._check_value(self, value)

        di.DirectoryItem._check_value = di.DirectoryItem.check_value
        di.DirectoryItem.check_value = check_value
        class ConfigEditor(dt.DataSet):
            """ ConfigEditor

                Please provide a global exchange folder for databases,
                scripts and configs shared among your lab.

                If you do not have such an exchange folder, leave the
                field empty.

                You need a metlin token for accessing the metlin
                web service. To register for this token go to

                    http://metlin.scripps.edu/soap/register.php

                You can leave this field empty.

                If you want to modify these values later, enter

                >>> import userConfig
                >>> userConfig.setMetlinToken("....")

            """
            exchangeFolder = di.DirectoryItem("Global exchange folder:",
                    notempty=False, default=self.exchangeFolder or "")
            metlinToken = di.StringItem("Metlin token:",
                    default = self.metlinToken or "")

        dlg = ConfigEditor()
        dlg.edit()
        self.exchangeFolder = dlg.exchangeFolder
        self.metlinToken = dlg.metlinToken
        di.DirectoryItem.check_value = di.DirectoryItem._check_value
        self.saveConfig()

    def saveConfig(self):
        p = ConfigParser.ConfigParser()
        p.set("DEFAULT", "exchange_folder", self.exchangeFolder or "")
        p.set("DEFAULT", "metlin_token", self.metlinToken or "")
        p.write(open(self.configFilePath, "w"))


def userShellFolderKey():
    import _winreg
    key =_winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
                        "Software\\Microsoft\\Windows\\CurrentVersion"
                        "\\Explorer\\User Shell Folders")
    return key

def _query(key, subKey):
    import _winreg
    val, _ = _winreg.QueryValueEx(key, subKey)
    return _winreg.ExpandEnvironmentStrings(val)

def linuxdefault(path):
    def wrapper(fun, path=path):
        @functools.wraps(fun)
        def new_fun():
            if sys.platform == "win32":
                return fun()
            else:
                return path
        return new_fun
    return wrapper


@linuxdefault(os.environ.get("HOME"))
def getDocumentFolder():
    key = userShellFolderKey()
    return _query(key, "Personal")

@linuxdefault(os.environ.get("HOME"))
def getAppDataFolder():
    key = userShellFolderKey()
    return _query(key, "AppData")

@linuxdefault(os.environ.get("HOME"))
def getLocalAppDataFolder():
    key = userShellFolderKey()
    return _query(key, "Local AppData")

def getEmzedFolder():
    if sys.platform == "win32":
        return os.path.join(getAppDataFolder(), "emzed")
    else:
        return os.path.join(getAppDataFolder(), ".emzed")


def getDataHome():
    dataHome = os.path.join(getDocumentFolder(), "emzed_files")
    return dataHome

#def getExchangeFolder():
#    import warnings
#    warnings.warn("getExchangeFolder is depreciated. Please use"\
#    " getVersionedExchangeFolder() instead")
#    return getVersionedExchangeFolder()

def getExchangeSubFolder(subfolder):
    folder = _GlobalConfig().getExchangeFolder()
    if folder:
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
    folder = os.path.join(getDataHome(), "shared")
    folder = os.path.join(folder, subfolder)
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder

def getTablesExchangeFolder():
    return getExchangeSubFolder("tables_1.3.2_or_newer")

def getVersionedExchangeFolder():
    return getExchangeSubFolder(version.version)

def getScriptsExchangeFolder():
    return getExchangeSubFolder("scripts_%s" % version.version)

def getMetlinToken():
    return _GlobalConfig().getMetlinToken()

def setMetlinToken(token):
    return _GlobalConfig().setMetlinToken(token)

# maintains state between setRVersion and getRVersion:"
_pseudo_globals = dict()

def setRVersion(r_version, g=_pseudo_globals):
    g["R_VERSION"] = r_version

def getRLibsFolder(g=_pseudo_globals):
    r_version = g.get("R_VERSION")
    if r_version is None:
        return getExchangeSubFolder("r_libs")

    return getExchangeSubFolder("r_libs_%s" % r_version)
    #return getExchangeFolder("r_libs_3")
    root = getVersionedExchangeFolder()
    if root is None:
        return None
    return os.path.join(root, "r_libs")
