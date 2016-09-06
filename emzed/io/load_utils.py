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


def loadCSV(path=None, sep=";", keepNone=False, dashIsNone=True, **specialFormats):
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

    result = Table.loadCSV(path, sep, keepNone, dashIsNone, **specialFormats)
    return result


def loadBlob(path=None):
    path = _prepare_path(path, extensions=None)
    if path is None:
        return None

    from emzed.core.data_types.col_types import Blob
    import os.path

    with open(path, "rb") as fp:
        data = fp.read()
    __, ext = os.path.splitext(path)
    type_ = ext[1:].upper()   # remove leading "."
    return Blob(data, type_)


def loadExcel(path=None, sheetname=0, types=None, formats=None):
    """`sheetname` is either an intger or string for indicating the sheet which will be extracted
    from the .xls or .xlsx file. The index 0 refers to the first sheet.

    `types` is either None or a dictionary mapping column names to their types.

    `formats` is either None or a dictionary mapping column names to formats.
    """
    path = _prepare_path(path, extensions=["xls", "xlsx"])
    if path is None:
        return None

    from emzed.core.data_types import Table
    import pandas

    # sheetname is reuqired for pandas < 0.14.0, later versions have default 0
    df = pandas.read_excel(path, sheetname=sheetname)
    return Table.from_pandas(df, types=types, formats=formats)
