# encoding: utf-8, division
from __future__ import print_function, division, absolute_import

from collections import OrderedDict
import functools
from itertools import tee

from types import GeneratorType



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

    def __delitem__(self, index):
        del self._data[index]


def lru_cache(maxsize):

    Tee = tee([], 1)[0].__class__

    def wrapper(fun):
        cache = LruDict(maxsize)

        @functools.wraps(fun)
        def inner(*args, **kwargs):
            key = args + tuple(kwargs.items())

            if key not in cache:
                result = fun(*args, **kwargs)
                cache[key] = result

            if isinstance(cache[key], (GeneratorType, Tee)):
                # the original can't be used any more,
                # so we need to change the cache as well
                cache[key], r = tee(cache[key])
                return r
            return cache[key]

        return inner

    return wrapper
