import sys, StringIO, difflib, traceback
import os.path
import numpy as np

from emzed.core.data_types import Table
from emzed.core.data_types.expressions import Value


here = os.path.dirname(os.path.abspath(__file__))


def record(fun, args, p=None):
    try:
        r = StringIO.StringIO()
        sys.stdout = r
        try:
            fun(*args)
        except Exception, e:
            print >> sys.stderr, r.getvalue()
            traceback.print_exc(file=sys.stderr)
            raise e

        data = r.getvalue()
        if p:
            full_p = os.path.join(here,
                                  "regression_test_data",
                                  p)
            with open(full_p, "w") as fp:
                fp.write(data)
        return [ l for l in data.split("\n") if not l.startswith("#") ], p
    finally:
        sys.stdout = sys.__stdout__

def check((lines, p), ptobe):
    full_p = os.path.join(here,
                            "regression_test_data",
                            ptobe)
    try:
        with open(full_p, "r") as fp:
            data = fp.read()
    except:
        raise
    tobe = [ l for l in data.split("\n") if not l.startswith("#") ]
    ok = True
    for line in difflib.unified_diff(lines, tobe, n=5):
        print line
        ok = False
    if not ok:
        raise Exception("diff in %s vs %s" % (p, ptobe))


def compare(*results):
    for i, (lines1, p1) in enumerate(results):
        for lines2, p2 in results[i+1:]:
            for line in difflib.unified_diff(lines1, lines2):
                raise Exception("diff in %s vs %s" % (p1, p2))

def setupTable():
    names="int long float str object array".split()
    types = [int, long, float, str, object, np.ndarray,]
    formats = [ "%3d", "%d", "%.3f", "%s", "%r", "'array(%r)' % o.shape" ]

    row1 = [ 1, 12323L, 1.0, "hi", { 1: 1 },  np.array((1,2,3)) ]
    row2 = [ 2, 22323L, 2.0, "hi2", [2,3,], np.array(((2,3,4),(1,2,3))) ]
    row3 = [ 3, 32323L, 3.0, "hi3", (3,) , np.array(((3,3,4,5),(1,2,3,4))) ]

    rows = [row1, row2, row3]
    t=Table(names, types, formats, rows, "testtabelle", meta=dict(why=42))
    t = t.extractColumns("int", "float", "str")
    t.addEnumeration()
    t._name = "t"
    t._print()
    return t

def testFilter():

    t = setupTable()
    out1 = record(run_num_compares,[t, t.int], "tint_noindex.is")
    check(out1, "tint_noindex.tobe")

    t.sortBy("int")
    out2 = record(run_num_compares,[t, t.int], "tint_withindex.is")

    compare(out1, out2)

    out2 = record(run_num_compares,[t, t.float], "tfloat_noindex.is")
    t.sortBy("float")
    out3 = record(run_num_compares,[t, t.float], "tfloat_withindex.is")
    compare(out1, out2, out3)

    out = record(run_logics, [t, t.int], "tint_logics_noindex.is")
    check(out, "tint_logics_noindex.tobe")

    out = record(run_str, [t], "tstr_tests.is")
    check(out, "tstr_tests.tobe")

def run_num_compares(t, col):
    expressions = []
    for rhs in [-1, 0, 0.5, 1, 2, 2.5, 3]:
        expressions.append(col >= rhs)
        expressions.append(col > rhs)
        expressions.append(col <= rhs)
        expressions.append(col > rhs)
        expressions.append(col == rhs)
        expressions.append(col != rhs)
        expressions.append(rhs >= col)
        expressions.append(rhs > col)
        expressions.append(rhs <= col)
        expressions.append(rhs > col)
        expressions.append(rhs == col)
        expressions.append(rhs != col)
        expressions.append(col == col)
        expressions.append(col != col)

    for e in expressions:
        print
        t.filter(e, debug=True)._print()

def run_logics(t, col):
    expressions = []
    expressions.append( (col >= 2) & (col <=3) )
    expressions.append( (col >= 2) & (col >=1) )
    expressions.append( (col >= 2) | (col >=1) )
    expressions.append( (col >= 2) | (col <=3) )
    expressions.append( (col >= 2) ^ (col >=1) )
    expressions.append( (col >= 2) | (col >=1) | True )
    expressions.append( (col >= 2) | (col >1) & False )
    expressions.append( (col >= 2) | (col <1) & False)
    expressions.append( Value(True))
    expressions.append( Value(False))
    expressions.append( ~(col >= 2) & ~(col >=3))
    for e in expressions:
        print 
        t.filter(e, debug=True)._print()

def run_str(t):
    print
    t.filter(t.str == "hi", debug=True)._print()
    print
    t.filter(t.str > "hi", debug=True)._print()
    print
    t.filter(t.str >= "hi", debug=True)._print()
    print
    t.filter(t.str <= "hi", debug=True)._print()
    print
    t.filter(t.str >= "a", debug=True)._print()
    print
    t.filter(t.str >= "z", debug=True)._print()
    print
    t.filter(t.str <= "z", debug=True)._print()
    print
    t.filter(t.str == "z", debug=True)._print()
    print
    t.filter(t.str != "z", debug=True)._print()
    print
    t.filter(t.str.startswith("hi"), debug=True)._print()

def testJoin():
    t1 = setupTable()
    t1._name ="t1"
    t2 = setupTable()
    t2._name ="t2"
    out = record(run_join_int, [t1.join, t1, t2], "tjoin_int.is")
    check(out, "tjoin_int.tobe")
    outf = record(run_join_float, [t1.join, t1, t2], "tjoin_float.is")
    compare(out, outf)
    outf = record(run_join_comp, [t1.join, t1, t2], "tjoin_comp.is")
    check(outf, "tjoin_comp.tobe")

def testLeftJoin():
    t1 = setupTable()
    t1._name ="t1"
    t2 = setupTable()
    t2._name ="t2"
    out = record(run_join_int, [t1.leftJoin, t1, t2], "tljoin_int.is")
    check(out, "tljoin_int.tobe")
    outf = record(run_join_float, [t1.leftJoin, t1, t2], "tljoin_float.is")
    compare(out, outf)
    outf = record(run_join_comp, [t1.leftJoin, t1, t2], "tljoin_comp.is")
    check(outf, "tljoin_comp.tobe")


def run_join_int(jf, t1, t2):
    jf(t2, t1.int > t2.int, debug=True)._print(w=8)
    print
    jf(t2, t2.int < t1.int, debug=True)._print(w=8)
    print
    jf(t2, t1.int == t2.int, debug=True)._print(w=8)
    print
    jf(t2, t2.int == t1.int, debug=True)._print(w=8)
    print
    jf(t2, t1.int != t2.int, debug=True)._print(w=8)
    print
    jf(t2, t2.int != t1.int, debug=True)._print(w=8)
    print
    jf(t2, t1.int >= t2.int, debug=True)._print(w=8)
    print
    jf(t2, t2.int <= t1.int, debug=True)._print(w=8)
    print
    jf(t2, t1.int <= t2.int, debug=True)._print(w=8)
    print
    jf(t2, t2.int >= t1.int, debug=True)._print(w=8)
    print
    jf(t2, t1.int < t2.int, debug=True)._print(w=8)
    print
    jf(t2, t2.int > t1.int, debug=True)._print(w=8)
    print
    jf(t2, t1.int > t2.int, debug=True)._print(w=8)
    print
    jf(t2, t2.int < t1.int, debug=True)._print(w=8)
    print
    jf(t2, t1.int == t1.int, debug=True)._print(w=8)
    print

def run_join_float(jf, t1, t2):
    jf(t2, t1.float > t2.float, debug=True)._print(w=8)
    print
    jf(t2, t2.float < t1.float, debug=True)._print(w=8)
    print
    jf(t2, t1.float == t2.float, debug=True)._print(w=8)
    print
    jf(t2, t2.float == t1.float, debug=True)._print(w=8)
    print
    jf(t2, t1.float != t2.float, debug=True)._print(w=8)
    print
    jf(t2, t2.float != t1.float, debug=True)._print(w=8)
    print
    jf(t2, t1.float >= t2.float, debug=True)._print(w=8)
    print
    jf(t2, t2.float <= t1.float, debug=True)._print(w=8)
    print
    jf(t2, t1.float <= t2.float, debug=True)._print(w=8)
    print
    jf(t2, t2.float >= t1.float, debug=True)._print(w=8)
    print
    jf(t2, t1.float < t2.float, debug=True)._print(w=8)
    print
    jf(t2, t2.float > t1.float, debug=True)._print(w=8)
    print
    jf(t2, t1.float > t2.float, debug=True)._print(w=8)
    print
    jf(t2, t2.float < t1.float, debug=True)._print(w=8)
    print
    jf(t2, t1.float == t1.float, debug=True)._print(w=8)
    print

def run_join_comp(jf, t1, t2):
    e = t1.float <= t2.float
    jf(t2, (t1.str>"hi") & e, debug=True)._print(w=8)
    print
    jf(t2, e & (t1.str>"hi"), debug=True)._print(w=8)
    print
    jf(t2, e & (t1.str>"hi") & e, debug=True)._print(w=8)
    print

    jf(t2, (t1.str>="hi") & e, debug=True)._print(w=8)
    print
    jf(t2, e & (t1.str>="hi"), debug=True)._print(w=8)
    print
    jf(t2, e & (t1.str>="hi") & e, debug=True)._print(w=8)
    print


    jf(t2, (t1.str>="hi") & e & False, debug=True)._print(w=8)
    print
    jf(t2, e & (t1.str>="hi") & False, debug=True)._print(w=8)
    print
    jf(t2, e & (t1.str>="hi") & e & False, debug=True)._print(w=8)
    print


    jf(t2, ((t1.str>="hi")  | True) & e, debug=True)._print(w=8)
    print
    jf(t2, ((t1.str>="hi")  | True) & e, debug=True)._print(w=8)
    print
    jf(t2, e & ((t1.str>="hi")  | True) & e, debug=True)._print(w=8)
    print


    jf(t2, t1.int <= t1.float, debug=True)._print(w=8)


