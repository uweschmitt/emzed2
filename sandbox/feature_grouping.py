import emzed
import sys
import numpy as np

from collections import Counter

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
        self.len_ = len(self.rts)

    def __len__(self):
        return self.len_

    @profile
    def match_for_same_adduct(self, other, mz_accuracy, rt_accuracy):
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

        for z in z_to_try:
            mz_self = self.mzs[:, None]
            mz_other = other.mzs[None, :]
            n_approx = (mz_self - mz_other) * z
            if np.any(n_approx > 13.0):
                continue
            # determine n
            n = np.round(n_approx / delta_C)
            diff = np.abs(n * delta_C / z + mz_other - mz_self)
            if np.any(diff > mz_accuracy):
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
        self.len_ = len(self.rts)
        other.ids = other.rts = other.mzs = []
        other.z = -1
        other.min_rt = other.max_rt = -1000.0
        other.len_ = 0


class ProgressCounter(object):

    def __init__(self, nmax):
        self.nmax = nmax
        self.last_percent = -1
        self.n = 0

    @profile
    def count_up(self, step_size=1):
        self.n += step_size
        percent = round(100.0 * self.n / self.nmax, -1)  # round to tens
        if percent != self.last_percent:
            print "%.f%%" % percent,
            sys.stdout.flush()
            self.last_percent = percent

    def done(self):
        print


class IsotopeMerger(object):

    def __init__(self, mz_accuracy=1e-4, rt_accuracy=10.0):
        self.mz_accuracy = mz_accuracy
        self.rt_accuracy = rt_accuracy

    def process(self, table, fid_column="feature_id"):

        col_names = table.getColNames()
        assert fid_column in col_names, (fid_column, col_names)
        assert "id" in col_names, col_names
        assert "mz" in col_names, col_names
        assert "rt" in col_names, col_names
        assert "z" in col_names, col_names
        assert "area" in col_names, col_names

        features = self._extract_features(table, fid_column)
        features = self._merge(features)
        table = self._add_new_columns(table, features, "isotope_cluster_id", "isotope_rank",
                                      fid_column)
        return table

    def _extract_features(self, table, fid_column):
        feature_tables = table.splitBy(fid_column)
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
        counter = ProgressCounter(n)
        start_idx = dict()
        last_l = -1
        for i, f in enumerate(features):
            l = len(f)
            if l != last_l:
                start_idx[l] = i
                last_l = l
        start_idx[0] = n

        for i, f0 in enumerate(features):
            counter.count_up(1)
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
                if f0.max_rt - f1.min_rt < self.rt_accuracy:
                    if f1.max_rt - f0.min_rt <  self.rt_accuracy:
                        z = f0.match_for_same_adduct(f1, self.mz_accuracy, self.rt_accuracy)
                        if z is not None:
                            f0.merge_feature(f1, z)
                j += 1
        counter.done()
        features = [f for f in features if len(f)]
        print len(features), "isotope clusters"
        return features

    def _add_new_columns(self, table, features, new_column_name, rank_column_name, fid_column):

        self._add_cluster_id_column(table, features, new_column_name, fid_column)
        table = self._add_isotope_ranks_column(table, rank_column_name, new_column_name,
                fid_column)
        table.sortBy([new_column_name, rank_column_name])
        return table

    def _add_cluster_id_column(self, table, features, new_column_name, fid_column):
        feature_id_map = dict()
        for fid, feature in enumerate(features):
            for id_ in feature.ids:
                feature_id_map[id_] = fid

        c = Counter(feature_id_map.values())
        print
        print "top 10 of large clusters:"
        for fid, count in c.most_common(10):
            print "  cluster_id=%4d" % fid, "traces = %d " % count
        print

        table.addColumn(new_column_name, table.id.apply(lambda i: feature_id_map.get(i)),
                        insertBefore=fid_column)

    def _add_isotope_ranks_column(self, table, rank_column_name, iso_cluster_column, fid_column):
        print "calculate isotope ranks"
        collected = []
        for t in table.splitBy(iso_cluster_column):
            if len(t) == 1:
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
            t.replaceColumn("z", z)
            mz_main_peak = t.filter(t.area == t.area.max()).mz.uniqueValue()
            def rank_peak(mz):
                return int(round((mz - mz_main_peak) / delta_C * z))
            t.addColumn(rank_column_name, t.mz.apply(rank_peak), insertBefore=fid_column)
            collected.append(t)
        return emzed.utils.mergeTables(collected)


table = IsotopeMerger().process(table[:])
emzed.io.storeTable(table, "isotope_clustered.table", True)
emzed.gui.inspect(table)
