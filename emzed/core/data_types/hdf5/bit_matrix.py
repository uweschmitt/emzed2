# encoding: utf-8, division
from __future__ import print_function, division

from tables import Atom
import numpy as np

from .store_base import filters
from .lru import LruDict


class BitMatrix(object):

    def __init__(self, file_, name, n_cols, cache_block_size=None):
        self.n_cols = n_cols
        self._n_cols_flags = n_cols // 8 + 1
        if not hasattr(file_.root, name):
            self.data = file_.create_earray(file_.root, name,
                                            Atom.from_dtype(np.dtype("uint8")), (0,),
                                            filters=filters,
                                            )
            self.n_rows = 0
        else:
            self.data = getattr(file_.root, name)
            self.n_rows = len(self.data) // (self._n_cols_flags)

        if cache_block_size is None:
            cache_block_size = 10000
        self.cache_block_size = cache_block_size  # in rows
        self.cache = LruDict(500)
        self.test_vec = (1 << np.arange(8, dtype="uint8"))[:, None]

    def resize(self, n_rows):
        additional_rows = n_rows - self.n_rows
        if additional_rows > 0:
            zeros = np.zeros(additional_rows * self._n_cols_flags, dtype="uint8")
            self.data.append(zeros)
            self.n_rows = n_rows
            idx = n_rows // self.cache_block_size
            if idx in self.cache:
                del self.cache[idx]

    def _lookup_cache(self, row):
        idx = row // self.cache_block_size
        if idx not in self.cache:
            start = idx * self.cache_block_size * self._n_cols_flags
            end = (idx + 1) * self.cache_block_size * self._n_cols_flags
            self.cache[idx] = (self.data[start:end], start, end)
        data_block = self.cache[idx][0]
        effective_row = row - idx * self.cache_block_size
        return effective_row, data_block

    def set_bit(self, row, col):
        assert row < self.n_rows, "resize first !"

        effective_row, data_block = self._lookup_cache(row)
        byte = col // 8 + effective_row * self._n_cols_flags
        bit = col % 8
        data_block[byte] |= (1 << bit)

    def unset_bit(self, row, col):
        assert row < self.n_rows, "resize first !"

        effective_row, data_block = self._lookup_cache(row)
        byte = col // 8 + effective_row * self._n_cols_flags
        bit = col % 8
        data_block[byte] &= 255 ^ (1 << bit)

    def positions_in_row(self, row):
        effective_row, data_block = self._lookup_cache(row)

        start = effective_row * self._n_cols_flags
        end = (effective_row + 1) * self._n_cols_flags
        flags = data_block[start:end]
        bits, bytes_ = np.where(self.test_vec & flags)
        return bytes_ * 8 + bits

    def positions_in_col(self, col):
        byte, bit = divmod(col, 8)
        result = set()
        for start in range(0, self.data.nrows, self.cache_block_size):
            effective_row, data_block = self._lookup_cache(start)
            col_values = data_block[byte::self._n_cols_flags]
            flags = col_values & (1 << bit)
            found = effective_row + np.where(flags)[0]
            result.update(found)
        return result

    def flush(self):
        for (block, start, end) in self.cache.values():
            self.data[start:end] = block
        self.cache.clear()
        self.data.flush()
