#encoding: utf-8

def loadPeakMap(path=None):
    """ loads mzXML, mzML and mzData files

        If *path* is missing, a dialog for file selection is opened
        instead.
    """

    # local import in order to keep namespaces clean
    import emzed.gui
    import os.path
    import sys
    from   pyopenms import MSExperiment, FileHandler
    from   ..core.data_types import PeakMap

    if isinstance(path, unicode):
        path = path.encode(sys.getfilesystemencoding())
    elif path is None:
        path = emzed.gui.askForSingleFile(extensions="mzML mzXML mzData".split())
        if path is None:
            return None

    # open-ms returns empty peakmap if file not exists, so we
    # check ourselves:
    if not os.path.exists(path):
        raise Exception("file %s does not exist" % path)
    if not os.path.isfile(path):
        raise Exception("path %s is not a file" % path)

    experiment = MSExperiment()
    fh  = FileHandler()
    if sys.platform == "win32":
        path = path.replace("/","\\") # needed for network shares
    fh.loadExperiment(path, experiment)

    return PeakMap.fromMSExperiment(experiment)


def loadTable(path=None):
    """ load pickled table

        If *path* is missing, a dialog for file selection is opened
        instead.
    """

    # local import in order to keep namespaces clean
    import emzed.gui
    import sys
    from   ..core.data_types import Table

    if isinstance(path, unicode):
        path = path.encode(sys.getfilesystemencoding())
    elif path is None:
        path = emzed.gui.askForSingleFile(extensions=["table"])
        if path is None:
            return None

    result = Table.load(path)
    result.compressPeakMaps()
    return result

def loadCSV(path=None, sep=";", keepNone = False, **specialFormats):
    # local import in order to keep namespaces clean
    import emzed.gui
    import csv, os.path, sys, re
    #from   libms.DataStructures.Table import (Table, common_type_for,\
                                              #bestConvert, guessFormatFor)

    from ..core.data_types.table import (Table, common_type_for, bestConvert, guessFormatFor)

    if isinstance(path, unicode):
        path = path.encode(sys.getfilesystemencoding())
    elif path is None:
        path = emzed.gui.askForSingleFile(extensions=["csv"])
        if path is None:
            return None

    with open(path,"r") as fp:
        # remove clutter at right margin
        reader = csv.reader(fp, delimiter=sep)
        # reduce multiple spaces to single underscore
        colNames = [ re.sub(" +", "_", n.strip()) for n in reader.next()]

        if keepNone:
            conv = bestConvert
        else:
            conv = lambda v: None if v=="None" else bestConvert(v)

        rows = [ [conv(c.strip()) for c in row] for row in reader]


    columns = [[row[i] for row in rows] for i in range(len(colNames))]
    types = [common_type_for(col) for col in columns]

    #defaultFormats = {float: "%.2f", str: "%s", int: "%d"}
    formats = dict([(name, guessFormatFor(name,type_)) for (name, type_)\
                                                  in zip(colNames, types)])
    formats.update(specialFormats)

    formats = [formats[n] for n in colNames]

    title = os.path.basename(path)
    meta = dict(loaded_from=os.path.abspath(path))
    return Table._create(colNames, types, formats, rows, title, meta)
