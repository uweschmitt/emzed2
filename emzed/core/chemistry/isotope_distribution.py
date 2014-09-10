import math
import itertools
import numpy as np

from elements import Elements
from molecular_formula import MolecularFormula


def multinomial(abundances, partition):
    """ mutinomial probability for

        (k1+...+kn)! / ( k1! ... kn!) * p1^k1 * ...* pn^kn

        with:
            partition = (k1, ... kn)
            abundances = (p1, ... pn)
    """
    n = sum(partition)
    mult = lambda a, b: a * b
    fac = math.factorial(n)
    denom = reduce(mult, [math.factorial(si) for si in partition])
    simpleprob = reduce(mult, [abundances[i] ** ni for (i, ni) in enumerate(partition)])
    return fac / denom * simpleprob


def sum_partition(n, s):
    """ generates nonnegative n-tuples which sum up to s """
    if n == 1:
        yield [s]
    elif n == 0:
        yield []
    else:
        for i in range(s + 1):
            for k in sum_partition(n - 1, s - i):
                yield [i] + k


def merge_none_entries_to_one_single_entry(centroids):
    result = []
    else_ = 0.0
    for m, mf, a in centroids:
        if m is None:
            else_ += a
        else:
            result.append((m, mf, a))
    result.append((None, None, else_))
    return result


class IsotopeDistributionGenerator(object):

    """
    Algorithms for generating IsotopeDistributions
    """

    def __init__(self, formula, R=None, minp=0.01, **kw):
        self.formula = formula
        self.minp = minp
        self.abundances = kw
        self.centroids = self._theoreticalCentroids()
        self.R = R
        if R is not None:
            # filter out "other isotopes" with abundance < minp:
            self.centroids = [(m, iso_mf, a) for (m, iso_mf, a) in self.centroids if m is not None]
            self.centroids = self._measuredCentroids()

    def _theoreticalCentroids(self):
        """ generates mass distribution for given *formula*
        """
        allIterators = []
        for (symbol, __), count in MolecularFormula(self.formula).asDict().items():
            decompositionIterator = self._isotopeDecompositions(symbol, count)
            allIterators.append(decompositionIterator)
        centroids = []
        # iterate over crossproduct over elementwise iterators:
        for item in itertools.product(*allIterators):
            totalmass = 0.0
            totalprob = 1.0
            mfs = []
            if any(mf is None for (mf, m, p) in item):
                totalprob = reduce(lambda a, b: a * b,
                                   [p for (__, __, p) in item], 1.0)
                centroids.append((None, None, totalprob))
                continue
            for iso_mf, m, p in item:
                totalprob *= p
                totalmass += m
                mfs.append(iso_mf)
            if totalprob >= self.minp:
                centroids.append((totalmass, " ".join(mfs), totalprob))
        return merge_none_entries_to_one_single_entry(sorted(centroids))

    def _isotopeDecompositions(self, symbol, count):
        """ generates isotope distribution for *count* atoms of element
            with symbol *symbol*
            yields "molecular formula", mass, abundance for abundance < self.minp
            and at last one yield (None, None, "sum of all abundances below minp").

            The last yield helps calculating abundances which correspond to probabilites
            of isotopes.
        """
        el = Elements()
        el = el.filter(el.symbol == symbol)
        massnums = el.massnumber.values
        masses = el.mass.values
        abundances = el.abundance.values
        if symbol in self.abundances:
            abundances = [self.abundances[symbol].get(symbol + str(massnum), 0)
                          for massnum in massnums]
        # iterate over all possible decompositions of count atoms into
        # isotopes:
        summed_p_below_minp = 0.0
        for partition in sum_partition(len(massnums), count):
            prob = multinomial(abundances, partition)
            # reduce computation cost by ignoring to low probabilites:
            if prob >= self.minp:
                decomp = ["[%d]%s%d" % (m, symbol, p)
                          for (m, p) in zip(massnums, partition) if p]
                iso_mf = " ".join(decomp)
                yield iso_mf, sum(n * masses[i] for i, n in enumerate(partition)), prob
            else:
                summed_p_below_minp += prob
        yield None, None, summed_p_below_minp

    def measuredIntensity(self, m0):
        """ measured intensity at mass *m0* for given resolution """
        sum_ = 0.0
        for mass, mf, abundance in self.centroids:
            if mass is None:
                continue
            deltam = mass / self.R
            two_sigma_square = deltam * deltam / math.log(16.0)
            sum_ += abundance * np.exp(-(m0 - mass) ** 2 / two_sigma_square)
        return sum_

    def _detectMaxima(self, peaks):
        masses, formulas, abundandes = zip(*peaks)
        minMass = masses[0]
        maxMass = masses[-1]
        w2 = minMass * minMass / self.R / self.R * math.log(100) / math.log(16)
        massrange = np.arange(minMass - w2, maxMass + w2, 1e-7)
        measured = self.measuredIntensity(massrange)
        dd = np.diff(measured)
        w = np.where((dd[:-1] > 0) * (dd[1:] < 0))[0] + 1
        mzs = massrange[w]
        abundances = measured[w]
        return zip(mzs, [self.formula] * len(mzs), abundances)

    def _measuredCentroids(self):
        allGroupedPeaks = []
        window = []
        self.centroids.sort()
        lastm = self.centroids[0][0]
        if lastm is not None:
            for m, iso_mf, a in self.centroids:
                if m is None:
                    continue
                if m > lastm + 0.10:
                    allGroupedPeaks.append(window)
                    window = []
                    lastm = m
                window.append((m, iso_mf, a))
            if window:
                allGroupedPeaks.append(window)

        allCentroids = []
        for groupedPeaks in allGroupedPeaks:
            centroids = self._detectMaxima(groupedPeaks)
            allCentroids.extend(centroids)

        # remove last "None" for remaining abundances
        return allCentroids

    def plot(self, plotGauss=None):
        import matplotlib
        matplotlib.use("Qt4Agg")
        import pylab as pl
        masses =  [c[0] for c in self.centroids if c[0] is not None]
        minMass = min(masses)
        maxMass = max(masses)
        if plotGauss is None:
            plotGauss = self.R is not None
        if plotGauss:
            # decay to one percent at shfit w2:
            massrange = np.arange(minMass - 0.1, maxMass + 0.1, 50.0 / self.R)
            measured = self.measuredIntensity(massrange)
            pl.plot(massrange, measured)
        else:
            # draw axis
            pl.plot([minMass - 0.05, maxMass + 0.05], [0, 0])
            # draw sticks
            for m, __, a in self.centroids:
                pl.plot([m, m], [0, a], "b")

        # rescale y axis, looks better:
        ymin, ymax = pl.ylim()
        pl.ylim(ymin, ymax * 1.1)
        title = self.formula
        if self.R is not None:
            title += " R=%.f" % self.R
        if self.abundances:
            for values in self.abundances.values():
                for k, v in values.items():
                    title += " %s: %.2f" % (k, v)
        pl.title(title)
        pl.xlabel("m/z")
        from matplotlib.ticker import FormatStrFormatter
        pl.gca().xaxis.set_major_formatter(FormatStrFormatter("%.1f"))

    def show(self, plotGauss=True):
        import pylab as pl
        self.plot(plotGauss)
        pl.show()

    def getCentroids(self):
        return self.centroids
