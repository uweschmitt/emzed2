from emzed.core.chemistry import (MolecularFormula as _MolecularFormula)

from emzed.core.chemistry.elements import (Elements as _Elements,
                                           MonoIsotopicElements as _MonoIsotopicElements,
                                           create_mass_mappings)

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

_all_masses, _mono_masses = create_mass_mappings()

for symbol, masses in _all_masses.items():
    for mass_number, mass in masses.items():
        locals()["%s%d" % (symbol, mass_number)] = mass

for symbol, mono_mass in _mono_masses.items():
    locals()[symbol] = mono_mass

# cleanup namespace
del symbol, masses, mass_number, mass, mono_mass
