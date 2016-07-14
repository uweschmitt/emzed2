# encoding: utf-8, division
from __future__ import print_function, division

import emzed
import os.path



def handler_1(table):
    table.rows = table.rows[1:]
    return table


def handler_2(table):
    table.rows = table.rows[:1]
    return table


here = os.path.dirname(os.path.abspath(__file__))
emzed.gui.inspect(os.path.join(here, "calibration_patterns.table"),
                  custom_buttons_config=[("Delete first row", handler_1),
                                         ("keep only first row", handler_2)])
