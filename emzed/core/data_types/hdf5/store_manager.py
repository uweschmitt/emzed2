from store_base import Store

# importing the classes below already registers them !
from peakmap_store import PeakMapStore
from timeseries_store import TimeSeriesStore
from string_store import StringStore
from object_store import ObjectStore


def setup_manager(file_, node=None):

    if node is None:
        node = file_.root

    manager = Store(file_, node)
    return manager


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
