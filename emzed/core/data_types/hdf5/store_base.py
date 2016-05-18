# encoding: utf-8, division
from __future__ import print_function, division


from .. import PeakMap
from ..col_types import TimeSeries, CheckState

from types import basic_type_map

from install_profile import profile


import abc
from datetime import datetime
import functools
import itertools
import time

import cPickle

from tables import (Filters, Int64Col, Atom, Float32Col, BoolCol,
                    UInt8Col, UInt32Col, UInt64Col, StringCol)

import numpy as np


from emzed_optimizations.sample import sample_peaks as optim_sample_peaks

from ..ms_types import Spectrum, PeakMap
from ..col_types import TimeSeries

filters = Filters(complib="blosc", complevel=9)

from .lru import LruDict, lru_cache

from .types import basic_type_map

from .install_profile import profile


def timeit(function):
    @functools.wraps(function)
    def inner(*args, **kwargs):
        started = time.time()
        result = function(*args, **kwargs)
        needed = time.time() - started
        print("calling %s needed %.2e seconds" % (function.__name__, needed))
        return result
    return inner



def setup_manager(file_, node=None):

    if node is None:
        node = file_.root

    manager = Store(file_, node)
    return manager



class Store(object):

    __metaclass__ = abc.ABCMeta

    ID_FLAG = None
    HANDLES = None

    def __init__(self, file_, node, **kw):

        assert self.__class__ == Store, "do not call __init__ from subclass !!"
        self.file_ = file_
        self.node = node
        self._flags = {}
        self._handlers = []
        self._store_for_column = {}

        # ObjectStore as fall back store must always have ID_FLAG 7 !!!
        store_classes = self.__class__.__subclasses__()
        store_classes.sort(key=lambda cls: cls.ID_FLAG)

        for store_class in store_classes:
            flag = store_class.ID_FLAG
            handles = store_class.HANDLES
            if flag is None:
                raise TypeError("%s does not implement ID_FLAG attribute" % store_class)
            if handles is None:
                raise TypeError("%s does not implement HANDLES attribute" % store_class)
            assert 0 <= flag < 8
            store = store_class(file_, node, **kw)
            self._flags[flag] = store
            self._handlers.append((handles, store))
            for column in store.available_columns():
                self._store_for_column[column] = store

    def store_object(self, col_index, obj, type_):
        if type_ in basic_type_map:
        #if any(isinstance(obj, type_) for type_ in basic_type_map):
            raise ValueError("something went wrong, you try to store a basic type in an object store")
        for (handles, store) in self._handlers:
            if type_ is handles:
                global_id = store.write(col_index, obj)
                return global_id
        raise TypeError("no store manager for %r found" % obj)

    def fetch(self, col_index, global_id):
        if global_id == 0:
            return None
        assert isinstance(global_id, (int, long))
        flag = Store.compute_flag(global_id)
        reader = self._flags.get(flag)
        if reader is None:
            raise Exception("invalid flag %d found" % flag)
        return reader.read(col_index, global_id)

    def fetch_store(self, col_index):
        return self._store_for_column.get(col_index)

    def write(self, col_index, obj):
        writer = self._write(col_index, obj)
        hash_key = writer.next()
        if (col_index, hash_key) in self.write_cache:
            return self.write_cache[col_index, hash_key]

        local_id = writer.next()
        global_id = (local_id << 3 | self.ID_FLAG) + 1
        self.write_cache[col_index, hash_key] = global_id
        return global_id

    def _write(self, col_index, obj):
        raise NotImplementedError()

    def read(self, col_index, global_id):
        local_id = (global_id - 1) >> 3
        result = self.read_cache.get((col_index, local_id))
        if result is not None:
            return result
        result = self._read(col_index, local_id)
        self.read_cache[col_index, local_id] = result
        return result

    def _read(col_index, index):
        raise NotImplementedError()

    def flush(self):
        for store in self._flags.values():
            store.flush()

    def close(self):
        self.file_.close()

    def dump(self):
        raise NotImplementedError()

    def available_columns(self):
        return []

    @staticmethod
    def compute_flag(global_id):
        return (global_id - 1) & 7


