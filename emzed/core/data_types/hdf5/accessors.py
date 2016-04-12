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
        missing_value_indices = self.missing_values_table.read().tolist()
        self.missing_values = {}
        for cell_index, row_index_in_table in itertools.izip(missing_value_indices,
                                                             itertools.count()):
            self.missing_values[cell_index] = row_index_in_table
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

    def select_col_values(self, col_index, row_indices):
        type_ = self.col_types[col_index]
        basic_types = {int, long, float, bool}
        if type_ not in basic_types:
            raise NotImplementedError("fetching selected values only works for basic types")

        is_missing = [(ri, col_index) in self.missing_values for ri in row_indices]

        name = self.col_names[col_index]
        values = getattr(self.row_table.cols, name)[:]
        values = [values[i] for i in row_indices]
        return [v if not im else None for (v, im) in zip(values, is_missing)]

    def replace_column(self, col_index, value, row_selection=None):
        type_ = self.col_types[col_index]
        self.row_cache.clear()

        if value is None:
            n = self.missing_values_table.nrows
            row_iter = row_selection if row_selection is not None else xrange(self.row_table.nrows)
            for row_index in row_iter:
                index = (row_index, col_index)
                if index not in self.missing_values:
                    row = self.missing_values_table.row
                    row["row_index"] = row_index
                    row["col_index"] = col_index
                    row.append()
                    self.missing_values[index] = n
                    n += 1
            self.missing_values_table.flush()
            return
        else:
            to_remove = []
            row_iter = row_selection if row_selection is not None else xrange(self.row_table.nrows)
            for row_index in row_iter:
                index = (row_index, col_index)
                if index in self.missing_values:  # we overwrite a previously None with a not None:
                    ri = self.missing_values[index]
                    to_remove.append(ri)
                    del self.missing_values[index]

            # we remove from the end !
            for ri in sorted(to_remove, reverse=True):
                self.missing_values_table.remove_row(ri)

        self.missing_values_table.flush()

        name = self.col_names[col_index]
        if type_ not in (int, long, float, bool):
            value = self.manager.store_object(value)

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

        index = (row_index, col_index)
        if value is None:
            if index not in self.missing_values:
                row = self.missing_values_table.row
                row["row_index"] = row_index
                row["col_index"] = col_index
                row.append()
                self.missing_values[index] = self.missing_values_table.nrows
                self.missing_values_table.flush()
                return
        elif index in self.missing_values:  # we overwrite a previously None with a not None:
            ri = self.missing_values[index]
            self.missing_values_table.remove_row(ri)
            self.missing_values_table.flush()
            del self.missing_values[index]

        row_iter = self.row_table.iterrows(row_index, row_index + 1)
        row = row_iter.next()
        name = self.col_names[col_index]

        if type_ not in (int, long, float, bool):
            value = self.manager.store_object(value)

        row[name] = value
        row.update()
        # we have to finish "iteration", else pytables will not update table buffers:
        try:
            row.next()
        except StopIteration:
            pass

    def replace_cell(self, row_index, col_index, value):
        self._replace_cell(row_index, col_index, value)
        self.flush()

    def flush(self):
        self.row_table.flush()
        self.missing_values_table.flush()
        self.manager.flush()

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
