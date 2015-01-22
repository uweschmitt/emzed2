import os
import numpy as np

import pyopenms

IS_PYOPENMS_2 = pyopenms.__version__.startswith("2.")

import emzed

from emzed.align import rtAlign

import pytest


@pytest.fixture
def input_tables():

    def path():
        import os.path
        here = os.path.dirname(os.path.abspath(__file__))

        def j(*a):
            return os.path.join(here, *a)
        return j

    ft = emzed.io.loadTable(path()("data", "features.table"))

    ft.replaceColumn("rtmin", ft.rt - 2.0)
    ft.replaceColumn("rtmax", ft.rt + 10.0)

    # make copy and shift
    ft2 = ft.copy()

    def shift(t, col):
        ix = t.getIndex(col)
        for r in t.rows:
            r[ix] += 2.0 + 0.1 * r[ix] - 0.005 * r[ix] * r[ix]

    shift(ft2, "rt")
    shift(ft2, "rtmin")
    shift(ft2, "rtmax")

    pms = set(ft2.getValue(row, "peakmap") for row in ft2.rows)
    pmrtsbefore = []
    assert len(pms) == 1
    for pm in pms:
        for spec in pm.spectra:
            pmrtsbefore.append(spec.rt)
            spec.rt += 2.0 + 0.1 * spec.rt - 0.005 * spec.rt * spec.rt

    # delete one row, so ft should become reference map !
    del ft2.rows[-1]

    return (ft, ft2)


def test_one(input_tables, regtest, tmpdir):

    tmpdir = tmpdir.strpath

    ft, ft2 = input_tables

    ftneu, ft2neu = rtAlign([ft, ft2], refTable=ft, destination=tmpdir, nPeaks=9999,
                            numBreakpoints=3)

    check(ft, ft2, ftneu, ft2neu, tmpdir, regtest)


def test_two(input_tables, regtest, tmpdir):

    tmpdir = tmpdir.strpath
    ft, ft2 = input_tables
    ft2neu, ftneu = rtAlign([ft2, ft], refTable=ft, destination=tmpdir, nPeaks=9999,
                            numBreakpoints=3)

    check(ft, ft2, ftneu, ft2neu, tmpdir, regtest)


def test_three(input_tables, regtest, tmpdir):

    tmpdir = tmpdir.strpath
    ft, ft2 = input_tables
    ftneu, ft2neu = rtAlign([ft, ft2], destination=tmpdir, nPeaks=9999,
                            numBreakpoints=3)

    check(ft, ft2, ftneu, ft2neu, tmpdir, regtest)


def test_four(input_tables, regtest, tmpdir):
    import emzed.utils
    ft, ft2 = input_tables
    ft = emzed.utils.integrate(ft, "max")
    tmpdir = tmpdir.strpath

    # fails becaus one is integrated, after alignment the integration would be infeasible:
    with pytest.raises(Exception):
        ftneu, ft2neu = rtAlign([ft, ft2], destination=tmpdir, nPeaks=9999,
                                numBreakpoints=3)

    assert ft.method.countNotNone() > 0
    assert ft.area.countNotNone() > 0
    assert ft.params.countNotNone() > 0

    # enforces alignment, but sets integration related columns to None
    ftneu, ft2neu = rtAlign([ft, ft2], destination=tmpdir, nPeaks=9999,
                            numBreakpoints=5, resetIntegration=True)

    # all Nones:
    assert ftneu.method.countNotNone() == 0
    assert ftneu.area.countNotNone() == 0
    assert ftneu.params.countNotNone() == 0


# as we have regression tests where the output changes from pyopenms to pyopenms2
# we have to distinguish both cases. the name of the file recording the output
# of the tests depend on the functions names, so we use different function names
# in order to force recording results in different files:

if IS_PYOPENMS_2:
    pf = "_2"
else:
    pf = "_1"

test_one.__name__ = "test_one_for_pyopenms" + pf
test_two.__name__ = "test_two_for_pyopenms" + pf
test_three.__name__ = "test_three_for_pyopenms" + pf
test_four.__name__ = "test_four_for_pyopenms" + pf


def getrtsfrompeakmap(table):
    pms = set(table.getValue(row, "peakmap") for row in table.rows)
    assert len(pms) == 1
    pm = pms.pop()
    return np.array([spec.rt for spec in pm.spectra])


def check(ft, ft2, ftneu, ft2neu, path, regtest):

    alignment_should_produce_plot(path)
    realignment_should_fail(ft, ft2, ftneu, ft2neu, path, regtest)
    spectra_rt_should_be_aligned(ft, ft2, ftneu, ft2neu, path, regtest)
    rt_values_in_peak_table_should_be_aligned(ft, ft2, ftneu, ft2neu, path, regtest)


def realignment_should_fail(ft, ft2, ftneu, ft2neu, path, regtest):
    ex = None
    try:
        ftneu, ft2neu = rtAlign([ftneu, ft2neu], destination=path, nPeaks=9999,
                                numBreakpoints=2)
    except Exception, e:
        ex = e
    assert ex.message.startswith("there are already rt_aligned peakmaps")
    assert ex is not None, "aligning of aligned maps should not be possible"


def alignment_should_produce_plot(path):
    assert os.path.exists(os.path.join(path, "test_mini_aligned.png"))


def spectra_rt_should_be_aligned(ft, ft2, ftneu, ft2neu, path, regtest):
    # rts of spctra should be aligned:

    t = emzed.utils.toTable("rt_peakmap_before", getrtsfrompeakmap(ft2))
    t.addColumn("rt_peakmap_after", getrtsfrompeakmap(ft2neu))

    print >> regtest, "rt comparision of spectra in peakmaps:"
    print >> regtest, t
    print >> regtest


def rt_values_in_peak_table_should_be_aligned(ft, ft2, ftneu, ft2neu, path, regtest):

    ft = ft.extractColumns("id", "rt")
    ft2 = ft2.extractColumns("id", "rt", "rtmin", "rtmax")
    ftneu = ftneu.extractColumns("id", "rt")
    ft2neu = ft2neu.extractColumns("id", "rt", "rtmin", "rtmax")

    ft.addPostfix("_1")

    before = ft.join(ft2, ft.id_1 == ft2.id)
    before.renamePostfixes(__0="_2")
    before.dropColumns("id_2")

    compared = before.join(ftneu, before.id_1 == ftneu.id)
    compared.dropColumns("id__0")
    compared.renamePostfixes(__0="_1_aligned")

    compared = compared.join(ft2neu, compared.id_1 == ft2neu.id)
    compared.dropColumns("id__0", "id_1")
    compared.renamePostfixes(__0="_2_aligned")

    print >> regtest, "peaks before and after alignment:"
    print >> regtest, compared
