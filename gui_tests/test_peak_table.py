import os

here = os.path.dirname(os.path.abspath(__file__))

import guidata
app = guidata.qapplication()

import emzed
import datetime
import math
import numpy as np

pm = emzed.io.loadPeakMap(os.path.join(here, "..", "tests", "data", "test_mini.mzXML"))

TimeSeries = emzed.core.data_types.TimeSeries
Spectrum = emzed.core.data_types.Spectrum

mzs = np.arange(100, 200, 10)
iis = np.log(mzs) * 10000.0
peaks = np.vstack((mzs, iis)).T
print peaks.shape

spectrum = Spectrum(peaks, rt=10.0, msLevel=2, polarity="-", precursors=[(1000.0, 20000)])
spectra = [spectrum]

spectrum = Spectrum(peaks + 2.0, rt=12.0, msLevel=2, polarity="-", precursors=[(1010.0, 30000)])
spectra += [spectrum]



print "TIME IS IN SECONDS"



t = emzed.utils.toTable("mzmin", 2 * range(0, 2000, 100), type_=float)

tsi = []
for i in range(len(t) / 2):
    x = range(10 + i) + [None, None] + range(10 + i, 20 + i)
    y = [100 + 100 * math.sin(0.3 * (xi + i)) if xi is not None else None for xi in x]
    x = [None if xi is None else datetime.datetime(2015, 1 + xi / 20, 1 + xi % 20)  for xi in x]
    ts = TimeSeries(x,y, label="mz=%.2f" % (123123.3434/(i + 7)))
    tsi.append(ts)
    tsi.append(ts)


# peak table with chromatograms

t.addColumn("mzmax", t.mzmin + 10.0)
t.addColumn("rtmin", 2 * range(10, 30), type_=float)
t.addColumn("rtmax", t.rtmin + 3)
t.addColumn("peakmap", pm)
t.addColumn("class_", t.rtmin > 20)


t.addColumn("spectra_ms2", t.class_.thenElse(spectra, None), format_=None)
t.addColumn("ms2_spectra_count", t.spectra_ms2.apply(len), type_=int, format_="%d")

ti = emzed.utils.integrate(t)
ti.setColFormat("params", "%r")

# t.dropColumns("peakmap", "rtmin")
t.addEnumeration()
t.addColumn("f", t.id / 3)
# t.addColumn("time_series", tsi, format_="%s", type_=TimeSeries)
t.setTitle("peak table")

# now we have a time series which should be shown
t1 = t[:]
t1.addColumn("time_series", tsi, format_="%s", type_=TimeSeries)
t1.setTitle("teime series table")
print t.getColFormats()


# the next table is not a complete peak table:
t2 = emzed.utils.toTable("mzmin", range(0, 2000, 200), type_=float)
t2.addColumn("mzmax", t2.mzmin + 10.0)
t2.addColumn("rtmin", range(10, 30, 2), type_=float)
t2.addColumn("rtmax", t2.rtmin + 3)
t2.addColumn("mz", 0.5 * (t2.mzmin + t2.mzmax))
t2.dropColumns("mzmin", "mzmax")
t2.addColumn("peakmap", pm)
t2.setTitle("incomplete peak table")

ti.sortBy("area", ascending=False)

# t2 = emzed.utils.integrate(t2)

# eic only
t_feat_and_ms2 = ti.copy()
t_feat_and_ms2.dropColumns("method", "area", "params")
t_feat_and_ms2.setTitle("feat and ms2")

t_feat_only = t_feat_and_ms2.copy()
t_feat_only.dropColumns("spectra_ms2")
t_feat_only.setTitle("feat only")

t_eic_only = t_feat_and_ms2.copy()
t_eic_only.dropColumns("peakmap", "spectra_ms2")
t_eic_only.setTitle("eic only")

t_integrated = ti
t_integrated.setTitle("integrated")

t_with_ts = t1
t_with_ts.setTitle("with ts")
t_with_ts.dropColumns("spectra_ms2")

t_with_ts.info()

def callback(*args):
    print(args)


emzed.gui.inspect((t_with_ts, t_integrated, t_eic_only, t_feat_only, t_feat_and_ms2),
        close_callback=callback)

print(t)



