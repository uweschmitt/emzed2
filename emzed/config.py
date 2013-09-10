from emzed.core.config import _UserConfig, global_config


def _is_first_start():
    import os
    return not os.path.exists(_UserConfig.config_file_path())


def edit(reset_to_defaults=False):
    if reset_to_defaults:
        global_config.set_defaults()
    aborted = global_config.edit()
    if not aborted:
        global_config.store()

def load():
    global_config.load()

