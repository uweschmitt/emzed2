import emzed
import sys
import numpy as np

from collections import Counter

from util import ProgressCounter

from collections import defaultdict
import numpy as np

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
feature_tables.sort(key=lambda t: (max(t.rt.values), -len(t),))
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
        return self.len_

    @profile
    def match_for_same_adduct(self, other, mz_accuracy, rt_accuracy, max_mz_range):
        if self.z < 0 or other.z < 0 or self.z > 0 and other.z > 0 and self.z != other.z:
            return None

    def __len__(self):
        return len(self.mzs)

    def match_for_same_adduct(self, other):
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
        self.min_mz = np.min(self.mzs)
        self.max_mz = np.max(self.mzs)
        self.len_ = len(self.rts)
        other.ids = other.rts = other.mzs = []
        other.z = -1
        other.min_rt = other.max_rt = -1000.0
        other.len_ = 0


class IsotopeMerger(object):

    def __init__(self, mz_accuracy=1e-4, rt_accuracy=10.0, max_mz_range=20):
        self.mz_accuracy = mz_accuracy
        self.rt_accuracy = rt_accuracy
        self.max_mz_range = max_mz_range

    def process(self, table, fid_column="feature_id"):

        nfeat = len(set(table.getColumn(fid_column).values))
        print "process table of length", len(table), "with", nfeat, "features"

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
                                      "isotope_cluster_size", "max_isotope_gap", fid_column)
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
                if f0.max_mz - f1.min_mz <= self.max_mz_range + 1:
                    if f1.max_mz - f0.min_mz <= self.max_mz_range + 1:
                        if f0.max_rt - f1.min_rt < self.rt_accuracy:
                            if f1.max_rt - f0.min_rt < self.rt_accuracy:
                                z = f0.match_for_same_adduct(f1, self.mz_accuracy,
                                        self.rt_accuracy, self.max_mz_range)
                                if z is not None:
                                    f0.merge_feature(f1, z)
                j += 1
        counter.done()
        features = [f for f in features if len(f)]
        print len(features), "isotope clusters"
        return features

    @profile
    def _add_new_columns(self, table, features, new_column_name, rank_column_name,
                         iso_cluster_size_column, iso_gap_column, fid_column):

        self._add_cluster_id_column(table, features, new_column_name, fid_column)
        table = self._add_isotope_ranks_column(table, rank_column_name, new_column_name,
                                               iso_cluster_size_column, iso_gap_column, fid_column)
        table.sortBy([new_column_name, rank_column_name])
        return table

    @profile
    def _add_cluster_id_column(self, table, features, new_column_name, fid_column):
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

        table.addColumn(new_column_name, table.id.apply(lambda i: feature_id_map.get(i)),
                        insertBefore=fid_column)

    @profile
    def _add_isotope_ranks_column(self, table, rank_column_name, iso_cluster_column,
                                  iso_cluster_size_column, iso_gap_column, fid_column):
        print "calculate isotope ranks"
        collected = []
        for t in table.splitBy(iso_cluster_column):
            if len(t) == 1:
                t.addColumn(iso_cluster_size_column, 1, insertBefore=fid_column)
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
            ranks = sorted(t.getColumn(rank_column_name).values)
            if len(ranks) > 1:
                max_gap = int(max(r1 - r0 for (r0, r1) in zip(ranks, ranks[1:])))
            else:
                max_gap = 0
            t.addColumn(iso_cluster_size_column, len(t), type_=int, format_="%d",
                        insertBefore=fid_column)
            t.addColumn(iso_gap_column, max_gap, type_=int, format_="%d",
                        insertBefore=fid_column)
            collected.append(t)
        return emzed.utils.mergeTables(collected)


table = IsotopeMerger().process(table[:])
emzed.io.storeTable(table, "isotope_clustered.table", True)
#emzed.gui.inspect(table)
        for z in z_to_try:
            all_match = True
            pairs = [(mz_self, mz_other) for mz_self in self.mzs for mz_other in other.mzs]
            for mz_self, mz_other in pairs:
                n = round((mz_self - mz_other) * z / delta_C)
                diff = abs(n * delta_C / z + mz_other - mz_self)
                if diff > mz_accuracy:
                    all_match = False
                    break
            if all_match:
                return z
        return None

    def merge_isotopes(self, other, z):
        self.rts.extend(other.rts)
        self.mzs.extend(other.mzs)
        self.ids.extend(other.ids)
        self.z = z
        self.min_rt = min(self.rts)
        self.max_rt = max(self.rts)
        other.ids = other.rts = other.mzs = []
        other.z = -1
        other.min_rt = other.max_rt = -1000.0



print "start"

features = []
for t in feature_tables:
    rts = t.rt.values
    mzs = t.mz.values
    ids = t.id.values
    z = t.z.uniqueValue()
    feat = Feature(rts, mzs, ids, z)
    features.append(feat)

for i, f0 in enumerate(features):
    if (i%100) == 0:
        print i
    for f1 in features[i+1:]:
        if f1.min_rt >= f0.max_rt + 3 * rt_accuracy:
            break
            pass
        #if max(f0.max_rt - f1.min_rt, f1.max_rt - f0.min_rt) >= 3 * rt_accuracy:
            #break
        z = f0.match_for_same_adduct(f1)
        if z is not None:
            f0.merge_isotopes(f1, z)


features = [f for f in features if len(f)]
print len(features), "features"
feature_id_map = dict()
for fid, feature in enumerate(features):
    for id_ in feature.ids:
        feature_id_map[id_] = fid


fzs = list(enumerate(features))
features.sort(key=lambda f:-len(f[1]))
for i, f in features[:5]:
    print i, len(f)

print "max fid=", lfid, lmax

table.addColumn("isotop_cluster_id", table.id.apply(lambda i: feature_id_map.get(i)),
        insertBefore="feature_id")

emzed.io.storeTable(table, "isotope_clustered.table", True)
emzed.gui.inspect(table)

exit()



min_overlap = 0.0

z_values = table.z.values
mz_values = table.mz.values
rt_values = table.rt.values
rtmin_values = table.rtmin.values
rtmax_values = table.rtmax.values
area_values = table.area.values
feature_ids = table.feature_id.values
ids = table.id.values

feat_id_dict = defaultdict(list)
for (feat_id, id_) in zip(feature_ids, ids):
    feat_id_dict[feat_id].append(id_)

mz_min = min(mz_values)
mz_max = max(mz_values)
mz_range = mz_max - mz_min
rt_min = min(rt_values)
rt_max = max(rt_values)
rt_range = rt_max - rt_min

id_bins = defaultdict(set)
areas = dict()
assignments = defaultdict(list)

m0_bins = []
rt_bins = []


for i in range(len(table)):
    assert i == ids[i]
    z = z_values[i]
    mz = mz_values[i]
    rt = rt_values[i]
    area = area_values[i]
    fid = feature_ids[i]

    rt_bin = int(rt / rt_accuracy)
    for n in range(12):
        for name, shift, z in emzed.adducts.negative.adducts:
            m0 = abs(z) * mz - n * delta_C + shift
            m0_bin = int(m0 / mz_accuracy)
            rt_bins.append(rt)
            m0_bins.append(m0)

            for m0_i in [m0_bin - 1, m0_bin, m0_bin + 1]:
                for rt_j in [rt_bin - 1, rt_bin, rt_bin + 1]:
                    id_bins[m0_i, rt_j].add(i)
                    areas[i] = area
                    assignments[i].append((m0_i, rt_j, fid, m0, n, name, rt))

# pylab.hist2d(rt_bins, m0_bins, 1000)
# pylab.show()

lens = dict((k, len(v)) for (k, v) in id_bins.items())



seen = set()
try:
    profile
except:
    profile = lambda func: func


@profile
def find_next_group():

    # find bin with max number of entries:
    #histo = id_bins.items()
    #top_bin = max(histo, key=lambda (k, v): len(list(vi for vi in v if vi not in seen)))
    #top_bin = max(histo, key=lambda (k, v): len(v))
    #m0_bin, rt0_bin = max(id_bins, key=lambda k: len(id_bins[k]))
    m0_bin, rt0_bin = max(lens, key=lambda k: lens[k])
    peak_ids_in_top_bin = id_bins[m0_bin, rt0_bin]
    #(m0_bin, rt0_bin), peak_ids_in_top_bin = top_bin

    # find peak with max area in this bin:
    id_max_peak = max(peak_ids_in_top_bin, key=lambda id_: areas[id_])

    # find data for this max peak:
    for m0_i, rt_j, fid, m0, n, name, rt in assignments[id_max_peak]:
        if m0_i == m0_bin and rt_j == rt0_bin:
            print "m0=", m0
            break
    else:
        raise Exception("internal error: peak not found")

    # find matching peaks:
    group = [id_max_peak]
    seen.add(id_max_peak)

    for m0_i, rt_j, __, __, __, __, __ in assignments[id_max_peak]:
        id_bins[m0_i, rt_j].remove(id_max_peak)
        lens[m0_i, rt_j] -= 1

    center_m0 = m0
    center_rt = rt
    min_m0 = max_m0 = center_m0
    min_rt = max_rt = center_rt

    area0 = areas[id_max_peak]

    data = []

    while True:
        # find next peak
        neighbours = []
        for peak_id in peak_ids_in_top_bin:
            if peak_id not in seen:
                area1 = areas[peak_id]
                if 0 and area1 < area0 * 0.02:
                    continue
                for m0_i, rt_j, fid, m0, n, name, rt in assignments[peak_id]:
                    if m0_i == m0_bin and rt_j == rt0_bin:
                        nb_dist = max(
                            abs(m0 - center_m0) / center_m0, abs(rt - center_rt) / center_rt)
                        neighbours.append((nb_dist, peak_id, m0, n, name, rt))

        # next peak
        if not neighbours:
            break
        print len(neighbours)
        dist_best_peak, id_best_peak, m0_best_peak, n_best_peak, z_best_peak, rt_best_peak = min(neighbours)

        #print min(neighbours)
        print id_best_peak

        # check if new peak extends precision window:
        #print id_best_peak, area0, areas[id_best_peak] / area0
        new_m0_range = max(max_m0, m0_best_peak) - min(min_m0, m0_best_peak)
        print "new_m0_range = %.3e" % new_m0_range
        if new_m0_range > 2*mz_accuracy:
            break
        new_rt_range = max(max_m0, m0_best_peak) - min(min_m0, m0_best_peak)
        print "new_rt_range = ", new_rt_range
        if new_rt_range > 2*rt_accuracy:
            break

        # calculate new limits of window:
        min_m0 = min(min_m0, m0_best_peak)
        max_m0 = max(max_m0, m0_best_peak)
        min_rt = min(min_rt, rt_best_peak)
        max_rt = max(max_rt, rt_best_peak)
        print min_m0, max_m0, "%.3e" % (max_m0-min_m0), mz_accuracy
        print

        # calcluate new center:
        center_rt = (max_rt + min_rt) / 2.0
        center_m0 = (max_m0 + min_m0) / 2.0
        group.append(id_best_peak)
        data.append((m0_best_peak, n_best_peak, z_best_peak, rt_best_peak))
        seen.add(id_best_peak)
        for m0_i, rt_j, __, __, __, __, __ in assignments[id_best_peak]:
            id_bins[m0_i, rt_j].remove(id_best_peak)
            lens[m0_i, rt_j] -= 1
    return group, data


count = 0
while True:
    group, data = find_next_group()
    ff_ids = set()
    for id_, (m0, n, name, rt) in zip(group, data):
        print "%5d" % id_,
        print "m0=%10.5f" % m0,
        print "rt=%6.1f" % rt,
        print "adduct=%8s" % name,
        print "n= %2d" % n,
        print "    fid=%5d" % feature_ids[id_], "  -> ",
        for idd in feat_id_dict[feature_ids[id_]]:
            print "%5d" % idd,
            ff_ids.add(idd)
        print
    if len(ff_ids) > len(group):
        print "*",
    else:
        print " ",
    print "%5d %5d" % (len(group), len(ff_ids))
    if not set(group) <= set(ff_ids):
        print sorted(ff_ids), sorted(group)
    break
    print
    count += 1


exit()

for (m0, rt0), data in histo[:4]:

    data.extend(bins[m0 - 1, rt0])
    data.extend(bins[m0 + 1, rt0])

    data.extend(bins[m0 - 1, rt0 - 1])
    data.extend(bins[m0, rt0 - 1])
    data.extend(bins[m0 + 1, rt0 - 1])

    data.extend(bins[m0 - 1, rt0 + 1])
    data.extend(bins[m0, rt0 + 1])
    data.extend(bins[m0 + 1, rt0 + 1])

    data.sort()
    print
    for area, id_, fid, m0, n, z, rt in data:
        print "area = %.2e" % area,
        print "id=%5d" % id_,
        print "feature_id=%5d" % fid,
        print "m0=%10.5f" % m0,
        print "n=%d" % n,
        print "z=%d" % z,
        print "rt=%5.2f" % (rt / 60.0)
