# encoding: utf-8
from __future__ import print_function, division, absolute_import


class RangeSet(object):

    """computing a set of numbers imin .. imax might consume time and
    memory for big hdf5 tables. We use this below to speed up row filtering.

    this class implements a minimal interface for evaluating "i in range_set" 
    and "len(range_set)".
    """

    def __init__(self, imin, imax):
        self.imin = imin
        self.imax = imax

    def __contains__(self, i):
        return self.imin <= i < self.imax

    def __len__(self):
        return self.imax - self.imin

    def intersection(self, other):
        return {i for i in other if self.imin <= i < self.imax}

