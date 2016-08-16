# encoding: utf-8, division
from __future__ import print_function, division

import contextlib
import os

from table import Table
from hdf5.accessors import Hdf5TableWriter, Hdf5TableAppender

from .table import try_to_move


def to_hdf5(table, path, atomic=True):
    """writes single table
    atomic mode assures that only a complete file will show up when the functions returns.
    On some Windows systems this causes trouble (other procecess as virus scanner may disallow
    renaming, on other systems creation of symlinks are not allowed for the current user),
    then the setting "atomic=False" will work at the risk of incomplete files in rare cases.
    """

    if atomic:
        writer = Hdf5TableWriter(path + ".incomplete")
        writer.write_table(table)
        writer.close()
        try_to_move(path + ".incomplete", path)
    else:
        writer = Hdf5TableWriter(path)
        writer.write_table(table)
        writer.close()


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
def atomic_hdf5_writer(path, atomic=True):

    if atomic:
        temp_path = path + ".incomplete"
    else:
        temp_path = path
    adder = _Adder(temp_path)
    try:
        yield adder
    except Exception, e:
        # do not keep an partially written file in case of errors:
        adder.close()
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e
    finally:
        adder.close()

    if atomic:
        try_to_move(temp_path, path)


def append_to_hdf5(tables, path, atomic=True):
    """appends single table or list of tables"""

    if isinstance(tables, Table):
        tables = [tables]

    assert os.path.exists(path), "you can append to an existing table only"

    if atomic:
        temp_path = path + ".inwriting"
        os.rename(path, temp_path)
    else:
        temp_path = path

    appender = Hdf5TableAppender(temp_path)
    for table in tables:
        appender.append_table(table)
    appender.close()

    if atomic:
        try_to_move(temp_path, path)
