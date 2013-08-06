import emzed.utils
import emzed.stats


def testOnColumns():
    t = emzed.utils.toTable("factor", [1,2,1,2,1,1,2])
    t.addColumn("dependent", t.factor*1.1)
    F, p = emzed.stats.oneWayAnova(t.factor, t.factor*1.1)
    assert p<1e-12, p

    H, p = emzed.stats.kruskalWallis(t.factor, t.factor*1.1)
    assert abs(p-0.014305)/0.014305 < 1e-4


    t.addColumn("dependent2", [1.01,2.01,1.02,2.02,.99, 0.98,1.98])
    F, p = emzed.stats.oneWayAnova(t.factor, t.dependent2)
    assert abs(p-1.3e-8)/1.3e-8 < 0.01

    H, p = emzed.stats.kruskalWallis(t.factor, t.dependent2)
    assert abs(p-0.033894)/0.033894 < 1e-4

def testOnTables():
    setOne = []
    t = emzed.utils.toTable("compound", ["A", "B"])
    t.addColumn("area", [ 1.0, 2.0])
    setOne.append(t)

    t = t.copy()
    t.area += 0.01
    setOne.append(t)

    t = t.copy()
    t.replaceColumn("area",[None, 4.2])
    setOne.append(t)

    t = t.copy()
    t.replaceColumn("area",[1.3, 4.7])
    setOne.append(t)

    t = t.copy()
    t.replaceColumn("area",[2.3, 8.7])
    setOne.append(t)

    setTwo = []

    t = t.copy()
    t.replaceColumn("area",[2.2, 7.7])
    setTwo.append(t)

    t = t.copy()
    t.replaceColumn("area",[2.2, 7.7])
    setTwo.append(t)

    t = t.copy()
    t.replaceColumn("area",[2.2, 7.7])
    setTwo.append(t)

    t = t.copy()
    t.replaceColumn("area",[2.6, 7.6])
    setTwo.append(t)

    t = t.copy()
    t.replaceColumn("area",[2.2, 7.7])
    setTwo.append(t)

    t = t.copy()
    t.replaceColumn("area",[2.9, 7.6])
    setTwo.append(t)

    tresult = emzed.stats.oneWayAnovaOnTables(setOne, setTwo, idColumn="compound",
                                              valueColumn="area")

    assert tresult.id.values == ["A", "B"]
    assert tresult.n1.values == [4, 5]
    assert tresult.n2.values == [6, 6]

    assert abs(tresult.p_value.values[0]-9.11e-3)/9.11e-3 < 1e-2
    assert abs(tresult.p_value.values[1]-1.44e-2)/1.44e-2 < 1e-2

    assert tresult.title=="ANOVA ANALYSIS"

    tresult = emzed.stats.kruskalWallisOnTables(setOne, setTwo, idColumn="compound",
                                                valueColumn="area")

    tresult.print_()

    assert tresult.id.values == ["A", "B"]
    assert tresult.n1.values == [4, 5]
    assert tresult.n2.values == [6, 6]


    assert abs(tresult.p_value.values[0]-7.84e-2)/7.84e-2 < 1e-2
    assert abs(tresult.p_value.values[1]-9.18e-2)/9.18e-2 < 1e-2

    assert tresult.title=="KRUSKAL WALLIS ANALYSIS"

