# encoding: utf-8
from __future__ import print_function, division, absolute_import

import operator
import sqlite3


from .sqlite_helpers import unpickle_object, chromatogram


class Sqlite3TableProxy(object):

    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.conn.execute('''ATTACH DATABASE ':memory:' AS mem''')
        self.read_table_info()

        self.sort_order = ""
        self.select_for_mixed_sort_order = None
        self.reset_filter()
        self.cursor = None

    def read_table_info(self):
        __, info = unpickle_object(1, self.conn)

        for (name, value) in info._asdict().items():
            setattr(self, name, value)

    def reset_filter(self):
        self.filter_expression = "0=0"

    def create_query(self):
        stmt = "SELECT * FROM rows WHERE {filter_} {order}".format(filter_=self.filter_expression,
                                                                   order=self.sort_order)
        if self.cursor is not None:
            self.cursor.close()
        print(stmt)
        self.cursor = self.conn.cursor().execute(stmt)
        return stmt

    def fetchone(self):
        assert self.cursor is not None, "call create_query() method first"
        return self.cursor.fetchone()

    def set_sort_order(self, items):
        assert all(len(item) == 2 for item in items)

        if len(items) == 0:
            self.sort_order = ""
            return

        term = ", ".join("%s %s" % (name, "ASC" if ascending else "DESC") for (name, ascending)
                         in items)
        self.sort_order = "ORDER BY %s" % term

    def set_filter(self, filter_expression):
        self.filter_expression = filter_expression

    def check_filter_expression(self, filter_expression):
        stmt = "SELECT * FROM rows WHERE (%s) LIMIT 1" % filter_expression
        cursor = self.conn.cursor()
        try:
            cursor.execute(stmt)
        except Exception as e:
            return str(e)
        return None

    def get_chromatogram(self, rtmin, rtmax, mzmin, mzmax, peakmap_entry):
        peakmap_id = int(peakmap_entry.split("!")[0])
        return chromatogram(self.conn, peakmap_id, rtmin, rtmax, mzmin, mzmax)
