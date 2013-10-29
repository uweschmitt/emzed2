import pdb
import emzed
import numpy
import sys

try:
    profile
except:
    profile = lambda x: x


def similarity(ch0, ch1):
    rts0, __ = ch0
    rts1, __ = ch1
    common_rts = sorted(set(rts0) & set(rts1))
    ii0 = [val for (rt, val) in zip(*ch0) if rt in common_rts]
    ii1 = [val for (rt, val) in zip(*ch1) if rt in common_rts]
    ii0 = numpy.array(ii0)
    ii1 = numpy.array(ii1)
    ii0 /= numpy.linalg.norm(ii0)
    ii1 /= numpy.linalg.norm(ii1)
    return numpy.linalg.norm(ii0 - ii1) / len(ii0)


def add_chromatograms(tab):
    assert set("mzmin mzmax rtmin rtmax peakmap".split()) <= set(tab.getColNames())

    def calculate_chromatogram(table, row, new_name):
        pm = table.getValue(row, "peakmap")
        mzmin = table.getValue(row, "mzmin")
        mzmax = table.getValue(row, "mzmax")
        rtmin = table.getValue(row, "rtmin")
        rtmax = table.getValue(row, "rtmax")
        chromo = pm.chromatogram(mzmin, mzmax, rtmin, rtmax)
        return chromo
    tab.addColumn("_chromatogram", calculate_chromatogram, format_="'%d peaks' % len(o)")


@profile
def remove_shoulders(tab, max_delta_mz=0.3, relative_intensity_barier=0.02, min_corr=0.9,
                     rt_widening=4.0, similarity_thresh=5e-3):

    tab.sortBy("intensity", ascending=False)
    removed_ids = set()
    print "start with %d peaks " % len(tab)

    back_t = list(tab[::-1])

    for i, row in enumerate(tab.filter(tab.intensity >= 1e5)):
        print i,
        print "%.1e" % row.intensity,
        mz0 = row.mz
        ii0 = row.intensity * relative_intensity_barier
        rtmin = row.rt - rt_widening
        rtmax = row.rt + rt_widening
        for row0 in back_t:
            if row0.intensity > ii0:
                print "%.1e" % row0.intensity,
                break
            if row0.id in removed_ids:
                continue
            if abs(mz0 - row0.mz) <= max_delta_mz:
                if rtmin <= row0.rt <= rtmax:
                    if row0.id in (769, 886, 762):
                        pm = tab.peakmap.uniqueValue()
                        t0 = tab.filter(tab.id.isIn((row.id, row0.id)))
                        tab.sortBy("mz")
                        emzed.gui.inspectPeakMap(pm, table=tab)
                    removed_ids.add(row0.id)

        print "total removed =", len(removed_ids)

    tab = tab.filter(~tab.id.isIn(removed_ids))
    removed = tab.filter(tab.id.isIn(removed_ids))

    print "removed", len(removed_ids), "peaks"
    print "final table has %d peaks" % len(tab)

    return tab, removed

@profile
def remove_peaks(pm, removed_peaks):
    for row in removed_peaks:
        pm.remove(row.mzmin, row.mzmax, row.rtmin, row.rtmax)
    return pm


if __name__ == "__main__":
    tab = emzed.io.loadTable("shoulders_table_with_chromos.table")
    emzed.gui.inspectPeakMap(tab.peakmap.uniqueValue())
    tab, removed = remove_shoulders(tab[:])
    emzed.io.storeTable(tab, "shoulders_removed.table", forceOverwrite=True)
