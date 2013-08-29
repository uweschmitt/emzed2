
from collections import defaultdict as _defaultdict

_abu=_defaultdict(dict)

from emzed.core.chemistry import (Elements as _Elements,
                                  )


_elements = _Elements()
_symbols = _elements.symbol.values
_massnumbers = _elements.massnumber.values
_abundances = _elements.abundance.values

for _symbol, _massnumber, _abundance in zip(_symbols,
                                           _massnumbers,
                                           _abundances):
    exec("%s=_abundance" % (_symbol+str(_massnumber)))
    _abu[_symbol][_massnumber] = _abundance


for _k in _abu.keys():
    exec("%s=_abu['%s']" % (_k, _k))

