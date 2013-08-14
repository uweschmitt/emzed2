#encoding: utf-8

def mzAlign(table, mz_reference_table, fullC13=False, tol=15*MMU,
            destination=None, minR2=0.95, minPoints=5, interactive=False):

    """
    performs affine linear mz-correction for a feature table.

    you need a ``mz_reference_table`` with the theoretical ideal masses
    and retention times of some universal metabolites. This table needs
    columns ``m0`` for the neutral mass, ``rtmin``, ``rtmax`` for the
    retention time window for restricting the match of the table against
    the  ``mz_reference_table`` and the molecular formula ``mf``.

    If you specify ``fullC13=True`` the ``mf`` is used to correct ``m0``.

    ``destination`` is a directory which will be used for storing the
    result and intermediate data.  If you do not specify this value, a
    dialog for choosing the destination directory will be opened.

    The input table **is not mofied** in place, the function returns the
    aligned table.

    """

    import os
    import numpy as np
    from _mzalign_helpers import (_buildHypotheseTable,
                                 _findMzMatches,
                                 _findParametersAutomatically,
                                 _findParametersManually,
                                 _plotAndSaveMatch,
                                 _applyTransform )
    if not interactive:
        assert minR2 <= 1.0
        assert minPoints > 1

    sources = set(table.source.values)
    assert len(sources) == 1
    source = sources.pop()

    univ = mz_reference_table
    univ.requireColumn("m0")
    univ.requireColumn("rtmin")
    univ.requireColumn("rtmax")
    univ.requireColumn("mf")
    assert univ.getColType("m0") == float, "col m0 is not float"
    assert univ.getColType("rtmin" )== float, "col rtmin is not float"
    assert univ.getColType("rtmax" )== float, "col rtmax is not float"

    polarities = set(table.polarity.values)
    assert len(polarities) == 1, "multiple polarities in table"
    polarity = polarities.pop()

    hypot = _buildHypotheseTable(polarity, univ.copy(), fullC13)

    if destination is not None:
        basename = os.path.basename(source)
        fname, _ = os.path.splitext(basename)
        hypot.store(os.path.join(destination, fname+"_hypot.table"), True)

    real, tobe, matches = _findMzMatches(hypot, table, tol)
    if len(real)<=1:
        print "NOT ENOUGH MATCHES FOR ALIGNMENT"
        return

    if interactive:
        from .. import utils
        utils.inspect(matches, offerAbortOption=True)

    elif len(tobe) < minPoints:
        raise Exception("could only match %d peaks" % len(tobe))

    if not interactive:
        transform, used = _findParametersAutomatically(tobe.copy(), real.copy(),\
                                                      minR2, minPoints)
    else:
        transform, used = _findParametersManually(tobe.copy(), real.copy())
        if transform is None:
            print "ABORTED"
            return

    if destination is not None:
        matches.addColumn("error", np.linalg.norm(transform(real)-tobe), float,\
                          "%.3e")
        matches.store(os.path.join(destination, fname+"_mzalign.table"), True)
        matches.storeCSV(os.path.join(destination, fname+"_mzalign.csv"))

        path = os.path.join(destination, fname+"_mzalign.png")
        _plotAndSaveMatch(tobe, real, used, transform, path)

    transformedTable = _applyTransform(table, transform)
    print "DONE"
    return transformedTable

