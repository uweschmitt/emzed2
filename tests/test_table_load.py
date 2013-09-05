

def test_load_old_versions():
    import os.path
    import glob
    import emzed.io
    here = os.path.dirname(os.path.abspath(__file__))
    for p in glob.glob(os.path.join(here, "data/feature_table_?.?.?.table")):
        print "load", p
        emzed.io.loadTable(p)
