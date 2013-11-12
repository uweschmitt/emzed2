import emzed
import sys
import numpy as np

from collections import Counter

#from util import ProgressCounter

try:
    table = emzed.io.loadTable("shoulders_table_integrated.table")
except:
    table = emzed.io.loadTable("shoulders_table_with_chromos.table")
    table = emzed.utils.integrate(table, "trapez")
    emzed.io.storeTable(table, "shoulders_table_integrated.table")

if 1:
    table = table.filter(table.area > 5e4)
    table.dropColumns("id")
    table.addEnumeration()

try:
    profile
except:
    profile = lambda x: x


delta_C = emzed.mass.C13 - emzed.mass.C12


class Feature(object):

    def __init__(self, rts, mzs, ids, z):
        assert len(rts) == len(mzs) == len(ids)
        assert z in range(5)
        self.rts = np.array(rts)
        self.mzs = np.array(mzs)
        self.ids = ids
        self.z = z
        self.min_rt = min(rts)
        self.max_rt = max(rts)
        self.min_mz = min(mzs)
        self.max_mz = max(mzs)
        self.len_ = len(self.rts)

    def __len__(self):
        return self.len_

    @profile
    def match_for_same_adduct(self, other, mz_accuracy, rt_accuracy, max_mz_range):
        if self.z < 0 or other.z < 0 or self.z > 0 and other.z > 0 and self.z != other.z:
            return None
        if self.z == 0:
            z = other.z
        else:
            z = self.z
        if z == 0:
            z_to_try = [1, 2, 3]
        else:
            z_to_try = [z]

        #if 1114 in self.ids and 6706 in other.ids:
            #import pdb; pdb.set_trace()

        for z in z_to_try:
            mz_self = self.mzs[:, None]
            mz_other = other.mzs[None, :]
            n_approx = (mz_self - mz_other) * z
            if np.any(np.abs(n_approx) > max_mz_range):
                continue
            # determine n
            n = np.round(n_approx / delta_C)
            diff = np.abs(n * delta_C / z + mz_other - mz_self)
            if np.any(np.abs(n) < 1e-10) or np.any(diff > mz_accuracy):
                continue
            return z
        return None

    @profile
    def merge_feature(self, other, z):
        self.rts = np.hstack((self.rts, other.rts))
        self.mzs = np.hstack((self.mzs, other.mzs))
        # self.rts.extend(other.rts)
        # self.mzs.extend(other.mzs)
        self.ids.extend(other.ids)
        self.z = z
        self.min_rt = np.min(self.rts)
        self.max_rt = np.max(self.rts)
        self.min_mz = np.min(self.mzs)
        self.max_mz = np.max(self.mzs)
        self.len_ = len(self.rts)
        other.ids = other.rts = other.mzs = []
        other.z = -1
        other.min_rt = other.max_rt = -1000.0
        other.len_ = 0


class IsotopeMerger(object):

    isotope_cluster_id_column_name = "isotope_cluster_id"
    isotope_rank_column_name = "isotope_rank"
    isotope_cluster_size_column_name = "isotope_cluster_size"
    isotope_gap_column_name = "isotope_gap"

    def __init__(self, mz_accuracy=1e-4, rt_accuracy=10.0, max_mz_range=20, fid_column="feature_id"):
        self.mz_accuracy = mz_accuracy
        self.rt_accuracy = rt_accuracy
        self.max_mz_range = max_mz_range
        self.fid_column = fid_column 

    def process(self, table):

        col_names = table.getColNames()
        assert self.fid_column in col_names, (self.fid_column, col_names)
        assert "id" in col_names, col_names
        assert "mz" in col_names, col_names
        assert "rt" in col_names, col_names
        assert "z" in col_names, col_names
        assert "area" in col_names, col_names

        nfeat = len(set(table.getColumn(self.fid_column).values))
        print "process table of length", len(table), "with", nfeat, "features"

        features = self._extract_features(table)
        features = self._merge(features)
        table = self._add_new_columns(table, features)
        self._add_missing_mass_traces(table)
        return table

    def _extract_features(self, table):
        feature_tables = table.splitBy(self.fid_column)
        features = list()
        for t in feature_tables:
            rts = t.rt.values
            mzs = t.mz.values
            ids = t.id.values
            z = t.z.uniqueValue()
            feat = Feature(rts, mzs, ids, z)
            features.append(feat)
        return features

    @profile
    def _merge(self, features):
        features.sort(key=lambda f: (-len(f), f.max_rt))

        n = len(features)
        #counter = ProgressCounter(n)
        start_idx = dict()
        last_l = -1
        for i, f in enumerate(features):
            l = len(f)
            if l != last_l:
                start_idx[l] = i
                last_l = l
        start_idx[0] = n

        for i, f0 in enumerate(features):
            #counter.count_up(1)
            j = i + 1
            while j < n:
                f1 = features[j]
                if f1.min_rt > f0.max_rt + self.rt_accuracy:
                    # skip to next group
                    next_len = len(f1) - 1
                    j = start_idx.get(next_len)
                    while j is None:
                        # this loop is finite as we put key 0 in start_idx
                        next_len -= 1
                        j = start_idx.get(next_len)
                    if j == n:
                        break
                if f0.max_mz - f1.min_mz <= self.max_mz_range + 1:
                    if f1.max_mz - f0.min_mz <= self.max_mz_range + 1:
                        if f0.max_rt - f1.min_rt < self.rt_accuracy:
                            if f1.max_rt - f0.min_rt < self.rt_accuracy:
                                z = f0.match_for_same_adduct(f1, self.mz_accuracy,
                                        self.rt_accuracy, self.max_mz_range)
                                if z is not None:
                                    f0.merge_feature(f1, z)
                j += 1
        #counter.done()
        features = [f for f in features if len(f)]
        print len(features), "isotope clusters"
        return features

    @profile
    def _add_new_columns(self, table, features):

        self._add_cluster_id_column(table, features)
        table = self._add_isotope_ranks_column(table)
        table.sortBy([self.isotope_cluster_id_column_name, self.isotope_rank_column_name])
        return table

    @profile
    def _add_cluster_id_column(self, table, features):
        feature_id_map = dict()
        for fid, feature in enumerate(features):
            for id_ in feature.ids:
                feature_id_map[id_] = fid

        import cPickle
        cPickle.dump(feature_id_map, open("withoutfilter.bin", "wb"))

        c = Counter(feature_id_map.values())
        print
        print "top 10 of large clusters:"
        for fid, count in c.most_common(10):
            print "  cluster_id=%4d" % fid, "traces = %d " % count
        print

        table.addColumn(self.isotope_cluster_id_column_name,
                        table.id.apply(lambda i: feature_id_map.get(i)),
                        insertBefore=self.fid_column)

    @staticmethod
    def guess_z(mzs):
        # we assume: max gap of two isotope peaks, z in range 1, 2, 3
        if 0 <= len(mzs) <=1:
            return 0   # can not say anything

        mzs = np.array(sorted(mzs))

        if len(mzs) >= 3:
            # as n_by_z are "clear" fractions we get it like this:
            # proof: use assumptions above and verify over all combinations :)
            # one case is special: 3 peaks, shifts 1*delta_c, 2*delta_c
            # could be explained by z=1 and z=2
            # in the latter case we would have two gaps which is quite unprobable
            # keep in mind that we reach this point only if we have weak mass tracec
            # which got no z value assigned before
            n_by_z = ((mzs[1:] - mzs[:-1]) / delta_C)
            for z in (1, 2, 3):
                ns = n_by_z * z
                if np.all(np.abs(ns - np.round(ns)) <= 0.1):
                    return z
            return 0

        # now len(mzs) is 2
        n_by_z = (mzs[1] - mzs[0] / delta_C)
        if abs(n_by_z - 3.0) < 0.1:
            return 1
        if abs(n_by_z - 2.0) < 0.1:
            return 1
        if abs(n_by_z - 1/3.0) < 0.1:
            return 3
        if abs(n_by_z - 1/2.0) < 0.1:
            return 2
        # now z could be 1 or 2 !
        return 0


    @profile
    def _add_isotope_ranks_column(self, table):
        print "calculate isotope ranks"
        collected = []
        for t in table.splitBy(self.isotope_cluster_id_column_name):
            if len(t) == 1:
                t.addColumn(self.isotope_cluster_size_column_name, 1, insertBefore=self.fid_column)
                collected.append(t)
                continue
            t.sortBy("mz")
            zs = set(t.z.values)
            assert len(zs) in (1, 2), len(zs)
            if len(zs) == 1:
                z = zs.pop()
            else:
                assert 0 in zs
                zs.remove(0)
                z = zs.pop()
            if z==0:
                print t.isotope_cluster_id.uniqueValue(), t.mz.values,
                z = self.guess_z(t.mz.values)
                print z
            t.replaceColumn("z", z)

            max_gap = None
            if z is not None:

                mz_main_peak = t.filter(t.area == t.area.max()).mz.uniqueValue()

                def rank_peak(mz):
                    return int(round((mz - mz_main_peak) / delta_C * z))

                t.addColumn(self.isotope_rank_column_name,
                            t.mz.apply(rank_peak),
                            insertBefore=self.fid_column)

                ranks = sorted(t.getColumn(self.isotope_rank_column_name).values)
                if len(ranks) > 1:
                    max_gap = int(max(r1 - r0 for (r0, r1) in zip(ranks, ranks[1:]))) - 1

            t.addColumn(self.isotope_cluster_size_column_name, len(t), type_=int, format_="%d",
                        insertBefore=self.fid_column)
            t.addColumn(self.isotope_gap_column_name, max_gap, type_=int, format_="%d",
                        insertBefore=self.fid_column)
            collected.append(t)
        return emzed.utils.mergeTables(collected)

    @profile
    def _add_missing_mass_traces(self, table):
        return
        iso_gap_column = table.getColumn(iso_gap_column_name)
        do_not_handle = table.filter((iso_gap_column == 0) | (iso_gap_column >= 3))
        do_handle = table.filter((iso_gap_column == 1) | (iso_gap_column == 2))
        #for subt in do_handle.splitBy("


table = IsotopeMerger().process(table[:1000])
emzed.io.storeTable(table, "isotope_clustered.table", True)
emzed.gui.inspect(table)
