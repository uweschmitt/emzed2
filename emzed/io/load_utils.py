# encoding: utf-8


from utils import _prepare_path


def loadPeakMap(path=None):
    """ loads mzXML, mzML and mzData files

        If *path* is missing, a dialog for file selection is opened
        instead.
    """

    # local import in order to keep namespaces clean
    from ..core.data_types import PeakMap

    path = _prepare_path(path, extensions=["mzML", "mzXML", "mzData"])
    if path is None:
        return None

    return PeakMap.load(path)


def loadTable(path=None, compress_after_load=True):
    """ load pickled table

        If *path* is missing, a dialog for file selection is opened
        instead.
    """

    # local import in order to keep namespaces clean
    from ..core.data_types import Table

    path = _prepare_path(path, extensions=["table"])
    if path is None:
        return None

    result = Table.load(path)
    if compress_after_load:
        result.compressPeakMaps()
    return result


def loadCSV(path=None, sep=";", keepNone=False, **specialFormats):
    """
    loads csv file from path. column separator is given by *sep*.
    If *keepNone* is set to True, "None" strings in file are kept as a string.
    Else this string is converted to Python None values.
    *specialFormats* collects positional arguments for setting formats
    of columns.

    Example: ``emzed.io.loadCSV("abc.csv", mz="%.3f")``

    """

    from ..core.data_types import Table

    path = _prepare_path(path, extensions=["csv"])
    if path is None:
        return None

    result = Table.loadCSV(path)
    return result


def loadBlob(path=None):
    path = _prepare_path(path, None)
    if path is None:
        return None

    from emzed.core.data_types.col_types import Blob
    import os.path

    with open(path, "rb") as fp:
        data = fp.read()
    __, ext = os.path.splitext(path)
    type_ = ext[1:].upper()   # remove leading "."
    return Blob(data, type_)
