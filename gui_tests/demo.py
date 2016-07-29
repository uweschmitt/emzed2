# encoding: utf-8, division
from __future__ import print_function, division

import logging
logger = logging.getLogger('simple_example')
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)


logger.debug("start import emzed")

import emzed
from emzed.core.data_types.hdf5_table_proxy import Hdf5TableProxy

logger.debug("open hdf5 file")
t = Hdf5TableProxy("../../../tmp/adf0ab693d8e9518db265f8d5c482be1bf08633e.hdf5")
logger.debug("opened hdf5 file")

logger.debug("open inspector")
emzed.gui.inspect(t)
t.close()

