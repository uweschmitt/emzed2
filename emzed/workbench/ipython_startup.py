
from emzed.core.config import _UserConfig

_c = _UserConfig(_no_load=True)
if _c.load() is False:
    _c.edit()

import emzed.updaters

emzed.updaters.check_emzed_updates()
emzed.updaters.print_update_status()

import emzed.abundance
import emzed.adducts
import emzed.align
import emzed.batches
import emzed.db
import emzed.elements
import emzed.gui
import emzed.stats
import emzed.utils

