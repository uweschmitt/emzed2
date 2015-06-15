import hashlib
import datetime
from collections import namedtuple

import numpy
import cPickle


def unique_id_from(*args):
    h = hashlib.sha256()
    for arg in args:
        if not isinstance(arg, basestring):
            arg = cPickle.dumps(arg)
        h.update(arg)
    return h.hexdigest()


class Blob(object):

    def __init__(self, data, type_=None):
        self.data = data
        self._unique_id = None
        if type_ is None:
            if data.startswith("\x89PNG"):
                type_ = "PNG"
            elif data[0] == "\xff":
                hex_header = "ff d8 ff e0 00 10 4a 46 49 46 00 01"
                jpg_soi_marker = "".join(chr(int(f, 16) for f in hex_header.split()))
                if jpg_soi_marker in data:
                    type_ = "JPG"
            elif data.startswith("emzed_version=2."):
                type_ = "TABLE"
            elif data.startswith("<?xml version=\""):
                type_ = "XML"
        self.type_ = type_

    def __str__(self):
        type_ = "unknown type" if self.type_ is None else "type %s" % self.type_
        return "<Blob %#x of %s>" % (id(self), type_)

    def uniqueId(self):
        if self._unique_id is None:
            self._unique_id = unique_id_from(self.data)
        return self._unique_id


class TimeSeries(object):

    def __init__(self, x, y):
        assert len(x) == len(y)
        self.x = list(x)  # no numpy arrays here
        self.y = list(y)
        self._unique_id = None

    def __str__(self):
        try:
            min_y = min(yi for yi in self.y if yi is not None)
        except ValueError:  # for empty sequencd
            return "<empty TimeSeries>"
        else:
            max_y = max(yi for yi in self.y if yi is not None)
            min_x = min(xi for xi in self.x if xi is not None)
            max_x = max(xi for xi in self.x if xi is not None)
            return "<TimeSeries, time=%s..%s, values=%s..%s>" % (min_x, max_x, min_y, max_y)

    def uniqueId(self):
        if self._unique_id is None:
            self._unique_id = unique_id_from((self.x, self.y))
        return self._unique_id

    def __len__(self):
        return len(self.x)

    def segments(self):
        """detects segments in x which are separated by one or multiple None values, so if a list
        contains None values indicating "nan", this supports plotting of the segments.

        this generate yields the pairs (xi, yi) for every segment.
        """
        ni = [-1] + [i for i, xi in enumerate(self.x) if xi is None] + [len(self.x)]
        for (si, ti) in zip(ni, ni[1:]):
            if si + 1 < ti:
                s = slice(si + 1, ti)
                yield self.x[s], self.y[s]
