from emzed.core.patch_utils import replace, add

def _interpret_indexing(self, keys):
    """Internal routine used by __getitem__ and __setitem__"""

    # we added handling of OverflowError below which is a bug in pytables
    # and happens for huge tables although this is not necessary.
    # the modifications in this function are:
    # - the next two lines of import statements
    # - the exception handling for OverflowError below

    from tables.array import numpy, SizeType, is_idx
    import math

    maxlen = len(self.shape)
    shape = (maxlen,)
    startl = numpy.empty(shape=shape, dtype=SizeType)
    stopl = numpy.empty(shape=shape, dtype=SizeType)
    stepl = numpy.empty(shape=shape, dtype=SizeType)
    stop_None = numpy.zeros(shape=shape, dtype=SizeType)
    if not isinstance(keys, tuple):
        keys = (keys,)
    nkeys = len(keys)
    dim = 0
    # Here is some problem when dealing with [...,...] params
    # but this is a bit weird way to pass parameters anyway
    for key in keys:
        ellipsis = 0  # Sentinel
        if isinstance(key, type(Ellipsis)):
            ellipsis = 1
            for diml in xrange(dim, len(self.shape) - (nkeys - dim) + 1):
                startl[dim] = 0
                stopl[dim] = self.shape[diml]
                stepl[dim] = 1
                dim += 1
        elif dim >= maxlen:
            raise IndexError("Too many indices for object '%s'" %
                                self._v_pathname)
        elif is_idx(key):
            key = operator.index(key)

            # Protection for index out of range
            if key >= self.shape[dim]:
                raise IndexError("Index out of range")
            if key < 0:
                # To support negative values (Fixes bug #968149)
                key += self.shape[dim]
            start, stop, step = self._process_range(
                key, key + 1, 1, dim=dim)
            stop_None[dim] = 1
        elif isinstance(key, slice):
            start, stop, step = self._process_range(
                key.start, key.stop, key.step, dim=dim)
        else:
            raise TypeError("Non-valid index or slice: %s" % key)
        if not ellipsis:
            startl[dim] = start
            stopl[dim] = stop
            stepl[dim] = step
            dim += 1

    # Complete the other dimensions, if needed
    if dim < len(self.shape):
        for diml in xrange(dim, len(self.shape)):
            startl[dim] = 0
            stopl[dim] = self.shape[diml]
            stepl[dim] = 1
            dim += 1

    # Compute the shape for the container properly. Fixes #1288792
    shape = []
    for dim in xrange(len(self.shape)):
        # The negative division operates differently with python scalars
        # and numpy scalars (which are similar to C conventions). See:
        # http://www.python.org/doc/faq/programming.html#why-does-22-10-return-3
        # and
        # http://www.peterbe.com/Integer-division-in-programming-languages
        # for more info on this issue.
        # I've finally decided to rely on the len(xrange) function.
        # F. Alted 2006-09-25
        # Switch to `lrange` to allow long ranges (see #99).
        # use xrange, since it supports large integers as of Python 2.6
        # see github #181
        try:
            new_dim = len(xrange(startl[dim], stopl[dim], stepl[dim]))
        except OverflowError:
            a, b, c = startl[dim], stopl[dim], stepl[dim]
            new_dim = int(math.ceil(abs(b - a) / abs(c)))

        if not (new_dim == 1 and stop_None[dim]):
            shape.append(new_dim)

    return startl, stopl, stepl, shape

def apply_():
    # checking for valid values from beginning:
    import guidata.dataset.qtitemwidgets
    @replace(guidata.dataset.qtitemwidgets.LineEditWidget.__init__)
    def __init__(self, item, parent_layout):
        guidata.dataset.qtitemwidgets.LineEditWidget._orig___init__(self, item, parent_layout)
        if not item.check_value(item.get()):
            self.edit.setStyleSheet("background-color:rgb(255, 175, 90);")

    from tables.array import Array
    Array._interpret_indexing = _interpret_indexing
    _interpret_indexing.patched = True
