# encoding: utf-8
from __future__ import print_function, division, absolute_import

import pickle
import itertools
import math
import os
import operator
import sqlite3
import time

from contextlib import contextmanager
from collections import namedtuple

from .table import Table
from .ms_types import PeakMap, PeakMapProxy


TableInformation = namedtuple("TableInformation", ["col_names", "col_types", "col_formats", "meta",
                                                   "object_columns"])


def _set_sort_permutation(conn, filter_expression, fields, ascending_indicators):

    c = conn.cursor()
    # c.execute('''DROP TABLE IF EXISTS mem.PERMUTATION_TABLE''')
    c.execute('''CREATE TABLE IF NOT EXISTS mem.PERMUTATION_TABLE (
                                        permutation INTEGER
                                        )''')

    q = c.execute("SELECT %s, ROWID FROM rows WHERE %s" % (", ".join(fields), filter_expression))
    rows = q.fetchall()
    for i, asc in list(enumerate(ascending_indicators))[::-1]:
        rows.sort(key=operator.itemgetter(i), reverse=not asc)
    perm = list((row[-1],) for row in rows)

    c.execute('''DELETE FROM mem.PERMUTATION_TABLE;''')

    c.executemany('''INSERT INTO mem.PERMUTATION_TABLE VALUES(?)''', perm)
    conn.commit()
    c.execute('''DROP INDEX IF EXISTS mem.permutation_index;''')
    c.execute('''CREATE INDEX mem.permutation_index on PERMUTATION_TABLE (permutation);''')
    conn.commit()

    select_stmt = '''SELECT rows.* FROM rows
                                   JOIN (SELECT ROWID, permutation FROM mem.PERMUTATION_TABLE) as P
                                   ON P.permutation = rows.ROWID
                                   ORDER BY P.ROWID'''
    c.close()
    return select_stmt


@contextmanager
def timeit(msg):
    started = time.time()
    yield
    needed = time.time() - started
    print("%s needed %e seconds" % (msg, needed))


def _setup_fresh_db(db_name="peaks.db"):
    if os.path.exists(db_name):
        os.remove(db_name)

    conn = sqlite3.connect(db_name)
    return conn


def _table_names(conn):
    names = conn.execute("""SELECT name FROM sqlite_master WHERE type='table';""").fetchall()
    return [n[0] for n in names]


class Sqlite3ObjectProxy(object):

    def __init__(self, id_, name):
        self.id_ = id_
        self.name = name

    def __str__(self):
        return self.name


class Sqlite3PeakMapProxy(Sqlite3ObjectProxy):

    pass


def _pickle_peakmap(obj, conn):
    names = _table_names(conn)
    next_id = len([n for n in names if n.startswith("ms1_spectra__")])
    table_name = "ms1_spectra__%d" % next_id

    cursor = conn.cursor()

    stmt = """CREATE TABLE %s (
                    rt INTEGER, mz FLOAT, iie INTEGER, iifrac INTEGER
              )""" % table_name

    cursor.execute(stmt)

    stmt = "INSERT INTO %s VALUES(?, ?, ?, ?)""" % table_name

    for spectrum in obj:
        if spectrum.msLevel == 1:
            rt = int(round(spectrum.rt * 10))
            for (mz, ii) in spectrum.peaks:
                iie = int(math.log10(ii))
                iifrac = int((ii / 10 ** iie) * 1000)
                cursor.execute(stmt, (rt, mz, iie, iifrac))

    cursor.execute("CREATE INDEX rt_index_%d_ms1 on %s(rt);" % (next_id, table_name))
    cursor.execute("CREATE INDEX mz_index_%d_ms1 on %s(mz);" % (next_id, table_name))

    conn.commit()

    cursor = conn.cursor()
    table_name = "ms2_spectra__%d" % next_id
    stmt = """CREATE TABLE %s (
                    rt INTEGER, mz FLOAT, iie INTEGER, iifrac INTEGER,
                    precursor FLOAT
              )""" % table_name

    cursor.execute(stmt)
    cursor.execute("CREATE INDEX rt_index_%d_ms2 on %s(rt);" % (next_id, table_name))
    cursor.execute("CREATE INDEX mz_index_%d_ms2 on %s(mz);" % (next_id, table_name))
    cursor.execute("CREATE INDEX precursor_index_%d on %s(precursor);" % (next_id, table_name))
    cursor = conn.cursor()

    stmt = "INSERT INTO %s VALUES(?, ?, ?, ?, ?)""" % table_name

    for spectrum in obj:
        if spectrum.msLevel == 2:
            precursor = spectrum.precursors[0][0]
            rt = int(round(spectrum.rt * 10))
            for (mz, ii) in spectrum.peaks:
                iie = int(math.log10(ii))
                iifrac = int((ii / 10 ** iie) * 1000)
                cursor.execute(stmt, (rt, mz, iie, iifrac, precursor))

    conn.commit()

    return Sqlite3PeakMapProxy(next_id, str(obj))


def _pickle_object(obj, conn):

    if type(obj) in (PeakMap, PeakMapProxy):
        return _pickle_peakmap(obj, conn)

    cursor = conn.cursor()
    name = str(type(obj))
    cursor.execute("""INSERT INTO blobs VALUES(NULL, ?, ?); """,
                   (name, buffer(pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)),))

    proxy = Sqlite3ObjectProxy(cursor.lastrowid, repr(obj))
    return proxy


def load_object(id_, conn):
    stmt = "SELECT name, blob FROM blobs WHERE id = ?"
    name, blob = conn.cursor().execute(stmt, (id_,)).fetchone()
    return name, blob


def unpickle_object(id_, conn):
    name, blob = load_object(id_, conn)
    return name, pickle.loads(blob)


def to_db(t, name):
    conn = _setup_fresh_db(name)
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
            declarations.append(("__id_%s" % name, "TEXT"))
            object_columns.append(name)
        else:
            declarations.append(("%s" % name, sql_type))

    col_definitions = ",\n".join("'%s' %s" % name_type_pair for name_type_pair in declarations)

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

    info = TableInformation(t._colNames, t._colTypes, t._colFormats, t.meta, object_columns)
    id_ = _pickle_object(info, conn).id_
    assert id_ == 1

    object_cache = {}
    n_cols = len(t._colNames)

    cursor = conn.cursor()

    for row in t.rows:

        stmt = """INSERT INTO rows VALUES(%s)""" % ", ".join(["?"] * n_cols)

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
                    value = None
                else:
                    value = object_cache.get(id(cell))
                    if value is None:
                        obj = _pickle_object(cell, conn)
                        value = "%d!%s" % (obj.id_, obj.name)
                        object_cache[id(cell)] = value
            values.append(value)

        cursor.execute(stmt, values)

    cursor.close()
    conn.commit()

    for name, __ in declarations:
        stmt = """CREATE INDEX '%s_index' ON rows ('%s'); """ % (name, name)
        conn.cursor().execute(stmt)
        conn.commit()


def print_meta(db_name):
    conn = sqlite3.connect(db_name)
    name, info = _unpickle_object(1, conn)
    for name, t, f in zip(info.col_names, info.col_types, info.col_formats):
        print(name, t, f)
    print(info)


def from_db(db_name, n_rows=None):

    conn = sqlite3.connect(db_name)
    name, info = unpickle_object(1, conn)

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

    db_col_names = [str(meta_row[1]) for meta_row in meta_rows]

    for i, name in enumerate(db_col_names):
        if name.startswith("__id_"):
            info.col_names[i] = name[5:]
            for row in rows:
                row[i], obj = lookup(row[i])

    return Table(info.col_names, info.col_types, info.col_formats, rows, meta=info.meta)


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

    c.execute('''ATTACH DATABASE ':memory:' AS memory;''')

    c.execute('''DROP TABLE IF EXISTS memory.TEMP''')
    c.execute('''CREATE TABLE memory.TEMP (v %s)''' % type_)
    conn.commit()
    print (time.time() - started)

    c.execute("PRAGMA synchronous=OFF")
    c.executemany('''INSERT INTO memory.TEMP VALUES(?)''', ((v,) for v in values))

    conn.commit()
    print (time.time() - started)
    c.execute('''ALTER TABLE rows ADD COLUMN %s %s;''' % (col_name, type_))
    conn.commit()
    print (time.time() - started)
    c.execute("PRAGMA synchronous=NORMAL")
    c.execute('''UPDATE rows SET %s = (SELECT v FROM memory.TEMP)''' % col_name)
    conn.commit()
    print (time.time() - started)
    c.execute('''CREATE INDEX %s_index on rows(%s)''' % (col_name, col_name))
    conn.commit()
    print (time.time() - started)
    return (time.time() - started)


if __name__ == "__main__":

    if True:
        t = Table.loadTable("peak_table.table")

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
        t = Table.stackTables(tables)
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
