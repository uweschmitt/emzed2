#encoding: latin-1

from string import (ascii_uppercase as _CAPITALS,
                   ascii_lowercase  as _LOWERS,
                   digits           as _DIGITS)

import re

_LEFT_PARENTHESIS ="("
_RIGHT_PARENTHESIS = ")"
_LEFT_BRACKET ="["
_RIGHT_BRACKET = "]"

def _next(reminder):
    return reminder[0], reminder[1:]

def _parseOptionalInt(reminder):
    count = 0
    # counst start with digit > 0
    if reminder[0] in "123456789":
        count = int(reminder[0])
        reminder = reminder[1:]
        while reminder[0] in _DIGITS:
            token, reminder = _next(reminder)
            count = 10 * count + int(token)
    return count, reminder

def _parseElementWithCount(reminder):
    token, reminder = _next(reminder)
    assert token in _CAPITALS, "illegal formula: stopped parsing at "+token+reminder
    element = token
    if reminder[0] in _LOWERS:
        token, reminder = _next(reminder)
        element += token
    count, reminder = _parseOptionalInt(reminder)
    if count == 0:
        count = 1
    return element,count, reminder

def _subFormulaParser(reminder, formula, indent):
    token, reminder = _next(reminder)
    subformula, reminder = _parse(reminder, indent+"    ")
    count, reminder = _parseOptionalInt(reminder)
    assert count > 0, "illegal formula: stopped parsing at "+reminder
    return reminder, formula +  subformula*count

def _isotopeParser(reminder, formula, indent):
    token, reminder = _next(reminder)
    isonumber, reminder = _parseOptionalInt(reminder)
    assert isonumber > 0, "illegal formula: stopped at "+reminder
    assert reminder[0] == _RIGHT_BRACKET
    token, reminder = _next(reminder)
    assert reminder[0] in _CAPITALS, "illegal formula: stopped at "+reminder
    elem, count, reminder = _parseElementWithCount(reminder)
    formula.extend(((elem, isonumber),)*count)
    return reminder, formula

def _elementParser(reminder, formula, indent):
    elem, count, reminder = _parseElementWithCount(reminder)
    formula.extend(((elem, None),)*count)
    return reminder, formula


_actions = { _LEFT_PARENTHESIS: _subFormulaParser,
             _LEFT_BRACKET    : _isotopeParser }

for k in  _CAPITALS:
    _actions[k] = _elementParser


def _parse(reminder, indent=""):
    formula = []
    while True:
        if reminder[0] in [chr(0), _RIGHT_PARENTHESIS]:
            return formula, reminder[1:]
        action = _actions.get(reminder[0])
        if action is None:
            raise Exception("parser stops at %r" % reminder)
        reminder, formula = action(reminder, formula, indent)


def parseFormula(mf, re = re.compile("\s")):
    """
    Returns Counter mapping (symbol, sassnumber) -> sount
    corresponding to mf.
    For symbols in mf, where no massnumber is specified, this
    funcion returns None as massnumber.

    Eg.::

        >>> parseFormula("[13]C2C4H")
        Counter({('C', None): 4, ('C', 13): 2, ('H', None): 1})

    """
    from collections import Counter
    mf = re.sub("", mf)  # remove whitespaces
    symbols, _ =  _parse(mf+chr(0))
    return Counter(symbols)


def joinFormula(cc):
    symbols = []
    order = dict( (s, i) for (i,s) in enumerate("CHNOPS"))
    items = cc.items()
    items.sort(key = lambda ((elem, iso), count): (order.get(elem, 99), iso))

    for (elem, isonumber), count in items:
        if isonumber:
            if count>1:
                symbols.append("[%d]%s%d" % (isonumber, elem, count))
            else:
                symbols.append("[%d]%s" % (isonumber, elem,))
        else:
            if count>1:
                symbols.append("%s%d" % (elem, count))
            if count == 1:
                symbols.append(elem)

    return "".join(symbols)


if __name__ == "__main__":
    x = parse("H2O")
    print x, join(x)
    x = parse("[13]Na")
    print x, join(x)
    x = parse("[13]C2[14]CC")
    print x, join(x)
    x = parse("NaCl")
    print x, join(x)
    x = parse("Cl(H2O)3")
    print x, join(x)
    x = parse("CHNOPS(NOPS)3NaClAr")
    print x, join(x)

# vim: ts=4 et sw=4 sts=4

