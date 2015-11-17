#encoding: latin-1

import mass as _mass

_all_adducts=[("M+H"      , _mass.p                    , 1),
              ("M+NH4"    , _mass.of("NH3") + _mass.p  , 1),
              ("M+Na"     , _mass.Na - _mass.e         , 1),
              ("M+H-2H2O" , _mass.p - 2*_mass.of("H2O"), 1),
              ("M+H-H2O"  , -_mass.of("OH") - _mass.e , 1),
              ("M+K"      , _mass.K - _mass.e          , 1),
              ("M+ACN+H"  , _mass.of("C2H3N") + _mass.p , 1),
              ("M+ACN+Na" , _mass.of("C2H3N") + _mass.Na - _mass.e , 1),
              ("M+2Na-H"  , _mass.of("Na2") - _mass.H - _mass.e, 1),
              ("M+2H"     , 2*_mass.p                 , 2),
              ("M+3H"     , 3*_mass.p                 , 3),
              ("M+H+Na"     , _mass.p + _mass.Na - _mass.e, 2),
              ("M+2H+Na"  , 2*_mass.p + _mass.Na - _mass.e, 3),
              ("M+2Na"    , 2*_mass.Na - 2*_mass.e    , 2),
              ("M+2Na+H"  , _mass.p + 2*_mass.Na - 2*_mass.e, 3),
              ("M+Li"      , _mass.Li - _mass.e          , 1),
              ("M+CH3OH+H", _mass.of("CH4O") + _mass.p , 1),

              ("M-H"      , -_mass.p                  , -1),
              ("M-H2O-H"  , -_mass.p - _mass.of("H2O"), -1),
              ("M+Na-2H"  , -2*_mass.p + _mass.Na     , -1),
              ("M+Cl"     , _mass.Cl + _mass.e  , -1),
              ("M+K-2H"   , -2*_mass.p + _mass.K      , -1),
              ("M+KCl-H"  , -1*_mass.p + _mass.K + _mass.Cl, -1),
              ("M+FA-H"   , _mass.of("H2CO2")-_mass.p , -1),
              ("M-2H"     , -2*_mass.p                 , -2),
              ("M-3H"     , -3*_mass.p                 , -3),
              ("M+CH3COO"  , _mass.of("H4C2O2")-_mass.p , -1),
              ("M+F"     , _mass.F-_mass.e       , -1),
              ("M"        , 0.0                        ,0)
             ]


_shortname = lambda key: key.replace("+", "_plus_").replace("-", "_minus_")

labels = [ _a[0] for _a in  _all_adducts ]
namedLabels = [ _shortname(_a) for _a in labels ]


class _Adducts(object):

    def __init__(self, adducts):
        self.adducts = adducts
        self.negatives = [ a for a in self.adducts if a[-1] < 0]
        self.positives = [ a for a in self.adducts if a[-1] > 0]
        self.neutrals = [ a for a in self.adducts if a[-1] == 0]
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
        t.title="adducts table"
        return t

    def createMultipleChoice(self, builder=None):
        if builder is None:
            from gui import DialogBuilder
            builder = DialogBuilder("Choose Adducts")
        if self.positives:
            labels = [a[0] for a in self.positives]
            builder.addMultipleChoice("positive adducts", labels, vertical=3,
                                      default=[0])
        if self.negatives:
            labels = [a[0] for a in self.negatives]
            builder.addMultipleChoice("negative adducts", labels, vertical=2,
                                      default=[0])
        if self.neutrals:
            labels = [a[0] for a in self.neutrals]
            builder.addMultipleChoice("neutral adducts", labels, vertical=2,
                                      default=[0])
        return builder

    def buildTableFromUserDialog(self):
        dlg = self.createMultipleChoice()
        res  = dlg.show()
        pos, neg, neut = [], [], []
        if self.positives and self.negatives and self.neutrals:
            pos, neg, neut = res
        elif self.positives and self.negatives:
            pos, neg = res
        elif self.positives:
            pos = res
        elif self.negatives:
            neg = res
        elif self.neutrals:
            neg = neut
        return self.getSelected(pos, neg).toTable()

    def getSelected(self, posIndices=None, negIndices=None, neutIndices=None):
        if posIndices is None:
            posIndices = []
        if negIndices is None:
            negIndices = []
        if neutIndices is None:
            neutIndices = []
        return _Adducts([self.positives[idx] for idx in posIndices]\
               +[self.negatives[idx] for idx in negIndices]\
               +[self.neeutral[idx] for idx in neutIndices])


all = _Adducts(_all_adducts)

def adductsForZ(*zs):
    return _Adducts([ (name, masscorr, mode) for (name, masscorr, mode)\
                                             in _all_adducts\
                                             if mode in zs ])

positive = adductsForZ(+1, +2, +3, +4, +5)
negative = adductsForZ(-1, -2, -3, -4, -5)
neutral = adductsForZ(0)
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
        raise KeyError("one of adducts %r unknown" % (tuple(names),))
    return _Adducts(found)


# vim: ts=4 et sw=4 sts=4
