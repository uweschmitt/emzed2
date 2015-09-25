# encoding: utf-8


def integrate(ftable, integratorid="std", msLevel=None, showProgress=True, n_cpus=-1,
              min_size_for_parallel_execution=500, eic_widening=30):
    """ integrates features  in ftable.
        returns processed table. ``ftable`` is not changed inplace.

        The peak integrator corresponding to the integratorId is
        defined in ``algorithm_configs.py`` or ``local_configs.py``

        n_cpus <= 0 has special meaning:
            n_cpus = 0 means "use all cpu cores"
            n_cpus = -1 means "use all but one cpu cores", etc

        eic_widinening uses rt limits rtmin - eic_widening .. rtmax + eic_widening
        for extracting an EIC (which is useful for plotting)
    """
    from ..core.data_types.table import Table, PeakMap

    assert isinstance(ftable, Table)

    neededColumns = ["mzmin", "mzmax", "rtmin", "rtmax", "peakmap"]
    supportedPostfixes = ftable.supportedPostfixes(neededColumns)
    if not supportedPostfixes:
        raise Exception("is no feature table")

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

    started = time.time()

    messages = []
    if multiprocessing.current_process().daemon and n_cpus != 1:
        messages.append("WARNING: you choose n_cpus = %d but integrate already runs inside a "
                        "daemon process which is not allowed. therefore set n_cpus = 1" % n_cpus)
        n_cpus = 1

    if n_cpus < 0:
        n_cpus = multiprocessing.cpu_count() + n_cpus

    if n_cpus <= 0:
        messages.append("WARNING: you requested to use %d cores, "
                        "we use single core instead !" % n_cpus)
        n_cpus = 1

    if n_cpus > 1 and len(ftable) < min_size_for_parallel_execution:
        messages.append("INFO: as the table has les thann %d rows, we switch to one cpu mode"
                        % min_size_for_parallel_execution)
        n_cpus = 1

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
        result = _integrate((ftable, supportedPostfixes, integratorid, msLevel, showProgress,
                             eic_widening))
    else:
        pool = multiprocessing.Pool(n_cpus)
        args = []
        all_pms = []
        for i in range(n_cpus):
            subt = ftable[i::n_cpus]
            show_progress = (i == 0)  # only first process prints progress status
            args.append(
                (subt, supportedPostfixes, integratorid, msLevel, show_progress, eic_widening))
            all_pms.append(subt.peakmap.values)

        # map_async() avoids bug of map() when trying to stop jobs using ^C
        tables = pool.map_async(_integrate, args).get()

        # as peakmaps are serialized/unserialized for paralell execution, lots of duplicate
        # peakmaps come back after. we reset those columns to their state before spreading
        # them:
        for t, pms in zip(tables, all_pms):
            t.replaceColumn("peakmap", pms, type_=ftable.getColType("peakmap"),
                            format_=ftable.getColFormat("peakmap"))

        pool.close()

        tables = [t for t in tables if len(t) > 0]
        result = Table.stackTables(tables)

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


def _integrate((ftable, supportedPostfixes, integratorid, msLevel, showProgress, eic_widening)):
    from ..algorithm_configs import peakIntegrators
    from ..core.data_types import Table
    import sys

    integrator = dict(peakIntegrators).get(integratorid)
    if integrator is None:
        raise Exception("unknown integrator '%s'" % integratorid)

    resultTable = ftable.copy()

    lastcent = -1
    for postfix in supportedPostfixes:
        areas = []
        rmses = []
        paramss = []
        eics = []
        baselines = []
        for i, row in enumerate(ftable.rows):
            if showProgress:
                # integer div here !
                cent = ((i + 1) * 20) / len(ftable) / len(supportedPostfixes)
                if cent != lastcent:
                    print cent * 5,
                    try:
                        sys.stdout.flush()
                    except IOError:
                        # migh t happen on win cmd console
                        pass
                    lastcent = cent
            rtmin = ftable.getValue(row, "rtmin" + postfix)
            rtmax = ftable.getValue(row, "rtmax" + postfix)
            mzmin = ftable.getValue(row, "mzmin" + postfix)
            mzmax = ftable.getValue(row, "mzmax" + postfix)
            peakmap = ftable.getValue(row, "peakmap" + postfix)
            if rtmin is None or rtmax is None or mzmin is None or mzmax is None\
                    or peakmap is None:
                area = rmse = params = eic = baseline = None
            else:
                integrator.setPeakMap(peakmap)
                result = integrator.integrate(mzmin, mzmax, rtmin, rtmax, msLevel, eic_widening)
                # take existing values which are not integration realated:
                area = result["area"]
                rmse = result["rmse"]
                params = result["params"]
                eic = result["eic"]
                baseline = result["baseline"]

            areas.append(area)
            rmses.append(rmse)
            paramss.append(params)
            eics.append(eic)
            baselines.append(baseline)

        resultTable._updateColumnWithoutNameCheck("method" + postfix,
                                                  integratorid, str, "%s",
                                                  insertBefore="peakmap" + postfix)

        resultTable._updateColumnWithoutNameCheck("area" + postfix, areas, float,
                                                  "%.2e", insertBefore="peakmap" + postfix)

        resultTable._updateColumnWithoutNameCheck("baseline" + postfix, baselines, float,
                                                  "%.2e", insertBefore="peakmap" + postfix)

        resultTable._updateColumnWithoutNameCheck("rmse" + postfix, rmses, float,
                                                  "%.2e", insertBefore="peakmap" + postfix)

        resultTable._updateColumnWithoutNameCheck("params" + postfix, paramss,
                                                  object, None, insertBefore="peakmap" + postfix)

        resultTable._updateColumnWithoutNameCheck("eic" + postfix, eics,
                                                  object, None, insertBefore="peakmap" + postfix)

    resultTable.meta["integrated"] = True, "\n"
    resultTable.title = "integrated: " + (resultTable.title or "")
    resultTable.resetInternals()
    return resultTable
