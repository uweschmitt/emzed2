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

    def _fetch_full_string_blob(self, col_index):
        return self.blobs[col_index][:].tostring()

    def _fetch_strings(self, col_index):
        """ we create an array which has None as first entry then the
        strings from the blob. This makes later fetching None values fast in case
        of many None values in the store.
        """
        starts = self.starts[col_index][:]
        if not len(starts):
            return []
        blobs = self._fetch_full_string_blob(col_index)

        def _iter():
            yield None
            for s, e in itertools.izip(starts, starts[1:]):
                yield blobs[s:e]
            yield blobs[starts[-1]:]

        # avoid appending to a list, np.fromiter does not work for dtype=object:
        rv = np.zeros((len(starts) + 1,), dtype=object)
        for i, o in itertools.izip(itertools.count(), _iter()):
            rv[i] = o

        return rv

    def fetch_column(self, col_index, global_indices):
        strings = self.fetched.get(col_index)
        if strings is None:
            strings = self._fetch_strings(col_index)
            self.fetched[col_index] = strings

        # we assume that _fetch_strings returns an array where the first
        # item is None (index 0) and then the strings start with index 1
        # this makes the global_index -> string_index computation a little
        # complex, because (0 - 1) >> 3 underflows here:
        global_indices = np.array(global_indices, dtype=int)

        # the first term is the "global to local" index computation, then we
        # add 1 because strings[] starts with None as described above:
        string_indices = ((global_indices - 1) >> 3) + 1
        # we fix the underflow:
        string_indices[global_indices == 0] = 0
        return strings[string_indices]

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


class UnicodeStore(StringStoreBase, Store):

    ID_FLAG = 5
    HANDLES = unicode

    def __init__(self, file_, node, blob_name_stem="unicode_blob", **kw):
        super(UnicodeStore, self).__init__(file_, node, blob_name_stem, **kw)

    def _write_str(self, col_index, s, index=None):
        utf8 = s.encode("utf-8")
        for i in super(UnicodeStore, self)._write_str(col_index, utf8, index):
            yield i
        self.blobs[0].flush()
        self.starts[0].flash()

    def _fetch_full_string_blob(self, col_index):
        return unicode(self.blobs[col_index][:].tostring(), "utf-8")


    def _read(self, col_index, index):
        utf8 = super(UnicodeStore, self)._read(col_index, index)
        return unicode(utf8, "utf-8")

