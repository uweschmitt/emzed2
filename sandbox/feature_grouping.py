import emzed

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
    if (i % 100) == 0:
        print i
    for f1 in features[i + 1:]:
        if f1.min_rt >= f0.max_rt + 3 * rt_accuracy:
            break
            pass
        # if max(f0.max_rt - f1.min_rt, f1.max_rt - f0.min_rt) >= 3 * rt_accuracy:
            # break
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
fzs.sort(key=lambda f: -len(f[1]))
for i, f in fzs[:5]:
    print i, len(f)

table.addColumn("isotop_cluster_id", table.id.apply(lambda i: feature_id_map.get(i)),
                insertBefore="feature_id")

emzed.io.storeTable(table, "isotope_clustered.table", True)
emzed.gui.inspect(table)
