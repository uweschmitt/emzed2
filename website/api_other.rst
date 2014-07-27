.. _api_other:

API helper modules
==================

Data of chemical Elements
-------------------------

.. automodule:: emzed.elements

.. pycon::
   :invisible:

   import emzed

Data of chemical elements are available from the *elements* module, e.g:

.. pycon::

   print emzed.elements.C
   print emzed.elements.C["m0"]
   print emzed.elements.C12
   print emzed.elements.C12["abundance"]

.. automodule:: emzed.mass

Masses and Mass Calculation
--------------------------

Masses can be queried like this:

.. pycon::
 
   print emzed.mass.C13
   print emzed.mass.of("C4H8O2")

Nested formulas are supported:

.. pycon::

   print emzed.mass.of("C(CH2)4COOH")

And isotopes can be specified in brackets:

.. pycon::

   print emzed.mass.of("[13]C4H8O2")
   print emzed.mass.of("[13]CC2H8O2")


Natural Abundances of isotopes
------------------------------

.. automodule:: emzed.abundance

.. pycon::

   print emzed.abundance.C
   print emzed.abundance.C[12]
   print emzed.abundance.C12


Data of common Adducts
----------------------

.. automodule:: emzed.adducts

The *adducts* module provides information about most common ESI adducts,
adduct lists can be converted to a *Table* eg:

.. pycon::

    print emzed.adducts.labels
    subgroup = emzed.adducts.get("M+H", "M+2Na-H")
    subgroup.toTable().print_()

    print emzed.adducts.namedLabels
    print emzed.adducts.M_plus_H
    print emzed.adducts.M_plus_2Na_minus_H


The following preselected groups of adducts exist:

.. pycon::

    print len(emzed.adducts.all)
    print len(emzed.adducts.positive)
    print len(emzed.adducts.negative)
    print len(emzed.adducts.single_charged)
    print len(emzed.adducts.double_charged)
    print len(emzed.adducts.triple_charged)
    print len(emzed.adducts.positive_single_charged)
    print len(emzed.adducts.positive_double_charged)
    print len(emzed.adducts.positive_triple_charged)
    print len(emzed.adducts.negative_single_charged)
    print len(emzed.adducts.negative_double_charged)
    print len(emzed.adducts.negative_triple_charged)


Further a default dialog can be opened for asking a multiple choice
selection of all adducts or of a subgroup:

.. image:: adduct_dialog.png

.. pycon::

    tab = emzed.adducts.all.buildTableFromUserDialog() !noexec
    tab.print_() !noexec
    adduct_name mass_shift z       !asoutput
    str         float      int     !asoutput
    ------      ------     ------  !asoutput
    [M+H]+      1.007276   +1      !asoutput
    [M+2Na-H]+  44.971165  +1      !asoutput
    [M-H]-      -1.007276  -1      !asoutput
    [M-H-H2O]-  -19.017842 -1      !asoutput

