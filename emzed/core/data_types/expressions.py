import collections
import re
import types
import warnings

import numpy as np

import col_types

__doc__ = """

Working with tables relies on so called ``Expressions``


"""


def warn(message):
    warnings.warn(message, UserWarning, stacklevel=3)


def depreciation_warning(message):
    warnings.warn(message, DeprecationWarning, stacklevel=3)


def le(a, x):
    return np.searchsorted(a, x, 'right') - 1


def ge(a, x):
    return np.searchsorted(a, x, 'left')


def lt(a, x):
    return np.searchsorted(a, x, 'left') - 1


def gt(a, x):
    return np.searchsorted(a, x, 'right')


def none_in_array(v):
    return None in v.tolist()
    return v.dtype == object


def find_nones(v):
    return v <= None  # trick !

##############################################################################
#
#  some design principles, READ FIRST:
#
#  column types int, long, float, bool are kept in np.array during _eval
#  calls with appropriate dtype if no Nones are present, else
#  dtype=object. So checking against dtype==object is the same as
#  testing if Nones are present.
#
#  other types are kept in lists.
#  TODO: eval performance for arrays with strings, dictionaries, etc...
#
#  as the dtype is not restrictive enough, _eval returns the column type
#  as python type as the last value.
#
#  Comparisons always return boolean arrays without missing values ==
#  Nones !!!! so eg comparing "<= None" is not allowed in contrast to "== None"
#
#  Logical operations always return boolean values in contrast to pythons
#  logical operations.
#
##############################################################################


_basic_num_types = [int, long, float, bool]


def is_numpy_int_type(t):
    return np.integer in t.__mro__


def is_numpy_float_type(t):
    return np.floating in t.__mro__


def is_numpy_bool_type(t):
    return np.bool_ in t.__mro__


def is_numpy_number_type(t):
    return is_numpy_int_type(t) or is_numpy_float_type(t) or is_numpy_bool_type(t)


def is_numpy_number(v):
    return is_numpy_number_type(type(v))


def numpy_to_python_number(v):
    return np.array((v,)).tolist()[0]


def common_type_for(li):

    types = set(type(x) for x in li if x is not None)

    reduced = set()

    for t in types:
        if t is None:
            reduced.add(None)
        elif is_numpy_int_type(t) or t in (int, long):
            reduced.add(int)
        elif is_numpy_float_type(t) or t is float:
            reduced.add(float)
        elif is_numpy_bool_type(t) or t is bool:
            reduced.add(bool)
        elif t is str:
            reduced.add(str)
        else:
            reduced.add(t)

    if None in reduced:
        if len(reduced) == 1:
            return None
        reduced.remove(None)

    non_std = [t for t in reduced if t not in (bool, int, float, str, long)]
    if len(non_std) > 1:
        return object
    elif len(non_std) == 1:
        return non_std[0]
    for t in (str, float, long, int, bool):
        if t in reduced:
            return t


def saveeval(expr, ctx):
    # try:
    return expr._eval(ctx)
    # except Exception, e:
    #    raise Exception("eval of %s failed: %s" % (expr, e))


def container(type_):
    if type_ in [int, long, float, bool]:
        return np.array
    if hasattr(type_, "__mro__") and np.number in type_.__mro__:
        return np.array
    return list


def cleanup(type_):
    # keeps pure python types as they are, converts
    # numpy values to their python equivalent:
    if type_ in [int, long, float, bool, str, list, dict, tuple, set, object]:
        return type_
    if hasattr(type_, "__mro__"):
        mro = type_.__mro__
        if np.number in mro:
            if np.bool_ in mro:
                return bool
            if np.integer in mro:
                return int
            if np.floating in mro:
                return float
        if basestring in mro:
            return str
    return type_


def common_type(t1, t2):
    if t1 == t2:
        return t1

    if t1 in _basic_num_types and t2 in _basic_num_types:
        if t1 == float or t2 == float:
            return float
        if t1 == long or t2 == long:
            return long
        if t1 == int or t2 == int:
            return int
        return bool

    return object


class Lookup(object):

    def __init__(self, values, abs_tol=None, rel_tol=None):
        if abs_tol is not None:
            assert abs_tol > 0.0
        if rel_tol is not None:
            assert rel_tol > 0.0
        if abs_tol is not None and abs_tol > 0.0:
            self.__class__ = FuzzyAbsoluteLookup
            # now __init__ depends on class we set before !
            self.__init__(values, abs_tol)
        elif rel_tol is not None and rel_tol > 0.0:
            self.__class__ = FuzzyRelativeLookup
            # now __init__ depends on class we set before !
            self.__init__(values, rel_tol)
        else:
            self.__class__ = ExactLookup
            # now __init__ depends on class we set before !
            self.__init__(values)

    def find(self, value):
        pass


class ExactLookup(Lookup):

    def __init__(self, values):
        if not isinstance(values, list):
            values = list(values)
        self.values = values
        self.index = collections.defaultdict(list)
        for (i, v) in enumerate(values):
            self.index[v].append(i)

    def find(self, value):
        return self.index.get(value, [])


class _FuzzyLookup(Lookup):

    def __init__(self, values, tol):
        if not isinstance(values, list):
            values = list(values)
        self.values = values
        self.index = collections.defaultdict(list)
        self.tol = tol
        for (i, v) in enumerate(values):
            if v is not None:
                k = self._bin(v)
                self.index[k].append((v, i))

    def find(self, value):
        if value is None:
            return []
        k = self._bin(value)
        candidates = self.index.get(k - 1, []) + self.index.get(k, []) + self.index.get(k + 1, [])
        result = []
        for value_i, i in candidates:
            if self._fit(value, value_i):
                result.append(i)
        return result


class FuzzyAbsoluteLookup(_FuzzyLookup):

    def _bin(self, value):
        try:
            return int(value / self.tol)
        except TypeError:
            raise TypeError("computing fraction  %s by %s failed" % (value, self.tol))

    def _fit(self, reference, other):
        try:
            return abs(reference - other) <= self.tol
        except TypeError:
            raise TypeError("computing absolute distance of %s and %s failed" % (refernce, other))


class FuzzyRelativeLookup(_FuzzyLookup):

    def __init__(self, values, tol):
        self.abs_tol = max(values) * tol
        _FuzzyLookup.__init__(self, values, tol)

    def _bin(self, value):
        try:
            return int(value / self.abs_tol)
        except TypeError:
            raise TypeError("computing fraction %s by %s failed" % (value, self.abs_tol))

    def _fit(self, reference, other):
        if reference == 0.0:
            return other == reference
        try:
            return abs(other - reference) / reference <= self.tol
        except TypeError:
            raise TypeError("computing relative distance of %s and %s failed" % (refernce, other))



class BaseExpression(object):

    """
    BaseClass for Expressions. For two Expressions ``t1`` and ``t2``
    this class generates new Expressions as follows:

    * Comparison Operators:

     *  ``t1 <= t2``
     *  ``t1 < t2``
     *  ``t1 >= t2``
     *  ``t1 > t2``
     *  ``t1 == t2``
     *  ``t1 != t2``

    * Algebraic Operators:

      *  ``t1 + t2``
      *  ``t1 - t2``
      *  ``t1 * t2``
      *  ``t1 > t2``

    * Logic Operators:

      *  ``t1 & t2``
      *  ``t1 | t2``
      *  ``t1 ^  t2``
      *  ``~t1``

      .. note::

          Due to some Python internals, these operators have a low precedence,
          so you have to use parentheses like ``(t1 <= t2) & (t1 > t3)```

    """

    def __init__(self, left, right):
        if not isinstance(left, BaseExpression):
            left = Value(left)
        if not isinstance(right, BaseExpression):
            right = Value(right)
        self.left = left
        self.right = right

    def _evalsize(self, ctx=None):
        # size of result when _eval is called:
        sl = self.left._evalsize(ctx)
        sr = self.right._evalsize(ctx)
        if sl == 1:  # numpy and list coercing
            return sr
        if sr == 1:  # numpy and list coercing
            return sl
        if sr == sl:
            return sl
        raise Exception("column lengths %d and %d do not fit" % (sl, sr))

    def __nonzero__(self):
        """ this one raises and exception if "and" or "or" are used to
            build expressions.
            "and" and "or" can not be used as there are no methods
            to overload these. Combining expressions this way always
            results in a call to this method to determine their
            equivalent "boolean value".

        """
        raise Exception("can not convert %s to boolean value" % self)

    def __str__(self):
        return "(%s %s %s)" % (self.left, self.symbol, self.right)

    def __ge__(self, other):
        return GeExpression(self, other)

    def __gt__(self, other):
        return GtExpression(self, other)

    def __le__(self, other):
        return LeExpression(self, other)

    def __lt__(self, other):
        return LtExpression(self, other)

    def __eq__(self, other):
        return EqExpression(self, other)

    def __ne__(self, other):
        return NeExpression(self, other)

    def __add__(self, other):
        return BinaryExpression(self, other, lambda a, b: a + b, "+", None)

    def __radd__(self, other):
        return BinaryExpression(other, self, lambda a, b: a + b, "+", None)

    def __sub__(self, other):
        return BinaryExpression(self, other, lambda a, b: a - b, "-", None)

    def __rsub__(self, other):
        return BinaryExpression(other, self, lambda a, b: a - b, "-", None)

    def __mul__(self, other):
        return BinaryExpression(self, other, lambda a, b: a * b, "*", None)

    def __rmul__(self, other):
        return BinaryExpression(other, self, lambda a, b: a * b, "*", None)

    def __div__(self, other):
        return BinaryExpression(self, other, lambda a, b: a / b, "/", None)

    def __rdiv__(self, other):
        return BinaryExpression(other, self,  lambda a, b: a / b, "/", None)

    def __and__(self, other):
        return AndExpression(self, other)

    def __rand__(self, other):
        raise NotImplementedError("not implemented, causes non predictable evaluation order")

    def __ror__(self, other):
        raise NotImplementedError("not implemented, causes non predictable evaluation order")

    def __rxor__(self, other):
        raise NotImplementedError("not implemented, causes non predictable evaluation order")

    def __or__(self, other):
        return OrExpression(self, other)

    def __xor__(self, other):
        return XorExpression(self, other)

    def __invert__(self):
        return FunctionExpression(lambda a: not a, "not", self, bool)

    def _neededColumns(self):
        lc = self.left._neededColumns()
        if hasattr(self, "right"):
            return lc + self.right._neededColumns()
        return lc

    def equals(self, other, abs_tol=None, rel_tol=None):
        """fast comparison for equality, maybe with some numerical tolerance.

        For example::

               tn = t.join(t2, t.mz.equals(t2.mz, rel_tol=5e-6) & t.rt.equals(t2.rt, abs_tol=30))

        **Attention**: This operation only works if the first arg of the join (here ``t2``)
        appears as the table in the first argument (here ``t2.mz``) of ``equals``. Else an
        exception will be thrown !
        """
        assert abs_tol is None or rel_tol is None
        if abs_tol is not None:
            assert abs_tol >= 0.0
        if rel_tol is not None:
            assert rel_tol >= 0.0

        lookup = Lookup(other, abs_tol, rel_tol)
        return FastEqualExpression(self, lookup)

    def startswith(self, other):
        """
        For two string valued expressions ``a`` and ``b`` the expression
        ``a.startswith(b)``
        evaluates if the string ``a`` starts with the string
        ``b``. The latter might be a fixed string, as ``tab.mf.startswith("H2")``

        """

        return BinaryExpression(self, other, lambda a, b: a.startswith(b),
                                "%s.startswith(%s)", bool)

    def contains(self, other):
        """
        ``a.contains(b)`` tests if ``b in a``.
        """
        return BinaryExpression(self, other, lambda a, b: b in a,
                                "%s.contains(%s)", bool)

    def containsElement(self, element):
        """
        For a string valued expression ``a`` which represents a
        molecular formula the expressions ``a.containsElement(element)``
        tests if the given ``element`` is contained in ``a``.

        Example:  ``tab.mf.containsElement("Na")``
        """
        return BinaryExpression(self, element,
                                lambda a, b: b in re.findall("([A-Z][a-z]?)\d*", a),
                                "%s.containsElement(%s)", bool)

    def containsOnlyElements(self, elements):
        """
        ``elements`` is either a list of strings where each item
        is a chemical symbol, or a string composed of such symbols.
        """

        def match(mf, elements):
            if isinstance(elements, basestring):
                elements = re.findall("([A-Z][a-z]?)", elements)
            elements = set(elements)
            elements_in_mf = set(re.findall("([A-Z][a-z]?)\d*", mf))
            return elements_in_mf <= elements
        return BinaryExpression(self, elements, match, "%s.containsOnlyElements(%s)", bool)

    def isIn(self, li):
        """
        ``a.isIn(li)`` tests if the value of ``a`` is contained in a
        list ``li``.

        Example: ``tab.id.isIn([1,2,3])``

        """
        return FunctionExpression(lambda a, b=li: a in b, "%%s.isIn(%s)" % list(li),
                                  self, bool)

    def inRange(self, minv, maxv):
        """
        ``a.inRange(low, up)`` tests if ``low <= a <= up``.

        Example: ``tab.rt.inRange(60, 120)``
        """

        return (self >= minv) & (self <= maxv)

    def approxEqual(self, what, tol):
        """

        ``a.approxEqual(b, tol)`` tests if ``|a-b| <= tol``.

        Example: ``tab.mz.approxEqual(meatbolites.mz, 0.001)``
        """
        depreciation_warning("you better may use .equals instead of .approxEqual !")
        return self.inRange(what - tol, what + tol)

    def thenElse(self, then, else_):
        """
        ``a.thenElse(b, c)`` evaluates to ``b`` if ``a`` is *True*, if not it
        evaluates to ``c``.
        """

        return IfThenElse(self, then, else_)

    def ifNotNoneElse(self, other):
        """
        ``a.ifNotNoneElse(b)`` evaluates to ``a`` if a is not *None*, else
        it evaluates to ``b``.

        Example: ``t.rt.replaceColumn("rt", rt.ifNotNoneElse(t.rt_default))``

        """
        return (self.isNotNone()).thenElse(self, other)

    def isNotNone(self):
        """
        This expression returns `False` for `None` values which indicate "missing value"
        """
        return IsNotNoneExpression(self)

    def isNone(self):
        """
        This expression returns `True` for `None` values which indicate "missing value"
        """
        return IsNoneExpression(self)

    def pow(self, exp):
        """
        ``a.pow(b)`` evaluates to ``a**b``.

        Example: ``tab.rmse.pow(2)``
        """
        return self.apply(lambda v, exp=exp: v ** exp)

    def apply(self, fun, filter_nones=True):
        """
        t.apply(*fun*) results in an expression which applies *fun* to the
        values in t if evaluated.

        Example::  ``tab.addColumn("amplitude", tab.time.apply(sin))``

        As None values indicate "unknown" value, the function is applied only to not None
        values in the columns, unless you specify *filter_nones=False*.

        """
        return FunctionExpression(fun, str(fun), self, None, filter_nones)

    def loadFileFromPath(self, type_=None):
        """
        inserts Blob column by reading files from paths listed in given column.
        """
        cache = dict()

        def read_from(p):
            if p not in cache:
                with open(p, "rb") as fp:
                    data = fp.read()
                cache[p] = col_types.Blob(data, type_)
            return cache[p]

        return FunctionExpression(read_from, "loadFileFromPath", self, col_types.Blob)

    def aggregate(self, efun, res_type=None, ignore_none=True, default_empty=None):
        """
        creates aggregate expression for aggregation function *efun*
        """
        return AggregateExpression(self, efun, "aggregate", res_type, ignore_none, default_empty)

    @property
    def min(self):
        """
        This is an **aggregation expression** which evaluates an
        expression to its minimal value.

        Example: ``tab.rt.min``
        """
        return AggregateExpression(self, lambda v: min(v), "min(%s)", None)

    @property
    def allTrue(self):
        """
        This is an **aggregation expression** which evaluates an
        expression to true if all values "represent" true.

        Example: ``tab.rt.allTrue``
        """
        return AggregateExpression(self,
                                   lambda v: all(v), "allTrue(%s)",
                                   None,
                                   ignore_none=False,
                                   default_empty=True)

    @property
    def anyTrue(self):
        """
        This is an **aggregation expression** which evaluates an
        expression to true if any value "represent" true.

        Example: ``tab.rt.anyTrue``
        """
        return AggregateExpression(self, lambda v: any(v), "anyTrue(%s)", None,
                                   ignore_none=False, default_empty=False)

    @property
    def allFalse(self):
        """
        This is an **aggregation expression** which evaluates an
        expression to true if all values "represent" false.

        Example: ``tab.rt.allFalse``
        """
        def test(values):
            if not values:
                return True
            return all(vi is not None and bool(vi) is False for vi in values)
        return AggregateExpression(self,
                                   test,
                                   None,
                                   ignore_none=False,
                                   default_empty=True)

    @property
    def allNone(self):
        """
        This is an **aggregation expression** which evaluates an
        expression to true if all values are Nones

        Example: ``tab.rt.allNone``
        """
        return AggregateExpression(self,
                                   lambda v: all(vi is None for vi in v), "allNone(%s)",
                                   None,
                                   ignore_none=False,
                                   default_empty=True)

    @property
    def anyNone(self):
        """
        This is an **aggregation expression** which evaluates an
        expression to true if at least one value is None.

        Example: ``tab.rt.anyNone``
        """
        return AggregateExpression(self,
                                   lambda v: any(vi is None for vi in v), "anyNone(%s)",
                                   None,
                                   ignore_none=False,
                                   default_empty=False)

    @property
    def anyFalse(self):
        """
        This is an **aggregation expression** which evaluates an
        expression to true if any values "represent" false.

        Example: ``tab.rt.anyTrue``
        """
        return AggregateExpression(self,
                                   lambda v: any(vi is not None and not vi for vi in v),
                                   "anyFalse(%s)",
                                   None,
                                   ignore_none=False,
                                   default_empty=False)

    @property
    def max(self):
        """
        This is an **aggregation expression** which evaluates an
        expression to its maximal value.

        Example: ``tab.rt.max``
        """
        return AggregateExpression(self, lambda v: max(v), "max(%s)", None)

    @property
    def sum(self):
        """
        This is an **aggregation expression** which evaluates an
        expression to its sum.

        Example: ``tab.area.sum``

        """
        return AggregateExpression(self, lambda v: sum(v), "sum(%s)", None)

    @property
    def mean(self):
        """
        This is an **aggregation expression** which evaluates an
        expression to its mean.

        Example: ``tab.area.mean``
        """
        return AggregateExpression(self, lambda v: np.mean(v).tolist(), "mean(%s)", float)

    @property
    def median(self):
        """
        This is an **aggregation expression** which evaluates an
        expression to its mean.

        Example: ``tab.area.mean``
        """
        return AggregateExpression(self, lambda v: np.median(v).tolist(), "mean(%s)", float)

    @property
    def std(self):
        """
        This is an **aggregation expression** which evaluates an
        expression to its standard deviation.

        Example: ``tab.area.std``
        """
        return AggregateExpression(self, lambda v: np.std(v).tolist(), "stddev(%s)", float)

    @property
    def len(self):
        """
        **This expression is depreciated**. Please use
        :py:meth:`~emzed.core.data_types.expressions.BaseExpression.count`
        instead.
        """
        return AggregateExpression(self, lambda v: len(v), "len(%s)",
                                   int, ignore_none=False, default_empty=0)

    @property
    def count(self):
        """
        This is an **aggregation expression** which evaluates an column expression to the number of
        values in the column.

        Example: ``tab.id.len``

        replaces ``len` expression.
        """
        return AggregateExpression(self, lambda v: len(v), "count(%s)",
                                   int, ignore_none=False, default_empty=0)

    @property
    def count_different(self):
        """
        This is an **aggregation expression** which evaluates an
        column expression to the number of different values in the column.

        Example:: ``tab.id.len``
        """
        return AggregateExpression(self, lambda v: len(set(v)), "count_different(%s)",
                                   int, ignore_none=False, default_empty=0)

    @property
    def countNone(self):
        """
        This is an **aggregation expression** which evaluates an
        Column expression to the number of None values in it.
        """
        return AggregateExpression(self,
                                   lambda v: sum(1 for vi in v if vi is None),
                                   "countNone(%s)", int, ignore_none=False,
                                   default_empty=0)

    @property
    def countNotNone(self):
        """
        This is an **aggregation expression** which evaluates an
        Column expression to the number of values != None in it.
        """
        return AggregateExpression(self,
                                   lambda v: sum(1 for vi in v if vi is not None),
                                   "countNotNone(%s)", int, ignore_none=False,
                                   default_empty=0)

    @property
    def hasNone(self):
        """
        This is an **aggregation expression** which evaluates an Column
        expression to *True* if and only if the column contains a *None*
        value.
        """
        return AggregateExpression(self, lambda v: int(None in v),
                                   "hasNone(%s)", bool, ignore_none=False,
                                   default_empty=0)

    @property
    def uniqueNotNone(self):
        """
        This is an **aggregation expression**. If applied to an
        expression ``t`` ``t.uniqueNotNone`` evaluates to ``v`` if ``t``
        only contains two values ``v`` and ``None``.  Else it raises an
        Exception.

        Example: ``tab.peakmap.uniqueNotNone``
        """
        def select(values):

            diff = set(v for v in values if v is not None)
            if len(diff) == 0:
                raise Exception("only None values in %s" % self)
            if len(diff) > 1:
                raise Exception("more than one not-None value in %s: %s" % (self, sorted(diff)))
            return diff.pop()
        return AggregateExpression(self, select, "uniqueNotNone(%s)",
                                   None, ignore_none=False)

    @property
    def values(self):
        values, _, t = self._eval(None)
        if len(values) and t in _basic_num_types:
            return tuple(values.tolist())
        return tuple(values)

    def __iter__(self):
        return iter(self.values)

    def __getitem__(self, what):
        """delegate index access and slicing"""
        return self.values[what]

    def uniqueValue(self, up_to_digits=None):

        values = self.values
        if up_to_digits is not None:
            try:
                values = [round(v, up_to_digits) if v is not None else v
                          for v in values]
            except:
                raise Exception("round to %d digits not possible" % up_to_digits)

        # working with a set would be easier, but we get problems if
        # there are unhashable objects in 'values', eg a dict...
        # so we resort to itertools.groupby:
        import itertools
        values = [k for k, v in itertools.groupby(sorted(values))]
        if len(values) != 1:
            raise Exception("not one unique value in %s, got %d values" % (self, len(values)))
        return values.pop()

    def value(self):
        values, _, t = self._eval(None)
        if len(values) and t in _basic_num_types:
            return values.tolist()
        return values

    def toTable(self, colName, fmt=None, type_=None, title="", meta=None):
        """
        Generates a one column :py:class:`~emzed.core.data_types.table.Table`
        from an expression.

        Example: ``tab = substances.name.toTable()``
        """
        from .table import Table
        return Table.toTable(colName, self.values, fmt, type_, title, meta)

    def callMethod(self, name, args=()):
        """
        calls method named ``name`` on values of given column or expression result.
        ``args`` can be used to pass parameters to the method call.

        .. pycon::
            import emzed
            t = emzed.utils.toTable("a", ("1", "23"))
            t.addColumn("l", t.a.callMethod("__len__"), type_=int)
            t.addColumn("x", t.a.callMethod("startswith", ("1",)), type_=bool)
            print t
        """

        results = []
        for v in self.values:
            if v is None:
                result = None
            else:
                try:
                    att = getattr(v, name)
                    result = att(*args)
                except Exception, e:
                    args = ", ".join([str(ai) for ai in args])
                    message = "calling %s(%s) raised error %s" % (name, args, str(e))
                    raise e.__class__, message
            results.append(result)
        return ColumnByValuesExpression(results)


class CompExpression(BaseExpression):

    # comparing to None is allowed by default, but is overridden in some
    # subclasses,
    # as eg  None <= x or None >=x give hard to predict results  and  is
    # very error prone:

    def _eval(self, ctx=None):
        lhs, ixl, tl = saveeval(self.left, ctx)
        rhs, ixr, tr = saveeval(self.right, ctx)

        assert len(lhs) <= 1 or len(rhs) <= 1 or len(lhs) == len(rhs),\
            "column lengths do not fit"

        if len(lhs) == 0:
            return np.zeros((0,), dtype=np.bool), None, bool

        if len(rhs) == 0:
            return np.zeros((0,), dtype=np.bool), None, bool

        if tl in _basic_num_types and tr in _basic_num_types:
            if ixl != None and len(rhs) == 1:
                result = self.fastcomp(lhs, rhs[0])
                # "None in lhs" does not work !
                if none_in_array(lhs):
                    result[lhs == None] = None
                return result, None, bool
            if ixr != None and len(lhs) == 1:
                result = self.rfastcomp(lhs[0], rhs)
                if none_in_array(lhs):
                    result[rhs == None] = None
                return result, None, bool
            if len(lhs) == 1:
                lhs = np.tile(lhs, len(rhs))
            elif len(rhs) == 1:
                rhs = np.tile(rhs, len(lhs))
            return self.numericcomp(lhs, rhs), None, bool

        if len(lhs) == 1:
            l = lhs[0]
            if l is None:
                values = [None] * len(rhs)
            else:
                values = [None if r is None else self.comparator(l, r) for r in rhs]

        elif len(rhs) == 1:
            r = rhs[0]
            if r is None:
                values = [None] * len(lhs)
            else:
                values = [None if l is None else self.comparator(l, r) for l in lhs]
        else:
            values = [None if l is None or r is None else self.comparator(
                l, r) for (l, r) in zip(lhs, rhs)]

        if tl is object or tr is object:
            if any(isinstance(v, np.ndarray) for v in values):
                values = [np.all(v) for v in values]
        return np.array(values, dtype=np.bool), None, bool

    def numericcomp(self, lvals, rvals):
        assert len(lvals) == len(rvals)
        # default impl: comparing to None is not poissble:
        l_nones, r_nones = None, None
        if none_in_array(lvals):
            l_nones = find_nones(lvals)
        if none_in_array(rvals):
            r_nones = find_nones(rvals)
        result = self.comparator(lvals, rvals).astype(object)
        if l_nones is not None:
            result[l_nones] = None
        if r_nones is not None:
            result[r_nones] = None
        return result  # .astype(bool)


def Range(start, end, len):
    rv = np.zeros((len,), dtype=np.bool)
    rv[start:end] = True
    return rv


class LtExpression(CompExpression):

    symbol = "<"
    comparator = lambda self, a, b: a < b

    def fastcomp(self, vec, refval):
        i0 = lt(vec, refval)
        return Range(0, i0 + 1, len(vec))

    def rfastcomp(self, refval, vec):
        # refval < vec
        i0 = gt(vec, refval)
        return Range(i0, len(vec), len(vec))


class GtExpression(CompExpression):

    symbol = ">"
    comparator = lambda self, a, b: a > b

    def fastcomp(self, vec, refval):
        # ix not used, we know that vec is sorted
        i0 = gt(vec, refval)
        return Range(i0, len(vec), len(vec))

    def rfastcomp(self, refval, vec):
        # refval > vec
        i0 = lt(vec, refval)
        return Range(0, i0 + 1, len(vec))


class LeExpression(CompExpression):

    symbol = "<="
    comparator = lambda self, a, b: a <= b

    def fastcomp(self, vec, refval):
        # ix not used, we know that vec is sorted
        i0 = le(vec, refval)
        return Range(0, i0 + 1, len(vec))

    def rfastcomp(self, refval, vec):
        # refval < vec
        i0 = ge(vec, refval)
        return Range(i0, len(vec), len(vec))


class GeExpression(CompExpression):

    symbol = ">="
    comparator = lambda self, a, b: a >= b

    def fastcomp(self, vec, refval):
        i0 = ge(vec, refval)
        return Range(i0, len(vec), len(vec))

    def rfastcomp(self, refval, vec):
        # refval < vec
        i0 = le(vec, refval)
        return Range(0, i0 + 1, len(vec))


class NeExpression(CompExpression):

    symbol = "!="
    comparator = lambda self, a, b: a != b

    def fastcomp(self, vec, refval):
        i0 = ge(vec, refval)
        i1 = le(vec, refval)
        return ~Range(i0, i1 + 1, len(vec))

    def rfastcomp(self, refval, vec):
        # refval < vec
        i0 = le(vec, refval)
        i1 = ge(vec, refval)
        return ~Range(i1, i0 + 1, len(vec))


class EqExpression(CompExpression):

    symbol = "=="
    comparator = lambda self, a, b: a == b

    def fastcomp(self, vec, refval):
        i0 = ge(vec, refval)
        i1 = le(vec, refval)
        return Range(i0, i1 + 1, len(vec))

    def rfastcomp(self, refval, vec):
        # refval < vec
        i0 = le(vec, refval)
        i1 = ge(vec, refval)
        return Range(i1, i0 + 1, len(vec))


class FastEqualExpression(BaseExpression):

    def __init__(self, left, lookup):
        self.lookup = lookup
        self.left = left

    def _eval(self, ctx=None):
        lvals, idxl, tl = saveeval(self.left, ctx)
        if len(lvals) > 1:
            msg = """
            your join/leftJoin/... uses .equals not as intended.  This operation only works if
            the first arg of the join appears as the table in the first argument of ``equals``.
            Have a look at the doc of `.equals` for an example."""
            msg = "\n".join([l.lstrip() for l in msg.split("\n")])
            raise Exception(msg)

        val = lvals[0]
        if val is None:
            return [False] * len(self.lookup.values), None, bool
        matching_row_idx = set(self.lookup.find(val))
        values = [m in matching_row_idx for m in xrange(len(self.lookup.values))]
        return values, None, bool

    def __and__(self, other):
        return FastAndExpression(self, other)

    def __or__(self, other):
        return FastOrExpression(self, other)


class FastAndExpression(BaseExpression):

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def _eval(self, ctx=None):
        lvals, idxl, tl = saveeval(self.left, ctx)
        rvals, idxl, tl = saveeval(self.right, ctx)
        result = [l and r for l, r in zip(lvals, rvals)]
        return result, None, bool


class FastOrExpression(BaseExpression):

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def _eval(self, ctx=None):
        lvals, idxl, tl = saveeval(self.left, ctx)
        rvals, idxl, tl = saveeval(self.right, ctx)
        result = [l or r for l, r in zip(lvals, rvals)]
        return result, None, bool


class BinaryExpression(BaseExpression):

    def __init__(self, left, right, efun, symbol, res_type):
        super(BinaryExpression, self).__init__(left, right)
        self.efun = efun
        self.symbol = symbol
        self.res_type = res_type

    def _eval(self, ctx=None):
        lvals, idxl, tl = saveeval(self.left, ctx)
        rvals, idxr, tr = saveeval(self.right, ctx)

        ll = len(lvals)
        lr = len(rvals)

        ct = self.res_type or common_type(tl, tr)

        if ll == 0 and lr == 0:
            return container(ct)([]), None, ct

        assert ll == 1 or lr == 1 or ll == lr,\
            "can not cast sizes %d and %d" % (ll, lr)

        if tl in _basic_num_types and tr in _basic_num_types:
            idx = None
            if ll == 1:
                if self.symbol in "+-":
                    idx = idxr
                elif self.symbol in "*/" and lvals[0] > 0:
                    idx = idxr
            if lr == 1:
                if self.symbol in "+-":
                    idx = idxl
                elif self.symbol in "*/" and rvals[0] > 0:
                    idx = idxl

            # problem is that numpy int division 0 / 0 is 0 not nan or inf as for floats
            # so just checking the result for nans or infs and converting them to None
            # does not work in general. so we have a particular check here:
            by_zero = None
            if self.symbol == "/":
                if lr > 1:
                    by_zero = np.where(rvals == 0)
                else:
                    if rvals[0] == 0:
                        by_zero = np.arange(ll)

            if none_in_array(lvals) or none_in_array(rvals):
                nones = find_nones(lvals) | find_nones(rvals)
                lfiltered = np.where(nones, 1, lvals)
                rfiltered = np.where(nones, 1, rvals)
                res = self.efun(lfiltered, rfiltered)
            else:
                nones = None
                res = self.efun(lvals, rvals)

            res = res.astype(ct)  # downcast: 2/3 -> 0 for int

            if nones is not None:
                res = res.astype(object)  # allows None values
                res[nones] = None

            if by_zero is not None:
                res = res.astype(object)  # allows None values
                res[by_zero] = None

            return res, idx, ct

        if ll == 1:
            if lvals[0] is None:
                values = [None] * len(rvals)
            else:
                values = [self.efun(lvals[0], r) if r is not None else None for r in rvals]
        elif lr == 1:
            if rvals[0] is None:
                values = [None] * len(lvals)
            else:
                values = [self.efun(l, rvals[0]) if l is not None else l for l in lvals]
        else:
            values = [self.efun(l, r) if l is not None and r is not None else None
                      for (l, r) in zip(lvals, rvals)]

        return container(ct)(values), None, ct


class GroupedAggregateExpression(BaseExpression):

    def __init__(self, left, efun, default_empty, ignore_none, group_by_columns):
        self.left = left
        self.efun = efun
        self.default_empty = default_empty
        self.ignore_none = ignore_none
        self.group_by_columns = group_by_columns

    def _evalsize(self, ctx=None):
        return self.left._evalsize(ctx)

    def _eval(self, ctx=None):
        child_values, __, child_type = saveeval(self.left, ctx)

        group_values = []
        for group_by_column in self.group_by_columns:
            values, __, group_type = saveeval(group_by_column, ctx)
            group_values.append(values)

        group_values = zip(*group_values)

        grouped_values = collections.defaultdict(list)
        for (g, v) in zip(group_values, child_values):
            grouped_values[g].append(v)

        aggregated_values = dict()
        for g, values in grouped_values.items():
            if self.ignore_none:
                values = [v for v in values if v is not None]
            if not len(values):
                aggregated_values[g] = self.default_empty
            elif any(gi is None for gi in g):
                aggregated_values[g] = None
            else:
                type_ = common_type_for(values)
                values = np.array(values)
                aggregated_values[g] = self.efun(values)

        result = [aggregated_values[g] for g in group_values]
        type_ = common_type_for(result)
        result = container(type_)(result)
        type_ = cleanup(type_)
        return np.array(result), None, type_


class AggregateExpression(BaseExpression):

    def __init__(self, left, efun, funname, res_type=None, ignore_none=True, default_empty=None):
        if not isinstance(left, BaseExpression):
            left = Value(left)
        self.left = left
        self.efun = efun
        self.funname = funname
        self.res_type = res_type
        self.ignore_none = ignore_none
        self.default_empty = default_empty

    def group_by(self, *group_by_columns):
        return GroupedAggregateExpression(self.left, self.efun, self.default_empty,
                                          self.ignore_none, group_by_columns)

    def __call__(self):
        values, _, type_ = self._eval()
        if len(values):
            rv = values[0]
            result = type_(rv)
            if is_numpy_number(result):
                return numpy_to_python_number(result)
            return result
        return self.default_empty

    def _eval(self, ctx=None):
        vals, _, type_ = saveeval(self.left, ctx)
        if len(vals) == 0:
            return [], self.default_empty, type_

        if type_ in _basic_num_types:
            vals = vals.tolist()
        if self.ignore_none:
            vals = [v for v in vals if v is not None]

        if len(vals):
            agg_value = self.efun(vals)
            result = container(type(agg_value))([agg_value] * len(vals))
            type_ = self.res_type or cleanup(type(result[0]))
            return result, None, type_

        type_ = self.res_type or type_
        if type_ in _basic_num_types:
            return np.array((self.default_empty,),).repeat(len(vals)), None, type_

        return [self.default_empty] * len(vals), None, type_

    def __str__(self):
        return self.funname % self.left

    def _evalsize(self, ctx=None):
        return self.left._evalsize(ctx)


class LogicExpression(BaseExpression):

    def __init__(self, left, right):
        super(LogicExpression, self).__init__(left, right)
        if right.__class__ == Value and type(right.value) != bool:
            print "warning: parenthesis for logic op set ?"

    def _eval(self, ctx=None):
        op = lambda a, b: self.operation_table[a, b]
        lhs, _, tlhs = saveeval(self.left, ctx)
        rhs, _, trhs = saveeval(self.right, ctx)
        if len(lhs) == 1:
            return np.array([op(lhs[0], r) for r in rhs], dtype=object), None, bool
        elif len(rhs) == 1:
            return np.array([op(l, rhs[0]) for l in lhs], dtype=object), None, bool

        if len(lhs) != len(rhs):
            raise Exception("operands for or-operation have different length %s and %s"
                            % (len(lhs), len(rhs)))
        return np.array([op(l, r) for (l, r) in zip(lhs, rhs)], dtype=object), None, bool


class AndExpression(LogicExpression):

    symbol = "&"

    operation_table = {
        (True, True): True,
        (True, False): False,
        (True, None): None,

        (False, True): False,
        (False, False): False,
        (False, None): False,

        (None, True): None,
        (None, False): False,
        (None, None): None,
    }


class OrExpression(LogicExpression):

    symbol = "|"

    operation_table = {
        (True, True): True,
        (True, False): True,
        (True, None): True,

        (False, True): True,
        (False, False): False,
        (False, None): None,

        (None, True): True,
        (None, False): None,
        (None, None): None,
    }


class XorExpression(LogicExpression):

    symbol = "^"

    operation_table = {
        (True, True): False,
        (True, False): True,
        (True, None): None,

        (False, True): True,
        (False, False): False,
        (False, None): None,

        (None, True): None,
        (None, False): None,
        (None, None): None,
    }


class Value(BaseExpression):

    def __init__(self, value):
        self.value = value

    def _eval(self, ctx=None):
        tt = cleanup(type(self.value))
        return container(tt)([self.value]), None, tt

    def __str__(self):
        return repr(self.value)

    def _evalsize(self, ctx=None):
        return 1

    def _neededColumns(self):
        return []


class IsNotNoneExpression(BaseExpression):

    def __init__(self, child):
        if not isinstance(child, BaseExpression):
            child = Value(child)
        self.child = child

    def _eval(self, ctx=None):
        values, index, type_ = saveeval(self.child, ctx)
        # the second expressions is true if values contains no Nones,
        # so we can apply ufucns/vecorized funs
        return np.array([v is not None for v in values]), None, bool

    def __str__(self):
        return "IsNotNone(%s)" % self.child

    def _evalsize(self, ctx=None):
        return self.child._evalsize(ctx)

    def _neededColumns(self):
        return self.child._neededColumns()


class IsNoneExpression(BaseExpression):

    def __init__(self, child):
        if not isinstance(child, BaseExpression):
            child = Value(child)
        self.child = child

    def _eval(self, ctx=None):
        values, index, type_ = saveeval(self.child, ctx)
        # the second expressions is true if values contains no Nones,
        # so we can apply ufucns/vecorized funs
        return np.array([v is None for v in values]), None, bool

    def __str__(self):
        return "IsNone(%s)" % self.child

    def _evalsize(self, ctx=None):
        return self.child._evalsize(ctx)

    def _neededColumns(self):
        return self.child._neededColumns()


class FunctionExpression(BaseExpression):

    def __init__(self, efun, efunname, child, res_type, filter_nones=True):
        if not isinstance(child, BaseExpression):
            child = Value(child)
        self.child = child
        self.efun = efun
        self.efunname = efunname
        self.res_type = res_type
        self.filter_nones = filter_nones

    def _eval(self, ctx=None):
        values, index, type_ = saveeval(self.child, ctx)
        # the second expressions is true if values contains no Nones,
        # so we can apply ufucns/vecorized funs
        if len(values) == 0:
            return [], None, self.res_type or None
        if type(values) == np.ndarray and not none_in_array(values):
            if type(self.efun) == np.ufunc:
                values = self.efun(values)
            else:
                values = [self.efun(v) for v in values]
                types = set(type(f) for f in values if f is not None)
                if None in types:
                    types.remove(None)
                if len(types) > 1:
                    raise Exception("no unique return type in function result: %r" % types)
                if types:
                    type_ = types.pop()
                else:
                    type_ = object
                if cleanup(type_) in _basic_num_types:
                    values = np.array(values)
                    return values, None, cleanup(type_)

            return values, None, common_type_for(values)

        if self.filter_nones:
            new_values = [self.efun(v) if v is not None else None for v in values]
        else:
            new_values = [self.efun(v) for v in values]
        type_ = self.res_type or common_type_for(new_values)
        if type_ in _basic_num_types:
            new_values = np.array(new_values)

        return new_values, None, type_

    def __str__(self):
        return "%s(%s)" % (self.efunname, self.child)

    def _evalsize(self, ctx=None):
        return self.child._evalsize(ctx)

    def _neededColumns(self):
        return self.child._neededColumns()


class IfThenElse(BaseExpression):

    def __init__(self, e1, e2, e3):
        if not isinstance(e1, BaseExpression):
            e1 = Value(e1)
        if not isinstance(e2, BaseExpression):
            e2 = Value(e2)
        if not isinstance(e3, BaseExpression):
            e3 = Value(e3)
        self.e1 = e1
        self.e2 = e2
        self.e3 = e3

    def _eval(self, ctx=None):
        values1, _, t1 = saveeval(self.e1, ctx)

        assert t1 == bool, t1

        eval2 = saveeval(self.e2, ctx)
        eval3 = saveeval(self.e3, ctx)

        eval_size = self._evalsize(ctx)
        if len(values1) == 1:
            return eval2 if values1[0] else eval3

        assert len(values1) == eval_size

        values2, ix2, t2 = eval2
        values3, ix3, t3 = eval3

        # stretch lists
        if len(values2) == 1:
            if t2 in _basic_num_types:
                values2 = np.tile(values2, eval_size)
            else:
                values2 = values2 * eval_size
        if len(values3) == 1:
            if t3 in _basic_num_types:
                values3 = np.tile(values3, eval_size)
            else:
                values3 = values3 * eval_size

        assert len(values1) == len(values2) == len(values3)

        ct = common_type(t2, t3)
        if type(values2) == type(values3) == np.ndarray:
            if none_in_array(values1):
                nones = find_nones(values1)
                res = np.where(values1, values2, values3).astype(object)
                res[nones] = None
                return res, _, ct
            return np.where(values1, values2, values3), _, ct

        return [None if v1 is None else (v2 if v1 else v3)
                for v1, v2, v3 in zip(values1, values2, values3)], _, ct

    def __str__(self):
        return "%s(%s)" % (self.efunname, self.child)

    def _evalsize(self, ctx=None):
        s1 = self.e1._evalsize(ctx)
        s2 = self.e2._evalsize(ctx)
        s3 = self.e3._evalsize(ctx)
        if s1 == 1:
            if (s2 == 1 and s3 > 1) or (s2 > 1 and s3 == 1):
                raise Exception("column lengths %d, %d and %d do not fit!" % (s1, s2, s3))
            return max(s2, s3)

        if s2 == s3 == 1:
            return s1

        if (s3 == 1 and s2 != s1) or (s2 == 1 and s3 != s1):
            raise Exception("column lengths %d, %d and %d do not fit!" % (s1, s2, s3))

        return s1

    def _neededColumns(self):
        return self.e1._neededColumns() \
            + self.e2._neededColumns() \
            + self.e3._neededColumns()


class ColumnByValuesExpression(BaseExpression):

    def __init__(self, values):
        self._values = values

    def _eval(self, ctx=None):
        return self._values, None, None

    def _evalsize(self, ctx=None):
        return len(self._values)

    def _neededColumns(self):
        return []

    @property
    def values(self):
        return self._values

    def __str__(self):
        if len(self._values) < 10:
            v = str(self._values)
        else:
            v = str(self._values[:5] + ".." + self._values[-5:])
        return "ColumnByValuesExpression(%s)" % v



class ColumnExpression(BaseExpression):

    """
    A ``ColumnExpression`` is the simplest form of an ``Expression``.
    It is generated from a ``Table`` ``t`` as ``t.x`` or by calling
    ``t.getColumn("x")``.

    """

    def __init__(self, table, colname, idx, type_):
        self.table = table
        self.colname = colname
        self.idx = idx
        self.type_ = type_

    def _setupValues(self):
        # delayed lazy evaluation
        if not hasattr(self, "_values"):
            self._values = tuple(row[self.idx] for row in self.table.rows)

    @property
    def values(self):
        self._setupValues()
        return self._values

    def __getstate__(self):
        dd = self.__dict__.copy()
        if "_values" in dd:
            del dd["_values"]
        return dd

    def __setstate__(self, dd):
        self.__dict__ = dd

    def __iter__(self):
        self._setupValues()
        return iter(self.values)

    def _eval(self, ctx=None):
        # self.values is always a list ! for speeding up things
        # we convert numerical types to np.ndarray during evaluation
        # of expressions
        if ctx is None:
            if self.type_ in _basic_num_types:
                # the dtype of the following array is determined
                # automatically, even if Nones are in values:
                return np.array(self.values), None, self.type_
            return self.values, None, self.type_
        cx = ctx.get(self.table)
        if cx is None:
            if self.type_ in _basic_num_types:
                # the dtype of the following array is determined
                # automatically, even if Nones are in values:
                return np.array(self.values), None, self.type_
            return self.values, None, self.type_
        values, idx, type_ = cx.get(self.colname)
        if type_ in _basic_num_types:
            values = np.array(values)
        return values, idx, type_

    def __str__(self):
        if not hasattr(self, "colname"):
            raise Exception("colname missing")
        if not hasattr(self, "table"):
            raise Exception("table missing")
        if not hasattr(self.table, "_name"):
            raise Exception("table._name missing")
        return "%s.%s" % (self.table._name, self.colname)

    def _evalsize(self, ctx=None):
        if ctx is None:
            return len(self.values)
        cx = ctx[self.table]
        rv, _, _ = cx[self.colname]
        return len(rv)

    def _neededColumns(self):
        return [(self.table, self.colname), ]

    def modify(self, operation):
        """
        Allows **inplace** modification of a Table column.

        Example: ``tab.time.modify(sin)`` replaces the content of in column
        ``time`` by its ``sin`` value.
        """

        self.table.replaceColumn(self.colname, map(operation, self.values))
        if hasattr(self, "_values"):
            del self._values

    def __iadd__(self, value):
        """
        Allows **inplace** modification of a Table column.

        Example: ``tab.id += 1``
        """
        self.modify(lambda v, value=value: v + value)
        return self

    def __isub__(self, value):
        """
        Allows **inplace** modification of a Table column.

        Example: ``tab.id -= 1``
        """
        self.modify(lambda v, value=value: v - value)
        return self

    def __imul__(self, value):
        """
        Allows **inplace** modification of a Table column.

        Example: ``tab.area *= 2``
        """
        self.modify(lambda v, value=value: v * value)
        return self

    def __idiv__(self, value):
        """
        Allows **inplace** modification of a Table column.

        Example: ``tab.area /= 3.141``
        """
        self.modify(lambda v, value=value: v / value)
        return self
