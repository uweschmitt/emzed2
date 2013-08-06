#encoding: latin-1

import mass as _mass

_all_adducts=[("[M+H]+"     , _mass.p                    , 1),
              ("[M+NH4]+"   , _mass.of("NH3") + _mass.p  , 1),
              ("[M+Na]+"    , _mass.Na - _mass.e         , 1),
              ("[M+H-H2O]+" , _mass.p - _mass.of("H20")  , 1),
              ("[M+H-H4O2]+", _mass.p - 2*_mass.of("H2O"), 1),
              ("[M+K]+"     , _mass.K - _mass.e          , 1),
              ("[M+CH4O+H]+", _mass.of("CH4O") + _mass.p , 1),
              ("[M+2Na-H]+" , _mass.of("Na2") - _mass.H - _mass.e, 1),
              ("[M+H2]2+"   , 2*_mass.p                 , 2),
              ("[M+H3]3+"   , 3*_mass.p                 , 3),
              ("[M+Na+H]2+" , _mass.p + _mass.Na - _mass.e, 2),
              ("[M+H2+Na]3+", 2*_mass.p + _mass.Na - _mass.e, 3),
              ("[M+Na2]2+"  , 2*_mass.Na - 2*_mass.e    , 2),
              ("[M+H+Na2]3+", _mass.p + 2*_mass.Na - 2*_mass.e, 3),
              ("[M-H]-"     , -_mass.p                  , -1),
              ("[M-H-H2O]-" , -_mass.p - _mass.of("H2O"), -1),
              ("[M+Na-H2]-" , -2*_mass.p + _mass.Na     , -1),
              ("[M+Cl]-"    , -(_mass.p - _mass.Cl)     , -1),
              ("[M+K-H2]-"  , -2*_mass.p + _mass.K      , -1),
              ("[M-H2]2-"   , -2*_mass.p                , -2),
              ("[M-H3]3-"   , -3*_mass.p                , -3)
             ]


_shortname = lambda key: key[1:].split("]")[0].replace("+", "_plus_")\
                                              .replace("-", "_minus_")

labels = [ _a[0] for _a in  _all_adducts ]
namedLabels = [ _shortname(_a) for _a in labels ]

class _Adducts(object):

    def __init__(self, adducts):
        self.adducts = adducts
        self.negatives = [ a for a in self.adducts if a[-1] < 0]
        self.positives = [ a for a in self.adducts if a[-1] > 0]
        for name, masscorr, mode in adducts:
            shortName = _shortname(name)
            setattr(self,  shortName, (name, masscorr, mode))

    def __iter__(self):
        return iter(self.adducts)

    def __len__(self):
        return len(self.adducts)

    def toTable(self):
        from .core.data_types import Table
        t = Table(["adduct_name", "mass_shift", "z_signed"],
                  [ str, float, int],
                  ["%s", "%.6f", "%+d"],
                   map(list, self.adducts))
        t.addColumn("z", t.z_signed.apply(abs))
        return t

    def createMultipleChoice(self, builder=None):
        if builder is None:
            from libms.gui.DialogBuilder import DialogBuilder
            builder = DialogBuilder("Choose Adducts")
        if self.positives:
            labels = [a[0] for a in self.positives]
            builder.addMultipleChoice("positive adducts", labels, vertical=3,
                                      default=[0])
        if self.negatives:
            labels = [a[0] for a in self.negatives]
            builder.addMultipleChoice("negative adducts", labels, vertical=2,
                                      default=[0])
        return builder

    def buildTableFromUserDialog(self):
        dlg = self.createMultipleChoice()
        res  = dlg.show()
        pos, neg = [], []
        if self.positives and self.negatives:
            pos, neg = res
        elif self.positives:
            pos = res
        elif self.negatives:
            neg = res
        return self.getSelected(pos, neg).toTable()

    def getSelected(self, posIndices=None, negIndices=None):
        if posIndices is None:
            posIndices = []
        if negIndices is None:
            negIndices = []
        return _Adducts([self.positives[idx] for idx in posIndices]\
               +[self.negatives[idx] for idx in negIndices])


all = _Adducts(_all_adducts)

def adductsForZ(*zs):
    return _Adducts([ (name, masscorr, mode) for (name, masscorr, mode)\
                                             in _all_adducts\
                                             if mode in zs ])

positive = adductsForZ(+1, +2, +3, +4, +5)
negative = adductsForZ(-1, -2, -3, -4, -5)
single_charged = adductsForZ(+1, -1)
double_charged = adductsForZ(+2, -2)
triple_charged = adductsForZ(+3, -3)
positive_single_charged = adductsForZ(+1)
positive_double_charged = adductsForZ(+2)
positive_triple_charged = adductsForZ(+3)
negative_single_charged = adductsForZ(-1)
negative_double_charged = adductsForZ(-2)
negative_triple_charged = adductsForZ(-3)

for name, masscorr, mode in _all_adducts:
    exec("%s=_Adducts([('%s', %e, %d)])" % (_shortname(name), name, masscorr,
                                            mode))

def get(*names):
    found = [ item for item in _all_adducts if item[0] in names ]
    if not found:
        raise KeyError("adduct %name unknown")
    return _Adducts(found)


# vim: ts=4 et sw=4 sts=4
