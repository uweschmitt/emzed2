
def is_started_as_emzed_console():

    if "__emzed_imported_by" in globals():
        return __emzed_imported_by == "emzed.console"
    return False

def is_started_as_emzed_workbench():

    if "__emzed_imported_by" in globals():
        return __emzed_imported_by == "emzed.workbench"
    return False


def gui_running():
    from PyQt4.QtGui import QApplication
    return QApplication.instance() is not None


def is_first_start():
    from emzed.core.config import _UserConfig
    import os
    return not os.path.exists(_UserConfig.config_file_path())
