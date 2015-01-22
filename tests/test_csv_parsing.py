import pdb
import emzed
import os.path

def test_csv_parsing():
    here = os.path.dirname(os.path.abspath(__file__))
    tab = emzed.io.loadCSV(os.path.join(here, "data", "mass.csv"))
    #fms = '"%.2fm" % (o/60.0)'
    assert tab.getFormat("RT_min") == "%.2f"


def test_type_converion(tmpdir):
    t = emzed.utils.toTable("id", (1, "1A"))
    # test conversion
    assert t.id.values == ("1", "1A")

    # dirty addition
    t.rows.append([2])
    t.resetInternals()
    assert t.id.values == ("1", "1A", 2)

    path = tmpdir.join("1.csv").strpath
    
    emzed.io.storeCSV(t, path)
    t = emzed.io.loadCSV(path)
    assert t.id.values == ("1", "1A", "2")
    assert t.getColTypes() == [str]
