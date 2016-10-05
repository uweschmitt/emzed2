# encoding: utf-8
from __future__ import print_function, division, absolute_import

import os

import sqlite3

db_name = "peaks.db"
if os.path.exists(db_name):
    os.remove(db_name)

conn = sqlite3.connect(db_name)

c = conn.cursor()

# Create tablpeaks
c.execute('''CREATE TABLE peaks
                     (id INTEGER PRIMARY KEY
                      ,target txt
                      ,dump_0 FLOAT
                      ,dump_1 FLOAT
                      ,dump_2 txt
                      ,dump_3 txt
                      ,dump_4 FLOAT
                      ,dump_5 FLOAT
                      ,dump_6 txt
                      ,dump_7 txt
                      )''')

conn.commit()

n = 1000000

for i in range(n):
    if i % 100 <= 3:
        target = "target_%d" % (i // 100)
    else:
        target = None

    d0 = i / 123.45
    d1 = i / 1223.45
    d2 = str(d0) * 10
    d3 = str(d1) * 10

    d4 = d0 + 1
    d5 = d1 + 1

    d6 = d2 + "x"
    d7 = d3 + "x"

    if 10 < i % 100 < 30:
        d2 = None
        d1 = None
    if 50 < i % 100 < 60:
        d3 = None
        d0 = None

    c.execute('''INSERT INTO peaks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (i, target, d0, d1, d2, d3,
                                                                             d4, d5, d6, d7))

conn.commit()


print("inserted rows")

#c = conn.cursor()
#c.execute(""" UPDATE peaks SET target=NULL WHERE target=''; """)
#c.close()

print("updated NULLS")
if 1:
    c = conn.cursor()
    c.execute('''CREATE INDEX targets_peaks_index ON peaks (target)''');
    c.close()
    print("created index")

conn.close()

import time

started = time.time()

conn = sqlite3.connect(db_name)

c = conn.cursor()

# Create tablpeaks
result = c.execute('''SELECT * from peaks where target like 'target_%' ''');
result.fetchall()
print(time.time() - started)

conn.close()

