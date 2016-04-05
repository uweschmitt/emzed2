# encoding: utf-8, division
from __future__ import print_function, division

import os.path

from table import Table
from hdf5.accessors import Hdf5TableWriter, Hdf5TableAppender


def to_hdf5(table, path):
    """writes single table"""
    writer = Hdf5TableWriter(path)
    writer.write_table(table)
    writer.close()


def append_to_hdf5(tables, path):
    """appends single table or list of tables"""

    if isinstance(tables, Table):
        tables = [tables]

    assert os.path.exists(path), "you can append to an existing table only"

    appender = Hdf5TableAppender(path)
    for table in tables:
        appender.append_table(table)

    appender.close()
