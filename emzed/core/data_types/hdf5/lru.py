# encoding: utf-8, division
from __future__ import print_function, division

import functools
from collections import OrderedDict


class LruDict(object):

    def __init__(self, maxsize):
        self.maxsize = maxsize
        self._data = OrderedDict()

    def __setitem__(self, k, v):
        self._data[k] = v
        if len(self._data) > self.maxsize:
            self._data.popitem(last=False)

    def __getitem__(self, k):
        return self._data[k]

    def __getattr__(self, name):
        return getattr(self._data, name)

    def __contains__(self, what):
        return what in self._data


def lru_cache(maxsize):

    def wrapper(fun):
        cache = LruDict(maxsize)
        @functools.wraps(fun)
        def inner(*args, **kwargs):
            key = args + tuple(kwargs.items())
            if key in cache:
                return cache[key]
            result = fun(*args, **kwargs)
            cache[key] = result
            return result
        return inner

    return wrapper
