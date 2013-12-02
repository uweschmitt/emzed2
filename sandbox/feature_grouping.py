import emzed
import numpy as np
import sys

from collections import Counter

try:
    profile
except:
    profile = lambda x: x


delta_C = emzed.mass.C13 - emzed.mass.C12
delta_N = emzed.mass.N15 - emzed.mass.N14
delta_O = emzed.mass.O18 - emzed.mass.O16
delta_S = emzed.mass.S34 - emzed.mass.S32

delta_Cl = emzed.mass.Cl37 - emzed.mass.Cl35
delta_Br = emzed.mass.Br81 - emzed.mass.Br79


class Feature(object):

    def __init__(self, rts, mzs, ids, z, areas, element_names=None, adducts=None):
        assert len(rts) == len(mzs) == len(ids)
        assert z in range(5)
        self.rts = np.array(rts)
        self.mzs = np.array(mzs)
        self.ids = ids
        self.z = z
        self.areas = np.array(areas)
        self.min_rt = min(rts)
        self.max_rt = max(rts)
        self.min_mz = min(mzs)
        self.max_mz = max(mzs)
        self.len_ = len(self.rts)
        self.element_names = set() if element_names is None else set(element_names)
        self.adducts = set() if adducts is None else set(adducts)

    def __len__(self):
        return len(self.mzs)

    def breakup(self):
        """ feature ff metabo is very tolerant for isotope shifts.
            here we regroup the traces of the current feature with high
            precision corresponding to given mass_shifts, eg delta_C or delta_Cl.
        """

        if len(self) <= 1:
            yield self
            return

        z = self.z
        mass_shifts = [(delta_C / z, "C"),
                       (delta_N / z, "N"),
                       (delta_O / z, "O"),
                       (delta_S / z, "S"),
                       (delta_Cl / z, "Cl"),
                       # (delta_Br / z, "Br"),
                       ]

        #if z == 1:
            #mass_shifts.append((delta_Cl, "Cl"))

        # build adjancy matrices for each isotope-shift which could explain a
        # pair of peaks
        distances = (self.mzs[:, None] - self.mzs[None, :])
        connections = []
        for mass_shift, element_name in mass_shifts:
            quotients = distances / mass_shift
            connection = abs(np.round(quotients) - quotients) < z * 5e-4
            connections.append((connection, element_name))

        components = []
        component_elements = []
        to_start = set(range(len(self)))
        # this is a kind of bfs graph search algorithm, with an labeled graph
        # we have a separate adjancy matrix called 'connection' for each label:
        while to_start:
            i = to_start.pop()
            stack = [(i, None)]
            component = []
            element_names = set()
            while stack:
                i0, element_name = stack.pop()
                if i0 not in component:
                    component.append(i0)
                    if element_name is not None:
                        element_names.add(element_name)
                    if i0 in to_start:
                        to_start.remove(i0)
                    for j in range(len(self)):
                        if j not in component:
                            for connection, element_name in connections:
                                if connection[i0, j]:
                                    stack.append((j, element_name))
            components.append(component)
            component_elements.append(element_names)

        if len(components) == 1:
            self.element_names = element_names
            yield self
            return

        for component, element_names in zip(components, component_elements):
            f0 = Feature([self.rts[i] for i in component],
                         [self.mzs[i] for i in component],
                         [self.ids[i] for i in component],
                         self.z,
                         [self.areas[i] for i in component],
                         element_names
                         )
            if len(f0) == 1:
                f0.z = 0
            yield f0


class FeatureCluster(object):

    def __init__(self, f0):
        self.features = [f0]

        self.rts = np.array(f0.rts)
        self.mzs = np.array(f0.mzs)
        self.ids = f0.ids[:]
        self.z = f0.z
        self.areas = f0.areas
        self.min_rt = min(self.rts)
        self.max_rt = max(self.rts)
        self.min_mz = min(self.mzs)
        self.max_mz = max(self.mzs)
        self.len_ = len(self.rts)
        self.element_names = set(f0.element_names)
        self.adducts = set(f0.adducts)

        self.merged_rts = self.rts
        self.merged_mzs = self.mzs
        self.merged_ids = self.ids
        self.merged_areas = self.areas
        self.merged_z = None
        self.merged_element_names = set(self.element_names)

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
        self.merged_areas = np.hstack((self.merged_areas, other.areas))
        self.merged_ids.extend(other.ids)
        self.merged_element_names.update(set(other.element_names))
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
                cluster.merge_feature(f1, self.merged_z)
                print "merge",
            print f0.ids, f1.ids, "mzs=", f0.mzs, f1.mzs, "gap=", n_gap, "z=", self.merged_z
        clusters.append(cluster)
        return clusters


class IsotopeMerger(object):

    isotope_cluster_id_column_name = "isotope_cluster_id"
    isotope_rank_column_name = "isotope_rank"
    isotope_cluster_size_column_name = "isotope_cluster_size"
    isotope_gap_column_name = "isotope_gap"

    def __init__(self, mz_accuracy=1e-4, rt_accuracy=10.0, max_mz_range=20, max_iso_gap=1,
                 mz_integration_window=4e-3, fid_column="feature_id"):
        self.mz_accuracy = mz_accuracy
        self.rt_accuracy = rt_accuracy
        self.max_mz_range = max_mz_range
        self.max_iso_gap = max_iso_gap
        self.mz_integration_window = mz_integration_window
        self.fid_column = fid_column

    def process(self, table):

        required = set(("id", "mz", "mzmin", "mzmax", "rt", "rtmin", "rtmax", "method", "z",
                        self.fid_column))

        col_names = set(table.getColNames())
        missing = required - col_names
        if missing:
            raise Exception("columns named %r missing among names %r" %
                            (sorted(missing), sorted(col_names)))

        n_features = len(set(table.getColumn(self.fid_column).values))
        n_z0_in = len(set(table.filter(table.z == 0).feature_id.values))

        print "process table of length", len(table), "with", n_features, "features"

        features = self._extract_features(table)
        features = self._breakup_features(features)
        candidates = self._detect_candidates(features)
        clusters = self._merge_candidates(candidates)

        if 0:
            rows = []
            for c in clusters:
                mzs = sorted(c.mzs)
                for (i, mz0) in enumerate(mzs):
                    for mz1 in mzs[i + 1:]:
                        if abs(mz1 - mz0 - delta_Cl) < 5e-4:
                            rows.append((c.min_rt, c.max_rt, c.min_mz - 0.005, c.max_mz + 0.005))
                            print c.ids, c.mzs, mz1, mz0, mz1 - mz0
            tt = emzed.utils.toTable("rtmin", [r[0] for r in rows])
            tt.addColumn("rtmax", [r[1] for r in rows])
            tt.addColumn("mzmin", [r[2] for r in rows])
            tt.addColumn("mzmax", [r[3] for r in rows])

            pm = table.peakmap.uniqueValue()

            emzed.gui.inspect(pm, table=tt)

        table = self._add_new_columns(table, features)
        n_z0_out = len(set(table.filter(table.z == 0).feature_id.values))
        table = self._add_missing_mass_traces(table)
        table.sortBy(self.isotope_cluster_id_column_name)

        n_candidates = len(candidates)
        n_clusters = len(clusters)
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
            areas = t.area.values
            feat = Feature(rts, mzs, ids, z, areas)
            features.append(feat)
        return features

    @profile
    def _breakup_features(self, features, shifts=(delta_C, delta_Cl)):
        """
        We assume only mass-shifts of C12->C13 and Cl35->Cl37 in our sample.
        The latter comes from negative Cl adducts. Other adducts have neglectable
        isotopes in repect of our overall analysis goal.
        """
        result = []
        for i, feature in enumerate(features):
            if i % 100 == 0:
                print i / 100,
                sys.stdout.flush()
            result.extend(feature.breakup())
        return result

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

        self._add_cluster_id_column_and_element_names(table, features)
        table = self._add_isotope_ranks_column(table)
        table.sortBy([self.isotope_cluster_id_column_name, self.isotope_rank_column_name])
        return table

    @profile
    def _add_cluster_id_column_and_element_names(self, table, features):
        feature_id = dict()
        feature_element_names = dict()
        for fid, feature in enumerate(features):
            for id_ in feature.ids:
                feature_id[id_] = fid
                feature_element_names[id_] = ", ".join(feature.element_names)

        c = Counter(feature_id.values())
        print
        print "top 10 of large clusters:"
        for fid, count in c.most_common(10):
            print "  cluster_id=%4d" % fid, "traces = %d " % count
        print

        table.addColumn(self.isotope_cluster_id_column_name,
                        table.id.apply(lambda i: feature_id.get(i)),
                        insertBefore=self.fid_column)
        table.addColumn("element_names",
                        table.id.apply(lambda i: feature_element_names.get(i)),
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
        # emzed.io.storeTable(table, "_cached.table", True)
        new_id = table.id.max() + 1
        igc = table.getColumn(self.isotope_gap_column_name)
        do_not_handle = table.filter(igc.isNone() | (igc == 0) | (igc > self.max_iso_gap))
        do_handle = table.filter(igc.isNotNone() & (igc > 0) & (igc <= self.max_iso_gap))
        filled_up_subtables = []
        for group in do_handle.splitBy(self.isotope_cluster_id_column_name):
            iso_cluster_id = group.getColumn(self.isotope_cluster_id_column_name).uniqueValue()
            rt_min = group.rtmin.min()
            rt_max = group.rtmax.max()
            rt_mean = group.rt.mean()
            mzs = sorted(group.mz.values)
            mz_min = min(mzs)
            mz_max = max(mzs)
            z = group.z.uniqueValue()
            n = int(np.round((mz_max - mz_min) * z / delta_C))
            proto = group.rows[0][:]
            for i in range(1, n):
                mz0 = mz_min + i * delta_C / z
                if any(abs(mz0 - mz) < 1e-2 for mz in mzs):
                    continue
                print "add integration window for iso cluster %d and mz= %.5f" % (iso_cluster_id,
                                                                                  mz0)
                proto[group.getIndex("mz")] = mz0
                proto[group.getIndex("mzmin")] = mz0 - self.mz_integration_window / 2.0
                proto[group.getIndex("mzmax")] = mz0 + self.mz_integration_window / 2.0
                proto[group.getIndex("rt")] = rt_mean
                proto[group.getIndex("rtmin")] = rt_min
                proto[group.getIndex("rtmax")] = rt_max
                proto[group.getIndex(self.fid_column)] = None
                proto[group.getIndex("id")] = new_id
                new_id += 1
                group.rows.append(proto)
                group.replaceColumn(self.isotope_gap_column_name, 0)

            group.resetInternals()
            integrator_id = group.method.values[0]
            integrated = emzed.utils.integrate(group, integrator_id, showProgress=False)

            imax = np.argsort(integrated.area.values)[-1]
            mz_main_peak = integrated.mz.values[imax]

            def rank_peak(mz):
                return int(round((mz - mz_main_peak) / delta_C * z))

            integrated.replaceColumn(self.isotope_rank_column_name, integrated.mz.apply(rank_peak))

            filled_up_subtables.append(integrated)
        return emzed.utils.mergeTables([do_not_handle] + filled_up_subtables)


if __name__ == "__main__":
    table = emzed.io.loadTable("s9_mtr_5ppm_integrated.table")
    table.setColFormat("peakmap", "%s")

    import time
    start = time.time()

    table = IsotopeMerger().process(table)

    needed = time.time() - start
    print
    print "needed overall %.0f seconds" % needed
    print

    emzed.io.storeTable(table, "S9_isotope_clustered.table", True)
    emzed.gui.inspect(table)
