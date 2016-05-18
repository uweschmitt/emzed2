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
