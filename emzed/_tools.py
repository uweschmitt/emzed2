

def runs_inside_emzed_console():
    import emzed
    return getattr(emzed, "_emzed_runs_inside", "") == "emzed.console"


def runs_inside_emzed_workbench():
    import emzed
    return getattr(emzed, "_emzed_runs_inside", "") == "emzed.workbench"


def gui_running():
    from PyQt4.QtGui import QApplication
    return QApplication.instance() is not None


def is_first_start():
    from emzed.core.config import _UserConfig
    import os
    return not os.path.exists(_UserConfig.config_file_path())
