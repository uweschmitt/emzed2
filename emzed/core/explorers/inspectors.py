from ..data_types import PeakMap, Table
from ..data_types.col_types import Blob


def has_inspector(clz):
    return clz in (PeakMap, Table, Blob)


def inspector(obj, *a, **kw):
    if isinstance(obj, PeakMap):
        from peakmap_explorer import inspectPeakMap
        return lambda: inspectPeakMap(obj, *a, **kw)
    elif isinstance(obj, Table):
        from table_explorer import inspect
        return lambda: inspect(obj, *a, **kw)
    elif isinstance(obj, (list, tuple)) and all(isinstance(t, Table) for t in obj):
        from table_explorer import inspect
        return lambda: inspect(obj, *a, **kw)
    elif isinstance(obj, Blob):
        from image_dialog import ImageDialog

        modal = kw.get("modal", True)

        if modal:
            def show():
                dlg = ImageDialog(obj.data)
                dlg.raise_()
                dlg.exec_()
        else:
            def show():
                dlg = ImageDialog(obj.data, parent=kw.get("parent"))
                dlg.show()
        return show

    return None


def inspect(*a, **kw):
    insp = inspector(*a, **kw)
    if insp is not None:
        return insp()
    else:
        raise Exception("no inspector for %r" % obj)


