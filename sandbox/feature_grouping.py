import emzed
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
        self.rts = rts
        self.mzs = mzs
        self.ids = ids
        self.z = z
        self.min_rt = min(rts)
        self.max_rt = max(rts)

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
