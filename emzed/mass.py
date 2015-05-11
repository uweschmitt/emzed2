from emzed.core.chemistry import (Elements as _Elements,
                                  MonoIsotopicElements as _MonoIsotopicElements,
                                  MolecularFormula as _MolecularFormula)

e = 5.4857990946e-4
p = 1.007276466812
n = 1.00866491600

def of(mf, **specialisations):
    """computes mass of given molecular formla "mf".
    some examples for using isotopes::

        print emzed.mass.of("[13]C3")
        print emzed.mass.of("C3", C=emzed.mass.C13)
    """
    return _MolecularFormula(mf).mass(**specialisations)

_elements = _Elements()
_symbols = _elements.symbol.values
_massnumbers = _elements.massnumber.values
_isomasses = _elements.mass.values

for (_sym, _massnumber, _isomass) in zip(_symbols, _massnumbers, _isomasses):
    exec("%s=_isomass" % (_sym+str(_massnumber)))

_mono_iso_elems =  _MonoIsotopicElements()
_symbols = _mono_iso_elems.symbol.values
_m0s = _mono_iso_elems.m0.values
for (_sym, _m0) in zip (_symbols, _m0s):
    exec("%s=_m0" % _sym)



