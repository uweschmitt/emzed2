import numpy as np
import emzed


def cleanup(pm, rtmin, rtmax, mzmin, mzmax):

    t_thresh = 1.1                        # cutting line starts 10 % above max shoulder peak
    shoulder_peak_max_dist = 0.18         # m/z width of shoulder peak range
    shoulder_peak_min_dist = 0.004        # min m/z diff of shoulder peaks to main peak
    shoulder_peak_max_proportion = 0.03   # max quotient I(shoulder_peak) / I(main_peak)

    rts, intensities = pm.chromatogram(mzmin, mzmax, rtmin, rtmax, msLevel=1)

    # find maximal intensity and correspondig rt values
    max_intensity, rt_with_max_intensity = max(zip(intensities, rts))

    # find mz_at_max_intensity value in mz-windows where max peak appears
    spec_at_max_intensity = [s for s in pm.spectra if s.rt == rt_with_max_intensity][0]
    peaks = spec_at_max_intensity.peaks
    peaks_in_window = peaks[(mzmin <= peaks[:, 0]) & (peaks[:, 0] <= mzmax)]
    mz_at_max_intensity = peaks_in_window[np.argmax(peaks_in_window[:, 1]), 0]

    upper_limit_shoulder_intensity = shoulder_peak_max_proportion * max_intensity

    for spec in pm.spectra:
        if rtmin <= spec.rt <= rtmax:
            peaks = spec.peaks

            # find indices of peaks below upper_limit_shoulder_intensity
            mask = (peaks[:, 1] <= upper_limit_shoulder_intensity)

            # no peaks below this threshold ? we have to catch this as np.max below throws
            # exception if argument ist empty.
            if not len(peaks[mask]):
                continue

            max_shoulder_intensity = np.max(peaks[mask, 1])

            # we draw two lines starting at
            #
            #      (mz_at_max_intensity, t_thresh * max_shoulder_intensity)
            #
            # falling down to
            #
            #      (mz_at_max_intensity +/- shoulder_peak_max_dist, 0)
            #
            # then we erase all peaks which have a min distance of shoulder_peak_min_dist
            # to mz_at_max_intensity and where the intensity is below these lines

            mz_dist = np.abs(peaks[:, 0] - mz_at_max_intensity)
            limit = max_shoulder_intensity * (t_thresh - mz_dist / shoulder_peak_max_dist)

            idx = (peaks[:, 1] < limit) & (mz_dist >= shoulder_peak_min_dist)
            spec.peaks[idx, 1] = 0.0


if __name__ == "__main__":

    tab = emzed.io.loadTable("shoulders_table_with_chromos.table")
    pm = tab.peakmap.uniqueValue()

    windows = [(25.45, 26.09, 292.937, 293.435),
               (25.48, 26.04, 294.117, 294.256),
               (25.45, 25.92, 329.101, 329.194),
               (16.55, 17.43, 245.985, 246.189)][1:4]

    for rtmin, rtmax, mzmin, mzmax in windows:
        rtmin *= 60.0
        rtmax *= 60.0

        pm = tab.peakmap.uniqueValue()
        pmsub_before = pm.extract(rtmin=rtmin, rtmax=rtmax, mzmin=mzmin, mzmax=mzmax)
        pmsub_before.meta["source"] = "before"
        #emzed.gui.inspectPeakMap(pmsub_before)

        cleanup(pm, rtmin, rtmax, mzmin, mzmax)
        pmsub_after = pm.extract(rtmin, rtmax, mzmin, mzmax)
        pmsub_after.meta["source"] = "after"
        #emzed.gui.inspectPeakMap(pmsub_after)

        emzed.gui.inspectPeakMap(pmsub_before, pmsub_after)
