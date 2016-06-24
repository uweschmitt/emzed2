# encoding: utf-8, division
from __future__ import print_function, division

from ..col_types import CheckState
from tables import Int64Col, Float64Col, BoolCol

basic_type_map = {int: Int64Col, long: Int64Col, float: Float64Col, bool: BoolCol,
                  CheckState: BoolCol}

none_replacements = {int: 0, long: 0, float: 0.0, bool: False, CheckState: False}


assert set(basic_type_map.keys()) == set(none_replacements.keys()), "broken setup in types.py"
