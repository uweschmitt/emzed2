import emzed.utils
import emzed.io
import os.path as osp


def testFormula():
    mf1 = emzed.utils.formula("H2O")
    mf2 = emzed.utils.formula("CH2O")
    assert str(mf1+mf2) == "CH4O2"
    mf3 = mf1 + mf2 - mf2
    assert str(mf3) == "H2O"


def testLoadMap(path, tmpdir):
    from_ = path(u"data/SHORT_MS2_FILE.mzData")
    ds = emzed.io.loadPeakMap(from_)
    assert osp.basename(ds.meta.get("source")) ==  osp.basename(from_)

    # with unicode
    emzed.io.storePeakMap(ds, tmpdir.join("utilstest.mzML").strpath)
    ds2 = emzed.io.loadPeakMap(tmpdir.join("utilstest.mzML").strpath)
    assert len(ds)==len(ds2)

    # without unicode
    emzed.io.storePeakMap(ds2, tmpdir.join("utilstest.mzData").strpath)
    ds3 = emzed.io.loadPeakMap(tmpdir.join("utilstest.mzData").strpath)
    assert len(ds)==len(ds3)

