from collections import defaultdict



def collect_children(node, graph, seen=None):
    rv = [node]
    if seen is None:
        seen = set()
    for node2 in graph[node]:
        if node2 not in seen:
            seen.add(node2)
            rv.extend(collect_children(node2, graph, seen))
    return rv

def find_roots(graph):
    return [k for k in graph.keys() if not any(k in v for v in graph.values())]


if __name__ == "__main__":
    graph = { 1: [ 2, 3, 4, 5, 7],
            2: [ 5, 6, 8],
            3: [ 7],
            4: [ 7],
            }


    predecessors = defaultdict(list)
    for (k, v) in graph.items():
        for j in v:
            predecessors[j].append(k)


    print "graph"
    for k, v in graph.items():
        print k, "->", v

    print
    print"reversed"

    for k, v in predecessors.items():
        print k, "->", v

    print

    print "components"
    for i in find_roots(predecessors):
        print "  ", i, "->", collect_children(i, predecessors)
