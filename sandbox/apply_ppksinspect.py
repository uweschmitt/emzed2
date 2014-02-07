import numpy as np
import emzed


def cleanup(pm, rtmin, rtmax, mzmin, mzmax):

    t_thresh = 1.1   # cutting line starts 10 % above max shoulder peak
    win_size = 0.18  # m/z width of shoulder peak range

    #pmsub = pm.extract(rtmin, rtmax, mzmin, mzmax)

    rts, intensities = pm.chromatogram(mzmin, mzmax, rtmin, rtmax, msLevel=1)

    # find maximal intensity and correspondig rt values
    max_intensity, rt_with_max_intensity = max(zip(intensities, rts))

    # shoulder peaks have max 3% intensity as main peak
    upper_limit_shoulder_intensity = 0.03 * max_intensity

    # find mz0 value where max peak appears
    spec_at_max_intensity = [s for s in pm.spectra if s.rt == rt_with_max_intensity][0]
    i1 = np.argmax(spec_at_max_intensity.peaks[:, 1])
    mz0 = spec_at_max_intensity.peaks[i1, 0]

    for spec in pm.spectra:
        if rtmin <= spec.rt <= rtmax:
            peaks = spec.peaks
            # find indices of peaks below upper_limit_shoulder_intensity
            mask = (peaks[:, 1] <= upper_limit_shoulder_intensity)

            # no peaks below this threshold ? we have to catch this as np.max below throws
            # exceptoin if argument ist empty.
            if not len(peaks[mask]):
                continue

            max_intensity = np.max(peaks[mask, 1])

            mz = peaks[:, 0]
            ii = peaks[:, 1] / max_intensity

            mz_diff = np.abs(mz - mz0)
            limit = t_thresh - mz_diff / win_size

            idx = ii < limit
            spec.peaks[idx, 1] = 0.0


if __name__ == "__main__":
    tab = emzed.io.loadTable("shoulders_table_with_chromos.table")
    pm = tab.peakmap.uniqueValue()

    windows = [(25.45, 26.09, 292.937, 293.435),
               (25.48, 26.04, 294.117, 294.256),
               (25.45, 25.92, 329.121, 329.194),
               (16.55, 17.43, 245.985, 246.189)]

    for rtmin, rtmax, mzmin, mzmax in windows:
        rtmin *= 60.0
        rtmax *= 60.0
        pmsub_before = pm.extract(rtmin, rtmax, mzmin, mzmax)
        cleanup(pm, rtmin, rtmax, mzmin, mzmax)
        pmsub_after = pm.extract(rtmin, rtmax, mzmin, mzmax)
        #emzed.gui.inspectPeakMap(pmsub_before, pmsub_after)
        emzed.gui.inspectPeakMap(pmsub_after)
    

