import numpy

import emzed.utils

def testIDGen():
    t = emzed.utils.isotopeDistributionTable("S4C4", R=50000)
    assert len(t) == 4
    t = emzed.utils.isotopeDistributionTable("S4C4", R=10000)
    assert len(t) == 3
    t._print()
    assert t.mf.values == ("S4C4",) * 3
    # rounding error less than 5e-3:

    t.abundance /= t.abundance.sum()

    assert numpy.max(numpy.array(t.abundance.values)-[0.8, 0.06, 0.14]) <= 5e-3
    assert numpy.max(numpy.array(t.mass.values)-[175.888283, 176.889972,
        177.884081]) < 5e-7

    t = emzed.utils.isotopeDistributionTable("S4C4", R=10000, fullC13=True)
    t.abundance /= t.abundance.sum()
    t._print()
    assert len(t) == 3
    assert t.mf.values == ("S4C4",) * 3
    assert numpy.max(numpy.array(t.abundance.values)-[0.82, 0.03, 0.15]) <= 5e-3
    assert numpy.max(numpy.array(t.mass.values)-[179.901703, 180.901091,
        181.897501]) < 5e-7

    t = emzed.utils.isotopeDistributionTable("C4", R=10000, C=dict(C12=0.5, C13=0.5))
    t.abundance /= t.abundance.sum()
    t._print()
    assert len(t) == 5
    assert t.mf.values == ("C4",) * 5
    assert numpy.max(numpy.array(t.abundance.values)-[0.06, 0.25, 0.37, 0.25, 0.06]) <= 5e-3
    assert numpy.max(numpy.array(t.mass.values)-[48.000000, 49.003355, 50.006710, 51.010065, 52.013420]) < 5e-7

    # for R=None exact formulas for peaks should be created, we check this:
    t = emzed.utils.isotopeDistributionTable("C4Cl", R=None)
    assert len(t) == 4
    assert all(abs(m1-m2) < 1e-5 for (m1, m2) in zip(t.mass.values,
                                                     t.mf.apply(emzed.mass.of).values))
