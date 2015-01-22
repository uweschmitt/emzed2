import pyopenms
import emzed
import pytest


IS_PYOPENMS_2 = pyopenms.__version__.startswith("2.")


@pytest.mark.slow
def test_centwave(path, regtest):

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

    table.print_(out=regtest)


@pytest.mark.slow
def test_matched_filter(path, regtest):

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
    table.print_(out=regtest)


def _test_metabo(path, regtest):
    pm = emzed.io.loadPeakMap(path("data", "test_mini.mzXML"))
    table = emzed.ff.runMetaboFeatureFinder(pm,
                                            common_noise_threshold_int=3000.0,
                                            common_chrom_peak_snr=3000.0)

    table.print_(out=regtest)


# as we have regression tests where the output changes from pyopenms to pyopenms2
# we have to distinguish both cases. the name of the file recording the output
# of the tests depend on the functions names, so we use different function names
# in order to force recording results in different files:

if IS_PYOPENMS_2:
    @pytest.mark.slow
    def test_metabo_ff_of_pyopenms_2(path, regtest):
        _test_metabo(path, regtest)

else:
    @pytest.mark.slow
    def test_metabo_ff_of_pyopenms_1(path, regtest):
        _test_metabo(path, regtest)
