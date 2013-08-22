
from emzed.core.config import _UserConfig

def _is_first_start():
    _c = _UserConfig(_no_load=True)
    return _c.load() is False

def edit():
    _c = _UserConfig()
    aborted = _c.edit()


