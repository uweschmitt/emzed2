from emzed.core.chemistry import Elements, MonoIsotopicElements
from emzed.core.chemistry import monoisotopicMass

import pyopenms

IS_PYOPENMS_2 = pyopenms.__version__.startswith("2.")


def test_elements(regtest):
    el = MonoIsotopicElements()
    el2 = MonoIsotopicElements()
    assert el.rows is el2.rows  # check if borg is working. which reduces startup

    el.sortBy("number")
    el.print_(out=regtest)

    el3 = Elements()
    el3.sortBy("number")

    assert len(el3) == 199 if IS_PYOPENMS_2 else 102

def test_mass_calculation():

    el = MonoIsotopicElements()
    m0H = monoisotopicMass("H")
    assert abs(m0H - el.m0.values[1]) < 1e-12
    m0H = monoisotopicMass("H2")
    assert abs(m0H - 2 * el.m0.values[1]) < 1e-12

    assert abs(monoisotopicMass("NaCl") - 57.9586219609) < 1e-7, monoisotopicMass("NaCl")

