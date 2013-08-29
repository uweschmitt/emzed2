import emzed.io
import os.path

def test_csv_parsing():
    here = os.path.dirname(os.path.abspath(__file__))
    tab = emzed.io.loadCSV(os.path.join(here, "data", "mass.csv"))
    #fms = '"%.2fm" % (o/60.0)'
    assert tab.getFormat("RT_min") == "%.2f"
