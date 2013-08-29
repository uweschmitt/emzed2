from emzed.core.chemistry import (Elements as _Elements,
                                  MonoIsotopicElements as _MonoIsotopicElements,
                                  )

_elements = _Elements()
for _row in _elements.rows:
    _symbol = _elements.getValue(_row, "symbol")
    _massnumber = _elements.getValue(_row, "massnumber")
    _data = _elements.getValues(_row)
    del _data["symbol"]
    del _data["massnumber"]
    exec("%s=_data" % (_symbol+str(_massnumber)))

_monoelements = _MonoIsotopicElements()
for _row in _monoelements.rows:
    _symbol = _monoelements.getValue(_row, "symbol")
    _data = _monoelements.getValues(_row)
    del _data["symbol"]
    exec("%s=_data" % _symbol)


