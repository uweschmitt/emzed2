#encoding: latin-1

def testParser():
    from emzed.core.chemistry import joinFormula, parseFormula

    assert joinFormula(parseFormula("CHNOPS"))=="CHNOPS"
    assert joinFormula(parseFormula("COPSHN"))=="CHNOPS"
    assert joinFormula(parseFormula("H2O"))=="H2O"
    assert joinFormula(parseFormula("[13]CC"))=="C[13]C"
    assert joinFormula(parseFormula("C(CH2)7"))=="C8H14"

def testFormulaOperations():
    from emzed.core.chemistry import MolecularFormula as MF

    assert (MF("H2O")+MF("NaCl")) == MF("H2ONaCl")
    assert (MF("H2ONaCl")-MF("NaCl")) == MF("H2O")

    assert abs(MF("H2O").mass()-18.010565) <=1e-5, MF("H2O").mass()
    assert abs(MF("[13]C").mass()-13.003355) <= 1e-6
    assert abs(MF("[12]C").mass()-12.0) <= 1e-6

    assert MF("Kr").mass() == None





# vim: ts=4 et sw=4 sts=4

