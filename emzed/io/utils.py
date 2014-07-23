

def _prepare_path(path, extensions, store=True):
    import sys
    if isinstance(path, unicode):
        path = path.encode(sys.getfilesystemencoding())
    elif path is None:
        from .. import gui
        if store:
            path = gui.askForSingleFile(extensions=extensions)
        else:
            path = gui.askForSave(extensions=extensions)
    return path
