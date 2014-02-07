import math
import itertools
import re
import numpy as np

from elements import Elements


def multinomial(abundances, partition):
    """ mutinomial probability for

        (k1+...+kn)! / ( k1! ... kn!) * p1^k1 * ...* pn^kn

        with:
            partition = (k1, ... kn)
            abundances = (p1, ... pn)
    """
    n = sum(partition)
    mult = lambda a,b: a*b
    fac = math.factorial(n)
    denom = reduce(mult, [math.factorial(si) for si in partition])
    simpleprob = reduce(mult, [abundances[i]**n for (i,n) in enumerate(partition)])
    return fac/denom * simpleprob

def sum_partition(n, s):
    """ generates nonnegative n-tuples which sum up to s """
    if n==1:
        yield [s]
    elif n==0:
        yield []
    else:
        for i in range(s+1):
            for k in sum_partition(n-1, s-i):
                yield [i] + k

def split_atoms(mf):
    for symbol, count in  re.findall("([A-Z][a-z]?)(\d*)", mf):
        if count=="":
            count ="1"
        count = int(count)
        yield symbol, count


def normalized(centroids):
    # scale amplitudes: m0 has 1.0
    if len(centroids):
        m, mf, a0 = centroids[0]
        return [ (m, mf, a/a0) for m, mf, a in centroids ]
    return []

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
            self.centroids = self._measuredCentroids()

    def _theoreticalCentroids(self):
        """ generates mass distribution for given *formula* """
        allIterators = []
        # split formula into symbols+counts of elements
        for symbol, count in split_atoms(self.formula):
            decompositionIterator = self._isotopeDecompositions(symbol, count)
            allIterators.append(decompositionIterator)
        centroids = []
        # iterate over crossproduct over elementwise iterators:
        for item in itertools.product(*allIterators):
            totalmass = 0.0
            totalprob = 1.0
            mfs = []
            for iso_mf, m, p in item:
                totalmass += m
                totalprob *= p
                mfs.append(iso_mf)
            if totalprob >= self.minp:
                centroids.append((totalmass, " ".join(mfs), totalprob))
        return normalized(sorted(centroids))

    def _isotopeDecompositions(self, symbol, count):
        """ generates isotope distribution for *count* atoms of element
            with symbol *symbol*
        """
        el = Elements()
        el = el.filter(el.symbol==symbol)
        massnums = el.massnumber.values
        masses = el.mass.values
        abundances = el.abundance.values
        if symbol in self.abundances:
            abundances = [self.abundances[symbol].get(symbol+str(massnum),0)\
                          for massnum in massnums]
        # iterate over all possible decompositions of count atoms into
        # isotopes:
        for partition in sum_partition(len(massnums), count):
            prob = multinomial(abundances, partition)
            # reduce computation cost by ignoring to low probabilites:
            if prob >= self.minp:
                decomp = ["[%d]%s%d" % (m, symbol, p) for (m, p) in zip(massnums, partition) if p]
                iso_mf = " ".join(decomp)
                yield iso_mf, sum(n*masses[i] for i,n in enumerate(partition)), prob

    def measuredIntensity(self, m0):
        """ measured intensity at mass *m0* for given resolution """
        sum_ = 0.0
        for mass, mf, abundance in self.centroids:
            deltam =  mass/self.R
            two_sigma_square = deltam*deltam/math.log(16.0)
            sum_ += abundance*np.exp(-(m0-mass)**2/two_sigma_square)
        return sum_

    def _detectMaxima(self, peaks):
        masses, formulas, abundandes = zip(*peaks)
        minMass = masses[0]
        maxMass = masses[-1]
        w2 = minMass*minMass/self.R/self.R*math.log(100)/math.log(16)
        massrange = np.arange(minMass-w2, maxMass+w2, 1e-7)
        measured = self.measuredIntensity(massrange)
        dd = np.diff(measured)
        w = np.where((dd[:-1]>0)*(dd[1:] <0))[0]+1
        mzs = massrange[w]
        abundances = measured[w]
        return zip(mzs, [self.formula] * len(mzs), abundances)

    def _measuredCentroids(self):
        allGroupedPeaks = []
        window = []
        self.centroids.sort()
        lastm = self.centroids[0][0]
        for m, iso_mf, a in self.centroids:
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

        return normalized(allCentroids)

    def plot(self, plotGauss=None):
        import matplotlib
        matplotlib.use("Qt4Agg")
        import pylab as pl
        minMass = self.centroids[0][0]
        maxMass = self.centroids[-1][0]
        if plotGauss is None:
            plotGauss = self.R is not None
        if plotGauss:
            # decay to one percent at shfit w2:
            massrange = np.arange(minMass-0.1, maxMass+0.1, 50.0/self.R)
            measured = self.measuredIntensity(massrange)
            pl.plot(massrange, measured)
        else:
            # draw axis
            pl.plot([minMass-0.05, maxMass+0.05],[0,0])
            # draw sticks
            for m, a in self.centroids:
                pl.plot([m, m], [0,a], "b")

        # rescale y axis, looks better:
        ymin, ymax = pl.ylim()
        pl.ylim(ymin, ymax*1.1)
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

