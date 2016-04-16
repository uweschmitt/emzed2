# encoding: utf-8, division
from __future__ import print_function, division

import contextlib
import os

from table import Table
from hdf5.accessors import Hdf5TableWriter, Hdf5TableAppender

from .table import try_to_move


def to_hdf5(table, path):
    """writes single table"""

    writer = Hdf5TableWriter(path + ".incomplete")
    writer.write_table(table)
    writer.close()

    if os.path.exists(path):
        os.remove(path)
    os.rename(path + ".incomplete", path)


class _Adder(object):

    def __init__(self, path):
        self.appender = None
        self.writer = None
        self.path = path

    def __call__(self, table):
        if self.writer is None:
            self.writer = Hdf5TableWriter(self.path)
            self.writer.write_table(table)
            self.writer.close()
        else:
            if self.appender is None:
                self.appender = Hdf5TableAppender(self.path)
            self.appender.append_table(table)

    def close(self):
        if self.appender is not None:
            self.appender.close()


@contextlib.contextmanager
def atomic_hdf5_writer(path):

    temp_path = path + ".incomplete"
    adder = _Adder(temp_path)
    try:
        yield adder
    finally:
        adder.close()

    try_to_move(temp_path, path)


def append_to_hdf5(tables, path):
    """appends single table or list of tables"""

    if isinstance(tables, Table):
        tables = [tables]

    assert os.path.exists(path), "you can append to an existing table only"

    temp_path = path + ".inwriting"
    os.rename(path, temp_path)

    appender = Hdf5TableAppender(temp_path)
    for table in tables:
        appender.append_table(table)
    appender.close()

    try_to_move(temp_path, path)
