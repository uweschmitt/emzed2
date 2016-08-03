# encoding: utf-8
from __future__ import print_function, division

from collections import defaultdict
import itertools

from tables import Atom, UInt32Col, Float64Col, Float32Col, UInt64Col, StringCol, Int32Col
import numpy as np

from emzed_optimizations import sample_peaks_from_lists

from .. import PeakMap

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
                description["scan_number"] = Int32Col(pos=2)
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
            description["rtmin_1"] = Float32Col(pos=3)
            description["rtmax_1"] = Float32Col(pos=4)
            description["rtmin_2"] = Float32Col(pos=5)
            description["rtmax_2"] = Float32Col(pos=6)
            description["mzmin_1"] = Float64Col(pos=7)
            description["mzmax_1"] = Float64Col(pos=8)
            description["mzmin_2"] = Float64Col(pos=9)
            description["mzmax_2"] = Float64Col(pos=10)
            pm_table = self.file_.create_table(self.node, 'pm_table', description, filters=filters)
            # every colums which appears in a where method call should/must be indexed !
            # this is not only for performance but for correct lookup as well (I had strange bugs
            # else)
            pm_table.cols.unique_id.create_index()
            pm_table.cols.index.create_index()

    @profile
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
        sn = spec.scan_number
        row["scan_number"] = -1 if sn is None else sn
        row["start"] = start
        row["end"] = start + size

        row.append()

    @profile
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

        rtmin_1, rtmax_1 = pm.rtRange(1)
        rtmin_2, rtmax_2 = pm.rtRange(2)
        mzmin_1, mzmax_1 = pm.mzRange(1)
        mzmin_2, mzmax_2 = pm.mzRange(2)

        index = self.node.pm_table.nrows
        row = self.node.pm_table.row
        row["unique_id"] = unique_id
        row["index"] = index
        row["ms_levels"] = as_str
        row["rtmin_1"] = rtmin_1
        row["rtmax_1"] = rtmax_1
        row["rtmin_2"] = rtmin_2
        row["rtmax_2"] = rtmax_2
        row["mzmin_1"] = mzmin_1
        row["mzmax_1"] = mzmax_1
        row["mzmin_2"] = mzmin_2
        row["mzmax_2"] = mzmax_2
        row.append()

        for spec in sorted(pm.spectra, key=lambda s: s.rt):
            self.add_spectrum(index, spec)

        yield int(index)

    def _read(self, col_index, index):
        result = list(self.node.pm_table.where("""index == %r""" % index))
        if len(result) == 0:
            raise ValueError("index %d not in table" % index)

        ms_levels = result[0]["ms_levels"]
        rtmin_1 = result[0]["rtmin_1"]
        rtmax_1 = result[0]["rtmax_1"]
        mzmin_1 = result[0]["mzmin_1"]
        mzmax_1 = result[0]["mzmax_1"]
        rtmin_2 = result[0]["rtmin_2"]
        rtmax_2 = result[0]["rtmax_2"]
        mzmin_2 = result[0]["mzmin_2"]
        mzmax_2 = result[0]["mzmax_2"]
        unique_id = result[0]["unique_id"]
        ms_levels = map(int, ms_levels.split(","))

        result = Hdf5PeakMapProxy(node=self.node,
                                  index=index,
                                  ms_levels=ms_levels,
                                  rtmin_1=rtmin_1,
                                  rtmax_1=rtmax_1,
                                  mzmin_1=mzmin_1,
                                  mzmax_1=mzmax_1,
                                  rtmin_2=rtmin_2,
                                  rtmax_2=rtmax_2,
                                  mzmin_2=mzmin_2,
                                  mzmax_2=mzmax_2,
                                  unique_id=unique_id)
        return result

    def flush(self):
        self.node.pm_table.flush()
        self.node.ms1_spec_table.flush()
        self.node.ms2_spec_table.flush()


class Hdf5PeakMapProxy(object):

    def __init__(self, **kw):
        for name, value in kw.items():
            setattr(self, name, value)
        self.setup(kw)

    def setup(self, kw):
        self.meta = {"unique_id": kw.get("unique_id")}
        rts = defaultdict(list)
        starts = defaultdict(list)
        scan_numbers = defaultdict(list)
        for level in (1, 2):
            t = getattr(self.node, "ms%d_spec_table" % level)
            has_scan_number = "scan_number" in t.colnames
            row = None
            for row in t.where("pm_index == %d" % self.index):
                rts[level].append(row["rt"])
                starts[level].append(row["start"])
                if has_scan_number:
                    scan_numbers[level].append(row["scan_number"])
                else:
                    scan_numbers[level].append(-1)
            # we save memory and only load starts, for the last item will be helpful for slicing,
            # row might be None if no spectra of given level are contained in peakmap
            if row is not None:
                starts[level].append(row["end"])

        for level in rts:
            rts[level] = np.array(rts[level], dtype=float)
            starts[level] = np.array(starts[level], dtype=int)
            scan_numbers[level] = np.array(scan_numbers[level], dtype=int)

        self.rts = rts
        self.starts = starts
        self.scan_numbers = scan_numbers

    def uniqueId(self):
        return self.unique_id

    def getMsLevels(self):
        return self.ms_levels

    def __str__(self):
        return "<Hdf5PeakmapProxy unique_id=%s>" % self.unique_id

    def _try_to_fix_for_unique_ms_level(self, msLevel):
        """if msLevel is None: return 1 if only MS1 are present,
                               return 2 if only MS2 are present,
                               return None if both are present
        """
        assert msLevel in (1, 2, None)
        if msLevel is None and 2 not in self.ms_levels:
            return 1
        elif msLevel is None and 1 not in self.ms_levels:
            return 2
        else:
            return msLevel

    def rtRange(self, msLevel=1):
        msLevel = self._try_to_fix_for_unique_ms_level(msLevel)
        if msLevel is not None and msLevel not in self.ms_levels:
            return None, None
        if msLevel == 1:
            return self.rtmin_1, self.rtmax_1
        elif msLevel == 2:
            return self.rtmin_2, self.rtmax_2
        else:
            return min(self.rtmin_1, self.rtmin_2), max(self.rtmax_1, self.rtmax_2)

    def mzRange(self, msLevel=1):
        msLevel = self._try_to_fix_for_unique_ms_level(msLevel)
        if msLevel == 1:
            return self.mzmin_1, self.mzmax_1
        elif msLevel == 2:
            return self.mzmin_2, self.mzmax_2
        else:
            return min(self.mzmin_1, self.mzmin_2), max(self.mzmax_1, self.mzmax_2)

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
