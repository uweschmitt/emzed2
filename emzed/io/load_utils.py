# encoding: utf-8


from utils import _prepare_path

def loadPeakMap(path=None):
    """ loads mzXML, mzML and mzData files

        If *path* is missing, a dialog for file selection is opened
        instead.
    """

    # local import in order to keep namespaces clean
    import os.path
    import sys
    from pyopenms import MSExperiment, FileHandler
    from ..core.data_types import PeakMap

    path = _prepare_path(path, extensions=["mzML", "mzXML", "mzData"])
    if path is None:
        return None

    # open-ms returns empty peakmap if file not exists, so we
    # check ourselves:
    if not os.path.exists(path):
        raise Exception("file %s does not exist" % path)
    if not os.path.isfile(path):
        raise Exception("path %s is not a file" % path)

    experiment = MSExperiment()
    fh = FileHandler()
    if sys.platform == "win32":
        path = path.replace("/", "\\")  # needed for network shares
    fh.loadExperiment(path, experiment)

    return PeakMap.fromMSExperiment(experiment)


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
    # local import in order to keep namespaces clean
    import csv
    import os.path
    import re

    from ..core.data_types.table import (Table, common_type_for, bestConvert, guessFormatFor)

    path = _prepare_path(path, extensions=["csv"])
    if path is None:
        return None

    with open(path, "r") as fp:
        # remove clutter at right margin
        reader = csv.reader(fp, delimiter=sep)
        # reduce multiple spaces to single underscore
        colNames = [re.sub(" +", "_", n.strip()) for n in reader.next()]

        if keepNone:
            conv = bestConvert
        else:
            conv = lambda v: None if v == "None" else bestConvert(v)

        rows = [[conv(c.strip()) for c in row] for row in reader]

    columns = [[row[i] for row in rows] for i in range(len(colNames))]
    types = [common_type_for(col) for col in columns]

    # defaultFormats = {float: "%.2f", str: "%s", int: "%d"}
    formats = dict([(name, guessFormatFor(name, type_)) for (name, type_) in zip(colNames, types)])
    formats.update(specialFormats)

    formats = [formats[n] for n in colNames]

    title = os.path.basename(path)
    meta = dict(loaded_from=os.path.abspath(path))
    return Table._create(colNames, types, formats, rows, title, meta)


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
