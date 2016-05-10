# encoding: utf-8, division
from __future__ import print_function, division


import itertools

from tables import Atom

import numpy as np

from .store_base import Store, filters
from .lru import LruDict

from .install_profile import profile


class StringStoreBase(object):

    def __init__(self, file_, node, blob_name_stem="string_blob", **kw):

        self.file_ = file_
        self.node = node

        if "__" in blob_name_stem:
            raise ValueError("'__' not allowed in blob_name_stem")

        self.write_cache = LruDict(10000)
        self.read_cache = LruDict(10000)
        self.col_cache = LruDict(100)
        self.fetched = {}

        self.blob_name_stem = blob_name_stem
        self.setup(node)

    def setup(self, node):

        self.blobs = {}
        self.starts = {}
        for node in self.file_.list_nodes(node):
            fields = node.name.split("__")
            if len(fields) == 2:
                name, col_index = fields
                try:
                    col_index = int(col_index)
                except ValueError:
                    pass
                if name == self.blob_name_stem:
                    self.blobs[col_index] = node
                elif name == self.blob_name_stem + "_starts":
                    self.starts[col_index] = node

    def available_columns(self):
        return self.blobs.keys()

    def create_store(self, col_index):

        blob = self.file_.create_earray(self.node, "%s__%s" % (self.blob_name_stem, col_index),
                                        Atom.from_dtype(np.dtype("uint8")), (0,),
                                        filters=filters)
        starts = self.file_.create_earray(self.node, "%s_starts__%s" % (self.blob_name_stem, col_index),
                                          Atom.from_dtype(np.dtype("uint64")), (0,),
                                          filters=filters)
        return blob, starts

    def _write(self, col_index, s):

        # hash key
        yield s

        # store and yield index
        yield int(self._write_str(col_index, s).next())

    def _write_str(self, col_index, s, index=None):

        if col_index not in self.blobs:
            blob, starts = self.create_store(col_index)
            self.blobs[col_index] = blob
            self.starts[col_index] = starts
        else:
            blob = self.blobs[col_index]
            starts = self.starts[col_index]

        start = blob.nrows

        blob.append(np.fromstring(s, dtype=np.uint8))
        index = starts.nrows
        starts.append([start])

        yield index

    def _fetch_column(self, col_index):
        starts = self.starts[col_index][:]
        if not len(starts):
            return []
        blobs = self.blobs[col_index][:].tostring()
        rv = [None]
        i = 0
        for i, s, e in itertools.izip(itertools.count(), starts, starts[1:]):
            rv.append(blobs[s:e])
        rv.append(blobs[starts[-1]:])
        return np.array(rv, dtype=object)

    def fetch_column(self, col_index, global_indices):
        strings = self.fetched.get(col_index)
        if strings is None:
            strings = self._fetch_column(col_index)
            self.fetched[col_index] = strings
        global_indices = np.array(global_indices)
        local_indices = np.array(global_indices + 1) >> 3
        values = strings[local_indices]
        return values

    def _read(self, col_index, index):

        starts = self.starts[col_index]
        blob = self.blobs[col_index]

        if index < starts.nrows - 1:
            start, end = starts[index:index + 2]
            return blob[start:end].tostring()
        elif index == starts.nrows - 1:
            start = starts[index:][0]  # starts[index] fails, error in pytables
            return blob[start:].tostring()
        else:
            raise ValueError("invalid index ! %d out of %d" % (index, starts.nrows))

    def flush(self):
        for node in self.blobs.values():
            node.flush()
        for node in self.starts.values():
            node.flush()


class StringStore(StringStoreBase, Store):

    ID_FLAG = 6
    HANDLES = str

