# encoding: utf-8
from __future__ import print_function, division, absolute_import

import pickle
import itertools
import os
import operator
import sqlite3
import time

import emzed


from contextlib import contextmanager


@contextmanager
def timeit(msg):
    started = time.time()
    yield
    needed = time.time() - started
    print("%s needed %e seconds" % (msg, needed))


def setup_fresh_db(db_name="peaks.db"):
    if os.path.exists(db_name):
        os.remove(db_name)

    conn = sqlite3.connect(db_name)
    return conn


def pickle_object(obj, conn):
    cursor = conn.cursor()
    name = str(type(obj))
    cursor.execute("""INSERT INTO blobs VALUES(NULL, ?, ?); """,
                   (name, buffer(pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)),))
    return cursor.lastrowid


def unpickle_object(id_, conn):
    stmt = "SELECT name, blob FROM blobs WHERE id = ?"
    name, blob = conn.cursor().execute(stmt, (id_,)).fetchone()
    return name, pickle.loads(blob)


def to_db(t, name):
    conn = setup_fresh_db(name)
    try:
        _to_db(t, conn)
    except Exception:
        conn.close()
        raise
    finally:
        conn.close()


def get_name(cell):
    return str(type(cell))


def _to_db(t, conn):

    type_map = {int: "INTEGER", float: "REAL", str: "TEXT", unicode: "TEXT",
                bool: "INTEGER"}

    declarations = []
    object_columns = []
    for name, type_ in zip(t._colNames, t._colTypes):
        sql_type = type_map.get(type_)
        if sql_type is None:
            declarations.append(("__str_%s" % name, "TEXT"))
            declarations.append(("__id_%s" % name, "INTEGER"))
            object_columns.append(name)
        else:
            declarations.append((name, sql_type))

    col_definitions = ",\n".join("%s %s" % name_type_pair for name_type_pair in declarations)

    stmt = """CREATE TABLE rows (
                 %s
              );
    """ % col_definitions

    conn.cursor().execute(stmt)
    conn.commit()

    stmt = """CREATE TABLE blobs (
                 id INTEGER PRIMARY KEY,
                 name TEXT,
                 blob BLOB
              );"""

    print(stmt)
    conn.cursor().execute(stmt)
    conn.commit()

    meta = (t._colNames, t._colTypes, t._colFormats, t.meta, object_columns)
    id_ = pickle_object(meta, conn)
    assert id_ == 1

    object_cache = {}
    n_cols = len(t._colNames)

    cursor = conn.cursor()

    for row in t.rows:

        stmt = """INSERT INTO rows VALUES(%s)""" % ", ".join(["?"] * (n_cols + len(object_columns)))

        values = [None]
        values = []
        for cell, type_ in zip(row, t._colTypes):
            if type_ in type_map:
                if cell is None:
                    value = None
                else:
                    value = type_(cell)
            else:
                if cell is None:
                    item = None, None
                else:
                    item = object_cache.get(id(cell))
                    if item is None:
                        value = pickle_object(cell, conn)
                        item = (get_name(cell), value)
                        object_cache[id(cell)] = item
                name, value = item
                values.append(name)
            values.append(value)

        cursor.execute(stmt, values)

    cursor.close()
    conn.commit()

    for name, __ in declarations:
        stmt = """CREATE INDEX %s_index ON rows (%s); """ % (name, name)
        conn.cursor().execute(stmt)
        conn.commit()


def print_meta(db_name):
    conn = sqlite3.connect(db_name)
    name, (col_names, col_types, col_formats, meta, object_columns) = unpickle_object(1, conn)
    for name, t, f in zip(col_names, col_types, col_formats):
        print(name, t, f)
    print(meta)


def from_db(db_name, n_rows=None):

    conn = sqlite3.connect(db_name)
    name, (col_names, col_types, col_formats, meta, object_columns) = unpickle_object(1, conn)

    # fetch all rows
    stmt = """SELECT * from rows;"""
    if n_rows is None:
        rows = map(list, conn.cursor().execute(stmt).fetchall())
    else:
        rows = map(list, conn.cursor().execute(stmt).fetchmany(n_rows))

    # resolve pickled objects
    cache = {}

    def lookup(id_):
        if id_ is None:
            return None
        if id_ not in cache:
            cache[id_] = unpickle_object(id_, conn)
        return cache[id_]

    meta_rows = conn.cursor().execute("""PRAGMA table_info(rows);""").fetchall()

    db_col_names = [str(meta_row[1]) for meta_row in meta_rows][0:]

    for i, name in enumerate(db_col_names):
        if name.startswith("__id_"):
            col_names[i] = name[5:]
            for row in rows:
                row[i], obj = lookup(row[i])

    import emzed
    return emzed.core.Table(col_names, col_types, col_formats, rows, meta=meta)


def _sort_permutation(db_name, col_names):

    stmt = """SELECT ROWID FROM rows ORDER BY %s""" % (", ".join(col_names))
    conn = sqlite3.connect(db_name)
    with timeit("compute permutation to order by %s with SQL   " % (", ".join(col_names))):
        permutation = [r[0] for r in conn.cursor().execute(stmt).fetchall()]
        print(len(permutation))

    stmt = """SELECT %s FROM rows""" % (", ".join(col_names))
    conn = sqlite3.connect(db_name)
    with timeit("compute permutation to order by %s with Python" % (", ".join(col_names))):
        decorated = [r + (i,) for i, r in enumerate(conn.cursor().execute(stmt).fetchall())]
        decorated.sort()
        permutation = [d[-1] for d in decorated]
        print(len(permutation))


def filter(db_name, filters, col_names):

    stmt = """SELECT ROWID FROM rows ORDER BY %s""" % (", ".join(col_names))
    conn = sqlite3.connect(db_name)

    with timeit("compute permutation to order by %s with SQL   " % (", ".join(col_names))):
        permutation = [r[0] for r in conn.cursor().execute(stmt).fetchall()]
        print(len(permutation))

    stmt = """SELECT %s FROM rows""" % (", ".join(col_names))
    conn = sqlite3.connect(db_name)
    with timeit("compute permutation to order by %s with Python" % (", ".join(col_names))):
        decorated = [r + (i,) for i, r in enumerate(conn.cursor().execute(stmt).fetchall())]
        decorated.sort()
        permutation = [d[-1] for d in decorated]
        print(len(permutation))


def fetch_column(db_name, col_name, blocksize=None):
    conn = sqlite3.connect(db_name)
    conn.commit()
    stmt = """SELECT %s FROM rows order by ROWID""" % col_name
    conn = sqlite3.connect(db_name)
    if blocksize is None:
        for (r,) in conn.cursor().execute(stmt).fetchall():
            yield r
    else:
        for block in conn.cursor().execute(stmt).fetchmany(blocksize):
            for r in block:
                yield r


def add_column(db_name, col_name, type_, values):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    started = time.time()

    c.execute('''ATTACH DATABASE ':memory:' AS aux1;''')

    # c.execute('''DROP TABLE IF EXISTS TEMP''')
    c.execute('''CREATE TABLE aux1.TEMP (v %s)''' % type_)
    conn.commit()
    print (time.time() - started)

    c.execute("PRAGMA synchronous=OFF")
    c.executemany('''INSERT INTO aux1.TEMP VALUES(?)''', ((v,) for v in values))

    conn.commit()
    print (time.time() - started)
    c.execute('''ALTER TABLE rows ADD COLUMN %s %s;''' % (col_name, type_))
    conn.commit()
    print (time.time() - started)
    c.execute("PRAGMA synchronous=NORMAL")
    c.execute('''UPDATE rows SET %s = (SELECT v FROM aux1.TEMP)''' % col_name)
    conn.commit()
    print (time.time() - started)
    c.execute('''CREATE INDEX %s_index on rows(%s)''' % (col_name, col_name))
    conn.commit()
    print (time.time() - started)
    return (time.time() - started)


def sort_permutation(db_name, filter_, fields, reverse_indicators):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('''ATTACH DATABASE ':memory:' AS mem''')
    c.execute('''CREATE TABLE mem.TEMP (
                                        permutation INTEGER
                                        )''')

    started = time.time()
    q = c.execute("SELECT %s, ROWID FROM rows WHERE %s" % (", ".join(fields), filter_))
    for i in range(1000):
        q.next()
        if i % 100 == 0:
            print(i, time.time() - started)
    print(i, time.time() - started)
    return

    rows = q.fetchall()
    print ("got values to sort by", time.time() - started)
    for i, r in list(enumerate(reverse_indicators))[::-1]:
        rows.sort(key=operator.itemgetter(i), reverse=r)
    perm = list((row[-1],) for row in rows)
    print ("got perm", len(perm), time.time() - started)

    c.executemany('''INSERT INTO mem.TEMP VALUES(?)''', perm)
    conn.commit()
    c.execute('''CREATE INDEX mem.abc on TEMP (permutation);''')
    conn.commit()
    print ("created temp table", time.time() - started)

    result = c.execute('''SELECT rows.* FROM rows
                          JOIN (SELECT ROWID, permutation FROM mem.TEMP) as T
                          ON T.permutation = rows.ROWID
                          ORDER BY T.ROWID''')
    print ("submitted select", time.time() - started)
    result.fetchmany(5)
    rib = [(ri[0],) for ri in result]
    print ("got sorted rows", time.time() - started)
    assert rib == perm

    return

if True:
    t = emzed.io.loadTable("peak_table.table")

    def generate(i):
        if i % 3 == 0:
            return None
        elif i % 3 == 1:
            return ""
        return "x"
    t.addColumn("empty", t.peak_id.apply(generate), type_=str)
    t.addColumn("sample_id", 0, type_=int)

    o0 = [range(i, j) for i in range(0, 10) for j in range(10, 20)]
    o1 = [set(range(i, j)) for i in range(0, 10) for j in range(10, 20)]
    o2 = [dict(zip(range(i, j), range(i, j))) for i in range(0, 10) for j in range(10, 20)]
    o3 = [o0, o1, o2]
    o4 = [[o3, [o3]], o3]
    o5 = [o0, o1, o2, o3, o4]

    objects = [o0, o1, o2, o3, o4, o5]

    def by_6(x):
        return x % 6

    t.addColumn("objects", t.peak_id.apply(by_6).apply(objects.__getitem__), type_=object)

    tables = []
    for i in range(500):
        if i % 10 == 0:
            print(i)
        t.replaceColumn("sample_id", i, type_=int)
        tables.append(t[:])
        break
    t = emzed.utils.stackTables(tables)
    to_db(t, "peaks.db")
    t.info()


elif 0:

    values = fetch_column("peaks.db", "peak_id")
    new_values = (v + 2.0 for v in values)
    add_column("peaks.db", "peak_id_plus_twoxxxf", "FLOAT", new_values)
elif 0:
    key = None
    pi = sort_permutation("peaks.db", "mz <= 101.1", ["peak_id", "sample_id"], [False, True])
    pi = sort_permutation("peaks.db", "mz <= 151.1", ["peak_id", "sample_id"], [False, True])
else:
    # benchmark deserialization
    tsub = from_db("peaks.db", 20)
    conn = sqlite3.connect("peaks.db")
    s = time.time()
    v = fetch_column("peaks.db", "__id_objects", blocksize=500)
    tunp = 0.0
    s = time.time()
    n = 10
    for vi in itertools.islice(v, n):
        st = time.time()
        name, o = unpickle_object(vi, conn)
        # eval(str(o))
        tunp += time.time() - st
    print("overall fetch", n, "objects:", time.time() - s)
    print("unpickle time is", tunp)


if 0:
    tn = from_db("peaks.db")
    tn.info()

    assert t._colNames == tn._colNames
    assert t._colTypes == tn._colTypes
    assert t._colFormats == tn._colFormats
    assert t.meta == tn.meta
    assert t.uniqueId() == tn.uniqueId()
