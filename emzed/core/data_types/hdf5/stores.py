# encoding: utf-8, division
from __future__ import print_function, division

import abc
from datetime import datetime
import functools
import time

import dill
from tables import (Filters, StringAtom, Int64Col, Atom, Float32Col, BoolCol,
                    UInt8Col, UInt32Col, UInt64Col, StringCol)
import numpy as np


from emzed_optimizations.sample import sample_peaks as optim_sample_peaks

from ..ms_types import Spectrum, PeakMap
from ..col_types import TimeSeries

filters = Filters(complib="blosc", complevel=9)


from install_profile import profile

from lru import LruDict, lru_cache


def timeit(function):
    @functools.wraps(function)
    def inner(*args, **kwargs):
        started = time.time()
        result = function(*args, **kwargs)
        needed = time.time() - started
        print("calling %s needed %.2e seconds" % (function.__name__, needed))
        return result
    return inner


class Store(object):

    __metaclass__ = abc.ABCMeta

    def write(self, obj):
        writer = self._write(obj)
        hash_key = writer.next()
        index = self.write_cache.get(hash_key)
        if index is not None:
            return index

        index = writer.next()
        self.write_cache[hash_key] = index
        return index

    @abc.abstractmethod
    def _write(obj):
        pass

    @profile
    def read(self, index):
        if index in self.read_cache:
            return self.read_cache[index]
        result = self._read(index)
        self.read_cache[index] = result
        return result

    @abc.abstractmethod
    def _read(index):
        pass

    @abc.abstractmethod
    def finalize():
        pass

    def close(self):
        if self.file_.isopen:
            self.file_.close()

    def dump(self):
        pass


class PeakMapStore(Store):

    MSLEVEL_FIELD_SIZE = 16

    def __init__(self, file_, node=None):
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
            spec_table = self.file_.create_table(self.node, 'spec_table', description, filters=filters)

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
        self.node.spec_table

    @profile
    def _write(self, pm):

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
            raise ValueError(
                "current implementation does not support so many ms levels: %s" % as_str)

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

    @profile
    def _read(self, index):
        result = list(self.node.pm_table.where("""index == %r""" % index))
        if len(result) == 0:
            raise ValueError("index %d not in table" % index)

        ms_levels = result[0]["ms_levels"]
        rtmin = result[0]["rtmin"]
        rtmax = result[0]["rtmax"]
        mzmin = result[0]["mzmin"]
        mzmax = result[0]["mzmax"]
        unique_id = result[0]["unique_id"]

        result = PeakMapProxy(node=self.node,
                              index=index,
                              ms_levels=map(int, ms_levels.split(",")),
                              rtmin=rtmin,
                              rtmax=rtmax,
                              mzmin=mzmin,
                              mzmax=mzmax,
                              unique_id=unique_id)
        return result

    def finalize(self):
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

    # @timeit
    @lru_cache(maxsize=1000)
    def chromatogram(self, mzmin=None, mzmax=None, rtmin=None, rtmax=None, ms_level=1):
        rts = []
        intensities = []
        for rt, mzs, iis in self._iter_peaks(rtmin, rtmax, mzmin, mzmax, ms_level):
            rts.append(rt)
            intensities.append(np.sum(iis))
        return rts, intensities

    # @timeit
    @lru_cache(maxsize=1000)
    def sample_peaks(self, rtmin, rtmax, mzmin, mzmax, npeaks, ms_level):
        spectra = []
        for rt, mzs, iis in self._iter_peaks(rtmin, rtmax, mzmin, mzmax, ms_level):
            peaks = np.vstack((mzs, iis)).T
            spectrum = Spectrum(peaks, rt, ms_level, "0", [])
            spectra.append(spectrum)
        peaks = optim_sample_peaks(PeakMap(spectra), rtmin, rtmax, mzmin, mzmax, npeaks, ms_level)
        return peaks


class StringStore(Store):

    def __init__(self, file_, node, block_size=None, blob_name="string_blob",
                 index_name="string_index"):
        if block_size is None:
            block_size = 64

        self.file_ = file_
        self.node = node
        self.block_size = block_size

        self.write_cache = LruDict(10000)
        self.read_cache = LruDict(10000)

        self.setup(node, block_size, blob_name, index_name)

        self.blob_array = getattr(node, blob_name)
        self.index_table = getattr(node, index_name)

        self.next_index = self.index_table.nrows

    def setup(self, node, block_size, blob_name, index_name):

        if not hasattr(node, blob_name):
            self.file_.create_earray(node, blob_name,
                                     StringAtom(itemsize=block_size), (0,),
                                     filters=filters)

            description = {}
            description["index"] = Int64Col(pos=0)
            description["start"] = UInt32Col(pos=1)
            description["size"] = UInt32Col(pos=2)

            # every colums which appears in a where method call should/must be indexed !
            # this is not only for performance but for correct lookup as well (I had strange bugs
            # else)
            string_index = self.file_.create_table(node, index_name, description, filters=None)
            string_index.cols.index.create_index()

    @profile
    def _write(self, s):

        # hash key
        yield s

        # store and yield index
        yield self._write_str(s).next()

    def _write_str(self, s):

        blob = self.blob_array
        start = blob.nrows
        for k in range(0, len(s), self.block_size):
            part = s[k:k + self.block_size]
            blob.append([part])

        row = self.index_table.row
        row["index"] = self.next_index
        row["start"] = start
        row["size"] = blob.nrows - start
        row.append()

        next_index = self.next_index
        self.next_index += 1
        yield next_index


    @profile
    def _read(self, index):

        rows = list(self.index_table.where("""index == %d""" % index))
        if len(rows) == 0:
            raise ValueError("index %d not in table" % index)
        assert len(rows) == 1, "internal error"

        row = rows[0]
        start = row["start"]
        size = row["size"]

        return "".join(self.blob_array[start:start + size])

    def finalize(self):
        self.index_table.flush()
        self.blob_array.flush()


class ObjectStore(StringStore):

    def __init__(self, file_, node):
        super(ObjectStore, self).__init__(file_, node, 32, "object_blob", "obect_index")
        self.obj_read_cache = LruDict(500)

    @profile
    def _write(self, obj):

        # hash key
        yield id(obj)

        code = dill.dumps(obj, protocol=2)
        code = code.replace("\\", "\\\\").replace("\0", "\\0")
        yield self._write_str(code).next()

    @profile
    def _resolve(self, index):
        if index in self.obj_read_cache:
            return self.obj_read_cache[index]
        code = StringStore._read(self, index)
        code = code.replace("\\\\", "\\").replace("\\0", "\0")
        obj = dill.loads(code)
        self.obj_read_cache[index] = obj
        return obj

    def _read(self, index):
        return ObjectProxy(self, index)


class ObjectProxy(object):

    def __init__(self, reader, index):
        self.reader = reader
        self.index = index
        self.obj = None

    def load(self):
        if self.obj is None:
            self.obj = self.reader._resolve(self.index)
        return self.obj


class TimeSeriesStore(Store):

    def __init__(self, file_, node=None):
        self.file_ = file_
        self.node = node
        if not hasattr(node, "ts_x_values"):
            self.setup()

        self.x_blob = self.node.ts_x_values
        self.y_blob = self.node.ts_y_values
        self.bp = self.node.bp
        self.ts_index = self.node.ts_index

        self.next_index = self.ts_index.nrows

        self.write_cache = LruDict(100)
        self.read_cache = LruDict(100)

    def setup(self):

        self.x_blob = self.file_.create_earray(self.node, "ts_x_values",
                                               Atom.from_dtype(np.dtype("int64")), (0,),
                                               filters=filters)

        self.y_blob = self.file_.create_earray(self.node, "ts_y_values",
                                               Atom.from_dtype(np.dtype("float64")), (0,),
                                               filters=filters)

        self.bp = self.file_.create_earray(self.node, "bp",
                                           Atom.from_dtype(np.dtype("int32")), (0,),
                                           filters=filters)

        description = {}
        description["unique_id"] = StringCol(itemsize=64, pos=0)
        description["index"] = UInt32Col(pos=1)
        description["blank_flags_is_none"] = BoolCol(pos=2)
        description["label"] = StringCol(itemsize=32, pos=3)
        description["start"] = UInt32Col(pos=4)
        description["size"] = UInt32Col(pos=5)

        description["bp_start"] = UInt32Col(pos=6)
        description["bp_size"] = UInt32Col(pos=7)

        self.ts_index = self.file_.create_table(self.node, "ts_index", description,
                                                filters=None)

        # every colums which appears in a where method call should/must be indexed !
        # this is not only for performance but for correct lookup as well (I had strange bugs
        # else)
        self.ts_index.cols.unique_id.create_index()
        self.ts_index.cols.index.create_index()

    def _write(self, obj):

        unique_id = obj.uniqueId()
        yield unique_id

        result = list(self.ts_index.where("""unique_id == %r""" % unique_id))
        if result:
            yield result[0]["index"]

        start = self.x_blob.nrows
        size = len(obj.x)

        self.x_blob.append([xi.toordinal() for xi in obj.x])
        self.y_blob.append(obj.y)

        bp_start = self.bp.nrows
        if obj.is_blank is None:
            bp_size = 0
        else:
            blank_positions = [i for (i, f) in enumerate(obj.is_blank) if f]
            self.bp.append(blank_positions)
            bp_size = len(blank_positions)

        row = self.ts_index.row
        row["unique_id"] = unique_id
        row["label"] = obj.label or ""
        row["blank_flags_is_none"] = obj.is_blank is None
        row["index"] = self.next_index
        row["start"] = start
        row["size"] = size
        row["bp_start"] = bp_start
        row["bp_size"] = bp_size
        row.append()

        next_index = self.next_index
        self.next_index += 1
        yield next_index

    @profile
    def _read(self, index):
        result = list(self.node.ts_index.where("""index == %r""" % index))
        if len(result) == 0:
            raise ValueError("index %d not in table" % index)

        assert len(result) == 1
        row = result[0]
        label = row["label"]
        start = row["start"]
        size = row["size"]
        bp_start = row["bp_start"]
        bp_size = row["bp_size"]
        blank_flags_is_none = row["blank_flags_is_none"]

        x = self.x_blob[start:start + size]
        x = map(datetime.fromordinal, x)

        y = self.y_blob[start:start + size]
        blank_pos = self.bp[bp_start:bp_start + bp_size]

        if blank_flags_is_none:
            is_blank = None
        else:
            is_blank = [i in blank_pos for i in range(len(x))]

        ts = TimeSeries(x, y, label, is_blank)
        return ts

    def dump(self):
        names = self.node.ts_index.colnames
        import emzed
        t = emzed.core.Table(names, [object] * len(names), ["%s"] * len(names), rows=[])
        tsi = []
        for row in self.node.ts_index:
            t.addRow(list(row.fetch_all_fields()))
            tsi.append(self._read(row["index"]))

        t.resetInternals()
        yvals = ["%s..%s" % (min(ti.y), max(ti.y)) for ti in tsi]
        t.addColumn("y", yvals, type_=object)
        print(t)

    def finalize(self):
        self.x_blob.flush()
        self.y_blob.flush()
        self.bp.flush()
        self.ts_index.flush()
