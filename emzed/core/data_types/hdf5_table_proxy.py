# encoding: utf-8, division
from __future__ import print_function, division

import itertools

from .table import Table

from .hdf5.stores import ObjectProxy, PeakMapProxy
from .hdf5.accessors import Hdf5TableReader
from .hdf5.install_profile import profile
from .hdf5.lru import LruDict

from base_classes import ImmutableTable


class Hdf5TableProxy(ImmutableTable):

    def __init__(self, path):
        self.reader = Hdf5TableReader(path)
        self.setup()

    def close(self):
        self.reader.close()

    def setup(self):
        self.perm = None
        self.row_cache = LruDict(10000)
        self.col_cache = LruDict(10)

        r = self.reader
        self._ghost_table = Table(r.col_names, r.col_types, r.col_formats,
                                  meta=r.meta, rows=[])

    @profile
    def findMatchingRows(self, filters):
        """accepts list of column names and functions operating on those columns,
        returns the indices of the remaining columns

        Example::

            t.findMatchingRows(("mz", lambda mz: 100 <= mz <= 200),
                               ("rt", lambda rt: 200 <= rt <= 1000))

            computes the row indices of all rows where mz and rt are in the given
            ranges.
        """

        indices_of_fitting_rows = set(range(len(self)))

        for col_name, filter_function in filters:

            if filter_function is None:
                continue

            col_values = self.reader.get_col_values(col_name)
            rows_to_remain = set()

            for row_idx in range(len(self)):
                v = col_values[row_idx]
                if v is not None:
                    match = filter_function(v)
                    if match:
                        rows_to_remain.add(row_idx)
            indices_of_fitting_rows = indices_of_fitting_rows.intersection(rows_to_remain)

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
            colNames = [colNames]

        if ascending in (True, False):
            ascending = [ascending] * len(colNames)

        assert len(colNames) == len(ascending)

        if not len(self):
            return []   # empty permutation

        for col_name in colNames:
            assert col_name in self._colNames
        for order in ascending:
            assert isinstance(order, bool)

        for col_name, order in reversed(zip(colNames, ascending)):
            values = self.reader.get_col_values(col_name)
            perm = [i for (v, i) in sorted(zip(values, itertools.count()), reverse=not order)]
        return perm

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
