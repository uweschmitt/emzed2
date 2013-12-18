import pdb
import emzed
import numpy as np
import sys
import textwrap

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
        assert z in [None, 1, 2, 3, 4]
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

    def breakup(self, mz_tolerance):
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

        debug = True
        debug = False
        #if any(i in self.ids for i in (1813, 1843)):
            #debug = True

        # build adjancy matrices for each isotope-shift which could explain a
        # pair of peaks
        if debug:
            print self.mzs
            print
        distances = (self.mzs[:, None] - self.mzs[None, :])
        connections = []
        for mass_shift, element_name in mass_shifts:
            ni = np.round(z * distances / mass_shift)
            connection = np.abs(ni * mass_shift - z * distances) <  mz_tolerance
            connections.append((connection, element_name))
            if debug:
                print element_name
                print np.abs(ni * mass_shift - z * distances)
                print connection
                print

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
            print "keep", self.ids
            self.element_names = element_names
            yield self
            return

        print "breakup",
        for component, element_names in zip(components, component_elements):
            f0 = Feature([self.rts[i] for i in component],
                         [self.mzs[i] for i in component],
                         [self.ids[i] for i in component],
                         self.z,
                         [self.areas[i] for i in component],
                         element_names
                         )
            print  "   ", f0.ids,
            if len(f0) == 1:
                f0.z = None
            yield f0
        print


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
        self.merged_z = f0.z
        self.merged_element_names = set(self.element_names)

    def __len__(self):
        return len(self.merged_mzs)

    def match_for_same_adduct(self, other, max_mz_range, mz_accuracy, rt_accuracy):
        assert isinstance(self, FeatureCluster)
        assert isinstance(other, Feature)
        if self.z is not None and other.z is not None and self.z != other.z:
            return None
        if self.z is not None and self.z < 0 or other.z is not None and other.z < 0:
            return None
        if max(self.max_rt - other.min_rt, other.max_rt - self.min_rt) >= rt_accuracy:
            return None
        if self.z is None:
            z = other.z
        else:
            z = self.z
        if z is None:
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

        if self.merged_z is None:
            if len(self) > 1:
                print "keep separated",
                for f0 in self.features:
                    print f0.ids,
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
    element_names_column_name = "element_names"

    def __init__(self, mz_accuracy=7e-4, rt_accuracy=10.0, max_mz_range=20, max_iso_gap=1,
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

        table.info()

        features = self._extract_features(table)
        features = self._breakup_features(features)
        candidates = self._detect_candidates(features)
        clusters = self._merge_candidates(candidates)

        table = self._add_new_columns(table, clusters)
        n_z0_out = len(set(table.filter(table.z==0).feature_id.values))
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
            try:
                z = t.z.uniqueValue() or None  # z=0 -> z=None
            except:
                print ids, t.z.values
                z = t.z.max() or None
            areas = t.area.values
            feat = Feature(rts, mzs, ids, z, areas)
            features.append(feat)
        return features

    @profile
    def _breakup_features(self, features):
        """
        We assume only mass-shifts of C12->C13 and Cl35->Cl37 in our sample.
        The latter comes from negative Cl adducts. Other adducts have neglectable
        isotopes in repect of our overall analysis goal.
        """
        result = []
        for i, feature in enumerate(features):
            result.extend(feature.breakup(self.mz_accuracy))
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

        print
        print "top 10 largest merge candidates:"
        candidates.sort(key=lambda c: -len(c))
        for ci in candidates[:10]:
            print "  %2d" % len(ci), ci.ids
        print
        print len(candidates), "isotope cluster candidates"
        return candidates

    def _merge_candidates(self, candidates):
        clusters = [c for cluster in candidates
                    for c in cluster.split_invalid_merges(self.max_iso_gap)]
        print len(clusters), "isotope clusters"
        return clusters

    @profile
    def _add_new_columns(self, table, clusters):

        self._add_cluster_id_column_and_element_names(table, clusters)
        table = self._add_isotope_ranks_column(table)
        table.sortBy([self.isotope_cluster_id_column_name, self.isotope_rank_column_name])
        return table

    @profile
    def _add_cluster_id_column_and_element_names(self, table, clusters):
        cluster_id = dict()
        cluster_z = dict(zip(table.id.values, table.z.values))
        cluster_element_names = dict()
        merged = []
        for fid, cluster in enumerate(clusters):
            if len(cluster.features)> 1:
                merged.append(fid)
            for id_ in cluster.ids:
                cluster_id[id_] = fid
                cluster_element_names[id_] = ", ".join(cluster.element_names)
                cluster_z[id_] = cluster.merged_z

        print
        print "merged clusters:"
        full_txt = ", ".join(map(str, sorted(merged)))
        print "\n".join(textwrap.wrap(full_txt, width=100))
        print

        c = Counter(cluster_id.values())
        print "top 10 of large clusters:"
        for fid, count in c.most_common(10):
            print "  cluster_id=%4d" % fid, "traces = %d " % count
        print

        table.updateColumn(self.isotope_cluster_id_column_name,
                           table.id.apply(lambda i: cluster_id.get(i)),
                           insertBefore=self.fid_column)
        table.updateColumn(self.element_names_column_name,
                           table.id.apply(lambda i: cluster_element_names.get(i)),
                           insertBefore=self.fid_column)
        table.replaceColumn("z", table.id.apply(lambda i: cluster_z.get(i) or 0))

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
                t.updateColumn(
                    self.isotope_cluster_size_column_name, 1, insertBefore=self.fid_column)
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

                t.updateColumn(self.isotope_rank_column_name,
                               t.mz.apply(rank_peak),
                               insertBefore=self.fid_column)

                ranks = sorted(t.getColumn(self.isotope_rank_column_name).values)
                if len(ranks) > 1:
                    max_gap = int(max(r1 - r0 for (r0, r1) in zip(ranks, ranks[1:]))) - 1

            t.updateColumn(self.isotope_cluster_size_column_name, len(t), type_=int, format_="%d",
                           insertBefore=self.fid_column)
            t.updateColumn(self.isotope_gap_column_name, max_gap, type_=int, format_="%d",
                           insertBefore=self.fid_column)
            collected.append(t)
        return emzed.utils.mergeTables(collected)

    @profile
    def _add_missing_mass_traces(self, table):
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
            pm = group.peakmap.uniqueValue()
            elements = group.getColumn(self.element_names_column_name).uniqueValue()
            elements = [e.strip() for e in elements.split(",")]

            def try_matches(mzs, mz_approx_gap, delta_m, z, rt_min, rt_max):
                """
                looks for best matching mzs for filling a given gap at mz_approx_gap.
                iterates over all possibilities and computes summed chromatogram for
                each trial.
                in the end those trials are recorded by the calle who decides which
                mz_i0 to choose.
                """
                matches = []
                for mz_i in mzs:
                    i0 = round((mz_approx_gap - mz_i) * z / delta_m)
                    mz_i0 = mz_i + i0 / z * delta_m
                    if abs(mz_i0 - mz_approx_gap) < 1e-1:
                        __, chromo = pm.chromatogram(mz_i0 - 1e-3, mz_i + 1e-3, rt_min, rt_max, 1)
                        area = sum(chromo)   # simple way of integration
                        matches.append((area, mz_i0))
                return matches

            for mz0, mz1 in zip(mzs[:-1], mzs[1:]):
                n = int(round((mz1 - mz0) * z / delta_C))
                # n is number of missing peaks between mz0 and mz1 plus one:
                # n == 1 means "no peak missing", aka the next loop is empty
                for i in range(1, n):
                    mz_approx_gap = (mz1 - mz0) * i / n + mz0
                    matches = []
                    if "Cl" in elements:
                        matches = try_matches(mzs, mz_approx_gap, delta_Cl, z, rt_min, rt_max)
                        matches += try_matches(mzs, mz_approx_gap, delta_C, z, rt_min, rt_max)
                    else:
                        matches = try_matches(mzs, mz_approx_gap, delta_C, z, rt_min, rt_max)

                    if not matches:
                        continue

                    # look for match with max area
                    matches.sort()
                    __, mzi = matches[-1]

                    print "add integration window for cluster %d and mz= %.5f" % (iso_cluster_id,
                                                                                  mzi)
                    proto[group.getIndex("mz")] = mzi
                    proto[group.getIndex("mzmin")] = mzi - self.mz_integration_window / 2.0
                    proto[group.getIndex("mzmax")] = mzi + self.mz_integration_window / 2.0
                    proto[group.getIndex("rt")] = rt_mean
                    proto[group.getIndex("rtmin")] = rt_min
                    proto[group.getIndex("rtmax")] = rt_max
                    proto[group.getIndex(self.fid_column)] = None
                    proto[group.getIndex("id")] = new_id
                    new_id += 1
                    group.rows.append(proto[:])
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
        result = emzed.utils.mergeTables([do_not_handle] + filled_up_subtables)
        return result


if __name__ == "__main__":
    import time, glob
    start = time.time()
    #for p in glob.glob("t_b1_for_feature_grouper.table"): # "b2_neu.table"):
    #for p in glob.glob("S9_shoulder_removed_and_integrated.table"):
    if 1:
        p = "sample_b3_integrated.table"
        print p
        table = emzed.io.loadTable(p)
        #table = table.filter(table.feature_id == 2734)
        #emzed.gui.inspect(table)
        #table.dropColumns("adduct_group", "possible_adducts")
        #AdductAssigner("negative_mode").process(table)
        table = IsotopeMerger().process(table)
        #emzed.io.storeTable(table, "b2_neu_fclustered.table", True)
        emzed.gui.inspect(table)
    # table = emzed.io.loadTable("s9_mtr_5ppm_integrated.table")

    needed = time.time() - start
    print
    print "needed overall %.0f seconds" % needed
    print

