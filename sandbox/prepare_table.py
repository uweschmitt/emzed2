
import emzed

t = emzed.io.loadTable("shoulders_table_with_feature_ids.table")

pm = t.peakmap.uniqueValue()

emzed.gui.inspectPeakMap(pm)

exit()

subtables = t.splitBy("group_id_0")
tables = [s for s in subtables if s.group_id_0.uniqueValue() is None]
sub_tables = [s for s in subtables if s.group_id_0.uniqueValue() is not None]

flattened_tables = []
for t in sub_tables:
    ti = t.splitBy("id")
    t0 = ti[0]
    for t1 in ti[1:]:
        t0 = t0.join(t1)
    flattened_tables.append(t0)

final_table = emzed.utils.mergeTables(flattened_tables)
emzed.io.storeTable(final_table, "shoulders_table_grouped.table")
emzed.gui.inspect(final_table)
