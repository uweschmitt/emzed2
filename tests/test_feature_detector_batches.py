import emzed.batches
import glob
import pytest


@pytest.mark.slow
def testRunCentwave(tmpdir, path):

    from emzed.core.r_connect import installXcmsIfNeeded
    installXcmsIfNeeded()

    tables = emzed.batches.runCentwave(path("data/test_mini.mzXML"),
                                       destination=tmpdir.strpath,
                                       configid="std",
                                       ppm=3,
                                       peakwidth=(8, 13),
                                       snthresh=40,
                                       prefilter=(8, 10000),
                                       mzdiff=1.5 )
    assert len(glob.glob(tmpdir.join("test_mini.csv").strpath)) == 1
    assert len(tables) == 1
    table=tables[0]
    assert len(table) == 1, len(table)
    assert len(table.getColNames()) ==  16, len(table.getColNames())
    assert len(table.getColTypes()) ==  16


@pytest.mark.slow
def testMatchedFilter(path, tmpdir):

    from emzed.core.r_connect import installXcmsIfNeeded
    installXcmsIfNeeded()

    tables = emzed.batches.runMatchedFilter(path("data/test.mzXML"),
            destination=tmpdir.strpath, configid="std", mzdiff=0, fwhm=50,
            steps=1, step=0.6)
    assert len(glob.glob(tmpdir.join("test.csv").strpath)) == 1
    table, = tables
    assert len(table) == 340, len(table)
    assert len(table.getColNames()) ==  18, len(table.getColNames())
    assert len(table.getColTypes()) ==  18

def testMetaboFF(path, tmpdir):

    tables = emzed.batches.runMetaboFeatureFinder(path("data/test.mzXML"),
            destination=tmpdir.strpath, configid="_test")
    assert len(glob.glob(tmpdir.join("test.csv").strpath)) == 1
    table, = tables
    assert len(table) == 1, len(table)
    assert len(table.getColNames()) ==  14, len(table.getColNames())
    assert len(table.getColTypes()) ==  14
