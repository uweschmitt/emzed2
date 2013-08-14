import pdb
#encoding: utf-8


def matchMetlin(table, massColumn, adducts, ppm):
    table.requireColumn(massColumn)
    from ..core.webservice_clients import MetlinMatcher

    masses = [ "%.6f" % m for m in table.getColumn(massColumn).values ]

    internalRefColumn = "__metlin_massmatch"
    if table.hasColumn(internalRefColumn):
        table.dropColumns(internalRefColumn)
    table._addColumnWithoutNameCheck(internalRefColumn, masses)

    try:
        metlinMatch = MetlinMatcher.query(masses, adducts, ppm)
        if metlinMatch is None:
            table.addColumn("molid", None)
            table.dropColumns(internalRefColumn)
            return table

        result = table.leftJoin(metlinMatch, table.getColumn(internalRefColumn)\
                                            == metlinMatch.m_z)
        # duplicate column from joining input vs metlin answer:
        for pf in sorted(result.findPostfixes(), reverse=True):
            if "m_z" + pf in result.getColNames():
                result.dropColumns("m_z" + pf)
                break
        result.dropColumns(internalRefColumn)
    finally:
        if table.hasColumn(internalRefColumn):
            table.dropColumns(internalRefColumn)
    return result


