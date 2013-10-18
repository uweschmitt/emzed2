import copy
import os
import itertools
import re
import numpy
import cPickle
import sys
import inspect
import numpy as np
from collections import Counter, OrderedDict, defaultdict
import warnings

import emzed
from .expressions import BaseExpression, ColumnExpression, Value, _basic_num_types, common_type_for
import pyopenms

from . import tools

__doc__ = """

"""


def deprecation(message):
    warnings.warn(message, UserWarning, stacklevel=3)

standardFormats = {int: "%d", long: "%d", float: "%.2f", str: "%s"}
fms = "'%.2fm' % (o/60.0)"  # format seconds to floating point minutes

formatSeconds = fms
formatHexId = "'%x' % id(o)"


def guessFormatFor(name, type_):
    if type_ in (float, int):
        if name.startswith("m"):
            return "%.5f"
        if name.startswith("rt"):
            return fms
    return standardFormats.get(type_)


def computekey(o):
    if type(o) in [int, float, str, long]:
        return o
    if type(o) == dict:
        return computekey(sorted(o.items()))
    if type(o) in [list, tuple]:
        return tuple(computekey(oi) for oi in o)
    return id(o)


def getPostfix(colName):
    if colName.startswith("__"):
        return None

    fields = colName.split("__")

    if len(fields) > 2:
        raise Exception("invalid colName %s" % colName)
    if len(fields) == 1:
        return ""
    return "__" + fields[1]


def convert_list_to_overall_type(li):
    ct = common_type_for(li)
    if ct is not object:
        return [None if x is None else ct(x) for x in li]
    return li


class Bunch(dict):
    __getattr__ = dict.__getitem__


class _CmdLineProgress(object):

    def __init__(self, imax, step=5):
        self.imax = imax
        self.step = step
        self.last = 0

    def progress(self, i):
        percent = int(100.0 * (i + 1) / self.imax)
        if percent >= self.last + self.step:
            print percent,
            sys.stdout.flush()
            self.last = percent


def bestConvert(val):
    assert isinstance(val, str)
    try:
        return int(val)
    except ValueError:
        try:
            return float(val)
        except ValueError:
            try:
                return float(val.replace(",", "."))  # probs with comma
            except ValueError:
                return str(val)


def _formatter(f):
    """ helper, is top level for supporting pickling of Table """

    if f is None:
        def noneformat(s):
            return None
        return noneformat
    elif f.startswith("%"):
        def interpolationformat(s, f=f):
            try:
                return "-" if s is None else f % s
            except:
                return ""
        return interpolationformat
    else:
        def evalformat(s, f=f):
            return "-" if s is None else eval(f, globals(), dict(o=s))
        return evalformat


class Table(object):
    """
    A table holds rows of the same length. Each Column of the table has
    a *name*, a *type* and *format* information, which indicates how to render
    values in this column.
    Further a table has a title and meta information which is a dictionary.

    column types can be any python type.

    format can be:

         - a string interpolation string, e.g. "%.2f"
         - ``None``, which suppresses rendering of this column
         - python code which renders an object of name ``o``, e.g.
           ``str(o)+"x"``

    """

    _to_pickle = ("_colNames",
                  "_colTypes",
                  "_colFormats",
                  "title",
                  "meta",
                  "rows")

    def __init__(self, colNames, colTypes, colFormats, rows=None, title=None,
                 meta=None):

        assert all("__" not in name for name in colNames),\
            "illegal column name(s), double underscores not allowed"
        self._setup_without_namecheck(colNames, colTypes, colFormats,
                                      rows, title, meta)

    @classmethod
    def _create(clz, colNames, colTypes, colFormats,
                rows=None, title=None, meta=None):
        inst = clz.__new__(Table)
        inst._setup_without_namecheck(colNames, colTypes, colFormats,
                                      rows, title, meta)
        return inst

    def _setup_without_namecheck(self, colNames, colTypes, colFormats,
                                 rows=None, title=None, meta=None):

        if len(colNames) != len(set(colNames)):
            counts = Counter(colNames)
            multiples = [name for (name, count) in counts.items() if count > 1]
            message = "multiple columns: " + ", ".join(multiples)
            raise Exception(message)

        assert len(colNames) == len(colTypes)
        if rows is not None:
            for row in rows:
                assert len(row) == len(colNames)
        else:
            rows = []

        if not all(isinstance(row, list) for row in rows):
            raise Exception("not all rows are lists !")

        self._colNames = list(colNames)

        self._colTypes = list(colTypes)

        is_numpy_type = lambda t: np.number in t.__mro__

        if any(is_numpy_type(t) for t in colTypes):
            raise Exception("using numpy floats instead of python floats is not a good idea. "
                            "Table operations may crash")

        self._colFormats = [None if f == "" else f for f in colFormats]

        self.rows = rows
        self.title = title
        self.meta = copy.copy(meta) if meta is not None else dict()

        self.primaryIndex = {}
        self._name = str(self)

        self.editableColumns = set()

        # as we provide  access to columns via __getattr__, colNames must
        # not be in objects __dict__ and must not be name of member
        # functions:

        warnings.simplefilter("ignore", UserWarning)
        memberNames = [name for name, obj in inspect.getmembers(self)]
        warnings.simplefilter("always", UserWarning)

        for name in colNames:
            if name in self.__dict__ or name in memberNames:
                raise Exception("colName '%s' not allowed" % name)

        self.resetInternals()

    def getColNames(self):
        """ returns a copied list of column names, one can operator on this
            list without corrupting the underlying table
        """
        return self._colNames[:]

    def getColTypes(self):
        """ returns a copied list of column names, one can operator on this
            list without corrupting the underlying table
        """
        return self._colTypes[:]

    def getColType(self, name):
        """ returns type of column ``name`` """
        return self._colTypes[self.getIndex(name)]

    def setColType(self, name, type_):
        """
        sets type of column ``name`` to type ``type_``.
        """
        self._colTypes[self.getIndex(name)] = type_
        self.resetInternals()

    def getColFormats(self):
        """ returns a copied list of column formats, one can operator on this
            list without corrupting the underlying table.
        """
        return self._colFormats[:]

    def getColFormat(self, name):
        """ returns format of column ``name`` """
        return self._colFormats[self.getIndex(name)]

    def setColFormat(self, name, format_):
        """
        sets format of column ``name`` to type ``format_``.
        """
        self._colFormats[self.getIndex(name)] = format_
        self.resetInternals()

    def info(self):
        """
        prints some table information and some table statistics
        """
        import pprint
        print
        print "table info:   title=", self.title
        print
        print "   meta=",
        pprint.pprint(self.meta)
        print "   rows=", len(self)
        print
        for i, p in enumerate(zip(self._colNames, self._colTypes,
                              self._colFormats)):
            vals = getattr(self, p[0]).values
            nones = sum(1 for v in vals if v is None)
            numvals = len(set(id(v) for v in vals))
            txt = "[%d diff vals, %d Nones]" % (numvals, nones)
            print "   #%-2d %-25s name=%-8r %-15r fmt=%r" % ((i, txt) + p)
        print

    def addRow(self, row, doResetInternals=True):
        """ adds a new row to the table, checks if values in row are of
            expected type or can be converted to this type.

            Raises an ``AssertException`` if the length of ``row`` does not
            match to the numbers of columns of the table.
            """

        assert len(row) == len(self._colNames), "length of row does not match"
        # check for conversion !
        for i, (v, t) in enumerate(zip(row, self._colTypes)):
            if v is not None and t in [int, float, long, str]:
                row[i] = t(v)
            else:
                row[i] = v
        self.rows.append(row)
        if doResetInternals:
            self.resetInternals()

    def isEditable(self, colName):
        return colName in self.editableColumns

    def _updateIndices(self):
        self.colIndizes = dict((n, i) for i, n in enumerate(self._colNames))

    def getVisibleCols(self):
        """ returns a list with the names of the columns which are
            visible. that is: the corresponding format is not None """
        return [n for (n, f) in zip(self._colNames, self._colFormats)
                if f is not None]

    def getFormat(self, colName):
        """ returns for format for the given column ``colName`` """
        return self._colFormats[self.getIndex(colName)]

    def getType(self, colName):
        """ returns for format for the given column ``colName`` """
        return self._colTypes[self.getIndex(colName)]

    def _setupFormatters(self):
        self.colFormatters = [_formatter(f) for f in self._colFormats]

    def getColumn(self, name):
        """ returns ColumnExpression object for column ``name``.
            to get the values of the column you can use
            ``table.getColumn("index").values``.

            See: :py:class:`~emzed.core.data_types.expressions.ColumnExpression`
        """
        return getattr(self, name)

    def _setupColumnAttributes(self):
        for name in self._colNames:
            ix = self.getIndex(name)
            col = ColumnExpression(self, name, ix, self._colTypes[ix])
            setattr(self, name, col)

    def numRows(self):
        """
        returns the number of rows
        """
        return len(self.rows)

    def __getitem__(self, ix):
        """
        supports creating a new table from a subset of current rows
        using brackets notation.

        Example::

                t = emzed.utils.toTable("a", [1, 2, 3])
                t[0].a.values == [1]
                t[:1].a.values == [1]
                t[1:].a.values == [2, 3]
                t[:].a.values == [1, 2, 3]

                t[:] == t.copy()

        """
        if not isinstance(ix, slice):
            ix = slice(ix, ix + 1)
        prototype = self.buildEmptyClone()
        for row in self.rows[ix]:
            prototype.rows.append(row[:])
        prototype.resetInternals()
        return prototype

    def __getstate__(self):
        """ **for internal use**: filters some attributes for pickling. """
        dd = self.__dict__.copy()
        # self.colFormatters can not be pickled
        del dd["colFormatters"]
        for name in self._colNames:
            del dd[name]
        return dd

    def __setstate__(self, dd):
        """ **for internal use**: builds table from pickled data."""
        # attribute conversion for loading tables of older emzed versions
        # which hat attributes colNames, colFormats and colTypes, which are
        # now properties to access _colNames, _colFormats and _colTypes.
        old_attribs = ["colNames", "colTypes", "colFormats"]
        if any(a in dd for a in old_attribs):
            if all(a in dd for a in old_attribs):
                for a in old_attribs:
                    dd["_" + a] = dd[a]
                    del dd[a]
            else:
                raise Exception("can not unpickle table, internal mismatch")

        self.__dict__ = dd
        self.resetInternals()

    def hasColumn(self, name):
        """ checks if column with given name ``name`` exists """
        return name in self._colNames

    def hasColumns(self, *names):
        """ checks if columns with given names exist.

            Example: ``tab.hasColumn("rt", "rtmin", "rtmax")``
        """
        return all(self.hasColumn(n) for n in names)

    def requireColumn(self, name):
        """ throws exception if column with name ``name`` does not exist"""
        if not name in self._colNames:
            raise Exception("column %r required" % name)
        return self

    def getIndex(self, colName):
        """ gets the integer index of the column ``colName``.

            Example: ``table.rows[0][table.getIndex("mz")]``
            """
        idx = self.colIndizes.get(colName, None)
        if idx is None:
            raise Exception("column with name %r not in table" % colName)
        return idx

    def setValue(self, row, colName, value, slow_but_checked=True):
        """ sets ``value`` of column ``colName`` in a given ``row``.

            Example: ``table.setValue(table.rows[0], "mz", 252.83332)``
        """
        if slow_but_checked:
            assert id(row) in map(id, self.rows)
        ix = self.getIndex(colName)
        if type(value) in [np.float32, np.float64]:
            value = float(value)
        row[ix] = value
        self.resetInternals()

    def getValues(self, row):
        """
            if ``colName`` is not provided, one gets the content of
            the ``row`` as a dictionary mapping column names to values.

            Example::

                row = table.getValues(table.rows[0])
                print row["mz"]
        """
        return Bunch((n, self.getValue(row, n)) for n in self._colNames)

    def getValue(self, row, colName):
        """ returns value of column ``colName`` in a given ``row``

            Example: ``table.getValue(table.rows[0], "mz")``
        """
        return row[self.getIndex(colName)]

    def setRow(self, idx, row):
        """ replaces row ``idx`` with ``row``.
            be carefull we only check the length not the types !
        """
        assert 0 <= idx < len(self)
        assert len(row) == len(self._colNames), "row as wrong length %d" % len(row)
        self.rows[idx] = row
        self.resetInternals()

    def _getColumnCtx(self, needed):
        names = [n for (t, n) in needed if t == self]
        return dict((n, (self.getColumn(n).values,
                         self.primaryIndex.get(n),
                         self.getColumn(n).type_)) for n in names)

    def addEnumeration(self, colName="id"):
        """ adds enumerated column as first column to table **in place**.

            if ``colName`` is not given the default name is *"id"*

            Enumeration starts with zero.
        """

        if colName in self._colNames:
            raise Exception("column with name %r already exists" % colName)
        self._colNames.insert(0, colName)
        self._colTypes.insert(0, int)
        if len(self) > 99999:
            fmt = "%6d"
        elif len(self) > 9999:
            fmt = "%5d"
        elif len(self) > 999:
            fmt = "%4d"
        elif len(self) > 99:
            fmt = "%3d"
        elif len(self) > 9:
            fmt = "%2d"
        else:
            fmt = "%d"
        fmt = "%d"
        self._colFormats.insert(0, fmt)
        for i, r in enumerate(self.rows):
            r.insert(0, i)
        self.resetInternals()

    def sortBy(self, colName, ascending=True):
        """
        sorts table in respect of column named *colName* **in place**.
        *ascending* is boolean and tells if the values are sorted
        in ascending order or descending.

        This is important to build an internal index for faster queries
        with ``Table.filter``, ``Table.leftJoin`` and ``Table.join``.

        For building an internal index, ascending must be *True*, you
        can have only one index per table.
        """
        idx = self.colIndizes[colName]

        decorated = [(row[idx], i) for (i, row) in enumerate(self.rows)]
        decorated.sort(reverse=not ascending)
        permutation = [i for (_, i) in decorated]

        self._applyRowPermutation(permutation)

        if ascending:
            self.primaryIndex = {colName: True}
        else:
            self.primaryIndex = {}
        return permutation

    def _applyRowPermutation(self, permutation):
        self.rows = [self.rows[permutation[i]] for i in range(len(permutation))]
        self.resetInternals()

    def copy(self):
        """ returns a 'semi-deep' copy of the table """
        # we are lucky that we implemented __getitem__:
        return self[:]

    def extractColumns(self, *names):
        """extracts the given column names ``names`` and returns a new
           table with these columns

           Example: ``t.extractColumns("id", "name"))``
           """
        assert len(set(names)) == len(names), "duplicate column name"
        indices = [self.getIndex(name) for name in names]
        types = [self._colTypes[i] for i in indices]
        formats = [self._colFormats[i] for i in indices]
        rows = [[row[i] for i in indices] for row in self.rows]
        return Table._create(names, types, formats, rows, self.title, self.meta.copy())

    def _renameColumnsUnchecked(self, *dicts, **keyword_args):
        for d in dicts:
            keyword_args.update(d)
        self._colNames = [keyword_args.get(n, n) for n in self._colNames]
        self.resetInternals()

    def renameColumns(self, *dicts, **keyword_args):
        """renames columns **in place**.

           So if you want to rename "mz_1" to "mz" and "rt_1"
           to "rt", ``table.renameColumns(mz_1=mz, rt_1=rt)``

           For memorization read the ``=`` as ``->``.

           Sometimes it is helpful to build dictionaries which describe the
           renaming. In this case you can pass an arbitrary number of
           dictionaries, and even additional keywword arguments (if you want)
           to this method.

           Example::

               table.renameColumns(dict(a="b", c="d"))
               table.renameColumns(dict(a="b"), dict(c="d"))
               table.renameColumns(dict(a="b"), c="d"))

        """

        assert all(isinstance(d, dict) for d in dicts), "expect dicts"

        def check_old_names(d, old_names):
            for old_name in d.keys():
                if old_name in old_names:
                    raise Exception("name overlap in column names to rename")
                if old_name not in self._colNames:
                    raise Exception("column %r does not exist" % old_name)
                old_names.add(old_name)
            return old_names

        old_names = check_old_names(keyword_args, set())
        for d in dicts:
            old_names = check_old_names(d, old_names)

        def check_new_names(d, new_names):
            for new_name in d.values():
                if new_name in new_names:
                    raise Exception("name overlap in new column names")
                if new_name in self._colNames:
                    raise Exception("column %s already exists" % new_name)
                if "__" in new_name:
                    raise Exception("double underscore in %r not allowed" %
                                    new_name)
                new_names.add(new_name)
            return new_names

        new_names = check_new_names(keyword_args, set())
        for d in dicts:
            new_names = check_new_names(d, new_names)

        self._renameColumnsUnchecked(*dicts, **keyword_args)

    def __len__(self):
        return len(self.rows)

    def storeCSV(self, path, onlyVisibleColumns=True):
        """writes the table in .csv format. The ``path`` has to end with
           '.csv'.

           If the file already exists, the routine tries names
           ``*.csv.1, *.csv.2, ...`` until a non-existing file name is found

           As .csv is a text format all binary information is lost !
        """
        if not os.path.splitext(path)[1].upper() == ".CSV":
            raise Exception("%s has wrong file type extension" % path)
        it = itertools
        for p in it.chain([path], ("%s.%d" % (path, i) for i in it.count(1))):
            if os.path.exists(p):
                print p, "exists"
            else:
                print "write ", p
                with file(p, "w") as fp:
                    if onlyVisibleColumns:
                        colNames = self.getVisibleCols()
                    else:
                        colNames = self._colNames
                    print >> fp, "; ".join(colNames)
                    for row in self.rows:
                        data = [self.getValue(row, v) for v in colNames]
                        print >> fp, "; ".join(map(str, data))
                break

    def store(self, path, forceOverwrite=False):
        """
        writes the table in binary format. All information, as
        corresponding peak maps are written too.
        The file name extension must be ".table".

        Latter the file can be loaded with :py:meth:`~.load`
        """
        if not forceOverwrite and os.path.exists(path):
            raise Exception("%s exists. You may use forceOverwrite=True" % path)
        with open(path, "w+b") as fp:
            fp.write("emzed_version=%s.%s.%s\n" % emzed.__version__)
            data = tuple(getattr(self, a) for a in Table._to_pickle)
            cPickle.dump(data, fp, protocol=2)

    @staticmethod
    def _load_strict(pickle_data):
        try:
            data = cPickle.loads(pickle_data)
        except Exception, e:
            raise Exception("file has invalid format: %s" % e)

        if not isinstance(data, (list, tuple)):
            raise Exception("data item from file is not list or tuple")
        if len(data) != len(Table._to_pickle):
            raise Exception("number of data items from file does not match Table._to_pickle")
        tab = Table([], [], [], [], None, None)
        for name, item in zip(Table._to_pickle, data):
            setattr(tab, name, item)
        return tab

    @staticmethod
    def _try_to_load_old_version(pickle_data):
        import sys
        from . import table, ms_types
        sys.modules["libms.DataStructures.Table"] = table
        sys.modules["libms.DataStructures.MSTypes"] = ms_types
        try:
            tab = cPickle.loads(pickle_data)
        finally:
            del sys.modules["libms.DataStructures.Table"]
            del sys.modules["libms.DataStructures.MSTypes"]
        return tab

    @staticmethod
    def load(path):
        """loads a table stored with :py:meth:`~.store`

           **Note**: as this is a static method, it has to be called as
           ``tab = Table.load("xzy.table")``
        """
        with open(path, "rb") as fp:
            data = fp.read()
            version_str, __, pickle_data = data.partition("\n")
            if not version_str.startswith("emzed_version="):
                try:
                    return Table._try_to_load_old_version(pickle_data)
                except:
                    return Table._try_to_load_old_version(data)
            v_number_str = version_str[14:]
            v_number = tuple(map(int, v_number_str.split(".")))
            try:
                tab = Table._load_strict(pickle_data)
                tab.version = v_number
                tab.meta["loaded_from"] = os.path.abspath(path)
                return tab
            except:
                return Table._try_to_load_old_version(pickle_data)

    def buildEmptyClone(self):
        """ returns empty table with same names, types, formatters,
            title and meta data """
        return Table._create(self._colNames, self._colTypes, self._colFormats,
                             [], self.title, self.meta.copy())

    def dropColumns(self, *names):
        """ removes columns with given ``names`` from the table.
            Works **in place**

            Example: ``tab.dropColumns("mz", "rt", "rmse")``
        """
        # check all names before manipulating the table,
        # so this operation is atomic
        for name in names:
            self.requireColumn(name)
        for name in names:
            delattr(self, name)

        indices = [self.getIndex(n) for n in names]
        indices.sort()
        for ix in reversed(indices):
            del self._colNames[ix]
            del self._colFormats[ix]
            del self._colTypes[ix]
            for row in self.rows:
                del row[ix]
        if len(self._colNames) == 0:
            # in this case we have here len(table) empty lists as rows, so we empty the tabl
            # totally:
            self.rows = []
        self.resetInternals()

    def splitBy(self, *colNames):
        """
        generates a list of subtables, where the columns given by ``colNames``
        are unique.

        If we have a table ``t1`` as

        === === ===
        a   b   c
        === === ===
        1   1   1
        1   1   2
        2   1   3
        2   2   4
        === === ===

        ``res = t1.splitBy("a")`` results in a table ``res[0]`` as

        === === ===
        a   b   c
        === === ===
        1   1   1
        1   1   2
        === === ===

        ``res[1]`` which is like

        === === ===
        a   b   c
        === === ===
        2   1   3
        === === ===

        and ``res[2]`` which is

        === === ===
        a   b   c
        === === ===
        2   2   4
        === === ===


        """
        for name in colNames:
            self.requireColumn(name)

        groups = set()
        for row in self.rows:
            key = computekey([self.getValue(row, n) for n in colNames])
            groups.add(key)

        # preserve order of rows
        subTables = OrderedDict()
        for row in self.rows:
            key = computekey([self.getValue(row, n) for n in colNames])
            if key not in subTables:
                subTables[key] = self.buildEmptyClone()
            subTables[key].rows.append(row[:])
        splitedTables = subTables.values()
        for table in splitedTables:
            table.resetInternals()
        return splitedTables

    def append(self, *tables):
        """
        appends ``tables`` to the existing table **in place**. Can be called as ::

              t1.append(t2, t3)
              t1.append([t2, t3])
              t1.append(t2, [t3, t4])

        the column names and the column types have to match !
        column format is taken from the original table.
        """
        alltables = []
        for table in tables:
            if type(table) in [list, tuple]:
                alltables.extend(table)
            elif isinstance(table, Table):
                alltables.append(table)
            else:
                raise Exception("can not join object %r" % table)

        names = set((tuple(t._colNames)) for t in alltables)
        if len(names) > 1:
            raise Exception("the column names do not match")

        types = set((tuple(t._colTypes)) for t in alltables)
        if len(types) > 1:
            raise Exception("the column types do not match")
        for t in alltables:
            self.rows.extend(t.rows)
        self.resetInternals()

    def replaceColumn(self, name, what, type_=None, format_=""):
        """
        replaces column ``name`` **in place**.

          - ``name`` is name of the new column
          - ``*type_`` is one of the valid types described above.
            If ``type_ == None`` the method tries to guess the type from ``what``.
          - ``format_`` is a format string as "%d" or ``None`` or an executable
            string with python code.
            If you use ``format_=""`` the method will try to determine a
            default format for the type.

        For the values ``what`` you can use

           - an expression (see :py:class:`~emzed.core.data_types.Expressions`)
             as ``table.addColumn("diffrt", table.rtmax-table.rtmin)``
           - a callback with signature ``callback(table, row, name)``
           - a constant value
           - a list with the correct length.

        """

        self.requireColumn(name)
        # we do:
        #      add tempcol, then delete oldcol, then rename tempcol -> oldcol
        # this is easier to implement, has no code duplication, but maybe a
        # bit slower. but that does not matter at this point of time:
        rv = self._addColumnWithoutNameCheck(name + "__tmp", what, type_, format_,
                                             insertBefore=name)
        self.dropColumns(name)
        self._renameColumnsUnchecked(**{name + "__tmp": name})
        return rv

    def _updateColumnWithoutNameCheck(self, name, what, type_=None, format_="",
                                      insertBefore=None):
        """
        Replaces the column ``name`` if it exists. Else the column is added.

        For the parameters see :py:meth:`~.addColumn`
        """
        if self.hasColumn(name):
            self.replaceColumn(name, what, type_, format_)
        else:
            self._addColumnWithoutNameCheck(name, what, type_, format_,
                                            insertBefore)

    def updateColumn(self, name, what, type_=None, format_="",
                     insertBefore=None):
        if self.hasColumn(name):
            self.replaceColumn(name, what, type_, format_)
        else:
            self.addColumn(name, what, type_, format_, insertBefore)

    def addColumn(self, name, what, type_=None, format_="", insertBefore=None):
        """
        adds a column **in place**.

        For the meaning of the  parameters
        see :py:meth:`~.replaceColumn`

        If you do not want the column be added at the end, one can use
        ``insertBefore``, which maybe the name of an existing column, or an
        integer index (negative values allowed !).

        """
        if "__" in name:
            raise Exception("double underscore in %r not allowed" % name)

        self._addColumnWithoutNameCheck(name, what, type_, format_, insertBefore)

    def _addColumnWithoutNameCheck(self, name, what, type_=None, format_="",
                                   insertBefore=None):
        import types

        assert isinstance(name, (str, unicode)), "colum name is not a  string"

        if type_ is not None:
            assert isinstance(type_, type), "type_ param is not a type"

        if name in self._colNames:
            raise Exception("column with name %r already exists" % name)

        if isinstance(what, BaseExpression):
            return self._addColumnByExpression(name, what, type_, format_,
                                               insertBefore)
        if callable(what):
            return self._addColumnByCallback(name, what, type_, format_,
                                             insertBefore)

        if type(what) in [list, tuple, types.GeneratorType, np.array]:
            return self._addColumFromIterable(name, what, type_, format_,
                                              insertBefore)

        return self._addConstantColumnWithoutNameCheck(name, what, type_,
                                                       format_, insertBefore)

    def _addColumnByExpression(self, name, expr, type_, format_, insertBefore):
        values, _, type2_ = expr._eval(None)
        # TODO: automatic table check for numpy values via decorator ?
        # switchable !?
        if type2_ in _basic_num_types:
            values = values.tolist()
        return self._addColumn(name, values, type_ or type2_, format_, insertBefore)

    def _addColumnByCallback(self, name, callback, type_, format_, insertBefore):
        values = [callback(self, r, name) for r in self.rows]
        return self._addColumn(name, values, type_, format_, insertBefore)

    def _addColumFromIterable(self, name, iterable, type_, format_, insertBefore):
        values = list(iterable)
        return self._addColumn(name, values, type_, format_, insertBefore)

    def _addColumn(self, name, values, type_, format_, insertBefore):
        # works for lists, numbers, objects: converts inner numpy dtypes
        # to python types if present, else does nothing !!!!

        assert len(values) == len(self), "length of new column %d does not "\
                                         "fit number of rows %d in table" % (len(values), len(self))

        if type(values) == np.ma.core.MaskedArray:
            values = values.tolist()  # handles missing values as None !

        # type_ may be None, so guess:
        type_ = type_ or common_type_for(values)

        if format_ == "":
            format_ = guessFormatFor(name, type_)

        if insertBefore is None:
            # list.insert(len(list), ..) is the same as append(..) !
            insertBefore = len(self._colNames)

        # colname -> index
        if isinstance(insertBefore, str):
            if insertBefore not in self._colNames:
                raise Exception("column %r does not exist", insertBefore)
            insertBefore = self.getIndex(insertBefore)

        # now insertBefore is an int, or something we can not handle
        if isinstance(insertBefore, int):
            if insertBefore < 0:  # indexing from back
                insertBefore += len(self._colNames)
            self._colNames.insert(insertBefore, name)
            self._colTypes.insert(insertBefore, type_)
            self._colFormats.insert(insertBefore, format_)
            for row, v in zip(self.rows, values):
                row.insert(insertBefore, v)

        else:
            raise Exception("can not handle insertBefore=%r" % insertBefore)

        self.resetInternals()

    def addConstantColumn(self, name, value, type_=None, format_="",
                          insertBefore=None):
        """
        see :py:meth:`~.addColumn`.

        ``value`` is inserted in the column, despite its class. So the
        cases in py:meth:`~.addColumn` are not considered, which is useful,
        e.g. if you want to set all cells in a column to as ``list``.
        """
        if "__" in name:
            raise Exception("double underscore in %r not allowed" % name)
        self._addConstantColumnWithoutNameCheck(name, value, type_, format_,
                                                insertBefore)

    def _addConstantColumnWithoutNameCheck(self, name, value, type_=None,
                                           format_="", insertBefore=None):

        if type_ is not None:
            assert isinstance(type_, type), "type_ param is not a type"
        if name in self._colNames:
            raise Exception("column with name '%s' already exists" % name)
        return self._addColumn(name, [value] * len(self), type_, format_,
                               insertBefore)

    def resetInternals(self):
        """  **internal method**

            must be called after manipulation  of

            - self._colNames
            - self._colFormats

        or

            - self.rows
        """
        self._setupFormatters()
        self._updateIndices()
        self._setupColumnAttributes()

    def uniqueRows(self):
        """
        extracts table with unique rows.
        Two rows are equal if all fields, including **invisible**
        columns (those with ``format_==None``) are equal.
        """
        result = self.buildEmptyClone()
        keysSeen = set()
        for row in self.rows:
            key = computekey(row)
            if key not in keysSeen:
                result.rows.append(row[:])
                keysSeen.add(key)
        return result

    def aggregate(self, expr, newName, groupBy=None):

        """
        adds new aggregated column to table **in place**.

        ``expr`` calculates the aggregation.

        The table can be split into several subtables by
        providing an extra ``groupBy`` parameter,
        which can be a column name or a list of column names,
        then the aggregation is only performed per group.

        In each group the values corresponding to ``groupBy``
        are constant.

        ``newName`` is the column name for the aggregations.

        If we have a table ``t1`` with

           ===    ======    =====
           id     source    value
           ===    ======    =====
           0      1         10.0
           1      1         20.0
           2      2         30.0
           ===    ======    =====

        Then the result of

        ``t1.aggregate(t1.value.mean, "mean")``

        is

           ===    ======    =====  ====
           id     source    value  mean
           ===    ======    =====  ====
           0      1         10.0   20.0
           1      1         20.0   20.0
           2      2         30.0   20.0
           ===    ======    =====  ====

        If you group by column ``source``, for example as

        ``t1.aggregate(t1.value.mean, "mean_per_source", groupBy="source")``

        the result is

           ===    ======    =====  ===============
           id     source    value  mean_per_source
           ===    ======    =====  ===============
           0      1         10.0   15.0
           1      1         20.0   15.0
           2      2         30.0   30.0
           ===    ======    =====  ===============

        Here we got two different row groups, in each group the value of *source*
        is constant. So we have one group:

           ===    ======    =====
           id     source    value
           ===    ======    =====
           0      1         10.0
           1      1         20.0
           ===    ======    =====

        and second one which is:

           ===    ======    =====
           id     source    value
           ===    ======    =====
           2      2         30.0
           ===    ======    =====


        And if we group by identical (id, source) pairs, each row is in separate
        group and so

        ``t1.aggregate(t1.value.mean, "mean_per_source", groupBy=["id", "source"])``

        delivers:

           ===    ======    =====  ===============
           id     source    value  mean_per_source
           ===    ======    =====  ===============
           0      1         10.0   10.0
           1      1         20.0   20.0
           2      2         30.0   30.0
           ===    ======    =====  ===============

        """

        if "__" in newName:
            raise Exception("double underscore in %r not allowed" % newName)

        if isinstance(groupBy, str):
            groupBy = [groupBy]
        elif groupBy is None:
            groupBy = []

        if len(self) == 0:
            rv = self.buildEmptyClone()
            rv._colNames.append(newName)
            rv._colTypes.append(object)
            rv._colFormats.append("%r")
            rv.resetInternals()
            return rv

        subTables = self.splitBy(*groupBy)
        nc = expr._neededColumns()
        for t, _ in nc:
            if t != self:
                raise Exception("illegal expression")
        names = [n for (t, n) in nc]
        collectedValues = []
        for t in subTables:
            print
            print "subt"
            t._print()
            ctx = dict((n, (t.getColumn(n).values,
                            t.primaryIndex.get(n),
                            t.getColumn(n).type_
                            )) for n in names)
            value, _, type_ = expr._eval({self: ctx})
            # works for numbers and objects to, but not if values is
            # iterable:
            assert len(value) == 1, "you did not use an aggregating "\
                "expression, or you aggregate over a column which has lists or numpy "\
                "arrays as entries"

            if type_ in _basic_num_types:
                value = value.tolist()
            collectedValues.extend(value * len(t))

        result = self.copy()
        result.addColumn(newName, collectedValues)
        result.primaryIndex = self.primaryIndex.copy()
        return result

    def filter(self, expr, debug=False):
        """builds a new table with columns selected according to ``expr``. E.g. ::

               table.filter(table.mz >= 100.0)
               table.filter((table.mz >= 100.0) & (table.rt <= 20))

        \\
        """
        if not isinstance(expr, BaseExpression):
            expr = Value(expr)

        if debug:
            print "#", expr

        ctx = {self: self._getColumnCtx(expr._neededColumns())}
        flags, _, _ = expr._eval(ctx)
        filteredTable = self.buildEmptyClone()
        filteredTable.primaryIndex = self.primaryIndex.copy()
        if len(flags) == 1:
            if flags[0]:
                filteredTable.rows = [r[:] for r in self.rows]
            else:
                filteredTable.rows = []
        else:
            assert len(flags) == len(self), "result of filter expression does not match table size"
            filteredTable.rows = [self.rows[n][:] for n, i in enumerate(flags) if i]
        return filteredTable

    def removePostfixes(self, *postfixes):
        """
        removes postfixes.
        throws exception if this process produces duplicate column names.

        if you ommit postfixes parameter, all "__xyz" postfixes are removed.
        else the given postfixes are stripped from the column names
        """
        new_column_names = list()
        for column_name in self._colNames:
            if not postfixes:
                new_column_name, __, __ = column_name.partition("__")
            else:
                for pf in postfixes:
                    if column_name.endswith(pf):
                        new_column_name = column_name[:-len(pf)]
                        break
                else:
                    new_column_name = column_name
            new_column_names.append(new_column_name)

        if len(set(new_column_names)) != len(new_column_names):
            raise Exception("removing postfix(es) %r results in ambiguous"
                            "column_names %s" % (postfixes, new_column_names))

        self._colNames = new_column_names
        self.resetInternals()

    def supportedPostfixes(self, colNamesToSupport):
        """

        For a table with column names ``["rt", "rtmin", "rtmax", "rt1", "rtmin1"]``

        ``supportedPostfixes(["rt"])`` returns ``["", "min", "max", "1", "min1"]``,

        ``supportedPostfixes(["rt", "rtmin"])`` returns ``["", "1"]``,

        ``supportedPostfixes(["rt", "rtmax"])`` returns ``[""]``,

        """

        collected = defaultdict(list)
        for name in self._colNames:
            for prefix in colNamesToSupport:
                if name.startswith(prefix):
                    collected[prefix].append(name[len(prefix):])

        counter = defaultdict(int)
        for postfixes in collected.values():
            for postfix in postfixes:
                counter[postfix] += 1

        supported = [pf for pf, count in counter.items()
                     if count == len(colNamesToSupport)]

        return sorted(set(supported))

    def join(self, t, expr=True, debug=False):
        """joins two tables.

           So if you have two table ``t1`` and ``t2`` as

           === ===
           id  mz
           === ===
           0   100.0
           1   200.0
           2   300.0
           === ===

           and

           ===    =====     ====
           id     mz        rt
           ===    =====     ====
           0      100.0     10.0
           1      110.0     20.0
           2      200.0     30.0
           ===    =====     ====

           Then the result of ``t1.join(t2, (t1.mz >= t2.mz -20) & (t1.mz <= t2.mz + 20)``
           is

           ====   =====  ====   =====  ====
           id_1   mz_1   id_2   mz_2   rt
           ====   =====  ====   =====  ====
           0      100.0  0      100.0  10.0
           0      100.0  1      110.0  20.0
           1      200.0  2      200.0  30.0
           ====   =====  ====   =====  ====

           If you do not provide an expression, this method returns the full
           cross product.

        """
        # no direct type check below, as databases decorate member tables:
        try:
            t._getColumnCtx
        except:
            raise Exception("first arg is of wrong type")

        if not isinstance(expr, BaseExpression):
            expr = Value(expr)

        table = self._buildJoinTable(t)

        if debug:
            print "# %s.join(%s, %s)" % (self._name, t._name, expr)
        tctx = t._getColumnCtx(expr._neededColumns())

        cmdlineProgress = _CmdLineProgress(len(self))
        rows = []
        for ii, r1 in enumerate(self.rows):
            r1ctx = dict(
                (n, ([v], None, t)) for (n, v, t) in zip(self._colNames, r1, self._colTypes))
            ctx = {self: r1ctx, t: tctx}
            flags, _, _ = expr._eval(ctx)
            if len(flags) == 1:
                if flags[0]:
                    rows.extend([r1[:] + row[:] for row in t.rows])
            else:
                rows.extend([r1[:] + t.rows[n][:] for (n, i) in enumerate(flags) if i])
            cmdlineProgress.progress(ii)
        print
        table.rows = rows
        return table

    def leftJoin(self, t, expr=True, debug=False):
        """performs an *left join* also known as *outer join* of two tables.

           It works similar to :py:meth:`~.join`
           but keeps non-matching rows of
           the first table. So if we take the example from
           :py:meth:`~.join`

           Then the result of ``t1.leftJoin(t2, (t1.mz >= t2.mz -20) & (t1.mz <= t2.mz + 20)``
           is

           ====   =====  ====   =====  ====
           id_1   mz_1   id_2   mz_2   rt
           ====   =====  ====   =====  ====
           0      100.0  0      100.0  10.0
           0      100.0  1      110.0  20.0
           1      200.0  2      200.0  30.0
           2      300.0  None   None   None
           ====   =====  ====   =====  ====

           If you do not provide an expression, this method returns the full
           cross product.
        """
        # no direct type check below, as databases decorate member tables:
        try:
            t._getColumnCtx
        except:
            raise Exception("first argument is of wrong type")

        if not isinstance(expr, BaseExpression):
            expr = Value(expr)

        table = self._buildJoinTable(t)

        if debug:
            print "# %s.leftJoin(%s, %s)" % (self._name, t._name, expr)
        tctx = t._getColumnCtx(expr._neededColumns())

        filler = [None] * len(t._colNames)
        cmdlineProgress = _CmdLineProgress(len(self))

        rows = []
        for ii, r1 in enumerate(self.rows):
            r1ctx = dict(
                (n, ([v], None, t)) for (n, v, t) in zip(self._colNames, r1, self._colTypes))
            ctx = {self: r1ctx, t: tctx}
            flags, _, _ = expr._eval(ctx)
            if len(flags) == 1:
                if flags[0]:
                    rows.extend([r1[:] + row[:] for row in t.rows])
                else:
                    rows.extend([r1[:] + filler[:]])
            elif numpy.any(flags):
                rows.extend([r1[:] + t.rows[n][:] for (n, i) in enumerate(flags) if i])
            else:
                rows.extend([r1[:] + filler[:]])
            cmdlineProgress.progress(ii)

        table.rows = rows
        return table

    def _postfixValues(self):
        ""  # no autodoc ?

        """ finds postfixes 0, 1, .. in  __0, __1, ... in self._colNames
            an empty postfix "" is recognized as -1 """
        postfixes = set(getPostfix(c) for c in self._colNames)
        postfixes.discard(None)  # internal cols starting witn __
        return [-1 if p == "" else int(p[2:]) for p in postfixes]

    def maxPostfix(self):
        """ returns last postfix in sorted postfixes of column names """
        return max(self._postfixValues())

    def minPostfix(self):
        """ returns first postfix in sorted postfixes of column names """
        return min(self._postfixValues())

    def findPostfixes(self):
        """ returns postfixes of column names """
        postfixes = set(getPostfix(c) for c in self._colNames)
        postfixes.discard(None)  # internal cols starting with __
        return postfixes

    def _incrementedPostfixes(self, by):
        newColNames = []
        for c in self._colNames:
            pf = getPostfix(c)
            if pf is not None:
                val = -1 if pf == "" else int(pf[2:])
                prefix = c if pf == "" else c.split("__")[0]
                newName = prefix + "__" + str(by + val)
            newColNames.append(newName)
        return newColNames

    def _buildJoinTable(self, t):

        incrementBy = self.maxPostfix() - t.minPostfix() + 1

        colNames = self._colNames + list(t._incrementedPostfixes(incrementBy))

        colFormats = self._colFormats + t._colFormats
        colTypes = self._colTypes + t._colTypes
        title = "%s vs %s" % (self.title, t.title)
        meta = {self: self.meta.copy(), t: t.meta.copy()}
        return Table._create(colNames, colTypes, colFormats, [], title, meta)

    def print_(self, w=8, out=None, title=None):
        """
        Prints the table to the console. ``w`` is the width of the columns,
        If you want to print to a file or stream instead, you can use the ``out``
        parameter, e.g. ``t.print_(out=sys.stderr)``.
        If you support a ``title`` string this will be printed above the
        content of the table.
        """
        if out is None:
            out = sys.stdout

        ix = [i for i, f in enumerate(self._colFormats) if f is not None]

        colwidths = []
        for i in ix:
            c = self._colNames[i]
            f = self.colFormatters[i]
            values = set(map(f, self.getColumn(c).values))
            values.discard(None)
            if values:
                mw = max(len(v) for v in values if v is not None)
            else:
                mw = 1  # for "-"
            colwidths.append(max(mw, len(c), w))

        # inner method is private, else the object can not be pickled !
        def _p(vals, colwidths=colwidths, out=out):
            for v, w in zip(vals, colwidths):
                expr = "%%-%ds" % w
                v = "-" if v is None else v
                print >> out, (expr % v),

        if title is not None:
            _p(len(title) * "=")
            print >> out
            _p([title])
            print >> out
            _p(len(title) * "=")
            print >> out

        _p([self._colNames[i] for i in ix])
        print >> out
        ct = [self._colTypes[i] for i in ix]

        _p(re.match("<(type|class) '((\w|[.])+)'>|(\w+)", str(n)).groups()[1] or str(n)
           for n in ct)
        print >> out
        _p(["------"] * len(ix))
        print >> out
        fms = [self.colFormatters[i] for i in ix]
        for row in self.rows:
            ri = [row[i] for i in ix]
            _p(fmt(value) for (fmt, value) in zip(fms, ri))
            print >> out

    _print = print_   # backwards compatibility

    def renamePostfixes(self, **kw):
        """
            Renames postfixes given as key-value arguments.

            Example: ``tab.renamePostfixes(__0 = "_new")``
        """
        collected = dict()
        for postfix_old, postfix_new in kw.items():
            for c in self._colNames:
                if c.endswith(postfix_old):
                    c_new = c[:-len(postfix_old)] + postfix_new
                    if "__" in c_new:
                        raise Exception(
                            "renaming %r results in double underscore in %r" % (c, c_new))
                    collected[c] = c_new
        self.renameColumns(**collected)

    @staticmethod
    def toTable(colName, iterable, format_="", type_=None, title="", meta=None):
        """ generates a one-column table from an iterable, e.g. from a list,
            colName is name for the column.

            - if ``type_`` is not given a common type for all values is determined,
            - if ``format_`` is not given, a default format for ``type_`` is used.

            further one can provide a title and meta data
        """
        if not isinstance(colName, str):
            raise Exception("colName is not a string. The arguments of this "
                            "function changed in the past !")

        values = convert_list_to_overall_type(list(iterable))
        if type_ is None:
            type_ = common_type_for(values)
        if format_ == "":
            format_ = guessFormatFor(colName, type_) or "%r"
        if meta is None:
            meta = dict()
        else:
            meta = meta.copy()
        rows = [[v] for v in values]
        return Table([colName], [type_], [format_], rows, meta=meta)

    @staticmethod
    def loadCSV(path, sep=";", keepNone=False, **specialFormats):
        """
        loads csv file from path. column separator is given by *sep*.
        If *keepNone* is set to True, "None" strings in file are kept as a string.
        Else this string is converted to Python None values.
        *specialFormats* collects positional arguments for setting formats
        of columns.

        Example: ``Table.loadCSV("abc.csv", mz="%.3f")``

        """
        import csv
        import os.path
        import sys
        import re
        if isinstance(path, unicode):
            path = path.encode(sys.getfilesystemencoding())

        with open(path, "r") as fp:
            # remove clutter at right margin
            reader = csv.reader(fp, delimiter=sep)
            # reduce multiple spaces to single underscore
            colNames = [re.sub(" +", "_", n.strip()) for n in reader.next()]

            if keepNone:
                conv = bestConvert
            else:
                conv = lambda v: None if v == "None" else bestConvert(v)

            rows = [[conv(c.strip()) for c in row] for row in reader]

        columns = [[row[i] for row in rows] for i in range(len(colNames))]
        types = [common_type_for(col) for col in columns]

        formats = dict([(name, guessFormatFor(name, type_)) for (name, type_)
                        in zip(colNames, types)])
        formats.update(specialFormats)

        formats = [formats[n] for n in colNames]

        title = os.path.basename(path)
        meta = dict(loaded_from=os.path.abspath(path))
        return Table._create(colNames, types, formats, rows, title, meta)

    def toOpenMSFeatureMap(self):
        """
        converts table to pyopenms FeatureMap type.
        """

        self.requireColumn("mz")
        self.requireColumn("rt")

        if "feature_id" in self._colNames:
            # feature table from openms
            ti = self.splitBy("feature_id")
            # intensity, rt, mz should be the same value for each feature table:
            areas = [t0.intensity.values[0] for t0 in ti]
            rts = [t0.rt.values[0] for t0 in ti]
            mzs = [t0.mz.values[0] for t0 in ti]
        else:
            # chromatographic peak table from XCMS
            if "into" in self._colNames:
                areas = self.into.values
            elif "area" in self._colNames:
                areas = self.area.values
            else:
                print "features have no area/intensity, we assume constant intensity"
                areas = [None] * len(self)
            mzs = self.mz.values
            rts = self.rt.values

        fm = pyopenms.FeatureMap()

        for (mz, rt, area) in zip(mzs, rts, areas):
            f = pyopenms.Feature()
            f.setMZ(mz)
            f.setRT(rt)
            f.setIntensity(area if area is not None else 1000.0)
            fm.push_back(f)
        return fm

    @staticmethod
    def mergeTables(tables, reference_table=None, force_merge=False):
        """ merges tables. Eg:

            .. pycon::
            t1 = emzed.utils.toTable("a",[1])
            t2 = t1.copy()
            t1.addColumn("b", 3)
            t2.addColumn("c", 5)

            t1.print_()
            t2.print_()
            t3 = emzed.utils.mergeTables([t1, t2])
            t3.print_()

            in case of conflicting names, name orders, types or formats
            you can try ``force_merge=True`` or provide a reference
            table. This reference table just serves information about
            wanted column names, types and formats and  is merged to the result
            only if it appers in  ``tables``.

        """
        assert isinstance(tables, (list, tuple)), "need list of tables as first argument"
        if reference_table is not None:
            final_colnames = reference_table._colNames
            start_with = reference_table.buildEmptyClone()
        else:
            final_colnames, final_types, final_formats = tools._build_starttable(
                tables, force_merge)
            start_with = Table._create(final_colnames, final_types, final_formats)

        extended_tables = []
        for table in tables:
            missing_names = [c for c in final_colnames if c not in table._colNames]
            if missing_names:
                table = table.copy()
                for name in missing_names:
                    type_ = start_with.getType(name)
                    format_ = start_with.getFormat(name)
                    table.addColumn(name, None, type_, format_)
            table = table.extractColumns(*final_colnames)
            extended_tables.append(table)

        result = extended_tables[0]
        result.append(extended_tables[1:])
        return result

    def compressPeakMaps(self):
        """
        sometimes duplicate peakmaps occur as different objects in a table,
        that is: different id() but same content.
        this function removes duplicates and replaces different instances
        of the same data by one particular instance.
        """
        import hashlib

        def _compute_digest(pm):
            h = hashlib.sha512()
            for spec in pm.spectra:
                # peaks.data is binary representation of numpy array peaks:
                h.update(str(spec.peaks.data))
            return h.digest()

        from .ms_types import PeakMap
        peak_maps = dict()
        digests = dict()
        for row in self.rows:
            for cell in row:
                if isinstance(cell, PeakMap):
                    if not hasattr(cell, "_digest"):
                        d = digests.get(id(cell))
                        if d is None:
                            d = _compute_digest(cell)
                            digests[id(cell)] = d
                        cell._digest = d
                    peak_maps[cell._digest] = cell
        for row in self.rows:
            for i, cell in enumerate(row):
                if isinstance(cell, PeakMap):
                    row[i] = peak_maps[cell._digest]
        self.resetInternals()

    @staticmethod
    def _conv_nan(val):
        try:
            is_nan = np.isnan(val)  # does not work for str values etc !
            return None if is_nan else val
        except:
            return val

    def to_pandas(self):
        """ converts table to pandas DataFrame object """
        import pandas
        data = dict((name, getattr(self, name).values) for name in self.getColNames())
        return pandas.DataFrame(data, columns=self.getColNames())

    @staticmethod
    def from_pandas(df, title=None, meta=None, types=None, formats=None):
        """ creates Table from pandas DataFrame

            * ``title`` and ``meta`` are parametrs according to the consctructor of ``Table``,
                see :py:meth:`~.__init__`

            * ``types`` is a mapping of column names to python types. If this parameter misses
              types are derived automatically from the pandas column types, missing colum names
              in this mapping are handled in the same way.

              This parameter is intended for non standard or special type conversions.

            * ``formats`` is a mapping for declaring column formats. The keys can be column_names,
              python types, or a mixture of them. Types are resolved in the first place, then
              column names.

              The values of this mapping are similar to the format declarations used in
              :py:meth:`~.__init__`

              For missing declarations, or a missing formats argument the formats are guessed
              from the column types.

            Comment: type resolution is done before determining the formats, so values in the
            ``types`` dictionary may appear as keys in ``formats``.

        """
        import pandas
        assert isinstance(df, pandas.DataFrame), df
        if types is None:
            types = dict()

        col_names = df.columns.values.tolist()

        col_types = [types.get(n) for n in col_names]

        kinds_to_type = dict(i=int, f=float, O=object, V=object, U=unicode, a=str, u=int, b=bool,
                             c=complex)

        # overwrite not declared types by guessing from dtype:
        col_types = [kinds_to_type.get(dt.kind) if t is None and hasattr(dt, "kind") else t
                     for (t, dt) in zip(col_types, df.dtypes)]

        # some numpy types have no kind, as numpy.float64
        col_types = [float if t is None and float in dt.__class__.__mro__ else t
                     for (t, dt) in zip(col_types, df.dtypes)]

        col_types = [int if t is None and int in dt.__class__.__mro__ else t
                     for (t, dt) in zip(col_types, df.dtypes)]

        rows = df.as_matrix().tolist()

        rows = [map(Table._conv_nan, row) for row in rows]

        for i, t in enumerate(col_types[:]):
            if t in (object, None):
                column = [row[i] for row in rows]
                t = common_type_for(column)
                col_types[i] = t

        _formats = {int: "%d", float: "%f", str: "%s", object: None, bool: "%s"}
        if formats is not None:
            _formats.update(formats)

        # first resolfe types by name
        col_formats = [_formats.get(n) for n in col_names]
        # then by type
        col_formats = [_formats.get(t) if f is None else f
                       for (f, t) in zip(col_formats, col_types)]

        table = Table(col_names, col_types, col_formats, rows, title, meta)
        return table

    @staticmethod
    def from_numpy_array(data, col_names, col_types, col_formats, title=None, meta=None):
        """
        Creates a Table from a numpy 2dim array. Arguments are given in the same manner as
        in the Table constructor :py:meth:`~.__init__`

        numpy.nan values are converted to None values for indicating missing values.
        numpy numerical types are converted to python types.

        """
        assert isinstance(data, np.ndarray)
        assert data.ndim == 2, data.ndim
        rows = [map(Table._conv_nan, row) for row in data.tolist()]

        table = Table(col_names, col_types, col_formats, rows, title, meta)
        rows = []
        for row in table.rows[:]:
            for i, t in enumerate(col_types):
                if t in (int, float, str):
                    val = row[i]
                    if val is not None:
                        row[i] = t(val)
            rows.append(row)
        table.rows = rows
        return table
