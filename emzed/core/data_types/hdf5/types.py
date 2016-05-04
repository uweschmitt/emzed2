# encoding: utf-8, division
from __future__ import print_function, division

from ..col_types import CheckState
from tables import Int64Col, Float64Col, BoolCol

basic_type_map = {int: Int64Col, long: Int64Col, float: Float64Col, bool: BoolCol,
                    CheckState: BoolCol}
