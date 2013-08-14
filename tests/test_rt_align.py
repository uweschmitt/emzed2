import pdb
import os
import numpy as np

import unittest

from emzed.utils import loadTable
from emzed.align import rtAlign


class TestAlignment(unittest.TestCase):


    def setUp(self):

        def path():
            import os.path
            here = os.path.dirname(os.path.abspath(__file__))
            def j(*a):
                return os.path.join(here, *a)
            return j
        ft = loadTable(path()("data", "features.table"))

        # make copy and shift
        ft2 = ft.copy()
        def shift(t, col):
            ix = t.getIndex(col)
            for r in t.rows:
                r[ix] += 2.0 + 0.1 * r[ix] - 0.005 * r[ix]*r[ix]

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
        self.ft = ft
        self.ft2 = ft2


    def test_one(self):

        import tempfile
        tmpdir = tempfile.mkdtemp()

        ft, ft2 = self.ft, self.ft2

        ftneu, ft2neu = rtAlign([ft,ft2], refTable=ft, destination=tmpdir, nPeaks=9999,
                                            numBreakpoints=5)

        check(ft, ft2, ftneu, ft2neu, tmpdir)


    def test_two(self):

        import tempfile
        tmpdir = tempfile.mkdtemp()
        ft, ft2 = self.ft, self.ft2
        ft2neu, ftneu = rtAlign([ft2,ft], refTable=ft, destination=tmpdir, nPeaks=9999,
                                            numBreakpoints=5)

        check(ft, ft2, ftneu, ft2neu, tmpdir)

    def test_three(self):
        import tempfile
        tmpdir = tempfile.mkdtemp()

        ft, ft2 = self.ft, self.ft2
        ftneu, ft2neu = rtAlign([ft,ft2], destination=tmpdir, nPeaks=9999,
                                            numBreakpoints=5)

        check(ft, ft2, ftneu, ft2neu, tmpdir)


def check(ft, ft2, ftneu, ft2neu, path):
    def getrt(t, what):
        return  np.array([t.getValue(row, what) for row in t.rows])

    # refmap ft should not be changed:
    assert np.all(getrt(ftneu, "rt") == getrt(ft, "rt"))
    assert np.all(getrt(ftneu, "rtmin") == getrt(ft, "rtmin"))
    assert np.all(getrt(ftneu, "rtmax") == getrt(ft, "rtmax"))

    # but ft2 should:
    assert np.linalg.norm(getrt(ft2neu, "rt") - getrt(ft2, "rt")) >= 2.0
    assert np.linalg.norm(getrt(ft2neu, "rtmin") - getrt(ft2, "rtmin")) >= 2.0
    assert np.linalg.norm(getrt(ft2neu, "rtmax") - getrt(ft2, "rtmax")) >= 2.0

    # now ftneu and ft2neu should be very near.
    # remenber: ft2 has not as much rows as ft, so:
    assert np.linalg.norm(getrt(ft2neu, "rt") - getrt(ftneu, "rt")[:-1]) < 1e-4

    assert  max(abs(getrt(ft2neu, "rtmin")- getrt(ftneu, "rtmin")[:-1])) < 0.2

    assert  max(abs(getrt(ft2neu, "rtmax")[:-1] - getrt(ftneu, "rtmax")[:-2])) < 1e-3

    def getrtsfrompeakmap(table):
        pms = set(table.getValue(row, "peakmap") for row in table.rows)
        assert len(pms) == 1
        pm = pms.pop()
        return np.array([ spec.rt for spec in pm.spectra])

    assert max(abs(getrtsfrompeakmap(ft2neu)- getrtsfrompeakmap(ftneu))) < 2.2

    ex = None
    try:
        ftneu, ft2neu = rtAlign([ftneu,ft2neu], destination=path, nPeaks=9999,
                                              numBreakpoints=2)
    except Exception, e:
        ex = e
    assert ex.message.startswith("there are already rt_aligned peakmaps")
    assert ex is not None, "aligning of aligned maps should not be possible"
    # alignmen should produce alignment map:
    assert os.path.exists(os.path.join(path, "test_mini_aligned.png"))



