import itertools
from collections import OrderedDict

from tables import (open_file, UInt64Col, Int64Col, UInt32Col, Float64Col, BoolCol, Filters)

from special_handlers import setup


def to_hdf5(table, path):

    file_ = open_file(path, mode="w")
    filters = Filters(complib="blosc", complevel=9)

    store, fetch, finalize = setup(file_, file_.root)

    meta_table = file_.create_table(file_.root, "meta_index",
                                    description=dict(index=UInt64Col()),
                                    filters=filters)

    missing_values = file_.create_table(file_.root, "missing_values",
                                        description=dict(row_index=UInt64Col(pos=0),
                                                         col_index=UInt64Col(pos=1)),
                                        filters=filters)

    def store_meta(what):
        meta_index = store(what)
        row = meta_table.row
        row["index"] = meta_index
        row.append()

    col_names = table.getColNames()
    col_types = table.getColTypes()
    col_formats = table.getColFormats()

    store_meta(table.meta)
    store_meta(col_names)
    store_meta(col_types)
    store_meta(col_formats)

    basic_type_map = {int: Int64Col, long: Int64Col, float: Float64Col, bool: BoolCol}

    description = OrderedDict()
    for (name, type_) in zip(col_names, col_types):
        tables_type = basic_type_map.get(type_)
        if tables_type is None:
            tables_type = UInt32Col
        description[name] = tables_type()

    row_table = file_.create_table(file_.root, "rows", description=description,
                                   filters=filters)

    for row_index, row in enumerate(table.rows):
        hdf_row = row_table.row
        for col_index, value, name, type_ in zip(itertools.count(), row, col_names, col_types):
            if value is None:
                m_row = missing_values.row
                m_row["row_index"] = row_index
                m_row["col_index"] = col_index
                m_row.append()
            else:
                if type_ in basic_type_map:
                    hdf_row[name] = value
                else:
                    hdf_row[name] = store(value)
        hdf_row.append()

    finalize()
    meta_table.flush()
    missing_values.flush()
    row_table.flush()

    for x in row_table:
        print(x.fetch_all_fields())


def main():
    import emzed

    t = emzed.utils.toTable("a", (1, 2, None, 4), type_=int)
    t.addColumn("b", t.a + 1.1, type_=float)
    t.addColumn("c", t.a.apply(str) * 3, type_=str)
    t.addColumn("d", t.a * (1, 2), type_=object)

    print(t)
    to_hdf5(t, "test.hdf5")

if __name__ == "__main__":
    main()
