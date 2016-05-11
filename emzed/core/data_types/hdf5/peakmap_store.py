# encoding: utf-8
from __future__ import print_function, division

from collections import defaultdict
import itertools

from tables import Atom, UInt32Col, Float32Col, UInt64Col, StringCol
import numpy as np

from emzed_optimizations import sample_peaks_from_lists

from .. import PeakMap, Spectrum

from .store_base import Store, filters
from .lru import LruDict, lru_cache

from .install_profile import profile

from .helpers import timethis


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
        if not hasattr(self.node, "ms1_mz_blob"):
            for level in (1, 2):
                self.file_.create_earray(self.node, "ms%d_mz_blob" % level,
                                         Atom.from_dtype(np.dtype("float64")), (0,),
                                         filters=filters,
                                         )

                self.file_.create_earray(self.node, "ms%d_ii_blob" % level,
                                         Atom.from_dtype(np.dtype("float32")), (0,),
                                         filters=filters,
                                         )

    def setup_spec_table(self):
        if not hasattr(self.node, "ms1_spec_table"):
            for level in (1, 2):
                description = {}
                description["pm_index"] = UInt32Col(pos=0)
                description["rt"] = Float32Col(pos=1)
                description["start"] = UInt64Col(pos=3)
                description["end"] = UInt64Col(pos=4)
                t = self.file_.create_table(self.node, 'ms%d_spec_table' % level, description,
                                            filters=filters)

                # every colums which appears in a where method call should/must be indexed !
                # this is not only for performance but for correct lookup as well (I had strange bugs
                # else)
                t.cols.pm_index.create_index()
                t.cols.rt.create_index()

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

        level = spec.msLevel
        mz_blob = getattr(self.node, "ms%d_mz_blob" % level)
        ii_blob = getattr(self.node, "ms%d_ii_blob" % level)

        start = mz_blob.nrows
        mz_blob.append(spec.peaks[:, 0])
        ii_blob.append(spec.peaks[:, 1])

        size = spec.peaks.shape[0]

        row = getattr(self.node, "ms%d_spec_table" % level).row

        row["pm_index"] = pm_index
        row["rt"] = spec.rt
        row["start"] = start
        row["end"] = start + size

        row.append()

    def _write(self, col_index, pm):

        # at the moment we ignore col_index, I guess it would not speed up so
        # much

        unique_id = pm.uniqueId()
        # hash key
        yield unique_id

        result = list(self.node.pm_table.where("""unique_id == %r""" % unique_id))
        if result:
            yield int(result[0]["index"])
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

        for spec in sorted(pm.spectra, key=lambda s: s.rt):
            self.add_spectrum(index, spec)

        yield int(index)

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
        self.node.ms1_spec_table.flush()
        self.node.ms2_spec_table.flush()


class PeakMapProxy(object):

    def __init__(self, **kw):
        for name, value in kw.items():
            setattr(self, name, value)
        self.setup(kw)

    def setup(self, kw):
        self.meta = {"unique_id": kw.get("unique_id")}
        rts = defaultdict(list)
        starts = defaultdict(list)
        for level in (1, 2):
            t = getattr(self.node, "ms%d_spec_table" % level)
            row = None
            for row in t.where("pm_index == %d" % self.index):
                rts[level].append(row["rt"])
                starts[level].append(row["start"])
            # we save memory and only load starts, for the last item will be helpful for slicing,
            # row might be None if no spectra of given level are contained in peakmap
            if row is not None:
                starts[level].append(row["end"])

        for level in rts:
            rts[level] = np.array(rts[level], dtype=float)
            starts[level] = np.array(starts[level], dtype=int)

        self.rts = rts
        self.starts = starts

    def uniqueId(self):
        return self.unique_id

    def getMsLevels(self):
        return self.ms_levels

    def rtRange(self):
        return self.rtmin, self.rtmax

    def mzRange(self):
        return self.mzmin, self.mzmax

    @profile
    def _iter_peaks(self, rtmin, rtmax, mzmin, mzmax, ms_level=1):
        if (mzmin is not None) != (mzmax is not None):
            # mixed settings are not optimized yet !
            raise ValueError("either mzmin and mzmax are None or both have to be numbers")

        """
        this two step process over two iterators increases cache hits because in one row of
        table explore we run it once with mzmin = None and one with mzmin set, but rtmin,
        rtmax and ms_level are the same !
        """

        if mzmin is None:
            for data in self._iter_full_spectra(rtmin, rtmax, ms_level):
                yield data
        else:
            for rt, mzs, iis in self._iter_full_spectra(rtmin, rtmax, ms_level):
                flags = (mzmin <= mzs) & (mzs <= mzmax)
                iis = iis[flags]
                mzs = mzs[flags]
                yield rt, mzs, iis


    @lru_cache(maxsize=1000)
    def _iter_full_spectra(self, rtmin, rtmax, ms_level):

        rts = self.rts[ms_level]
        i0 = np.searchsorted(rts, rtmin, "left")
        i1 = np.searchsorted(rts, rtmax, "right")

        starts = self.starts[ms_level][i0:i1]
        if not len(starts):
            return
        ends = self.starts[ms_level][i0 + 1:i1 + 1]
        if not len(ends):
            return

        s0 = starts[0]
        e0 = ends[-1]

        full_mzs = getattr(self.node, "ms%d_mz_blob" % ms_level)[s0:e0]
        full_iis = getattr(self.node, "ms%d_ii_blob" % ms_level)[s0:e0]

        for i_start, i_end, rt in itertools.izip(starts, ends, rts[i0:]):
            mzs = full_mzs[i_start - s0: i_end - s0]
            iis = full_iis[i_start - s0: i_end - s0]
            yield rt, mzs, iis

    @lru_cache(maxsize=1000)
    @profile
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
    @profile
    def sample_peaks(self, rtmin, rtmax, mzmin, mzmax, npeaks, ms_level):

        if rtmin <= rtmax and mzmin < mzmax:
            all_mzs = []
            all_iis = []
            for rt, mzs, iis in self._iter_peaks(rtmin, rtmax, None, None, ms_level):
                all_mzs.append(mzs)
                all_iis.append(iis)
            peaks = sample_peaks_from_lists(all_mzs, all_iis, mzmin, mzmax, npeaks)
        else:
            peaks = np.zeros((0, 2))
        return peaks

    def get_rts(self, msLevel=1):
        return self.rts[msLevel]
