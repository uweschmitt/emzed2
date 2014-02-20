#encoding: utf-8


def _topo_sort_with_in_order(orderings):

    for ordering in orderings:
        assert isinstance(ordering, (list, tuple, str, unicode))

    # give nodes some rank according to first appearance
    # in orderings:
    rank = dict()
    for i, n in enumerate(orderings):
        for ni in n:
            if ni not in rank: # first occurance ?
                rank[ni]=i

    # build graph. each node has follower list, sinks have
    # empty follower list
    nodes = set(ni for n in orderings for ni in n)
    graph = dict()
    for node in nodes:
        graph[node] = set()

    for ordering in orderings:
        for n0, n1 in zip(ordering[:-1], ordering[1:]):
            graph[n0].add(n1)

    # topological sort is easy: remove sinks until graph is empty
    topo_ordering = []

    sinks_to_process = set(n for n in graph if not graph[n])
    while sinks_to_process:
        # here comes special modification: remove sink which appears
        # last in input args of this function:
        current_sink = max(sinks_to_process, key = lambda n: rank[n])

        # remove current sink from todo list
        sinks_to_process.remove(current_sink)
        # update topo_ordering
        topo_ordering.insert(0, current_sink)

        # remove current sink from graph
        del graph[current_sink]
        for followers in graph.values():
            if current_sink in followers:
                followers.remove(current_sink)

        # as we removed sink, maybe new sinks appeared, so
        # update sinks_to_process:
        for n in graph:
            if not graph[n]:
                sinks_to_process.add(n)

    if len(topo_ordering) != len(nodes):
        return None # failed
    return topo_ordering


def _build_starttable(tables, force_merge):
    colname_orders = []
    for table in tables:
        colname_orders.append(table._colNames)

    colum_names = _topo_sort_with_in_order(colname_orders)
    if colum_names is None:
        raise Exception("could not combine all column names to a "\
                "consistent order. you have to provide a reference table")

    types = dict()
    for table in tables:
        for name in table._colNames:
            type_ = table.getType(name)
            expected_type = types.get(name, type_)
            if expected_type != type_:
                msg = "type conflict for column %s: expected %r and got %r" % (name,
                                                                                expected_type,
                                                                                type_)
                if not force_merge:
                    raise Exception(msg)
                print msg
            types[name] = type_

    formats = dict()
    for table in tables:
        for name in table._colNames:
            format_ = table.getFormat(name)
            expected_format = formats.get(name, format_)
            if expected_format != format_:
                msg = "format conflict for column %s: expected %r and got %r" % (name,
                                                                                 expected_format,
                                                                                 format_)
                if not force_merge:
                    raise Exception(msg)
                print msg

            formats[name] = format_

    final_types = [types.get(n) for n in colum_names]
    final_formats = [formats.get(n) for n in colum_names]

    return colum_names, final_types, final_formats

