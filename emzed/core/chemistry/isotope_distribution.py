import pdb
import math
import itertools
import re

import numpy as np
from scipy.fftpack import fftn, ifftn

from molecular_formula import MolecularFormula

from ...core.chemistry.elements import (create_abundance_mapping,
                                        create_mass_mappings)



def fast_multinomial(pii, nsum, thresh):
    """generate multinomial distribution for given probability tuple pii.

    *nsum* is the overal number of atoms of a fixed element, pii is a tuple holding the
    distribution of the isotopes.

    this generator yields all combinations and their probabilities which are above *thresh*.

    Remark: the count of the first isotope of all combinations is not computed and "yielded", it is
    automatically *nsum* minus the sum of the elemens in the combinations. We could compute this
    value in this generator, but it is faster to do this later (so only if needed).

    Example:: given three isotopes ([n1]E, [n2]E, [n3]E) of an element E which have
              probabilities 0.2, 0.3 and 0.5.

    To generate all molecules consisting of 5 atoms of this element where the overall probability
    is abore 0.1 we can run:

        for index, pi in gen_n((0.2, 0.3, 0.5), 5, 0.1):
            print(index, pi)

    which prints:

        (1, 3) 0.15
        (2, 2) 0.135
        (2, 3) 0.1125

    the first combination refers to (1, 1, 3) (sum is 5), the second to (1, 2, 2) and the last to
    (0, 2, 3).

    So the probability of an molecule with the overall formula [n1]E1 [n2]E1 [n3]E3 is 0.15, for
    [n1]E1 [n2]E2 [n3]E2 is 0.135, and for [n2]E2 [n3]E3 is 0.1125.

    Implementation:: multinomial distribution can be described as the n times folding (convolution)
    of an underlying simpler distribution. convolution can be fast computed with fft + inverse
    fft as we do below.

    This is often 100 times faster than the old implementatation computing the full distribution
    using its common definition.
    """
    n = len(pii)

    if n == 1:
        yield (0,), pii[0]
        return

    dim = n - 1
    a = np.zeros((nsum + 1,) * dim)
    a[(0,) * dim] = pii[0]
    for i, pi in enumerate(pii[1:]):
        idx = [0] * dim
        idx[i] = 1
        a[tuple(idx)] = pi

    probs = ifftn(fftn(a) ** nsum).real
    mask = (probs >= thresh)
    pi = probs[mask]
    ii = zip(*np.where(mask))
    for iii, pii in zip(ii, pi):
        yield iii, pii


def gen_patterns(elems, thresh):
    """yields all isotope combinations of the given *elems* where the probability
    is above *thresh*.

    elems is a list of tuples, the first item of the tuple is the number of isotopes of a element
    in the overall mass formula, the following values are the probabilities of the isotopes.
    For example we have for the mass formula C20O6 the setting (with rounded aboundances):

        elems = [(20, .989, .011), (6, .9976, .00038, .002)]

    """
    for item in _gen_patterns(elems, thresh, 0):
        yield item


def _gen_patterns(elems, thresh, i0):
    """recursive implementation of pattern generation. the *elems* and *thresh* parameters
    are given as described for *gen_patterns*. *i0* tracks the current element when recursing
    over the items in *elems*.
    """
    if i0 < len(elems):
        sum = np.sum  # speedup, avoids dynamic lookup in iteration below
        n_atoms = elems[i0][0]
        probabilites = elems[i0][1:]
        for decomp_rec, proba_rec in _gen_patterns(elems, thresh, i0 + 1):
            if proba_rec >= thresh:
                for decomp, proba in fast_multinomial(probabilites, n_atoms, thresh / proba_rec):
                    # we complete the decomosition, because fast_multinomial ommits the first entry
                    # for improving speed:
                    decomp = (n_atoms - sum(decomp),) + decomp
                    yield (decomp,) + decomp_rec, proba_rec * proba
    else:
        yield (), 1.0


_abundances = create_abundance_mapping()
_masses, __ = create_mass_mappings()


def create_centroids(mf, thresh, fixed_abundances, _abundances=_abundances, _masses=_masses):

    def _fix_keys(dd):
        """ fixed keys like "C13" -> 13 """
        result = dict()
        for k, v in dd.items():
            k = int(re.sub("[A-Z][a-z]?", "", k))
            result[k] = v
        return result

    aa = []
    mi = []
    elems = []
    massnums = []
    for (elem, __), count in MolecularFormula(mf).asDict().items():
        if elem in fixed_abundances:
            isos = sorted(_fix_keys(fixed_abundances[elem]).items())
        else:
            isos = sorted(_abundances[elem].items())
        counts, abundances = zip(*isos)
        masses = [_masses[elem][ci] for ci in counts]
        tp = (count,) + abundances
        aa.append(tp)
        mi.append(masses)
        elems.append(elem)
        massnums.append(counts)

    centroids = []
    for comb, p0 in gen_patterns(aa, thresh):
        mass_sum = 0.0
        mf = []
        for elem_idx, iso_dist in enumerate(comb):
            for (iso_num, num_iso) in enumerate(iso_dist):
                if num_iso:
                    single_mass = mi[elem_idx][iso_num]
                    mass_sum += single_mass * num_iso
                    mn = massnums[elem_idx][iso_num]
                    mfi = "[%d]%s%d" % (mn, elems[elem_idx], num_iso)
                    mf.append(mfi)
        centroids.append([mass_sum, " ".join(mf), p0])

    return centroids


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
        centroids = create_centroids(self.formula, self.minp, self.abundances)
        centroids.sort()
        # add line with summed up abundance of isotopologues filtered out because
        # of thresholding:
        missing = 1.0 - sum(abundance for (__, __, abundance) in centroids)
        centroids.append((None, None, missing))
        return centroids

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
