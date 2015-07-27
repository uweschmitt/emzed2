import numpy

import emzed.utils


def testIDGen(regtest):
    t = emzed.utils.isotopeDistributionTable("S4C4", R=50000)
    t._print(out=regtest)

    t = emzed.utils.isotopeDistributionTable("S4C4", R=10000)

    t._print(out=regtest)

    t = emzed.utils.isotopeDistributionTable("S4C4", R=10000, fullC13=True)
    t._print(out=regtest)

    t = emzed.utils.isotopeDistributionTable("C4", R=10000, C=dict(C12=0.5, C13=0.5))
    t._print(out=regtest)

    t = emzed.utils.isotopeDistributionTable("C4Cl", R=None)
    t._print(out=regtest)
