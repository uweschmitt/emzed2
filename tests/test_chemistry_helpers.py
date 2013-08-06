import emzed.elements as elements
import emzed.mass     as mass
import emzed.abundance as abundance
import emzed.adducts   as adducts

def testAccessAndConsistency():
    c12 = elements.C12
    assert c12["abundance"] == abundance.C12
    assert c12["abundance"] is not None
    assert abs(c12["abundance"]-0.989) < 0.001
    assert c12["mass"] ==  mass.C12
    assert c12["name"] == "Carbon"
    assert c12["number"] == 6
    assert  mass.of("[13]C") - mass.of("C") == mass.C13-mass.C12
    assert  mass.of("C", C=mass.C13) == mass.of("[13]C")
    assert  mass.of("C", C=elements.C13) == mass.of("[13]C")


def testAdducts():
    assert len(adducts.all) == 21, len(adducts.all)
    #test subgroups
    assert len(adducts.positive) == 14, len(adducts.positive)
    assert len(adducts.negative) == 21-14, len(adducts.negative)
    assert len(adducts.single_charged)>0
    assert len(adducts.double_charged)>0
    assert len(adducts.triple_charged )>0
    assert len(adducts.positive_single_charged)>0
    assert len(adducts.positive_double_charged)>0
    assert len(adducts.positive_triple_charged)>0
    assert len(adducts.negative_single_charged)>0
    assert len(adducts.negative_double_charged)>0
    assert len(adducts.negative_triple_charged )>0


    # tst namespace constants
    assert adducts.M_plus_H.toTable().z.uniqueValue() == 1
    assert adducts.M_plus_NH4.toTable().z.uniqueValue() == +1
    assert adducts.M_plus_Na.toTable().z.uniqueValue() == 1
    assert adducts.M_plus_H_minus_H2O.toTable().z.uniqueValue()  ==1
    assert adducts.M_plus_H_minus_H4O2.toTable().z.uniqueValue()  ==1
    assert adducts.M_plus_K.toTable().z.uniqueValue()  ==1
    assert adducts.M_plus_CH4O_plus_H.toTable().z.uniqueValue()  ==1
    assert adducts.M_plus_2Na_minus_H.toTable().z.uniqueValue()  ==1
    assert adducts.M_plus_H2.toTable().z.uniqueValue()  ==2
    assert adducts.M_plus_H3.toTable().z.uniqueValue()  ==3
    assert adducts.M_plus_Na_plus_H.toTable().z.uniqueValue()  ==2
    assert adducts.M_plus_H2_plus_Na.toTable().z.uniqueValue()  ==3
    assert adducts.M_plus_Na2.toTable().z.uniqueValue()  ==2
    assert adducts.M_plus_H_plus_Na2.toTable().z.uniqueValue()  ==3
    assert adducts.M_plus_Na_minus_H2.toTable().z.uniqueValue()  ==1
    assert adducts.M_plus_Cl.toTable().z.uniqueValue()  ==1
    assert adducts.M_plus_K_minus_H2.toTable().z.uniqueValue()  ==1
    assert adducts.M_plus_Na_minus_H2.toTable().z.uniqueValue() == 1

    assert adducts.M_plus_H.toTable().z_signed.uniqueValue() == 1
    assert adducts.M_plus_NH4.toTable().z_signed.uniqueValue() == +1
    assert adducts.M_plus_Na.toTable().z_signed.uniqueValue() == 1
    assert adducts.M_plus_H_minus_H2O.toTable().z_signed.uniqueValue()  ==1
    assert adducts.M_plus_H_minus_H4O2.toTable().z_signed.uniqueValue()  ==1
    assert adducts.M_plus_K.toTable().z_signed.uniqueValue()  ==1
    assert adducts.M_plus_CH4O_plus_H.toTable().z_signed.uniqueValue()  ==1
    assert adducts.M_plus_2Na_minus_H.toTable().z_signed.uniqueValue()  ==1
    assert adducts.M_plus_H2.toTable().z_signed.uniqueValue()  ==2
    assert adducts.M_plus_H3.toTable().z_signed.uniqueValue()  ==3
    assert adducts.M_plus_Na_plus_H.toTable().z_signed.uniqueValue()  ==2
    assert adducts.M_plus_H2_plus_Na.toTable().z_signed.uniqueValue()  ==3
    assert adducts.M_plus_Na2.toTable().z_signed.uniqueValue()  ==2
    assert adducts.M_plus_H_plus_Na2.toTable().z_signed.uniqueValue()  ==3

    assert adducts.M_plus_Na_minus_H2.toTable().z_signed.uniqueValue()  == -1
    assert adducts.M_plus_Cl.toTable().z_signed.uniqueValue()  == -1
    assert adducts.M_plus_K_minus_H2.toTable().z_signed.uniqueValue()  == -1
    assert adducts.M_plus_Na_minus_H2.toTable().z_signed.uniqueValue() ==  -1


    assert adducts.M_minus_H.toTable().z.uniqueValue()  ==1
    assert adducts.M_minus_H_minus_H2O.toTable().z.uniqueValue() == 1
    assert adducts.M_minus_H2.toTable().z.uniqueValue()  ==2
    assert adducts.M_minus_H3.toTable().z.uniqueValue()  ==3
    assert adducts.M_minus_H.toTable().z_signed.uniqueValue()  == -1
    assert adducts.M_minus_H_minus_H2O.toTable().z_signed.uniqueValue() == -1
    assert adducts.M_minus_H2.toTable().z_signed.uniqueValue()  == -2
    assert adducts.M_minus_H3.toTable().z_signed.uniqueValue()  == -3

    t = adducts.positive.toTable()
    assert len(t) == 14
    assert len(t.getColNames()) == 4

def testfoumulaadd():
    from  emzed.utils import addmf
    assert addmf("H2O") == "H2O"
    assert addmf("H2O", "O") == "H2O2"
    assert addmf("H2O", "-O") == "H2"
    assert addmf("H2O", "-H2") == "O"
    assert addmf("H2O", "O", "O", "O2") == "H2O5"
    assert addmf("(CH2)7", "COOH", "Cl", "-H2O") == "C8H13OCl"


