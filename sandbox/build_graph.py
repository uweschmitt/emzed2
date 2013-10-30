import emzed
import collections

from graph_algo import collect_children, find_roots

table = emzed.io.loadTable("shoulders_table_integrated.table")
table.sortBy("mz", ascending=True)
table.dropColumns("id")
table.addEnumeration()

table.info()

#table = emzed.utils.integrate(table, "trapez")
#emzed.io.storeTable(table, "shoulders_table_integrated.table")
#exit()

predecessors = collections.defaultdict(lambda: collections.defaultdict(list))

zmax = 3
max_gap = 2

delta_mz = emzed.mass.C13 - emzed.mass.C12

mz_accuracy = 5e-4

min_overlap = 0.0
max_rt_diff = 10.0


z_values = table.z.values
mz_values = table.mz.values
rt_values = table.rt.values
rtmin_values = table.rtmin.values
rtmax_values = table.rtmax.values
intensity_values = table.area.values
feature_ids = table.feature_id.values
ids = table.id.values

cc = collections.Counter(feature_ids)
for id_, count in cc.most_common(10):
        print id_, count
print

fp = open("nodes.txt", "w")

for i in range(len(table)):
    z = z_values[i]
    mz = mz_values[i]
    rt = rt_values[i]
    rtmin = rtmin_values[i]
    rtmax = rtmax_values[i]
    intensity = intensity_values[i]

    if z == 0:
        z_range = range(1, zmax + 1)
    else:
        z_range = [z]

    print >> fp, "i=%5d" % i, "id=%5d" % ids[i],
    print >> fp, "fid=%5d" % feature_ids[i],
    print >> fp, "mz=%10.5f" % mz, "rtmin=%4.2f" % (rtmin / 60.0), "rtmax=%4.2f" % (rtmax / 60.0),
    print >> fp, "z=", z, "intensity = %.2e" % intensity
    for zi in z_range:
        maxmz = mz + (max_gap * delta_mz) / zi

        for j in range(i + 1, len(table)):
            mz2 = mz_values[j]

            if mz2 >= maxmz + 0.1:
                break

            z2 = z_values[j]
            if z2 > 0 and z2 != zi:
                continue

            rtmin2 = rtmin_values[j]
            rtmax2 = rtmax_values[j]
            rt2 = rt_values[j]
            intensity2 = intensity_values[j]

            #if intensity >= intensity2:
                #if not (rtmin - 1.0 <= rtmin2 and rtmax2 <= rtmax + 1.0):
                    #continue
#
            #if intensity <= intensity2:
                #if not (rtmin2 - 1.0 <= rtmin and rtmax <= rtmax2 + 1.0):
                    #continue

            overlap = min(rtmax, rtmax2) - max(rtmin, rtmin2)
            fullrange = max(rtmax, rtmax2) - min(rtmin, rtmin2)

            if overlap / fullrange < min_overlap:
                continue

            if abs(rt - rt2) > max_rt_diff:
                continue

            n = round((mz2 - mz) * zi / delta_mz)
            mz2_tmp = n * delta_mz / zi + mz
            if n > 0 and abs(mz2 - mz2_tmp) < mz_accuracy:
                gap = n - 1
                predecessors[zi][j].append(i)
                print >> fp, "   zi=%d" % zi, "n=%d" % n, "mz=%10.5f" % mz2, "rtmin=%4.2f" % (rtmin2 / 60.0),
                print >> fp, "rtmax=%4.2f" % (rtmax2 / 60.0),
                print >> fp, "intensity = %.2e" % intensity2


components = collections.defaultdict(list)

i=0
for zi in range(1, zmax + 1):
    print >> fp, "z=", zi
    for k, v in predecessors[zi].items():
        print >> fp, k, v
    print >> fp

    graph = predecessors[zi]
    roots = find_roots(graph)
    for r in roots:
        children = collect_children(r, graph)
        print >> fp, r, "->", children
        for c in children:
            components[c].append((zi, r, i))
        i+= 1


for row in table.rows:
    id_ = table.getValue(row, "id")
    features = components.get(id_, [])
    new_columns = []
    for (zi, root, feat_id) in features:
        new_columns.append("%d_%d" % (feat_id, zi))
    # fill up
    new_columns = (new_columns + 3*[None])[:3]
    row.extend(new_columns)

names_before = table.getColNames()[1:]  # withot id
table._colNames.extend(["group_id_0", "group_id_1", "group_id_2"])
table._colFormats.extend(["%s", "%s", "%s"])
table._colTypes.extend([str, str, str])
table.resetInternals()
table.info()

table = table.extractColumns(*(["id", "group_id_0", "group_id_1", "group_id_2"] + names_before))

table.info()

emzed.io.storeTable(table, "shoulders_table_with_feature_ids.table", forceOverwrite=True)



#for c, v in components.items():
    #if len(v) > 2:
        #for (zi, r, i) in v:
            #print mz_values[c]
            #print zi,
            #children = collect_children(r, graph)
            #for ci in children:
                #print mz_values[ci],
            #print
        #print
#







