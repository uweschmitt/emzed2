
def is_started_from_cmdline():

    import inspect
    info = inspect.stack()[-1][1]
    result = False
    if info != "<string>":
        if info.endswith("emzed.workbench"):
            result = True
    return result


def gui_running():
    from PyQt4.QtGui import QApplication
    return QApplication.instance() is not None


def is_first_start():
    from emzed.core.config import _UserConfig
    import os
    return not os.path.exists(_UserConfig.config_file_path())
