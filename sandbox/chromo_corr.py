import emzed
import numpy
t = emzed.io.loadTable("shoulders_integrated.table")
t.sortBy("intensity", ascending=False)
t.print_()

pm = t.peakmap.values[0]

chromos = []
for row in t.rows:
    values = t.getValues(row)
    mzmin, mzmax, rtmin, rtmax = [values.get(n) for n in ("mzmin", "mzmax", "rtmin", "rtmax")]
    chromo = pm.chromatogram(mzmin, mzmax, rtmin, rtmax)
    chromos.append(chromo)

rts0, ch0 = chromos[0]
for rts1, ch1 in chromos[1:]:
    common_rts = sorted(set(rts0) & set(rts1))
    i0 = [val for rt, val in zip(rts0, ch0) if rt in common_rts]
    i1 = [val for rt, val in zip(rts1, ch1) if rt in common_rts]

    i0 = numpy.array(i0)
    i1 = numpy.array(i1)
    i0 /= numpy.linalg.norm(i0)
    i1 /= numpy.linalg.norm(i1)
    print numpy.dot(i0, i1), numpy.linalg.norm(i0 - i1) / len(i0)

