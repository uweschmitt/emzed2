import emzed.ff
import emzed.io
import pytest


@pytest.mark.slow
def test_centwave(path):

    pm = emzed.io.loadPeakMap(path("data", "test_mini.mzXML"))
    table = emzed.ff.runCentwave(pm,
                                 ppm=3,
                                 peakwidth=(8, 13),
                                 snthresh=40,
                                 prefilter=(8, 10000),
                                 mzdiff=1.5)
    assert len(table) == 1, len(table)
    assert len(table.getColNames()) == 16, len(table.getColNames())
    assert len(table.getColTypes()) == 16

    tobe = """
id       mz         mzmin      mzmax      rt       rtmin    rtmax    into     intb     maxo     sn         sample
int      float      float      float      float    float    float    float    float    float    float      int
------   ------     ------     ------     ------   ------   ------   ------   ------   ------   ------     ------
0         386.32577  386.32529  386.32678 0.58m    0.58m    0.75m    1.30e+07 1.28e+07 6.47e+06 3.88e+02   1
    """

    import cStringIO
    out = cStringIO.StringIO()
    table.print_(out=out)
    table.print_()
    is_ = out.getvalue()
    for (i, t) in zip(is_.split("\n"), tobe.split("\n")[1:]):
        assert [ii.strip() for ii in i.split()] == [tt.strip() for tt in t.split()]


@pytest.mark.slow
def testmatched_filter(path):

    pm = emzed.io.loadPeakMap(path("data", "test_mini.mzXML"))

    # for faster test we prune the peakmap
    pm.spectra = pm.spectra[800:1600]

    table = emzed.ff.runMatchedFilters(pm,
                                       destination="temp_output",
                                       mzdiff=0,
                                       fwhm=50,
                                       steps=1,
                                       step=0.6)

    assert len(table) == 29, len(table)
    assert len(table.getColNames()) == 18, len(table.getColNames())
    assert len(table.getColTypes()) == 18
    tobe = """
id       mz         mzmin      mzmax      rt       rtmin    rtmax    into     intf     maxo     maxf     i        sn       sample
int      float      float      float      float    float    float    float    float    float    float    int      float    int
------   ------     ------     ------     ------   ------   ------   ------   ------   ------   ------   ------   ------   ------
0         351.13948  350.72253  351.26160 0.49m    0.30m    0.50m    2.42e+06 6.81e+07 4.10e+06 6.31e+06 1        1.53e+01 1
1         354.85775  354.33618  354.89337 0.31m    0.30m    0.50m    1.78e+05 5.00e+06 2.48e+05 4.59e+05 1        1.07e+01 1
"""

    import cStringIO
    out = cStringIO.StringIO()
    table[:2].print_(out=out)
    table[:2].print_()
    is_ = out.getvalue()
    for (i, t) in zip(is_.split("\n"), tobe.split("\n")[1:]):
        assert [ii.strip() for ii in i.split()] == [tt.strip() for tt in t.split()]


@pytest.mark.slow
def test_metabo(path):
    pm = emzed.io.loadPeakMap(path("data", "test_mini.mzXML"))
    table = emzed.ff.runMetaboFeatureFinder(pm,
                                            common_noise_threshold_int=5000.0,
                                            common_chrom_peak_snr=5000.0)

    assert len(table) == 2, len(table)
    assert len(table.getColNames()) == 14, len(table.getColNames())
    assert len(table.getColTypes()) == 14
