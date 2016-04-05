from .. import PeakMap, TimeSeries

from stores import (Store, PeakMapStore, StringStore, ObjectStore, TimeSeriesStore)



class StoreManager(object):

    """
    every implementaion has an call attribute flag 0..7 to create a global_id which identifies the
    used implementation.
    """

    def __init__(self):
        self._flags = dict()
        self._classes = []

    def register(self, flag, clz, store):
        assert 0 <= flag < 8
        # assert flag not in StoreManager._flags
        assert isinstance(store, Store)

        self._flags[flag] = store
        self._classes.append((clz, store, flag))

    def store_object(self, obj):
        for (clz, store, flag) in self._classes:
            if isinstance(obj, clz):
                id_ = store.write(obj)
                global_id = id_ << 3 | flag
                return global_id
        raise TypeError("no store manager for %r found" % obj)

    def fetch(self, global_id):
        assert isinstance(global_id, (int, long))
        for flag in self._flags:
            if global_id & 7 == flag:
                return self._flags[flag].read(global_id >> 3)

    def finalize(self):
        for store in self._flags.values():
            store.finalize()

    def close(self):
        for store in self._flags.values():
            store.close()

# order of regisration mattters:


def setup_manager(file_, node=None):

    if node is None:
        node = file_.root

    manager = StoreManager()
    manager.register(0, PeakMap, PeakMapStore(file_, node))
    manager.register(1, TimeSeries, TimeSeriesStore(file_, node))
    manager.register(6, basestring, StringStore(file_, node))
    manager.register(7, object, ObjectStore(file_, node))
    return manager


if __name__ == "__main__":
    from tables import open_file
    file_ = open_file("peakmap.h5", mode="w")
    store, fetch, finalize = setup(file_, file_.root)

    #import emzed
    #pm = emzed.io.loadPeakMap("141208_pos001.mzXML")

    data = " asdlfadlsfjal " * 10
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
