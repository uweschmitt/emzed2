import os, sys
import functools


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
