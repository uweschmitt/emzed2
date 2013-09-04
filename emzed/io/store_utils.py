#encoding: utf-8

def storePeakMap(pm, path=None):
    """ Stores peakmap *pm* in mzXML, mzML or mzData format.
        The used format depends on the file extension given
        in *path*. If no *path* is given, a dialog for
        choosing an output file name is opened.
    """

    # local import in order to keep namespaces clean
    import sys
    from pyopenms import FileHandler

    if isinstance(path, unicode):
        path = path.encode(sys.getfilesystemencoding())
    elif path is None:
        from .. import gui
        path = gui.askForSave(extensions="mzML mzXML mzData".split())
        if path is None:
            return None

    if sys.platform == "win32":
        path = path.replace("/","\\") # needed for network shares

    experiment = pm.toMSExperiment()
    fh = FileHandler()
    fh.storeExperiment(path, experiment)


def storeTable(tab, path=None, forceOverwrite=False):
    """ Saves *tab* in a binary ``.table`` file.
        If *path* is not provided, a file dialog opens
        for choosing the files name and location.

        *path* must have file extension ``.table``.
    """

    # local import in order to keep namespaces clean
    import sys

    tab.compressPeakMaps()

    if isinstance(path, unicode):
        path = path.encode(sys.getfilesystemencoding())
    elif path is None:
        startAt = tab.meta.get("loaded_from", "")
        from .. import gui
        path = gui.askForSave(extensions=["table"], startAt=startAt)
        if path is None:
            return None
    tab.store(path, forceOverwrite)


def storeCSV(tab, path=None):
    """ Saves *tab* in a textual ``.csv`` file.
        If *path* is not provided, a file dialog opens
        for choosing the files name and location.
    """

    # local import in order to keep namespaces clean
    import sys

    if isinstance(path, unicode):
        path = path.encode(sys.getfilesystemencoding())
    elif path is None:
        from .. import gui
        path = gui.askForSave(extensions=["csv"])
        if path is None:
            return None
    tab.storeCSV(path)
