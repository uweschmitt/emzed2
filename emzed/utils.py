def toTable(colName, iterable,  format_="", type_=None, title="", meta=None):
    import emzed.core.data_types
    return emzed.core.data_types.Table.toTable(colName, iterable, format_, type_, title, meta)


def formula(mf):
    """
    Creates formula object which allows addition and subtraction:

    .. pycon::

       import ms   !onlyoutput
       mf1 = ms.formula("H2O")
       mf2 = ms.formula("NaOH")
       mf3 = mf1 + mf2
       print str(mf3)
       print str(mf3 - mf1)

    Mass calculation is supported too:

    .. pycon::

       print mf1.mass()

    If you need some internal representation, you can get a dictionary.
    Keys are pairs of *(symbol, massnumber)*, where *massnumber = None*
    refers to the lowest massnumber. Values of the dictionary are counts:

    .. pycon::

       print mf1.asDict()
       mixed = ms.formula("[13]C2[14]C3")
       print mixed.asDict()


    """
    from emzed.core.chemistry import MolecularFormula
    return MolecularFormula(mf)

def addmf(formula0, *formulas):
    """
    Combines molecular formulas by addition and subtraction:

    .. pycon::

       import ms !onlyoutput
       print ms.addmf("H2O", "COOH")
       print ms.addmf("H2O", "COOH", "NaCl")

    A leading minus sign subtracts the formula following this sign:

    .. pycon::

       print ms.addmf("H2O2", "-H2O")
       print ms.addmf("H2O", "COOH", "NaCl", "-H2O2")
       print ms.addmf("(CH2)7COOH", "-C7")

    """

    mf0 = formula(formula0)
    for f in formulas:
        if f.startswith("-"):
            mf0 -= formula(f[1:])
        else:
            mf0 += formula(f)
    return str(mf0)


