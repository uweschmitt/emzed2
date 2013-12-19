# encoding: utf-8


def integrate(ftable, integratorid="std", msLevel=None, showProgress=True, n_cpus=-1,
        min_size_for_parallel_execution=500):
    """ integrates features  in ftable.
        returns processed table. ``ftable`` is not changed inplace.

        The peak integrator corresponding to the integratorId is
        defined in ``algorithm_configs.py`` or ``local_configs.py``

        n_cpus <= 0 has special meaning:
            n_cpus = 0 means "use all cpu cores"
            n_cpus = -1 means "use all but one cpu cores", etc
    """
    import sys
    import multiprocessing
    if sys.platform == "win32":
        # if subprocesses use python.exe a console window pops up for each
        # subprocess. this is quite ugly..
        import os.path
        multiprocessing.set_executable(os.path.join(
                                       os.path.dirname(sys.executable),
                                       "pythonw.exe")
                                       )
    import time
    from ..core.data_types.table import Table

    started = time.time()

    if n_cpus < 0:
        n_cpus = multiprocessing.cpu_count() + n_cpus

    messages = []
    if n_cpus <= 0:
        messages.append("WARNING: you requested to use %d cores, "
                        "we use single core instead !" % n_cpus)
        n_cpus = 1

    if n_cpus > 1 and len(ftable) < min_size_for_parallel_execution:
        messages.append("WARNING: as the table has les thann %d rows, we switch to one cpu mode"
                        % min_size_for_parallel_execution)

    elif n_cpus > multiprocessing.cpu_count():
        messages.append("WARNING: more processes demanded than available cpu cores, this might be "
                        "inefficient")

    if showProgress:
        print
        if messages:
            print "\n".join(messages)
        print "integrate table using", n_cpus, "processes"
        print

    if n_cpus == 1:
        result = _integrate((ftable, integratorid, msLevel, showProgress))
    else:
        pool = multiprocessing.Pool(n_cpus)
        args = []
        all_pms = []
        for i in range(n_cpus):
            subt = ftable[i::n_cpus]
            show_progress = (i == 0)  # only first process prints progress status
            args.append((subt, integratorid, msLevel, show_progress))
            all_pms.append(subt.peakmap.values)

        # map_async() avoids bug of map() when trying to stop jobs using ^C
        tables = pool.map_async(_integrate, args).get()

        # as peakmaps are serialized/unserialized for paralell execution, lots of duplicate
        # peakmaps come back after. we reset those columns to their state before spreading
        # them:
        for t, pms in zip(tables, all_pms):
            t.replaceColumn("peakmap", pms)

        pool.close()
        result = Table.mergeTables(tables)

    if showProgress:
        needed = time.time() - started
        minutes = int(needed) / 60
        seconds = needed - minutes * 60
        print
        if minutes:
            print "needed %d minutes and %.1f seconds" % (minutes, seconds)
        else:
            print "needed %.1f seconds" % seconds
    return result


def _integrate((ftable, integratorid, msLevel, showProgress,)):
    from .._algorithm_configs import peakIntegrators
    from ..core.data_types import Table
    import sys

    assert isinstance(ftable, Table)

    neededColumns = ["mzmin", "mzmax", "rtmin", "rtmax", "peakmap"]
    supportedPostfixes = ftable.supportedPostfixes(neededColumns)
    if not supportedPostfixes:
        raise Exception("is no feature table")

    integrator = dict(peakIntegrators).get(integratorid)
    if integrator is None:
        raise Exception("unknown integrator '%s'" % integratorid)

    resultTable = ftable.copy()

    lastcent = -1
    for postfix in supportedPostfixes:
        areas = []
        rmses = []
        paramss = []
        for i, row in enumerate(ftable.rows):
            if showProgress:
                # integer div here !
                cent = ((i + 1) * 20) / len(ftable) / len(supportedPostfixes)
                if cent != lastcent:
                    print cent * 5,
                    sys.stdout.flush()
                    lastcent = cent
            rtmin = ftable.getValue(row, "rtmin" + postfix)
            rtmax = ftable.getValue(row, "rtmax" + postfix)
            mzmin = ftable.getValue(row, "mzmin" + postfix)
            mzmax = ftable.getValue(row, "mzmax" + postfix)
            peakmap = ftable.getValue(row, "peakmap" + postfix)
            if rtmin is None or rtmax is None or mzmin is None or mzmax is None\
                    or peakmap is None:
                area, rmse, params = (None, ) * 3
            else:
                # this is a hack ! ms level n handling should first be
                # improved and gerenalized in MSTypes.py
                integrator.setPeakMap(peakmap)
                result = integrator.integrate(mzmin, mzmax, rtmin, rtmax,
                                              msLevel)
                # take existing values which are not integration realated:
                area, rmse, params = result["area"], result["rmse"],\
                    result["params"]

            areas.append(area)
            rmses.append(rmse)
            paramss.append(params)

        resultTable._updateColumnWithoutNameCheck("method" + postfix,
                                                  integratorid, str, "%s",
                                                  insertBefore="peakmap" + postfix)

        resultTable._updateColumnWithoutNameCheck("area" + postfix, areas, float,
                                                  "%.2e", insertBefore="peakmap" + postfix)

        resultTable._updateColumnWithoutNameCheck("rmse" + postfix, rmses, float,
                                                  "%.2e", insertBefore="peakmap" + postfix)

        resultTable._updateColumnWithoutNameCheck("params" + postfix, paramss,
                                                  object, None, insertBefore="peakmap" + postfix)

    resultTable.meta["integrated"] = True, "\n"
    resultTable.title = "integrated: " + (resultTable.title or "")
    resultTable.resetInternals()
    return resultTable
