import datetime
import hashlib
import cPickle

import pandas as pd
import numpy as np


def unique_id_from(*args):
    h = hashlib.sha256()
    for arg in args:
        if not isinstance(arg, basestring):
            arg = cPickle.dumps(arg)
        h.update(arg)
    return h.hexdigest()


class SpecialColType(object):

    pass



class CheckState(SpecialColType):

    def __init__(self, is_checked):
        self._is_checked = bool(is_checked)

    def is_checked(self):
        return self._is_checked

    def set_checked(self, is_checked):
        self._is_checked = is_checked

    def __nonzero__(self):
        return self._is_checked

    def __eq__(self, other):
        if isinstance(other, CheckState):
            return self._is_checked == other._is_checked
        elif isinstance(other, bool):
            return self._is_checked == other
        else:
            return False

    def __ne__(self, other):
        return not (self == other)


class Blob(SpecialColType):

    def __init__(self, data, type_=None):
        self.data = data
        self._unique_id = None
        if type_ is None and data:
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


class TimeSeries(SpecialColType):

    def __init__(self, x, y, label=None, blank_flags=None):
        assert len(x) == len(y)
        assert all(isinstance(xi, datetime.datetime) or xi is None for xi in x)
        self.x = np.array(x, dtype="object")
        self.y = np.array(y, dtype="float64")
        self._unique_id = None
        self._unique_ids_cutted = {}
        self.label = label
        self.is_blank = blank_flags

    def uniqueId(self):
        if self._unique_id is None:
            self._unique_id = unique_id_from(self.x, self.y, self.is_blank, self.label)
        return self._unique_id

    def _unique_id_cutted(self, n):
        """computes unique id of time series truncated by last entries
        """
        if n not in self._unique_ids_cutted:
            id_ = unique_id_from(self.x[:n], self.y[:n], self.is_blank[:n], self.label)
            self._unique_ids_cutted[n] = id_
        return self._unique_ids_cutted[n]

    def continues(self, other):
        """checks if other "is a prefix" of self. So if we compute a new time series we can
        detect if it is a continuation of another already existing time series
        """
        return len(self) > len(other) and self._unique_id_cutted(len(other)) == other.uniqueId()

    def __len__(self):
        return len(self.x)

    def __str__(self):
        return "<TimeSeries %#x of length %d>" % (id(self), len(self))

    @staticmethod
    def detect_segments(x, y):
        """detects segments in x which are separated by one or multiple None values, so if a list
        contains None values indicating "nan", this supports plotting of the segments.

        this generate yields the pairs (xi, yi) for every segment.
        """
        segments = []
        ni = [-1] + [i for i, (xi, yi) in enumerate(zip(x, y)) if pd.isnull(xi) or pd.isnull(yi)]\
                  + [len(x)]
        for (si, ti) in zip(ni, ni[1:]):
            if si + 1 < ti:
                s = slice(si + 1, ti)
                segments.append((x[s], y[s]))
        return segments

    def for_plotting(self):
        if self.is_blank is None:
            return self.detect_segments(self.x, self.y)

        signal_xy = [(x, y)
                     for (x, y, is_blank) in zip(self.x, self.y, self.is_blank) if not is_blank]
        blank_xy = [(x, y) for (x, y, is_blank) in zip(self.x, self.y, self.is_blank) if is_blank]

        def segments(list_of_tuples):
            if list_of_tuples:
                return self.detect_segments(*zip(*list_of_tuples))
            return []

        seg_xy = segments(signal_xy)
        seg_blanks = [(x, y, dict(linestyle="DashLine")) for (x, y) in segments(blank_xy)]
        return seg_xy + seg_blanks
