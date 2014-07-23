# encoding: utf-8

MMU = 0.001

def mzAlign(table, mz_reference_table, tol=15 * MMU,
            destination=None, minR2=0.95, maxTol=1 * MMU, minPoints=5,
            interactive=False):

    """
    performs affine linear mz-correction for a feature table.

    and retention times of  known metabolites. This table needs
    columns ``mz_calc`` for the mz value calculated from the mass of the isotope,
    ``rtmin``, ``rtmax`` for the retention time window where the peak is expected
    to elute from the column in order to restrict the match of the table against
    the  ``mz_reference_table`.


    ``destination`` is a directory which will be used for storing the
    result and intermediate data.  If you do not specify this value, a
    dialog for choosing the destination directory will be opened.

    The input table **is not modified** in place, the function returns the
    aligned table.

    the parameter *tol* is related to find matching peaks, *maxTol* and
    *minR2* determine stop criterion when removing outlier points in
    non interactive mode.

    """

    import os
    import numpy as np
    from _mzalign_helpers import (_findMzMatches,
                                  _findParametersAutomatically,
                                  _findParametersManually,
                                  _plotAndSaveMatch,
                                  _applyTransform)
    if not interactive:
        assert minR2 <= 1.0
        assert minPoints > 1

    sources = set(table.source.values)
    assert len(sources) == 1
    source = sources.pop()
    polarities = set(table.polarity.values)
    assert len(polarities) == 1, "multiple polarities in table"
    polarity = polarities.pop()

    hypot = mz_reference_table
    hypot.requireColumn("mz_hypot")
    hypot.requireColumn("rtmin")
    hypot.requireColumn("rtmax")
    hypot.requireColumn("name")
    hypot.requireColumn("polarity")
    polarity_hypot = hypot.getColumn("polarity").uniqueValue()
    assert hypot.getColType("mz_hypot") == float, "col mz_hypot is not float"
    assert hypot.getColType("rtmin") == float, "col rtmin is not float"
    assert hypot.getColType("rtmax") == float, "col rtmax is not float"
    assert polarity_hypot == polarity, "polarity of mz reference table (%s)"\
        "does not correspond to polarity of sample tables %s" \
        % (polarity_hypot, polarity)

#    hypot = _buildHypotheseTable(polarity, univ.copy(), fullC13)

    if destination is not None:
        basename = os.path.basename(source)
        fname, _ = os.path.splitext(basename)
        hypot.store(os.path.join(destination, fname + "_hypot.table"), True)

    real, tobe, matches = _findMzMatches(hypot, table, tol)
    if len(real) <= 1:
        print "NOT ENOUGH MATCHES FOR ALIGNMENT"
        return

    if interactive:
        from .. import gui
        gui.inspect(matches, offerAbortOption=True)

    elif len(tobe) < minPoints:
        raise Exception("could only match %d peaks" % len(tobe))

    if not interactive:
        transform, used = _findParametersAutomatically(tobe.copy(), real.copy(),
                                                       minR2, maxTol, minPoints)
    else:
        transform, used = _findParametersManually(tobe.copy(), real.copy())
        if transform is None:
            print "ABORTED"
            return

    if destination is not None:
        matches.addColumn("error", np.linalg.norm(transform(real) - tobe), float,
                          "%.3e")
        matches.store(os.path.join(destination, fname + "_mzalign.table"), True)
        matches.storeCSV(os.path.join(destination, fname + "_mzalign.csv"))

        path = os.path.join(destination, fname + "_mzalign.png")
        _plotAndSaveMatch(tobe, real, used, transform, path)

    transformedTable = _applyTransform(table, transform)
    print "DONE"
    return transformedTable
