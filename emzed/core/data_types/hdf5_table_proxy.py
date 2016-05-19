# encoding: utf-8, division
from __future__ import print_function, division

import csv
import itertools
import re
import time
import types

import numpy as np
import pandas as pd

from .table import Table

# PeakMapProxy no needed here, but convenient if it can be importet the same way as ObjectProxy:
from .hdf5.object_store import ObjectProxy
from .hdf5.peakmap_store import PeakMapProxy  # analysis:ignore

from .hdf5.accessors import Hdf5TableReader
from .hdf5.lru import LruDict

from base_classes import ImmutableTable

from hdf5.install_profile import profile

from .range_set import RangeSet


class UfuncWrapper(object):

    def __init__(self, f):
        self.f = f

    def __call__(self, *a, **kw):
        return self.f(*a, **kw)


class LogAll(object):

    """this can be used as __metaclass__ of Hdf5TableProxy to see how long
    method calls take. This is helpful during development.
    """

    def __new__(clz, name, bases, attributes):

        def wrap(f):
            """wrap methods to report execution time"""

            # this produces A LOT of output and the corresponding access to the ghost table
            # should be very fast...
            if f.__name__ == "__getattr__":
                return f

            def decorated(*a, **kw):
                started = time.time()
                result = f(*a, **kw)
                needed = time.time() - started
                print("calling", f.__name__, "needed %.4f secs" % needed)
                return result
            return decorated

        wrapped_methods = {name: wrap(a) for (name, a) in attributes.items() if callable(a)}
        attribs = {name: a for (name, a) in attributes.items() if not callable(a)}
        attribs.update(wrapped_methods)
        return type(name, bases, attribs)


class Hdf5TableProxy(ImmutableTable):

    def __init__(self, path):
        self.reader = Hdf5TableReader(path)
        self.setup()

    def close(self):
        self.reader.close()

    def setup(self):
        self.perm = None

        r = self.reader
        self._ghost_table = Table(r.col_names, r.col_types, r.col_formats,
                                  meta=r.meta, rows=[])

        # we add rows later, because the Table constructor tries to setup column expressions
        # which is expensive for large hdf5 tables:
        self._ghost_table.rows = self.reader

        # we forbid to call _setupColumnAttributes, which would destroy
        # all the benefits of hdf5 proxy tables. we do this to prevent slow
        # operations and to enforce reimplementation here if needed.
        def _not_allowed(self, *a, **kw):
            raise NotImplementedError("this method call is not allowed yet !")
        # to patch a method we first must bound the free function to the instance:
        not_allowed = types.MethodType(_not_allowed, self._ghost_table)
        self._ghost_table._setupColumnAttributes = not_allowed
        self._ghost_table.getColumn = not_allowed
        self.hdf5_meta = r.hdf5_meta

    def resetInternals(self):
        raise NotImplementedError()

    def info(self):
        """
        prints some table information and some table statistics
        """

        import emzed.utils

        def extract_type(col_name):
            type_ = self.getColType(col_name)
            match = re.match("<(type|class) '(.+)'>", str(type_))
            if match is not None:
                type_str = match.group(2).split(".")[-1]
            else:
                type_str = str(type_)
            return type_str

        def extract_format(col_name):
            return self.getColFormat(col_name)

        table = emzed.utils.toTable("name", self._colNames, type_=str)
        table.addEnumeration()
        table.addColumn("type", table.name.apply(extract_type), type_=str)
        table.addColumn("format", table.name.apply(extract_format), type_=str, format_="%r")
        table.addColumn("diff values", "(unknown)", type_=str)
        table.addColumn("nones", "(unknown)", type_=str)

        print
        table.print_(max_lines=None)

    def findMatchingRows(self, filters):
        """accepts list of column names and functions operating on those columns,
        returns the indices of the remaining columns

        Example::

            t.findMatchingRows(("mz", lambda mz: 100 <= mz <= 200),
                               ("rt", lambda rt: 200 <= rt <= 1000))

            computes the row indices of all rows where mz and rt are in the given
            ranges.
        """

        indices_of_fitting_rows = RangeSet(0, len(self))

        for col_name, filter_function in filters:

            if filter_function is None:
                continue

            if isinstance(filter_function, UfuncWrapper):

                values, missing_values = self.reader.get_raw_col_values(col_name)
                keep = set(np.where(filter_function(values))[0])
                keep -= set(missing_values)
                rows_to_remain = keep

            else:
                values = self.reader.get_col_values(col_name)

                # trick, "!=" does not work, but all not None values are larger than None !
                iflags = (values > None) 

                # somehow this happened once, although I do not understand how, the only reason
                # can be when self.reader.get_col_values(..) above retured a single bool:
                if isinstance(iflags, bool):
                    iflags = np.array([iflags], dtype=bool)

                subset = values[iflags]
                subflags = np.vectorize(filter_function)(subset)
                iflags[iflags] = subflags
                keep = set(np.where(iflags)[0])

            indices_of_fitting_rows = indices_of_fitting_rows.intersection(keep)

        # prevent speed deterioration:
        assert isinstance(indices_of_fitting_rows, (set, RangeSet))
        return indices_of_fitting_rows

    def __len__(self):
        return len(self.reader)

    def __getitem__(self, index):
        return self.reader.fetch_row(index)

    def sortBy(self, colNames, ascending=True):
        raise RuntimeError("in place sort not supported !")

    def sortPermutation(self, colNames, ascending=True):
        """
        sorts table in respect of column named *colName* **in place**.
        *ascending* is boolean and tells if the values are sorted
        in ascending order or descending.

        This is important to build an internal index for faster queries
        with ``Table.filter``, ``Table.leftJoin`` and ``Table.join``.

        For building an internal index, ascending must be *True*, you
        can have only one index per table.
        """
        if isinstance(colNames, basestring):
            colNames = (colNames,)

        if ascending in (True, False):
            ascending = (ascending,) * len(colNames)

        msg = "got colNames=%r and ascending=%r" % (colNames, ascending)

        if len(colNames) != len(ascending):
            raise ValueError("number of column names and ascending option mismatch: %s" % msg)

        if not len(self):
            return []   # empty permutation

        for col_name in colNames:
            assert col_name in self._colNames
        for order in ascending:
            assert isinstance(order, bool)

        def fill_in(values, ascending):
            if isinstance(values.dtype.type(0), np.integer):
                info = np.iinfo(values.dtype)
                return info.min if ascending else info.max
            elif isinstance(values.dtype.type(0), np.floating):
                info = np.finfo(values.dtype)
                return info.min if ascending else info.max
            return None

        perm = range(len(self))
        all_values = dict()
        for col_name, asc in reversed(zip(colNames, ascending)):
            t = self.getColType(col_name)
            if t in (int, float, long):
                values, missing_values = self.reader.get_raw_col_values(col_name)
                missing_values = np.fromiter(missing_values, dtype=int)
                values[missing_values] = fill_in(values, ascending)
                all_values[col_name] = values
            else:
                values = self.reader.get_col_values(col_name)
                all_values[col_name] = values
        if len(all_values) == 1:
            # mergesort turned out to work best:
            perm = np.argsort(values, kind="mergesort")
            if not asc:
                perm = perm[::-1]
            return perm
        all_values["_i"] = perm
        df = pd.DataFrame(all_values, columns=colNames + ("_i",))
        df = df.sort_values(list(colNames), ascending=list(ascending))
        perm = df["_i"].values
        return perm

    def setCellValue(self, row_indices, col_indices, values):
        for ri, ci, v in self._ghost_table._resolve_write_operations(row_indices, col_indices,
                                                                     values):
            self.reader._replace_cell(ri, ci, v)
        self.reader.flush()

    def replaceColumn(self, name, what, **kw):
        if "type_" in kw:
            raise NotImplementedError("argument type_ not supported yet")
        if "format_" in kw:
            raise NotImplementedError("argument format_ not supported yet")
        if what is not None and not isinstance(what, (bool, int, long, str)):
            raise NotImplementedError(
                "what argument must be constant value, no iterables supported")

        self.reader.replace_column(self.getIndex(name), what)

    def replaceSelectedRows(self, name, what, rowIndices):
        self.reader.replace_column(self.getIndex(name), what, rowIndices)

    def selectedRowValues(self, name, rowIndices):
        return [self.reader.get_col_values(name)[i] for i in rowIndices]

    def toTable(self):
        rows = []
        for row in self.reader:
            resolved_row = []
            for cell in row:
                if isinstance(cell, ObjectProxy):
                    cell = cell.load()
                resolved_row.append(cell)
            rows.append(resolved_row)
        rv = Table(self._colNames, self._colTypes, self._colFormats, rows=rows, meta=self.meta)
        return rv

    @property
    def rows(self):
        # to allow iterating as we know from Table class:
        return self.reader

    def __getattr__(self, name):
        return getattr(self._ghost_table, name)


def main():
    proxy = Hdf5TableProxy("hdf5/test.hdf5")
    print(len(proxy))
    import time

    proxy.filter_("floats_0", 400, 450)
    proxy.sortBy(["floats_0"], [True])
    s = time.time()
    for t in proxy:
        print(t)
        print()

    print((time.time() - s) / len(proxy))


if __name__ == "__main__":
    main()
