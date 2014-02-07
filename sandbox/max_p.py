import emzed


import math
import numpy as np


def fac(n):
    return math.gamma(n + 1)


def binom(n, m):
    return fac(n) / fac(m) / fac(n - m)


def test(elem, n):

    abundances = getattr(emzed.abundance, elem)
    p = max(abundances.values())

    print emzed.utils.isotopeDistributionTable("%s%d" % (elem, n))

    k = p * n
    print k

def max_p(p1, p2):
    from math import log, sqrt


    def f(n):
        return n * (n - 1) * p1 * p2 * (1.0 - p1 -p2) ** (n-2)

    print f(8)

    n = -1/2.0*(sqrt(log(-p1 - p2 + 1)**2 + 4) - log(-p1 - p2 + 1) + 2)/log(-p1 - p2 + 1)
    print n
    print f(int(round(n)-1))
    print f(int(round(n)))
    print f(int(round(n)+1))

    import pylab
    x = np.arange(n*2)
    y = f(x)
    pylab.plot(x, y)
    print
    n = 1/2.0*(sqrt(log(-p1 - p2 + 1)**2 + 4) + log(-p1 - p2 + 1) - 2)/log(-p1 - p2 + 1)
    print n
    print f(int(round(n)-1))
    print f(int(round(n)))
    print f(int(round(n)+1))
    pylab.show()


if __name__ == "__main__":
    import emzed
    t = emzed.utils.isotopeDistributionTable("N4Cl4", minp=0.0001)
    t.replaceColumn("abundance", t.abundance / t.abundance.sum(), format_="%.4f")
    print t
    t = emzed.utils.isotopeDistributionTable("NClH6", minp=0.0001)
    t.replaceColumn("abundance", t.abundance / t.abundance.sum(), format_="%.4f")
    print t
    t = emzed.utils.isotopeDistributionTable("Cl4", minp=0.0001)
    t.replaceColumn("abundance", t.abundance / t.abundance.sum(), format_="%.4f")
    print t

    max_p(emzed.abundance.N15, emzed.abundance.Cl37)





