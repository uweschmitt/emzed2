# encoding: utf-8, division
from __future__ import print_function, division

from collections import defaultdict
import itertools


from tables import open_file, Filters, Int64Col, Float64Col, BoolCol, UInt64Col, UInt32Col

from .store_manager import setup_manager
from .stores import ObjectProxy
from .lru import LruDict


filters = Filters(complib="blosc", complevel=9)


class Hdf5Base(object):

    basic_type_map = {int: Int64Col, long: Int64Col, float: Float64Col, bool: BoolCol}

    def _initial_setup(self, path, mode):
        self.file_ = open_file(path, mode)
        self.manager = setup_manager(self.file_)

    def close(self):
        self.manager.close()


class Hdf5TableWriter(Hdf5Base):

    def __init__(self, path):
        self._initial_setup(path, "w")
        self.row_offset = 0

    def write_table(self, table):

        self._setup_for_table(table)
        self._add_rows(table)

    def _setup_for_table(self, table):

        file_ = self.file_
        self.meta_table = file_.create_table(file_.root, "meta_index",
                                             description=dict(index=UInt64Col()),
                                             filters=filters)

        self.missing_values_table = file_.create_table(file_.root, "missing_values",
                                                       description=dict(row_index=UInt64Col(pos=0),
                                                                        col_index=UInt64Col(pos=1)),
                                                       filters=filters)

        def store_meta(what):
            meta_index = self.manager.store_object(what)
            row = self.meta_table.row
            row["index"] = meta_index
            row.append()

        col_names = table.getColNames()
        col_types = table.getColTypes()
        col_formats = table.getColFormats()

        store_meta(table.meta)
        store_meta(col_names)
        store_meta(col_types)
        store_meta(col_formats)

        self.meta_table.flush()

        description = {}
        for (pos, name, type_) in zip(itertools.count(), col_names, col_types):
            tables_type = self.basic_type_map.get(type_)
            if tables_type is None:
                tables_type = UInt32Col
            description[name] = tables_type(pos=pos)

        self.row_table = file_.create_table(file_.root, "rows", description=description,
                                            filters=filters)

    def _add_rows(self, table):

        col_names = table.getColNames()
        col_types = table.getColTypes()

        for row_index, row in enumerate(table.rows):
            hdf_row = self.row_table.row
            for col_index, value, name, type_ in zip(itertools.count(), row, col_names, col_types):
                if value is None:
                    m_row = self.missing_values_table.row
                    m_row["row_index"] = row_index + self.row_offset
                    m_row["col_index"] = col_index
                    m_row.append()
                else:
                    if type_ in self.basic_type_map:
                        hdf_row[name] = value
                    else:
                        hdf_row[name] = self.manager.store_object(value)
            hdf_row.append()

        self.row_offset += len(table)

        self.missing_values_table.flush()
        self.row_table.flush()
        self.manager.finalize()


class Hdf5TableReader(Hdf5Base):

    def __init__(self, path):
        self._initial_setup(path, "r")
        self._load_meta()
        self.row_cache = LruDict(10000)
        self.col_cache = LruDict(100)

    def _load_meta(self):

        rows = iter(self.file_.root.meta_index)

        meta_index = rows.next()["index"]
        self.meta = self.manager.fetch(meta_index).load()

        col_names_index = rows.next()["index"]
        self.col_names = self.manager.fetch(col_names_index).load()

        col_types_index = rows.next()["index"]
        self.col_types = self.manager.fetch(col_types_index).load()

        col_formats_index = rows.next()["index"]
        self.col_formats = self.manager.fetch(col_formats_index).load()

        # read full table -> numpy array -> list -> set
        self.missing_values_table = self.file_.root.missing_values
        self.missing_values = set(self.missing_values_table.read().tolist())
        self.missing_values_in_column = defaultdict(set)

        idx_to_name = dict(enumerate(self.col_names))
        for (ridx, cidx) in self.missing_values:
            self.missing_values_in_column[idx_to_name[cidx]].add(ridx)

        self.row_table = self.file_.root.rows
        self.nrows = self.file_.root.rows.nrows

    def fetch_row(self, index):
        if index in self.row_cache:
            return self.row_cache[index]
        values = self.row_table[index].tolist()
        basic_types = {int, long, float, bool}
        row = []
        for (col_idx, value, type_) in zip(itertools.count(), values, self.col_types):
            if (index, col_idx) in self.missing_values:
                value = None
            elif type_ not in basic_types:
                value = self.manager.fetch(value)
            row.append(value)
        self.row_cache[index] = row
        return row

    def __len__(self):
        return self.nrows

    __getitem__ = fetch_row

    def get_col_values(self, col_name):
        if col_name in self.col_cache:
            return self.col_cache[col_name]
        missing = self.missing_values_in_column[col_name]
        col_values = getattr(self.row_table.cols, col_name)[:]
        if missing:
            col_values = col_values.tolist()
            for ridx in missing:
                col_values[ridx] = None
        self.col_cache[col_name] = col_values
        return col_values


class Hdf5TableAppender(Hdf5TableWriter, Hdf5TableReader):

    def __init__(self, path):
        self._initial_setup(path, "a")
        self._load_meta()
        self.row_offset = self.nrows

    def write_table(self, table):
        raise NotImplementedError("makes no sense for appending, use append_table method instead")

    def append_table(self, table):

        assert table.getColNames() == self.col_names, "table does not match to exisiting table"
        assert table.getColFormats() == self.col_formats, "table does not match to exisiting table"
        assert table.getColTypes() == self.col_types, "table does not match to exisiting table"

        self._add_rows(table)
