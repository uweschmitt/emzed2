# encoding: utf-8, division
from __future__ import print_function, division

from functools import partial
import os.path

import emzed


def handler_1(table):
    table.rows = table.rows[1:]
    return table


def handler_2(table):
    table.rows = table.rows[:1]
    return table


here = os.path.dirname(os.path.abspath(__file__))

"""
emzed.gui.inspect(os.path.join(here, "calibration_patterns.table"),
                  custom_buttons_config=[("Delete first row", handler_1),
                                         ("keep only first row", handler_2)])

"""

def activate(flag, table):
    table.replaceColumn("check", flag)

handler_1 = partial(activate, True)
handler_2 = partial(activate, False)

t = emzed.io.Hdf5TableProxy(os.path.join(here, "test_1000000.hdf5"))
emzed.gui.inspect(t,  # os.path.join(here, "calibration_patterns.table"),
                  custom_buttons_config=[("check all", handler_1),
                                         ("unchech_all", handler_2)])
