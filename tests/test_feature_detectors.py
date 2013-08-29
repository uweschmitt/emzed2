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
                                 mzdiff=1.5 )
    assert len(table) == 1, len(table)
    assert len(table.getColNames()) ==  16, len(table.getColNames())
    assert len(table.getColTypes()) ==  16

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
    assert len(table.getColNames()) ==  18, len(table.getColNames())
    assert len(table.getColTypes()) ==  18

@pytest.mark.slow
def test_metabo(path):
    pm = emzed.io.loadPeakMap(path("data", "test_mini.mzXML"))
    table = emzed.ff.runMetaboFeatureFinder(pm,
                                            common_noise_threshold_int=5000.0,
                                            common_chrom_peak_snr=5000.0)

    assert len(table) == 2, len(table)
    assert len(table.getColNames()) ==  14, len(table.getColNames())
    assert len(table.getColTypes()) ==  14



