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
                                            common_noise_threshold_int=3000.0,
                                            common_chrom_peak_snr=3000.0)

    tobe = """
id       feature_id mz        mzmin      mzmax      rt       rtmin    rtmax    intensity quality  fwhm     z        source
int      int        float     float      float      float    float    float    float     float    float    int      str
------   ------     ------    ------     ------     ------   ------   ------   ------    ------   ------   ------   ------
0        0          396.34662  396.34558  396.34781 0.62m    0.36m    0.72m    2.51e+07  3.69e-01 0.03m    1        test_mini.mzXML
1        0          397.34997  397.34879  397.35309 0.62m    0.57m    0.70m    2.51e+07  3.69e-01 0.03m    1        test_mini.mzXML
2        1          358.29469  358.29382  358.29553 0.64m    0.31m    0.72m    1.90e+07  2.68e-01 0.03m    1        test_mini.mzXML
3        1          359.29804  359.29691  359.29880 0.64m    0.57m    0.70m    1.90e+07  2.68e-01 0.03m    1        test_mini.mzXML
4        2          386.32590  386.32486  386.32690 0.57m    0.30m    0.65m    1.44e+07  1.75e-01 0.04m    0        test_mini.mzXML
5        3          424.37787  424.37677  424.37924 0.64m    0.49m    0.72m    1.05e+07  1.27e-01 0.04m    0        test_mini.mzXML
6        4          386.32608  386.32516  386.32651 0.68m    0.66m    0.70m    3.03e+06  3.69e-02 0.04m    0        test_mini.mzXML
"""

    import cStringIO
    out = cStringIO.StringIO()
    table.print_(out=out)
    is_ = out.getvalue()
    for (i, t) in zip(is_.split("\n"), tobe.split("\n")[1:]):
        assert i.rstrip() == t.rstrip()
