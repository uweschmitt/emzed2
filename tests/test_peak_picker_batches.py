import emzed.batches
import glob

def testPeakPickerHiRes(path, tmpdir):

    inPath  = path("data/gauss_data.mzML")
    outPath = "temp_output/gauss_data_centroided.mzML"
    outPath = tmpdir.join("gauss_data_centroided.mzML").strpath
    emzed.batches.runPeakPickerHiRes(inPath, destination=tmpdir.strpath, configid="std")
    assert len(glob.glob(outPath)) == 1

