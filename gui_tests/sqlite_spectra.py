# encoding: utf-8
from __future__ import print_function, division, absolute_import

import collections
import math
import os
import time

import sqlite3


def get_conn(db_name):
    conn = sqlite3.connect(db_name)
    return conn


def setup_db(mzxml_file, db_name):
    conn = get_conn(db_name)

    c = conn.cursor()

    c.execute('''CREATE TABLE spectra
                        (
                         rt        INTEGER
                        ,mz        FLOAT
                        ,intensity INTEGER
                        ,intensity_e INTEGER
                        )''')

    import emzed
    pm = emzed.io.loadPeakMap(mzxml_file)

    for s in pm:
        for (mz, intensity) in s.peaks:
            if intensity > 0:
                istr ="%.2e" % intensity
                f1, f2 = istr.split("e")
                f1 = int(f1.replace(".", ""))
                f2 = int(f2)
                c.execute('''INSERT INTO spectra VALUES(?, ?, ?, ?)''', (round(10 * s.rt), mz, f1, f2))

    c.execute('''CREATE INDEX mz_rt_index ON spectra (mz, rt)''')

    conn.commit()


def chromatogram_0(file, rtmin, rtmax, mzmin, mzmax):
    started = time.time()
    conn = get_conn(file)
    c = conn.cursor()
    rtmin = math.floor(rtmin * 10)
    rtmax = math.ceil(rtmin * 10)
    print(time.time() - started)
    result = c.execute('''SELECT rt, mz, intensity, intensity_e
                          FROM spectra
                          WHERE
                                (? <= rt) AND (rt <= ?)
                          AND
                                (? <= mz) AND (mz <= ?)
                        ''', (rtmin, rtmax, mzmin, mzmax)).fetchall()

    c = collections.defaultdict(float)
    for (rt, mz, f1, f2) in result:
        rt = rt / 10.0
        ii = f1 / 100.0 * 10 ** f2
        c[rt] += ii
    return len(c), (time.time() - started)


def add_column(conn):
    c = conn.cursor()
    started = time.time()
    c.execute('''DROP TABLE IF EXISTS TEMP''')
    c.execute('''CREATE TABLE TEMP (abc FLOAT)''')
    conn.commit()
    print (time.time() - started)

    for f1, f2 in c.execute('''SELECT intensity, intensity_e FROM spectra;''').fetchall():
        ii = f1 / 100.0 * 10 ** f2
        c.execute('''INSERT INTO TEMP VALUES(%s)''' % ii)

    conn.commit()
    print (time.time() - started)

    # update_column would
    c.execute('''ALTER TABLE spectra ADD COLUMN III4 FLOAT;''')
    conn.commit()
    print (time.time() - started)
    c.execute('''UPDATE spectra SET III4 = (SELECT * FROM TEMP)''')
    print (time.time() - started)
    return (time.time() - started)


def chromatogram_1(conn, rtmin, rtmax, mzmin, mzmax):
    c = conn.cursor()
    started = time.time()
    result = c.execute('''SELECT rt, mz, intensity
                          FROM spectra
                          WHERE
                                (? <= mz) AND (mz <= ?)
                          AND
                                (? <= rt) AND (rt <= ?)
                        ''', (rtmin, rtmax, rtmin, rtmax)).fetchall()
    return len(result), (time.time() - started)


import sys
file = sys.argv[1]

if file.endswith(".mzXML"):
    db_name = os.path.splitext(file)[0] + ".db"
    if os.path.exists(db_name):
        os.remove(db_name)
    setup_db(file, db_name)
    os.system("ls -lh %s" % file)
    os.system("ls -lh %s" % db_name)

else:
    conn = get_conn(file)
    print("start")
    #add_column(conn)
    #sys.exit(0)

    rtmin, rtmax = 600, 1200
    rtmin, rtmax = 1000, 1300

    mzmin, mzmax = 329.018, 329.02
    mzmin, mzmax = 192.123, 192.125

    for i in range(3):
        n, t0 = chromatogram_0(file, rtmin, rtmax, mzmin + i,  mzmax + i)
        print("i=", i, "n=", n)
        n, t1 = chromatogram_0(file, rtmin, rtmax, mzmin + i,  mzmax + i)
        print("rt first:")
        print("   t0=%e" % t0, "t1=%e" % t1)
        continue
        n, t0 = chromatogram_1(conn, rtmin, rtmax, mzmin + i,  mzmax + i)
        n, t1 = chromatogram_1(conn, rtmin, rtmax, mzmin + i,  mzmax + i)
        print("mz first:")
        print("   t0=%e" % t0, "t1=%e" % t1)
