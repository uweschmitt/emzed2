#encoding: utf-8


def _setupIsotopeDistributionGenerator(formula, R, fullC13, minp, **kw):
    from emzed.core.chemistry import IsotopeDistributionGenerator
    if fullC13:
        kw.update(dict(C=dict(C12=0.0, C13=1.0)))
    return IsotopeDistributionGenerator(formula, R, minp, **kw)


def plotIsotopeDistribution(formula, R=None, fullC13=False, minp=0.01,
                            plotGauss=None, **kw):
    """
    plots isotope distribution for given molecular formula *formula*.
    for all parameters, despite *plotGauss*: see isotopeDistributionTable()

    If *R* is provided, gaussian peaks are plotted, else centroids.
    This behavior can be overrun by setting *plotGauss* to *True* or *False*.

    If *plotGauss* is *True*, bell shaped curves are plotted, else the
    centroids according to the used resolution are shown.

    For low *minp* the choice *plotGauss=False* the plot is drawn faster.

    .. pycon::

       emzed.utils.plotIsotopeDistribution("C3H7NO2", C=dict(C13=0.5, C12=0.5), R=5000) !noexec

    .. image:: isopattern_alanin.png

    """
    gen = _setupIsotopeDistributionGenerator(formula, R, fullC13, minp, **kw)
    gen.show(plotGauss)


def isotopeDistributionTable(formula, R=None, fullC13=False, minp=0.01, **kw):
    """
    generates Table for most common isotopes of molecule with given mass
    *formula*.

    If the resolution *R* is given, the measurement device is simulated, and
    overlapping peaks may merge.

    *fullC13=True* assumes that only C13 carbon is present in formula.

    Further you can give a threshold *minp* for considering only isotope
    peaks with an abundance above the value. Standard is *minp=0.01*.

    If you have special elementary isotope abundances which differ from
    the natural abundances, you can tell that like
    ``emzed.utils.isotopeDistributionTable("S4C4", C=dict(C13=0.5, C12=0.5))``

    Examples:

    .. pycon::

       import emzed
       # natural abundances:
       tab = emzed.utils.isotopeDistributionTable("C3H7NO2")
       tab.abundance /= tab.abundance.sum()
       print tab

       # artifical abundances:
       tab = emzed.utils.isotopeDistributionTable("C3H7NO2", C=dict(C13=0.5, C12=0.5))
       tab.abundance /= tab.abundance.sum()
       print tab

    \
    """
    from ..core.data_types import Table
    gen = _setupIsotopeDistributionGenerator(formula, R, fullC13, minp, **kw)
    t = Table(["mf", "mass", "abundance"], [str, float, float],
                                           ["%s", "%.6f", "%.3f"], [])
    for mass, formula, abundance in gen.getCentroids():
        t.addRow([formula, mass, abundance], False)
    t.resetInternals()
    t.replaceColumn("abundance", t.abundance / t.abundance.sum, format_ = "%.4f", type_=float)
    return t
