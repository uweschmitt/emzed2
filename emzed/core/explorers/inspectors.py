from ..data_types import PeakMap, Table
from ..data_types.col_types import Blob


def has_inspector(clz):
    return clz in (PeakMap, Table, Blob)


def inspector(obj):
    if isinstance(obj, PeakMap):
        from peakmap_explorer import inspectPeakMap
        return lambda: inspectPeakMap(obj)
    elif isinstance(obj, Table):
        from table_explorer import inspect
        return lambda: inspect(obj)
    elif isinstance(obj, Blob):
        from image_dialog import ImageDialog

        def show():
            dlg = ImageDialog(obj.data)
            dlg.raise_()
            dlg.exec_()
        return show

    return None


def inspect(obj):
    insp = inspector(obj)
    if insp is not None:
        insp()
    else:
        raise Exception("no inspector for %r" % obj)


