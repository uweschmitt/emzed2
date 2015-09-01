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

    path = _prepare_path(path, extensions=["mzML", "mzXML", "mzData"], store=False)
    if path is None:
        return None

    pm.store(path)


def storeTable(tab, path=None, forceOverwrite=False, compressed=True, peakmap_cache_folder=None):
    """Writes the table in binary format. All information, as corresponding peak maps too.

    The file name extension in ``path``must be ``.table``.

    ``forceOverwrite`` must be set to ``True`` to overwrite an existing file.

    ``compressed`` replaces duplicate copies of the same peakmap of a single one to save
    space on disk.

    ``peakmap_cache_folder`` is a folder. if provided the table data and the peakmap
    are stored separtely. so the table file can then be loaded much faster and the peakmaps are
    lazily loaded only if one tries to access their spectra. This speeds up workflows but the
    developer must care about consistency: if the peakmap folder is deleted the table may
    becom useless !

    Latter the file can be loaded with ``emzed.io.loadTable``
    """

    path = _prepare_path(path, extensions=["table"], store=False)
    if path is None:
        return None
    tab.store(path, forceOverwrite, compressed, peakmap_cache_folder)


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
