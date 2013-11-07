

def _prepare_path(path, extensions):

    import sys
    if isinstance(path, unicode):
        path = path.encode(sys.getfilesystemencoding())
    elif path is None:
        from .. import gui
        path = gui.askForSingleFile(extensions=extensions)
    return path
