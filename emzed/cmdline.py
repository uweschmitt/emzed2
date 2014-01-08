def inspect():
    import sys
    to_show = sys.argv[1]
    import emzed
    if to_show.endswith(".table"):
        emzed.gui.inspect(emzed.io.loadTable(to_show))
    else:
        emzed.gui.inspect(emzed.io.loadPeakMap(to_show))
