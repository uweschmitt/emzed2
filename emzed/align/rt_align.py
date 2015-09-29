# encoding:utf-8


def rtAlign(tables, refTable=None, destination=None, nPeaks=-1,
            numBreakpoints=5, maxRtDifference=100, maxMzDifference=0.3,
            maxMzDifferencePairfinder=0.5, forceAlign=False, resetIntegration=False):

    """ aligns feature tables in respect to retention times.
        the algorithm produces new tables with aligned data.
        **input tables including the assiciatoted peakmap(s) are not modified**.

        Parameters:

        - *nPeaks*: max number of peaks matched by superimposer, -1
          means: all peaks

        - *maxRtDifference*: max allowed difference in rt values for
          searching matching features.

        - *maxMzDifference*: max allowed difference in mz values for
          super imposer.

        - *maxMzDifferencePairfinder*: max allowed difference in mz values
          for pair finding.

        - *numBreakpoints*: number of break points of fitted spline.
          default:5, more points result in splines with higher variation.

        - *forceAlign*: has to be *True* to align already rt aligned tables.

        - *refTable*: extra reference table, if *None* the table
          with most features among *tables* is taken.
    """

    import os.path
    import pyopenms
    import copy
    from ..core.data_types import Table

    assert refTable is None or isinstance(refTable, Table)
    assert destination is None or isinstance(destination, basestring)

    integration_columns = ("method", "area", "params", "rmse")

    found_integrated = False
    for t in tables:
        if all(t.hasColumn(n) for n in integration_columns):
            found_integrated = True
            break

    if found_integrated and not resetIntegration:
        raise Exception("one ot the tables to align is integrated which will turn invalid "
                        "after alignment. Either remove the integration columns, or set\n"
                        "parameter resetIntegration to True")

    if found_integrated and resetIntegration:
        for t in tables:
            if all(t.hasColumn(n) for n in integration_columns):
                for n in integration_columns:
                    t.replaceColumn(n, None)

    for table in tables:
        # collect all maps
        maps = set(table.peakmap.values)
        assert len(maps) == 1, "can only align features from one single peakmap"
        map = maps.pop()
        assert map != None, "None value for peakmaps not allowed"
        if forceAlign:
            map.meta["rt_aligned"] = False
        else:
            if map.meta.get("rt_aligned"):
                raise Exception("there are already rt_aligned peakmaps in the tables. you have to "
                                "to provide the forceAlign parameter of this function to align "
                                "all tables.")
        assert isinstance(table, Table), "non table object in tables"
        table.requireColumn("mz"), "need mz column for alignment"
        table.requireColumn("rt"), "need rt column for alignment"

    if destination is None:
        from .. import gui
        destination = gui.askForDirectory()
        if destination is None:
            print "aborted"
            return

    if refTable is not None:
        maps = set(refTable.peakmap.values)
        assert len(maps) == 1, "can only align features from one single peakmap"
        map = maps.pop()
        assert map != None, "None value for peakmaps not allowed"
        refTable.requireColumn("mz"), "need mz column in reftable"
        refTable.requireColumn("rt"), "need rt column in reftable"

    assert os.path.isdir(os.path.abspath(destination)), "target is no directory"

    # setup algorithm
    algo = pyopenms.MapAlignmentAlgorithmPoseClustering()
    algo.setLogType(pyopenms.LogType.CMD)

    ap = algo.getDefaults()
    ap["max_num_peaks_considered"] = nPeaks
    ap["superimposer:num_used_points"] = nPeaks
    ap["superimposer:mz_pair_max_distance"] = float(maxMzDifferencePairfinder)
    ap["pairfinder:distance_RT:max_difference"] = float(maxRtDifference)
    ap["pairfinder:distance_MZ:max_difference"] = float(maxMzDifference)
    ap["pairfinder:distance_MZ:unit"] = "Da"
    algo.setParameters(ap)

    # convert to pyOpenMS types and find map with max num features which
    # is taken as refamp:
    fms = [(table.toOpenMSFeatureMap(), table) for table in tables]
    if refTable is None:
        refMap, refTable = max(fms, key=lambda (fm, t): fm.size())
        print
        print "REFMAP IS",
        print os.path.basename(refTable.meta.get("source", "<noname>"))
    else:
        if refTable in tables:
            refMap = fms[tables.index(refTable)][0]
        else:
            refMap = refTable.toOpenMSFeatureMap
    results = []
    for fm, table in fms:
        # we do not modify existing table inkl. peakmaps: (rt-values
        # might change below in _transformTable) !
        table = copy.deepcopy(table)
        if fm is refMap:
            results.append(table)
            continue
        sources = set(table.source.values)
        assert len(sources) == 1, "multiple sources in table"
        source = sources.pop()
        filename = os.path.basename(source)
        print
        print "ALIGN FEATURES FROM ", filename
        print
        transformation = _computeTransformation(algo, refMap, fm, numBreakpoints)
        _plot_and_save(transformation, filename, destination)
        _transformTable(table, transformation)
        results.append(table)
    for t in results:
        t.meta["rt_aligned"] = True
    return results


class LowessTrafoHolder(object):

    def __init__(self, trafo, data_points):
        self.trafo = trafo
        self.data_points = data_points

    def getDataPoints(self):
        return self.data_points

    def apply(self, x):
        return trafo.apply(x)


def _computeTransformation(algo, refMap, fm, numBreakpoints):
    # be careful: alignFeatureMaps modifies second arg,
    # so you MUST NOT put the arg as [] into this
    # function ! in this case you have no access to the calculated
    # transformations.
    import pyopenms
    is_v2 = pyopenms.__version__.startswith("2.0.")
    # ts = []
    # index is 1-based, so 1 refers to refMap when calling
    # alignFeatureMaps below:
    algo.setReference(refMap)
    trafo = pyopenms.TransformationDescription()
    if (refMap == fm):
        trafo.fitModel("identity")
    else:
        algo.align(fm, trafo)
        model_params = pyopenms.Param()
        if is_v2:
            model_params.setValue("num_nodes", numBreakpoints, "", [])
            model_params.setValue("wavelength", 0.0, "", [])
            model_params.setValue("boundary_condition", 2, "", [])
            model_params.setValue("extrapolate", "bspline", "", [])
        else:
            pyopenms.TransformationModelBSpline.getDefaultParameters(model_params)
            model_params.setValue("num_breakpoints", numBreakpoints, "", [])
        trafo.fitModel("b_spline", model_params)

        # from here on used:
        # trafo.getDataPoints
        # trafo.apply
        lowess = False
        if lowess:
            dp = trafo.getDataPoints()
            x, y = zip(*dp)
            smoother = None  # smoother_lowess(y, x, frat, iterations)
            trafo = LowessTrafoHolder(smoother, dp)
    return trafo


def _plot_and_save(transformation, filename, destination):
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")  # runs without X-server !
    import pylab
    import os.path
    dtp = transformation.getDataPoints()
    print len(dtp), "matching data points"
    if len(dtp) == 0:
        raise Exception("no matches found.")

    x, y = zip(*dtp)
    x = np.array(x)
    y = np.array(y)
    pylab.clf()
    pylab.plot(x, y - x, ".")
    x.sort()
    yn = [transformation.apply(xi) for xi in x]
    pylab.plot(x, yn - x)
    filename = os.path.splitext(filename)[0] + "_aligned.png"
    target_path = os.path.join(destination, filename)
    print
    print "SAVE", os.path.abspath(target_path)
    print
    pylab.savefig(target_path)


def _transformTable(table, transformation):

    transfun = lambda x: transformation.apply(x)

    table.replaceColumn("rt", table.rt.apply(transfun))
    table.replaceColumn("rtmin", table.rtmin.apply(transfun))
    table.replaceColumn("rtmax", table.rtmax.apply(transfun))

    # we know that there is only one peakmap in the table
    peakmap = table.peakmap.values[0]
    peakmap.meta["rt_aligned"] = True
    table.meta["rt_aligned"] = True
    for spec in peakmap.spectra:
        spec.rt = transformation.apply(spec.rt)
    table.replaceColumn("peakmap", peakmap)
