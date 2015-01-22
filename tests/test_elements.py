from emzed.core.chemistry import Elements, MonoIsotopicElements
from emzed.core.chemistry import monoisotopicMass


import pyopenms
IS_PYOPENMS_2  = pyopenms.__version__.startswith("2.")

def test_elements():
    el = MonoIsotopicElements()
    el2 = MonoIsotopicElements()
    assert el.rows is el2.rows # check if borg is working. which reduces startup

    el.sortBy("number")
    assert el.symbol.values[0] == "H"
    assert el.name.values[0] == "Hydrogen"
    assert abs(el.m0.values[0]-1.0078250319)<1e-7

    m0H = monoisotopicMass("H")
    assert abs(m0H-el.m0.values[0])<1e-12
    m0H = monoisotopicMass("H2")
    assert abs(m0H-2*el.m0.values[0])<1e-12

    assert abs(monoisotopicMass("NaCl")-57.9586219609)<1e-7, monoisotopicMass("NaCl")

    el3 = Elements()
    assert len(el3) == 108 if IS_PYOPENMS_2 else 102

    assert len(el3.getColNames()) == 6
    assert len(el3.number.values)
    assert len(el3.symbol.values)
    assert len(el3.name.values)
    assert len(el3.massnumber.values)
    assert len(el3.mass.values)
    assert len(el3.abundance.values)




