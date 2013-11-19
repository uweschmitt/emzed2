import pdb
import emzed
import numpy as np
import sys

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

negative_adducts = emzed.adducts.negative

mz_accuracy = 1e-4
rt_accuracy = 5

feature_tables = table.splitBy("feature_id")
feature_tables.sort(key=lambda t: (-len(t), max(t.rt.values), -len(t),))


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
        return len(self.mzs)


class FeatureCluster(object):

    def __init__(self, f0):
        self.features = [f0]

        self.rts = np.array(f0.rts)
        self.mzs = np.array(f0.mzs)
        self.ids = f0.ids[:]
        self.z = f0.z
        self.min_rt = min(self.rts)
        self.max_rt = max(self.rts)
        self.min_mz = min(self.mzs)
        self.max_mz = max(self.mzs)
        self.len_ = len(self.rts)

        self.merged_rts = self.rts
        self.merged_mzs = self.mzs
        self.merged_ids = self.ids
        self.merged_z = None

    def match_for_same_adduct(self, other, max_mz_range, mz_accuracy, rt_accuracy):
        assert isinstance(self, FeatureCluster)
        assert isinstance(other, Feature)
        if self.z < 0 or other.z < 0 or self.z > 0 and other.z > 0 and self.z != other.z:
            return None
        if max(self.max_rt - other.min_rt, other.max_rt - self.min_rt) >= rt_accuracy:
            return None
        if self.z == 0:
            z = other.z
        else:
            z = self.z
        if z == 0:
            z_to_try = [1, 2, 3]
        else:
            z_to_try = [z]

        matches = []
        for z in z_to_try:
            mz_self = self.merged_mzs[:, None]
            mz_other = other.mzs[None, :]
            n_approx = (mz_self - mz_other) * z
            if np.any(np.abs(n_approx) > max_mz_range):
                continue
            # determine n
            n = np.round(n_approx / delta_C)
            diff = np.abs(n * delta_C / z + mz_other - mz_self)
            if np.any(np.abs(n) < 1e-10) or np.any(diff > mz_accuracy):
                continue
            matches.append(z)
        if len(matches) == 1:
            return matches[0]
        return None

    @profile
    def merge_feature(self, other, z):
        assert isinstance(self, FeatureCluster)
        assert isinstance(other, Feature)
        self.merged_rts = np.hstack((self.merged_rts, other.rts))
        self.merged_mzs = np.hstack((self.merged_mzs, other.mzs))
        self.merged_ids.extend(other.ids)
        self.merged_z = z
        self.min_rt = np.min(self.merged_rts)
        self.max_rt = np.max(self.merged_rts)
        self.min_mz = np.min(self.merged_mzs)
        self.max_mz = np.max(self.merged_mzs)
        self.len_ = len(self.merged_rts)
        self.features.append(other)

    def split_invalid_merges(self, max_iso_gap=1):

        if self.merged_z == 0:
            print "keep separated",
            for f0 in self.features:
                print f0.id,
            print "mzs=",
            for f0 in self.features:
                print f0.mzs,
            print "z=", self.merged_z

            return [FeatureCluster(f0) for f0 in self.features]

        self.features.sort(key=lambda f: min(f.mzs))

        clusters = []

        cluster = FeatureCluster(self.features[0])
        for f0, f1 in zip(self.features, self.features[1:]):
            mz_gap = min(f1.mzs) - max(f0.mzs)
            n_gap = int(round(mz_gap * (self.merged_z / delta_C))) - 1
            if n_gap > max_iso_gap:
                print "keep separated",
                clusters.append(cluster)
                cluster = FeatureCluster(f1)
            else:
                print "merge",
                cluster.merge_feature(f1, self.merged_z)
            print f0.ids, f1.ids, "mzs=", f0.mzs, f1.mzs, "gap=", n_gap, "z=", self.merged_z
        clusters.append(cluster)
        return clusters


class IsotopeMerger(object):

    isotope_cluster_id_column_name = "isotope_cluster_id"
    isotope_rank_column_name = "isotope_rank"
    isotope_cluster_size_column_name = "isotope_cluster_size"
    isotope_gap_column_name = "isotope_gap"

    def __init__(self, mz_accuracy=1e-4, rt_accuracy=10.0, max_mz_range=20, max_iso_gap=1,
                    mz_integration_window=1e-3, fid_column="feature_id"):
        self.mz_accuracy = mz_accuracy
        self.rt_accuracy = rt_accuracy
        self.max_mz_range = max_mz_range
        self.max_iso_gap = max_iso_gap
        self.mz_integration_window = mz_integration_window
        self.fid_column = fid_column

    def process(self, table):

        col_names = table.getColNames()
        assert self.fid_column in col_names, (self.fid_column, col_names)
        assert "id" in col_names, col_names
        assert "mz" in col_names, col_names
        assert "rt" in col_names, col_names
        assert "z" in col_names, col_names
        assert "area" in col_names, col_names

        n_features = len(set(table.getColumn(self.fid_column).values))
        n_z0_in = len(set(table.filter(table.z == 0).feature_id.values))
        print "process table of length", len(table), "with", n_features, "features"

        features = self._extract_features(table)
        candidates = self._detect_candidates(features)
        n_candidates = len(candidates)
        clusters = self._merge_candidates(candidates)
        n_clusters = len(clusters)

        table = self._add_new_columns(table, features)
        n_z0_out = len(set(table.filter(table.z == 0).feature_id.values))
        table = self._add_missing_mass_traces(table)
        print
        print "started with  %5d features which had %5d features with z=0" % (n_features, n_z0_in)
        print "detected      %5d candidates" % n_candidates
        print "finally found %5d clusters which had %5d features with z=0" % (n_clusters, n_z0_out)
        print
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
    def _detect_candidates(self, features):
        features.sort(key=lambda f: (-len(f), f.max_rt))

        n = len(features)
        # counter = ProgressCounter(n)
        start_idx = dict()
        last_l = -1
        for i, f in enumerate(features):
            l = len(f)
            if l != last_l:
                start_idx[l] = i
                last_l = l
        start_idx[0] = n

        candidates = []

        used = set()
        last = ""

        for i, f0 in enumerate(features):
            if i % 100 == 0:
                now = "%.0f" % (round(100.0 * i / len(features) / 5) * 5)
                if now != last:
                    print now,
                    sys.stdout.flush()
                    last = now
            if i in used:
                continue
            cluster = FeatureCluster(f0)
            j = i + 1
            while j < n:
                if j not in used:
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
                                    z = cluster.match_for_same_adduct(f1,
                                                                      self.max_mz_range,
                                                                      self.mz_accuracy,
                                                                      self.rt_accuracy
                                                                      )
                                    if z is not None:
                                        cluster.merge_feature(f1, z)
                                        used.add(j)
                j += 1
            candidates.append(cluster)
        print len(candidates), "isotope cluster candidates"
        return candidates

    def _merge_candidates(self, candidates):
        clusters = [c for cluster in candidates
                      for c in cluster.split_invalid_merges(self.max_iso_gap)]
        print len(clusters), "isotope clusters"
        return clusters

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
    def guess_z(mzs, mz_accuracy, max_gap_size=1, max_num_gaps=2):
        matches = []
        mzs = np.array(sorted(mzs))
        for z in (1, 2, 3):
            iis = (mzs - mzs[0]) * z / delta_C
            iis = np.round(iis)
            max_dist = np.max(np.abs((mzs - mzs[0] - iis * delta_C / z)))
            if max_dist > mz_accuracy:
                continue

            iis = iis.astype(np.int)
            num_gaps = np.sum(iis[1:] - iis[:-1] > 1)
            largest_gap = np.max(iis[1:] - iis[:-1] - 1)
            if num_gaps <= max_num_gaps and largest_gap <= max_gap_size:
                matches.append(z)
        if len(matches) == 1:
            return matches[0]
        # no matches or multitude of matches
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
            if z == 0:
                z = self.guess_z(t.mz.values, self.mz_accuracy)
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
        igc = table.getColumn(self.isotope_gap_column_name)
        do_not_handle = table.filter((igc.isNone() | (igc == 0) | (igc > self.max_iso_gap))
        do_handle = table.filter(igc.isNotNone() & (igc >0 ) & (igc <= self.max_iso_gap))
        filled_up_subtables = []
        for group in do_handle.splitBy(self.isotope_cluster_id_column_name):
            iso_cluster_id = group.getColumn(self.isotope_cluster_id_column_name).uniqueValue()
            rtmin = group.rt.min()
            rtmax = group.rt.max()
            mzs = sorted(group.mz.values)
            z = group.z.uniqeValue()
            mz0 = min(mzs)
            proto = group.rows[0]
            while mz0 < max(mzs):
                mz0 += delta_C / z
                if any(abs(mz0-mz) < 1e-2 for mz in mzs):
                    continue
                print "add integration window for iso cluster %d and mz= %.5f" % (iso_cluster_id,
                        mz0)
                proto[group.getIndex("mz")] = mz0
                proto[group.getIndex("mzmin")] = mz0 - self.mz_integration_window / 2.0
                proto[group.getIndex("mzmax")] = mz0 + self.mz_integration_window / 2.0
                proto[group.getIndex("rtmin")] = rtmin
                proto[group.getIndex("rtmax")] = rtmax
            integrated = emzed.utils.integrate(group)
            filled_up_subtables.append(integrated)
        return emzed.utils.mereTables([do_not_handle] + filled_up_subtables)





# mzs = [0.0, delta_C,  delta_C * 3.0]
# print IsotopeMerger.guess_z(mzs, 1e-3)
# exit()

table = IsotopeMerger().process(table[:100000])
emzed.io.storeTable(table, "isotope_clustered.table", True)
emzed.gui.inspect(table)
