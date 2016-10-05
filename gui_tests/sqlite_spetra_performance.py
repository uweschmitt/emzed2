# encoding: utf-8
from __future__ import print_function, division, absolute_import

import os
import time

import sqlite3

db_name = "spectra.db"


def get_conn():
    conn = sqlite3.connect(db_name)
    return conn


def setup_db():
    conn = get_conn()

    c = conn.cursor()

    c.execute('''CREATE TABLE spectra
                        (rt        FLOAT
                        ,mz        FLOAT
                        ,intensity FLOAT
                        )''')

    import emzed
    #pm = emzed.io.loadPeakMap("Danu.mzML")
    pm = emzed.io.loadPeakMap("141208_pos187.mzXML")

    for s in pm:
        for (mz, intensity) in s.peaks:
            c.execute('''INSERT INTO spectra VALUES(?, ?, ?)''', (s.rt, mz, intensity))

    c.execute('''CREATE INDEX mz_rt_index ON spectra (mz, rt)''')

    conn.commit()


def chromatogram_0(conn, rtmin, rtmax, mzmin, mzmax):
    c = conn.cursor()
    started = time.time()
    result = c.execute('''SELECT rt, mz, intensity
                          FROM spectra
                          WHERE
                                (? <= rt) AND (rt <= ?)
                          AND
                                (? <= mz) AND (mz <= ?)
                        ''', (rtmin, rtmax, mzmin, mzmax)).fetchall()
    return len(result), (time.time() - started)


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


if 1:
    if os.path.exists(db_name):
        os.remove(db_name)
    setup_db()
    os.system("ls -lh %s" % db_name)

if 1:
    conn = get_conn()
    print("start")

    rtmin, rtmax = 600, 1200
    rtmin, rtmax = 1000, 1300

    mzmin, mzmax = 329.018, 329.02
    mzmin, mzmax = 192.123, 192.125

    for i in range(3):
        n, t0 = chromatogram_0(conn, rtmin, rtmax, mzmin + i,  mzmax + i)
        print("i=", i, "n=", n)
        n, t1 = chromatogram_0(conn, rtmin, rtmax, mzmin + i,  mzmax + i)
        print("rt first:")
        print("   t0=%e" % t0, "t1=%e" % t1)
        n, t0 = chromatogram_1(conn, rtmin, rtmax, mzmin + i,  mzmax + i)
        n, t1 = chromatogram_1(conn, rtmin, rtmax, mzmin + i,  mzmax + i)
        print("mz first:")
        print("   t0=%e" % t0, "t1=%e" % t1)
