# encoding: utf-8
from __future__ import print_function, division

import itertools

from tables import Atom, UInt32Col, Float32Col, UInt8Col, UInt64Col, StringCol
import numpy as np

from emzed_optimizations import sample_peaks as optim_sample_peaks

from .. import PeakMap, Spectrum

from .store_base import Store, filters
from .lru import LruDict, lru_cache

from .install_profile import profile


class PeakMapStore(Store):

    ID_FLAG = 0
    HANDLES = PeakMap

    MSLEVEL_FIELD_SIZE = 16

    def __init__(self, file_, node, **kw):
        self.file_ = file_
        self.node = node
        self.setup()
        self.write_cache = LruDict(100)
        self.read_cache = LruDict(100)

    def setup(self):
        self.setup_blobs()
        self.setup_spec_table()
        self.setup_peakmap_table()

    def setup_blobs(self):
        if not hasattr(self.node, "mz_blob"):
            self.file_.create_earray(self.node, "mz_blob",
                                     Atom.from_dtype(np.dtype("float64")), (0,),
                                     filters=filters,
                                     )

        if not hasattr(self.node, "ii_blob"):
            self.file_.create_earray(self.node, "ii_blob",
                                     Atom.from_dtype(np.dtype("float32")), (0,),
                                     filters=filters,
                                     )

    def setup_spec_table(self):
        if not hasattr(self.node, "spec_table"):
            description = {}
            description["pm_index"] = UInt32Col(pos=0)
            description["rt"] = Float32Col(pos=1)
            description["ms_level"] = UInt8Col(pos=2)
            description["start"] = UInt64Col(pos=3)
            description["size"] = UInt32Col(pos=4)
            spec_table = self.file_.create_table(self.node, 'spec_table', description,
                                                 filters=filters)

            # every colums which appears in a where method call should/must be indexed !
            # this is not only for performance but for correct lookup as well (I had strange bugs
            # else)
            spec_table.cols.pm_index.create_index()
            spec_table.cols.rt.create_index()

    def setup_peakmap_table(self):
        if not hasattr(self.node, "pm_table"):
            description = {}
            description["unique_id"] = StringCol(itemsize=64, pos=0)
            description["index"] = UInt32Col(pos=1)
            description["ms_levels"] = StringCol(itemsize=self.MSLEVEL_FIELD_SIZE, pos=2)
            description["rtmin"] = Float32Col(pos=3)
            description["rtmax"] = Float32Col(pos=4)
            description["mzmin"] = Float32Col(pos=5)
            description["mzmax"] = Float32Col(pos=6)
            pm_table = self.file_.create_table(self.node, 'pm_table', description, filters=filters)
            # every colums which appears in a where method call should/must be indexed !
            # this is not only for performance but for correct lookup as well (I had strange bugs
            # else)
            pm_table.cols.unique_id.create_index()
            pm_table.cols.index.create_index()

    def add_spectrum(self, pm_index, spec):

        start = self.node.mz_blob.nrows
        self.node.mz_blob.append(spec.peaks[:, 0])
        self.node.ii_blob.append(spec.peaks[:, 1])

        size = spec.peaks.shape[0]

        row = self.node.spec_table.row
        row["pm_index"] = pm_index
        row["rt"] = spec.rt
        row["ms_level"] = spec.msLevel
        row["start"] = start
        row["size"] = size

        row.append()

    def _write(self, col_index, pm):

        # at the moment we ignore col_index, I guess it would not speed up so much

        unique_id = pm.uniqueId()
        # hash key
        yield unique_id

        result = list(self.node.pm_table.where("""unique_id == %r""" % unique_id))
        if result:
            yield result[0]["index"]
            return

        ms_levels = sorted(set(pm.getMsLevels()))
        as_str = ",".join(map(str, ms_levels))
        if len(as_str) > self.MSLEVEL_FIELD_SIZE:
            raise ValueError("ms level description %r is to long" % as_str)

        rtmin, rtmax = pm.rtRange()
        mzmin, mzmax = pm.mzRange()

        index = self.node.pm_table.nrows
        row = self.node.pm_table.row
        row["unique_id"] = unique_id
        row["index"] = index
        row["ms_levels"] = as_str
        row["rtmin"] = rtmin
        row["rtmax"] = rtmax
        row["mzmin"] = mzmin
        row["mzmax"] = mzmax
        row.append()

        for spec in pm.spectra:
            self.add_spectrum(index, spec)

        yield index

    def _read(self, col_index, index):
        result = list(self.node.pm_table.where("""index == %r""" % index))
        if len(result) == 0:
            raise ValueError("index %d not in table" % index)

        ms_levels = result[0]["ms_levels"]
        rtmin = result[0]["rtmin"]
        rtmax = result[0]["rtmax"]
        mzmin = result[0]["mzmin"]
        mzmax = result[0]["mzmax"]
        unique_id = result[0]["unique_id"]
        ms_levels = map(int, ms_levels.split(","))

        result = PeakMapProxy(node=self.node,
                              index=index,
                              ms_levels=ms_levels,
                              rtmin=rtmin,
                              rtmax=rtmax,
                              mzmin=mzmin,
                              mzmax=mzmax,
                              unique_id=unique_id)
        return result

    def flush(self):
        self.node.pm_table.flush()
        self.node.spec_table.flush()


class PeakMapProxy(object):

    def __init__(self, **kw):
        for name, value in kw.items():
            setattr(self, name, value)

        self.meta = {"unique_id": kw.get("unique_id")}

    def uniqueId(self):
        return self.unique_id

    def getMsLevels(self):
        return self.ms_levels

    def rtRange(self):
        return self.rtmin, self.rtmax

    def mzRange(self):
        return self.mzmin, self.mzmax

    def _iter_peaks(self, rtmin, rtmax, mzmin, mzmax, ms_level=1):
        if rtmin is not None and rtmax is not None:
            query = """(pm_index == %d) & (%f <= rt) & (rt <= %f)""" % (self.index, rtmin, rtmax)
        elif rtmin is not None:
            query = """(pm_index == %d) & (%f <= rt)""" % (self.index, rtmin)
        elif rtmax is not None:
            query = """(pm_index == %d) & (rt <= %f)""" % (self.index, rtmax)
        else:
            query = """(pm_index == %d)""" % (self.index,)
        mz_blob = self.node.mz_blob
        ii_blob = self.node.ii_blob
        for row in self.node.spec_table.where(query):
            if ms_level != row["ms_level"]:
                continue
            rt = row["rt"]
            i_start = row["start"]
            i_end = i_start + row["size"]
            mzs = mz_blob[i_start:i_end]
            iis = ii_blob[i_start:i_end]

            flags = True
            if mzmin is not None:
                flags = flags * (mzmin <= mzs)
            if mzmax is not None:
                flags = flags * (mzs <= mzmax)

            if flags is not True:
                idx = np.where(flags)[0]
                iis = iis[idx]
                mzs = mzs[idx]

            yield rt, mzs, iis

    @lru_cache(maxsize=1000)
    def chromatogram(self, mzmin=None, mzmax=None, rtmin=None, rtmax=None, ms_level=1):
        rts = []
        intensities = []
        for rt, mzs, iis in self._iter_peaks(rtmin, rtmax, mzmin, mzmax, ms_level):
            rts.append(rt)
            intensities.append(np.sum(iis))
        rts = np.array(rts)
        intensities = np.array(intensities)
        perm = np.argsort(rts)
        rts = rts[perm]
        intensities = intensities[perm]
        return rts, intensities

    @lru_cache(maxsize=1000)
    def sample_peaks(self, rtmin, rtmax, mzmin, mzmax, npeaks, ms_level):
        spectra = []
        for rt, mzs, iis in self._iter_peaks(rtmin, rtmax, mzmin, mzmax, ms_level):
            peaks = np.vstack((mzs, iis)).T
            spectrum = Spectrum(peaks, rt, ms_level, "0", [])
            spectra.append(spectrum)
        if rtmin <= rtmax and mzmin < mzmax:
            peaks = optim_sample_peaks(PeakMap(spectra),
                                       rtmin, rtmax, mzmin, mzmax, npeaks, ms_level)
        else:
            peaks = np.zeros((0, 2))
        return peaks

    def get_rts(self, msLevel=1):
        t = self.node.spec_table
        pm_indices = t.cols.pm_index[:]
        rts = t.cols.rt[:]
        ms_levels = t.cols.ms_level[:]
        return [r for (r, i, l) in itertools.izip(rts, pm_indices, ms_levels) if i == self.index and
                l == msLevel]
