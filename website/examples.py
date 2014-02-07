
import sys
sys.path.insert(0, "..")
import cStringIO

import ms, mass, elements, abundance

def run(txt):
    print "\n\n..pycon::"
    print
    for line in txt.split("\n"):
        print "   ",line
    print
    #captured = cStringIO.StringIO()
    #sys.stdout = captured
    #exec(txt, globals())
    #sys.stdout = sys.__stdout__
    #out= captured.getvalue()
    #for line in out.split("\n"):
        #print"   ", line



print """
========
Tutorial
========


Working with Tables
===================

Tables are a central data structure in mzExplore. We give a short demonstration of its capabilities::

"""
run("""substances=ms.loadCSV("example.csv")
substances.info()""")
print """

That is the table has two columns named *name* and *mf* and both
contain data of type ``str``.

This is a small table which we print the table on the console::

"""

run("""substances._print()""")

print """

If the table is to complex or large for printing, we have a graphical interface for inspecting the table:

"""
run("""ms.inspect(substances)""")
print """

Adding a new, computed column is easy. Here we introduce a new column *m0* which contains the monoisotopic masses corresponding to the contents of the *mf* column::

"""
run("""print mass.of("H2O") # calculates monoisotopic weights""")
run("""substances.addColumn("m0", substances.mf.apply(mass.of))
substances._print()""")
print """

We load another table::

"""

run("""info=ms.loadCSV() # without path -> opens dialog
info._print()""")
print """

And use an SQL-like *LEFTJOIN* to match rows with the same molecular formula::

"""

run("""joined=substances.leftJoin(info, substances.mf==info.mf)
joined._print()""")

print """We want to get rid of non terrestial substances by filtering the rows
::

"""
run("""common = joined.filter(joined.onEarth_1==1)
common._print()""")

MMU=0.001

print """

The ``tab`` module contains some databases, eg the substances from pubchem 
categorized as *metabolomic compounds*::

"""

run("""import tab # some standard tables
pc = tab.pc_full
ms.inspect(pc)""")

print """

Before matching our data against the large pubchem table, we build an index on tthis table in order to speed up the following ``leftJoin`` call. Building an index is done by sorting the corresponding column::

"""
run("""pc.sortBy("m0")
matched=joined.leftJoin(pc, (joined.onEarth_1==1) 
                           & joined.m0.approxEqual(pc.m0, 15*MMU))""")
run("matched.meta=dict()")
run("""print matched.numRows()""")
run("""ms.inspect(matched)""")

print """
Another way to identify compounds is to use the Metlin webpage which provides a formular for running queries against the database. This access is automated::

"""
run("""common.addColumn("polarity", "-") # metlin need this
matched2=ms.matchMetlin(common, "m0", ppm=15)
ms.inspect(matched2)""")

print"""

Modules providing chemical data
===============================

The ``mass`` module provides the masses of an electron, a
proton or a neutron and all all important elements::

"""


run("""print mass.e # electron""")
run("""print mass.C, mass.C12, mass.C13""")
print """

Further it helps to calculate masses of molecules from their sum
formula::

"""
run("""print mass.of("C6H2O6")""")

run("""print mass.of("C6H2O6", C=elements.C13)""")

print """

The ``elements`` module provides information
of important elements::

"""
run("print elements.C")
run("print elements.C13")

print """
``abundance`` is a module which provides the natural abundances of
common elements::

"""
run("print abundance.C")

print"""

Analysing isotope patterns
==========================

As the ``Table`` objects provide powerfull matchings, all we need to
analyse isotope patterns occuring in feature tables is a way to generate
tables containing theese data. ``ms.isotopeDistributionTable``
does this:: 

"""
run("""tab = ms.isotopeDistributionTable("C4S4", minp=0.01)
tab._print()""")
print """

Non natural distributions as in marker experiments can be
simmulated too::

"""
run("""iso=ms.isotopeDistributionTable("C4S4", C=dict(C12=0.5, C13=0.5))
iso.replaceColumn("abundance", iso.abundance / iso.abundance.sum() * 100.0)
iso._print()""")

print """

The method can simulate the resolution of the used mass analyzer::

"""

run("""tab = ms.isotopeDistributionTable("C4S4", R=10000, minp=0.01)
tab._print()""")

print """

Matching isotope patterns now works like this::

"""
run("""iso=ms.isotopeDistributionTable("H2O", minp=1e-3)
iso.addEnumeration()
iso._print()""")
run("""common.dropColumns("mf_1", "onEarth_1")
matched=iso.leftJoin(common, iso.mass.approxEqual(common.m0, 1*MMU))
matched._print()""")

print """"

Statistical Analysis
====================

The framework provides two methods for comparing two datasets by analysis of variance: classical *one way ANOVA* and
non parametric *Kruskal Wallis* analysis.

These methods work on tables (is anybody surprised ?) like
this::

"""
t = ms.toTable("group", [ 1,1,1,1,1,2,2,2,2,2,2])
t.addColumn("measurement", [ 1.0, 0.9, 1.2, 1.4, 2.1, 1.0, 2.2, 2.3, 1.9, 2.8, 2.3])
t.sortBy("measurement")

run("""t._print()""")
print """

``ms.oneWayAnova`` returns the correspoding *F* and *p* value, ``ms.kruskalWallis`` the *H* and *p* value::

"""
run("""F, p = ms.oneWayAnova(t.group, t.measurement)
print p""")
run("""H, p = ms.kruskalWallis(t.group, t.measurement)
print p""")


print """

Building graphical interfaces
=============================

Beyond the ``Table``-Explorer ``ms.inspect`` and the
Peakmap-Explorer ``ms.inspectPeakMap`` assisted workflows
request certain parameters and decisions at certain processing steps. To support this mzExplore has an builder for
graphical input forms::

"""

run("""b=ms.DialogBuilder(title="Please provide data")
b.addInstruction("For Algorithm A please provide")
b.addInt("Level")
b.addFloat("Threshold")
b.addFileOpen("Input File")
print b.show()""")

