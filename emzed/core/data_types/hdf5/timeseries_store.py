# encoding: utf-8, division
from __future__ import print_function, division


from datetime import datetime

from tables import Atom, UInt32Col, StringCol, BoolCol
import numpy as np

from ..col_types import TimeSeries

from .store_base import Store, filters
from .lru import LruDict

from .install_profile import profile


class TimeSeriesStore(Store):

    ID_FLAG = 1
    HANDLES = TimeSeries

    def __init__(self, file_, node=None, **kw):
        self.file_ = file_
        self.node = node
        if not hasattr(node, "ts_x_values"):
            self.setup()

        self.x_blob = self.node.ts_x_values
        self.y_blob = self.node.ts_y_values
        self.bp = self.node.bp
        self.ts_index = self.node.ts_index

        self.next_index = self.ts_index.nrows

        self.write_cache = LruDict(100)
        self.read_cache = LruDict(100)

    def setup(self):

        self.x_blob = self.file_.create_earray(self.node, "ts_x_values",
                                               Atom.from_dtype(np.dtype("int64")), (0,),
                                               filters=filters)

        self.y_blob = self.file_.create_earray(self.node, "ts_y_values",
                                               Atom.from_dtype(np.dtype("float64")), (0,),
                                               filters=filters)

        self.bp = self.file_.create_earray(self.node, "bp",
                                           Atom.from_dtype(np.dtype("int32")), (0,),
                                           filters=filters)

        description = {}
        description["unique_id"] = StringCol(itemsize=64, pos=0)
        description["index"] = UInt32Col(pos=1)
        description["blank_flags_is_none"] = BoolCol(pos=2)
        description["label"] = StringCol(itemsize=32, pos=3)
        description["start"] = UInt32Col(pos=4)
        description["size"] = UInt32Col(pos=5)

        description["bp_start"] = UInt32Col(pos=6)
        description["bp_size"] = UInt32Col(pos=7)

        self.ts_index = self.file_.create_table(self.node, "ts_index", description,
                                                filters=None)

        # every colums which appears in a where method call should/must be indexed !
        # this is not only for performance but for correct lookup as well (I had strange bugs
        # else)
        self.ts_index.cols.unique_id.create_index()
        self.ts_index.cols.index.create_index()

    def _write(self, col_index, obj):

        unique_id = obj.uniqueId()
        yield unique_id

        result = list(self.ts_index.where("""unique_id == %r""" % unique_id))
        if result:
            yield result[0]["index"]

        start = self.x_blob.nrows
        size = len(obj.x)

        # transform missing values to -1 which is not possible for int representation of
        # dates:
        xvals = [xi.toordinal() if xi is not None else -1 for xi in obj.x]

        self.x_blob.append(xvals)
        self.y_blob.append(obj.y)

        bp_start = self.bp.nrows
        if obj.is_blank is None:
            bp_size = 0
        else:
            blank_positions = [i for (i, f) in enumerate(obj.is_blank) if f]
            self.bp.append(blank_positions)
            bp_size = len(blank_positions)

        row = self.ts_index.row
        row["unique_id"] = unique_id
        row["label"] = obj.label or ""
        row["blank_flags_is_none"] = obj.is_blank is None
        row["index"] = self.next_index
        row["start"] = start
        row["size"] = size
        row["bp_start"] = bp_start
        row["bp_size"] = bp_size
        row.append()

        next_index = self.next_index
        self.next_index += 1
        yield next_index

    def _read(self, col_index, index):
        result = list(self.node.ts_index.where("""index == %r""" % index))
        if len(result) == 0:
            raise ValueError("index %d not in table" % index)

        assert len(result) == 1
        row = result[0]
        label = row["label"]
        start = row["start"]
        size = row["size"]
        bp_start = row["bp_start"]
        bp_size = row["bp_size"]
        blank_flags_is_none = row["blank_flags_is_none"]

        x = self.x_blob[start:start + size]

        x = [datetime.fromordinal(xi) if xi >= 0 else None for xi in x]

        y = self.y_blob[start:start + size]
        blank_pos = self.bp[bp_start:bp_start + bp_size]

        if blank_flags_is_none:
            is_blank = None
        else:
            is_blank = [i in blank_pos for i in range(len(x))]

        ts = TimeSeries(x, y, label, is_blank)
        return ts

    def dump(self):
        names = self.node.ts_index.colnames
        import emzed
        t = emzed.core.Table(names, [object] * len(names), ["%s"] * len(names), rows=[])
        tsi = []
        for row in self.node.ts_index:
            t.addRow(list(row.fetch_all_fields()))
            tsi.append(self._read(None, row["index"]))

        t.resetInternals()
        yvals = ["%s..%s" % (min(ti.y), max(ti.y)) for ti in tsi]
        t.addColumn("y", yvals, type_=object)
        print(t)

    def flush(self):
        self.x_blob.flush()
        self.y_blob.flush()
        self.bp.flush()
        self.ts_index.flush()
