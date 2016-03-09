from emzed.core import PeakMap
import cPickle

from stores import (Store, PeakMapStore, StringStore, ObjectStore)

class GeneralHandler(object):

    """
    every implementaion has an call attribute flag 0..7 to create a global_id which identifies the
    used implementation.
    """

    _flags = dict()
    _classes = []

    @staticmethod
    def register(flag, clz, store):
        assert 0 <= flag < 8
        assert flag not in GeneralHandler._flags
        assert isinstance(store, Store)

        GeneralHandler._flags[flag] = store
        GeneralHandler._classes.append((clz, store, flag))

    @staticmethod
    def store(obj):
        for (clz, store, flag) in GeneralHandler._classes:
            if isinstance(obj, clz):
                id_ = store.write(obj)
                global_id = id_ << 3 | flag
                return global_id
        raise TypeError("no store manager for %r found" % obj)

    @staticmethod
    def fetch(global_id):
        assert isinstance(global_id, (int, long))
        for flag in GeneralHandler._flags:
            if global_id & 7 == flag:
                return GeneralHandler._flags[flag].read(global_id >> 3)

    @staticmethod
    def finalize():
        for store in GeneralHandler._flags.values():
            store.finalize()


# order of regisration mattters:


def setup(file_, node):

    GeneralHandler.register(1, PeakMap, PeakMapStore(file_, node))
    GeneralHandler.register(2, basestring, StringStore(file_, node))
    GeneralHandler.register(7, object, ObjectStore(file_, node))

    store = GeneralHandler.store
    fetch = GeneralHandler.fetch
    finalize = GeneralHandler.finalize

    return store, fetch, finalize


if __name__ == "__main__":
    from tables import open_file
    file_ = open_file("peakmap.h5", mode="w")
    store, fetch, finalize = setup(file_, file_.root)

    #import emzed
    #pm = emzed.io.loadPeakMap("141208_pos001.mzXML")

    data =" asdlfadlsfjal "* 10
    data = (1, 2, 3)

    import time
    s = time.time()
    id_ = store(data)
    print(time.time() - s)
    s = time.time()
    id_ = store(data)
    print(time.time() - s)
    finalize()

    print(id_)
    data = fetch(id_)
    print(data)


