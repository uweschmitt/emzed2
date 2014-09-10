import emzed.core.data_types

def toTable(colName, iterable,  format_="", type_=None, title="", meta=None):
    return emzed.core.Table.toTable(colName, iterable, format_, type_, title, meta)

toTable.__doc__ = emzed.core.Table.toTable.__doc__

def formula(mf):
    """
    Creates formula object which allows addition and subtraction:

    .. pycon::

       import emzed
       mf1 = emzed.utils.formula("H2O")
       mf2 = emzed.utils.formula("NaOH")
       mf3 = mf1 + mf2
       print str(mf3)
       print str(mf3 - mf1)

    Mass calculation is supported too:

    .. pycon::

       print mf1.mass()

    If you need some internal representation, you can get a dictionary.
    Keys are pairs of *(symbol, massnumber)*, where *massnumber = None*
    refers to the lowest massnumber. Values of the dictionary are counts:

    .. pycon::

       print mf1.asDict()
       mixed = emzed.utils.formula("[13]C2[14]C3")
       print mixed.asDict()


    """
    from emzed.core.chemistry import MolecularFormula
    return MolecularFormula(mf)

def addmf(formula0, *formulas):
    """
    Combines molecular formulas by addition and subtraction:

    .. pycon::

       import emzed
       print emzed.utils.addmf("H2O", "COOH")
       print emzed.utils.addmf("H2O", "COOH", "NaCl")

    A leading minus sign subtracts the formula following this sign:

    .. pycon::

       print emzed.utils.addmf("H2O2", "-H2O")
       print emzed.utils.addmf("H2O", "COOH", "NaCl", "-H2O2")
       print emzed.utils.addmf("(CH2)7COOH", "-C7")

    """

    mf0 = formula(formula0)
    for f in formulas:
        if f.startswith("-"):
            mf0 -= formula(f[1:])
        else:
            mf0 += formula(f)
    return str(mf0)


###


def openInBrowser(urlPath):
    """
    opens *urlPath* in browser, eg:

    .. pycon::
        emzed.utils.openInBrowser("http://emzed.biol.ethz.ch") !noexec

    """
    from PyQt4.QtGui import QDesktopServices
    from PyQt4.QtCore import QUrl
    import os.path

    url = QUrl(urlPath)
    scheme = url.scheme()
    if scheme not in ["http", "ftp", "mailto"]:
        # C:/ or something simiar:
        if os.path.splitdrive(urlPath)[0] != "":
            url = QUrl("file:///"+urlPath)
    ok = QDesktopServices.openUrl(url)
    if not ok:
        raise Exception("could not open '%s'" % url.toString())


def _recalculateMzPeakFor(postfix):
    def calculator(table, row, name, postfix=postfix):

        mzmin = table.getValue(row, "mzmin"+postfix)
        mzmax = table.getValue(row, "mzmax"+postfix)
        rtmin = table.getValue(row, "rtmin"+postfix)
        rtmax = table.getValue(row, "rtmax"+postfix)
        pm    = table.getValue(row, "peakmap"+postfix)
        mz = pm.representingMzPeak(mzmin, mzmax, rtmin, rtmax)
        return mz if mz is not None else (mzmin+mzmax)/2.0
    return calculator

def _hasRangeColumns(table, postfix):
    return all([table.hasColumn(n + postfix) for n in ["rtmin", "rtmax",
                                                 "mzmin", "mzmax", "peakmap"]])

def recalculateMzPeaks(table):
    """Adds mz value for peaks not detected with centwaves algorithm based on
       rt and mz window: needed are columns mzmin, mzmax, rtmin, rtmax and
       peakmap mz, postfixes are automaticaly taken into account"""
    postfixes = [ "" ] + [ "__%d" % i for i in range(len(table._colNames))]
    for postfix in postfixes:
        if _hasRangeColumns(table, postfix):
            mz_col = "mz" + postfix
            if table.hasColumn(mz_col):
                table.replaceColumn(mz_col, _recalculateMzPeakFor(postfix),
                                    format_="%.5f", type_=float)
            else:
                table.addColumn(mz_col, _recalculateMzPeakFor(postfix),
                                format_="%.5f", type_=float)

def startfile(path):
    import sys, os
    if sys.platform == "win32":
        path = path.replace("/", "\\") # needed for network paths
    return os.startfile(path)

