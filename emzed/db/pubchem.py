from ..core import updaters
from ..core.data_bases.pubchem_db import *
from ..core import config


def init_pubchem(data_home=None, exchange_folder=None):
    # init db and install updater
    if data_home is None:
        data_home = config.folders.getDataHome()
    if exchange_folder is None:
        exchange_folder = config.folders.getExchangeSubFolder(None)

    if not os.path.exists(data_home):
        os.makedirs(data_home)
    if exchange_folder is not None and not os.path.exists(exchange_folder):
        os.makedirs(exchange_folder)

    pc_updater = updaters.Updater(PubChemUpdateImpl, data_home, exchange_folder)
    updaters.registry.register(pc_updater)
    return pc_updater.impl.db
