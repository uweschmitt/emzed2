# encoding: utf-8, division
from __future__ import print_function, division

from collections import defaultdict
import itertools
import warnings

import numpy as np

from tables import open_file, Filters, Int64Col, Float64Col, BoolCol, UInt64Col, UInt32Col

from .store_manager import setup_manager
from .bit_matrix import BitMatrix
from .lru import LruDict

from install_profile import profile


filters = Filters(complib="blosc", complevel=9)


class Hdf5Base(object):

    from types import basic_type_map

    def _initial_setup(self, path, mode):
        self.file_ = open_file(path, mode)
        self.manager = setup_manager(self.file_)

    def close(self):
        self.manager.close()


class Hdf5TableWriter(Hdf5Base):

    LATEST_HDF5_TABLE_VERSION = (2, 26, 13)

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


        def store_meta(what):
            meta_index = self.manager.store_object("meta", what, object)
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

        self.missing_values_flags = BitMatrix(file_, "flags", len(col_names))

        # this table vesion was last modified in:
        store_meta(dict(hdf5_table_version=self.LATEST_HDF5_TABLE_VERSION))

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

        num_rows_exisiting = self.row_table.nrows
        self.missing_values_flags.resize(num_rows_exisiting + len(table))

        for row_index, row in enumerate(table.rows):
            hdf_row = self.row_table.row
            for col_index, value, name, type_ in zip(itertools.count(), row, col_names, col_types):
                if value is None:
                    self.missing_values_flags.set_bit(num_rows_exisiting + row_index, col_index)
                else:
                    if type_ not in self.basic_type_map:
                        value = self.manager.store_object(col_index, value, type_)
                    hdf_row[name] = value
            hdf_row.append()

        self.row_offset += len(table)

        self.missing_values_flags.flush()
        self.row_table.flush()
        self.manager.flush()


class Hdf5TableReader(Hdf5Base):

    """opens written table for reading, inplace modification of table cells is supported
       for some data types.
    """

    def __init__(self, path):
        self._initial_setup(path, "r+")
        self._load_meta()
        self.row_cache = LruDict(10000)
        self.col_cache = LruDict(100)
        self.col_cache_raw = LruDict(100)

    def _load_meta(self):

        rows = iter(self.file_.root.meta_index)

        def fetch_next():
            idx = rows.next()["index"]
            return self.manager.fetch("meta", idx).load()

        self.meta = fetch_next()
        self.col_names = fetch_next()
        self.col_types = fetch_next()
        self.col_formats = fetch_next()

        self.col_type_of_name = dict(zip(self.col_names, self.col_types))

        try:
            self.hdf5_meta = fetch_next()
        except StopIteration:
            raise Exception("hdf5 file is too old and can not be loaded any more, I'm sorry.")

        self.hdf5_table_version = self.hdf5_meta["hdf5_table_version"]
        expected = Hdf5TableWriter.LATEST_HDF5_TABLE_VERSION

        if self.hdf5_table_version != expected:
            if self.hdf5_table_version < (2, 26, 12):
                if not hasattr(self.file_, "flags"):
                    self.missing_values_flags = BitMatrix(self.file_, "flags", len(self.col_names))
                    mv = self.file_.root.missing_values
                    n = mv.nrows
                    for s in range(0, n, 10000):
                        rows = mv.cols.row_index[s: s + 10000]
                        cols = mv.cols.col_index[s: s + 10000]
                        self.missing_values_flags.resize(int(max(rows)) + 1)
                        for row, col in itertools.izip(rows, cols):
                            self.missing_values_flags.set_bit(int(row), int(col))
                    self.missing_values_flags.flush()
                message = ("you read from / append to a hdf5 table which has version %s and older "
                           "as the current version %s, you might have problems...." %
                           (self.hdf5_table_version, expected))

            warnings.warn(message, UserWarning, stacklevel=2)

        # read full table -> numpy array -> list -> set
        self.missing_values_flags = BitMatrix(self.file_, "flags", len(self.col_names))

        self.row_table = self.file_.root.rows
        self.nrows = self.file_.root.rows.nrows

    def fetch_row(self, row_index):
        row = self._fetch_row(row_index)
        return row

    def _fetch_row(self, row_index):
        if row_index in self.row_cache:
            return self.row_cache[row_index]
        values = self.row_table[row_index].tolist()
        row = []
        missing = self.missing_values_flags.positions_in_row(row_index)
        for (col_idx, value, type_) in zip(itertools.count(), values, self.col_types):
            if col_idx in missing:
                value = None
            elif type_ not in self.basic_type_map:
                value = self.manager.fetch(col_idx, value)
            row.append(value)
        self.row_cache[row_index] = row
        return row

    def _replace_column_with_missing_values(self, col_index, row_selection):
        row_iter = row_selection if row_selection is not None else xrange(self.row_table.nrows)
        for row_index in row_iter:
            self.missing_values_flags.set_bit(row_index, col_index)
        self.missing_values_flags.flush()

    def _remove_missing_value_entries_in_column(self, col_index, row_selection):

        row_iter = row_selection if row_selection is not None else xrange(self.row_table.nrows)
        for row_index in row_iter:
            self.missing_values_flags.unset_bit(row_index, col_index)
        self.missing_values_flags.flush()

    def replace_column(self, col_index, value, row_selection=None):
        type_ = self.col_types[col_index]
        self.row_cache.clear()
        col_name = self.col_names[col_index]
        if col_name in self.col_cache:
            del self.col_cache[col_name]
            del self.col_cache_raw[col_name]

        if value is None:
            self._replace_column_with_missing_values(col_index, row_selection)
            return

        self._remove_missing_value_entries_in_column(col_index, row_selection)

        if type_ not in (int, long, float, bool):
            value = self.manager.store_object(col_index, value, type_)

        name = self.col_names[col_index]
        if row_selection is None:
            n = self.row_table.nrows
            bulk_size = 10000
            for start in range(0, n, bulk_size):
                stop = min(n, start + bulk_size)
                data = [value] * (stop - start)
                self.row_table.modify_column(start=start, stop=stop, colname=name, column=data)
        else:
            col = getattr(self.row_table.cols, name)
            for row_index in row_selection:
                col[row_index] = value

        self.row_table.flush()
        self.manager.flush()

    def _replace_cell(self, row_index, col_index, value):
        type_ = self.col_types[col_index]
        if row_index in self.row_cache:
            del self.row_cache[row_index]
        col_name = self.col_names[col_index]
        if col_name in self.col_cache:
            del self.col_cache[col_name]
            del self.col_cache_raw[col_name]

        if value is None:
            self.missing_values_flags.set_bit(row_index, col_index)
            self.missing_values_flags.flush()
            return
        else:
            self.missing_values_flags.unset_bit(row_index, col_index)
            self.missing_values_flags.flush()

        row_iter = self.row_table.iterrows(row_index, row_index + 1)
        row = row_iter.next()
        name = self.col_names[col_index]

        if type_ not in self.basic_type_map:
            value = self.manager.store_object(col_index, value, type_)

        row[name] = value
        row.update()
        # we have to finish "iteration", else pytables will not update table
        # buffers:
        try:
            row.next()
        except StopIteration:
            pass

    def replace_cell(self, row_index, col_index, value):
        self._replace_cell(row_index, col_index, value)
        self.flush()

    def flush(self):
        self.row_table.flush()
        self.missing_values_flags.flush()
        self.manager.flush()

    def __len__(self):
        return self.nrows

    __getitem__ = fetch_row

    def get_col_values(self, col_name):
        if col_name in self.col_cache:
            return self.col_cache[col_name]
        col_index = self.col_names.index(col_name)
        store = self.manager.fetch_store(col_index)
        col_values = getattr(self.row_table.cols, col_name)[:]
        if store is not None:
            values = store.fetch_column(col_index, col_values)
            self.col_cache[col_name] = values
            return values

        missing = self.missing_values_flags.positions_in_col(col_index)

        type_ = self.col_type_of_name[col_name]
        col_values = col_values.astype(object)
        if type_ not in self.basic_type_map:
            for i, v in enumerate(col_values):
                if v == 0:
                    col_values[i] = None
                else:
                    col_values[i] = self.manager.fetch(col_index, int(v))
        else:
            col_values[np.fromiter(missing, dtype=int)] = None
        self.col_cache[col_name] = col_values
        return col_values

    def get_raw_col_values(self, col_name):
        if col_name in self.col_cache_raw:
            return self.col_cache_raw[col_name]
        col_index = self.col_names.index(col_name)
        missing = self.missing_values_flags.positions_in_col(col_index)
        col_values = getattr(self.row_table.cols, col_name)[:]
        self.col_cache_raw[col_name] = (col_values, missing)
        return col_values, missing


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
        self.flush()
