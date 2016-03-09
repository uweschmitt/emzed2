# encoding: utf-8, division
from __future__ import print_function, division

import abc

from collections import OrderedDict

import dill
from tables import (open_file, Filters, StringAtom, Int64Col, Float64Col, Atom, Float32Col,
                    UInt8Col, UInt32Col, UInt64Col, StringCol)
import numpy as np

from backports.functools_lru_cache import lru_cache


filters = Filters(complib="blosc", complevel=9)


class LruDict(object):

    def __init__(self, maxsize):
        self.maxsize = maxsize
        self._data = OrderedDict()

    def __setitem__(self, k, v):
        self._data[k] = v
        if len(self._data) > self.maxsize:
            self._data.popitem(last=False)

    def __getattr__(self, name):
        return getattr(self._data, name)

    def __contains__(self, what):
        return what in self._data


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


class PeakMapStore(Store):


    def __init__(self, file_, node=None):
        self.file_ = file_
        self.node = node
        if not hasattr(node, "mz_blob"):
            self.setup()

        self.write_cache = LruDict(100)
        self.read_cache = LruDict(100)


    def setup(self):
        """
        plan: array for mzs, array for intensities
        table:  rt, ms_level, i_start, i_end
        table:  peakmap_hash_code, i_start, i_end
        """
        self.setup_blobs()
        self.setup_spec_table()
        self.setup_peakmap_table()

    def setup_blobs(self):
        self.mz_blob = self.file_.create_earray(self.node, "mz_blob",
                                                Atom.from_dtype(np.dtype("float64")), (0,),
                                                filters=filters,
                                                # chunkshape=(1e4,),
                                                )

        self.ii_blob = self.file_.create_earray(self.node, "ii_blob",
                                                Atom.from_dtype(np.dtype("float32")), (0,),
                                                filters=filters,
                                                # chunkshape=(5e4,),
                                                )

    def setup_spec_table(self):
        description = OrderedDict()
        description["pm_index"] = UInt32Col()
        description["rt"] = Float32Col()
        description["ms_level"] = UInt8Col()
        description["start"] = UInt64Col()
        description["size"] = UInt32Col()
        self.spec_table = self.file_.create_table(self.node, 'spectra', description, filters=filters)

    def setup_peakmap_table(self):
        description = OrderedDict()
        description["unique_id"] = StringCol(itemsize=64)
        description["index"] = UInt32Col()
        self.pm_table = self.file_.create_table(self.node, 'peakmaps', description, filters=filters)

    def add_spectrum(self, pm_index, spec):

        start = self.last_peak_idx
        self.mz_blob.append(spec.peaks[:, 0])
        self.ii_blob.append(spec.peaks[:, 1])

        size = spec.peaks.shape[0]

        row = self.spec_table.row
        row["pm_index"] = pm_index
        row["rt"] = spec.rt
        row["ms_level"] = spec.msLevel
        row["start"] = start
        row["size"] = size

        self.last_peak_idx = start + size

        row.append()

    def _write(self, pm):

        unique_id = pm.uniqueId()
        # hash key
        yield unique_id

        result = list(self.pm_table.where("""unique_id == %r""" % unique_id))
        if result:
            yield result[0]["index"]
            return

        index = self.pm_table.nrows
        row = self.pm_table.row
        row["unique_id"] = unique_id
        row["index"] = index
        row.append()
        self.pm_table.flush()

        self.last_peak_idx = self.spec_table.nrows
        for spec in pm.spectra:
            self.add_spectrum(index, spec)
        self.spec_table.flush()

        yield index

    def _read(self, index):
        result = list(self.node.peakmaps.where("""index == %r""" % index))
        if len(result) == 0:
            raise ValuError("index %d not in table" % index)

        result = PeakMapProxy(index)
        return result

    def finalize(self):

        self.pm_table.cols.unique_id.create_index()
        self.spec_table.cols.pm_index.create_index()
        self.spec_table.cols.rt.create_index()
        self.pm_table.flush()
        self.spec_table.flush()


class PeakMapProxy(object):

    def __init__(self, index):
        self.index = index

    def fetch_chromatogram(self, rtmin, rtmax, mzmin, mzmax, ms_level=1):

        mz_blob = self.file_.root.mz_blob
        ii_blob = self.file_.root.ii_blob

        rts = []
        intensities = []

        query = """(index == %d) & (%f <= rt) & (rt <= %f)""" % (self.index, rtmin, rtmax)
        for row in self.file_.root.spectra.where(query):
            rt = row["rt"]
            if ms_level != row["ms_level"]:
                continue
            i_start = row["i_start"]
            i_end = row["i_end"]
            mzs = mz_blob[i_start:i_end]
            iis = ii_blob[i_start:i_end]
            idx = np.where((mzmin <= mzs) * (mzs <= mzmax))[0]
            iis = iis[idx]
            rts.append(rt)
            intensities.append(np.sum(iis))

        return rts, intensities


class StringStore(Store):

    def __init__(self, file_, node, block_size=None, blob_name="string_blob", index_name="string_index"):
        if block_size is None:
            block_size = 16

        self.file_ = file_
        self.node = node
        self.block_size = block_size

        self.write_cache = LruDict(10000)
        self.read_cache = LruDict(10000)

        if not hasattr(node, blob_name):
            self.setup(node, block_size, blob_name, index_name)

        self.blob_array = getattr(node, blob_name)
        self.index_table = getattr(node, index_name)

    def setup(self, node, block_size, blob_name, index_name):

        self.string_blob = self.file_.create_earray(node, blob_name,
                                                    StringAtom(itemsize=block_size), (0,),
                                                    filters=None)

        description = OrderedDict()
        description["index"] = Int64Col()
        description["start"] = UInt32Col()
        description["size"] = UInt32Col()

        self.string_index = self.file_.create_table(node, index_name, description, filters=None)

        self.last_index = 0
        self.last_blob_index = 0

    def _write(self, s):

        # hash key
        yield s

        start = self.last_blob_index
        for k in range(0, len(s), self.block_size):
            part = s[k:k + self.block_size]
            self.blob_array.append([part])
            self.last_blob_index += 1

        row = self.index_table.row
        row["index"] = self.last_index
        row["start"] = start
        row["size"] = self.last_blob_index - start
        row.append()

        last_index = self.last_index
        self.last_index += 1
        yield last_index

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
        self.index_table.cols.index.create_index()
        self.index_table.flush()


class ObjectStore(StringStore):

    def __init__(self, file_, node):
        super(ObjectStore, self).__init__(file_, node, 32, "object_blob", "obect_index")

    def _write(self, obj):
        code = dill.dumps(obj, protocol=2)
        code = code.replace("\\", "\\\\").replace("\0", "\\0")
        for item in StringStore._write(self, code):
            yield item

    def _read(self, index):
        code = StringStore._read(self, index)
        code = code.replace("\\\\", "\\").replace("\\0", "\0")
        return dill.loads(code)


