# encoding: utf-8, division
from __future__ import print_function, division

import cPickle

import numpy as np

from .string_store import StringStoreBase
from .store_base import Store
from .lru import LruDict

from .install_profile import profile


class ObjectStore(StringStoreBase, Store):

    # ObjectStore as fall back store must always have ID_FLAG 7 !!!
    ID_FLAG = 7
    HANDLES = object

    def __init__(self, file_, node):
        StringStoreBase.__init__(self, file_, node, "object_blob")
        self.obj_read_cache = LruDict(10000)

    def _write(self, col_index, obj):

        # hash key
        yield id(obj)

        code = cPickle.dumps(obj, protocol=2)

        yield int(self._write_str(col_index, code).next())

    def _resolve(self, col_index, index):
        if (col_index, index) in self.obj_read_cache:
            return self.obj_read_cache[col_index, index]
        code = StringStoreBase._read(self, col_index, index)
        try:
            obj = cPickle.loads(code)
        except (IndexError, ):
            print(repr(code))
            obj = None
        self.obj_read_cache[col_index, index] = obj
        return obj

    def _read(self, col_index, index):
        return ObjectProxy(self, col_index, index)

    def fetch_column(self, col_index, global_indices):
        codes = StringStoreBase.fetch_column(self, col_index, global_indices)

        strings = self.fetched.get(col_index)
        if strings is None:
            strings = self._fetch_column(col_index)
            self.fetched[col_index] = strings
        global_indices = np.array(global_indices)
        local_indices = np.array(global_indices + 1) >> 3
        return map(ObjectProxyCodeLoaded, strings[local_indices])


class ObjectProxy(object):

    def __init__(self, reader, col_index, index):
        self.reader = reader
        self.index = index
        self.col_index = col_index
        self.obj = None

    def load(self):
        if self.obj is None:
            self.obj = self.reader._resolve(self.col_index, self.index)
        return self.obj


class ObjectProxyCodeLoaded(ObjectProxy):

    def __init__(self, code):
        self.code = code

    def load(self):
        return cPickle.loads(self.code)


if __name__ == "__main__":
    from tables import open_file
    file_ = open_file("peakmap.h5", mode="w")

    store, fetch, flush = setup_manager(file_, file_.root)

    data = " asdlfadlsfjal " * 10
    data = (1, 2, 3)

    import time
    s = time.time()
    id_ = store(data)
    print(time.time() - s)
    s = time.time()
    id_ = store(data)
    print(time.time() - s)
    flush()

    print(id_)
    data = fetch(id_)
    print(data)
