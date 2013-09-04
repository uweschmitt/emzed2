import emzed.align
import emzed.io
import glob
import sys

def testMzAlign(path, tmpdir, monkeypatch):


    if 0 and sys.platform != "win32":
        import matplotlib
        old = matplotlib.get_backend()
        matplotlib.use("Qt4Agg")
        try:
            import pylab
            pylab.figure()
        except:
            pass
            matplotlib.use(old)
            reload(pylab)
        else:
            raise Exception("exepcted exception when opening figure on absent X windows system")

    tab = emzed.io.loadTable(path("data/ftab_for_mzalign.table"))
    reftable = emzed.io.loadCSV(path("data/universal_metabolites_.csv"))
    reftable.renameColumns(mz_calc="mz_hypot")
    reftable.info()
    pm = tab.peakmap.values[0]
    s0 = pm.spectra[0].peaks[:,0]
    print tmpdir.strpath
    tab_aligned = emzed.align.mzAlign(tab, reftable, interactive=False, minPoints=4, tol=14*MMU,
                      destination=tmpdir.strpath)
    assert tab_aligned is not None
    after = tab_aligned.mz.values
    pm = tab_aligned.peakmap.values[0]
    s0 = pm.spectra[0].peaks[:,0]
    assert abs(s0[0]-202.12121582) < 1e-5, float(s0[0])
    assert abs(after[0]-272.199238673) < 1e-5, float(after[0])

    assert len(glob.glob(tmpdir.join("2011-10-06_054_PKTB*").strpath))==4

    # former errror: transformation resulted in numpy.float64 values
    assert tab_aligned.getColType("mz") == float
    assert tab_aligned.getColType("mzmin") == float
    assert tab_aligned.getColType("mzmax") == float
