# encoding: utf-8

from utils import _prepare_path


def storeBlob(data, path=None):
    assert isinstance(data, basestring)
    path = _prepare_path(path, extensions=None, store=False)
    if path is None:
        return None
    with open(path, "wb") as fp:
        fp.write(data)


def storePeakMap(pm, path=None):
    """ Stores peakmap *pm* in mzXML, mzML or mzData format.
        The used format depends on the file extension given
        in *path*. If no *path* is given, a dialog for
        choosing an output file name is opened.
    """

    # local import in order to keep namespaces clean
    import sys
    from pyopenms import FileHandler

    path = _prepare_path(path, extensions=["mzML", "mzXML", "mzData"], store=False)
    if path is None:
        return None

    if sys.platform == "win32":
        path = path.replace("/", "\\")  # needed for network shares

    experiment = pm.toMSExperiment()
    fh = FileHandler()
    fh.storeExperiment(path, experiment)


def storeTable(tab, path=None, forceOverwrite=False, compressed=True):
    """ Saves *tab* in a binary ``.table`` file.
        If *path* is not provided, a file dialog opens
        for choosing the files name and location.

        *path* must have file extension ``.table``.
    """

    # local import in order to keep namespaces clean

    path = _prepare_path(path, extensions=["table"], store=False)
    if path is None:
        return None

    tab.store(path, forceOverwrite, compressed)


def storeCSV(tab, path=None):
    """ Saves *tab* in a textual ``.csv`` file.
        If *path* is not provided, a file dialog opens
        for choosing the files name and location.
    """

    # local import in order to keep namespaces clean
    path = _prepare_path(path, extensions=["csv"], store=False)
    if path is None:
        return None
    tab.storeCSV(path)
