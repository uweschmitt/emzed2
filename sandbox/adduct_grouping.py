import pdb
import emzed
from collections import defaultdict
from itertools import product


class MainPeak(object):

    def __init__(self, id_, mz_main, rt_main, area_main, z, mzs, elements):
        self.id_ = id_
        self.mz_main = mz_main
        self.rt_main = rt_main
        self.area_main = area_main
        self.z = z
        self.mzs = mzs
        self.elements = set(elements)

    def __len__(self):
        return len(self.mzs)


class AdductAssigner(object):

    def __init__(self, mode, mz_tolerance=8e-4, rt_tolerance=5, cl_only_as_adduct=True,
                 allow_acetate=False):

        assert mode == "negative_mode", "other modes not implemented yet"
        self.mode = mode
        self.mz_tolerance = mz_tolerance
        self.rt_tolerance = rt_tolerance
        self.cl_only_as_adduct = cl_only_as_adduct
        self.allow_acetate = allow_acetate

    def process(self, table):

        col_names = table.getColNames()

        assert "isotope_cluster_id" in col_names
        assert "mz" in col_names
        assert "rt" in col_names
        assert "element_names" in col_names
        assert "area" in col_names
        assert "z" in col_names

        peaks, peak_from_id = self._extract_main_peaks(table)
        graph = self._build_graph(peaks)
        groups = self._decompose(graph)
        assigned_adducts = self._resolve_adducts(graph, groups)
        self._enrich_table(table, groups, peak_from_id, assigned_adducts)

        for j, adducts in assigned_adducts.items():
            if len(adducts) > 1:
                print "isotope_cluster=", j, "alternatives=", adducts

    @staticmethod
    def find_consistent_assignments(graph):

        """
        we consider the nodes of the graph as variables and each connection
        represents an constraint.
        so we iterate over all possible variable assignments and check
        the constraints.

        we assume a symmetric graph, that is each starting node occurs in another
        nodes target nodes and vice versa.
        """

        def find_closed_components(graph):
            nodes = set(graph.keys())
            seen = set()
            n = len(nodes)
            while len(seen) < n and nodes:
                start_with = nodes.pop()
                if start_with not in seen:
                    # dfs search starting with 'start_with' node
                    stack = [start_with]
                    component = set()
                    while stack:
                        active_node = stack.pop()
                        seen.add(active_node)
                        component.add(active_node)
                        for follower in graph[active_node]:
                            if follower not in seen and follower not in stack:
                                stack.append(follower)
                    yield component

        nodes = set(graph.keys())

        # we iterativliy look for components which have max size and are consistent
        # with the adduct asignment hypthesises

        TO_OBSERVE = None

        if TO_OBSERVE in nodes:
            import pprint
            pprint.pprint(graph)

        # create map  node -> list of poosible assignments
        assignments = defaultdict(set)
        for in_, v in graph.items():
            if in_ in nodes:
                for out, a0, a1 in v:
                    if out in nodes:
                        assignments[out].add(a1)
                        assignments[in_].add(a0)

        if not(assignments):
            # might happen if nodes are not connected
            return

        # now we iterate over each possible node assignment setting
        # and try to find the best one, aka the one which creates the largest sub graph
        partial_solutions = []
        for assignment in product(*[assignments[k] for k in nodes]):
            if len(set(assignment)) < len(assignment):
                # assignment if same adduct to two isotope clustes
                continue
            if TO_OBSERVE in nodes:
                print assignment
            assignment = dict(zip(nodes, assignment))
            # create sub graph which is consistent with the current assignemtn
            # that is: only one edge per pair of nodes, not multipls
            single_linked_graph = defaultdict(set)
            for in_node, possibilities in graph.items():
                for (out_node, a0, a1) in possibilities:
                    if assignment[in_node] == a0 and assignment[out_node] == a1:
                        single_linked_graph[in_node].add(out_node)

            if TO_OBSERVE in nodes:
                print
                print single_linked_graph

            partial_solution = []
            max_comp_size = -1
            for component in find_closed_components(single_linked_graph):
                if TO_OBSERVE in nodes:
                    print "  ", component

                reduced_assignment = dict((k, v) for (k, v) in assignment.items() if k in
                                          component)
                partial_solution.append(reduced_assignment)
                max_comp_size = max(max_comp_size, len(component))
            if TO_OBSERVE in nodes:
                print max_comp_size, partial_solution
            partial_solutions.append((len(partial_solution), max_comp_size, partial_solution))

        if partial_solutions:
            __, __, max_solution = max(partial_solutions)
            if TO_OBSERVE in nodes:
                print max_solution
            for assignment in max_solution:
                yield assignment

    @staticmethod
    def test_resolve_graph():

        graph = dict(a=[("b", "l0", "l1"), ("c", "l0", "l4"), ("c", "l6", "l5")],
                     b=[("c", "l2", "l3"), ("c", "l1", "l4")],
                     c=[("b", "l4", "l1"), ("b", "l3", "l2"), ("a", "l4", "l0"),
                        ("a", "l5", "l6")])

        found, = AdductAssigner.find_consistent_assignments(graph)
        assert found == dict(a="l0", b="l1", c="l4")

    def _extract_main_peaks(self, table):
        peaks = []
        peak_from_id = dict()
        table.sortBy("isotope_cluster_id")
        for group in table.splitBy("isotope_cluster_id"):
            if group.z.uniqueValue() == 0:
                continue
            id_ = group.isotope_cluster_id.uniqueValue()
            if len(group) == 1:
                main_peak = group
            else:
                main_peak = group.filter(group.isotope_rank == 0)
            mz_main = main_peak.mz.values[0]
            rt_main = main_peak.rt.values[0]
            area_main = main_peak.area.values[0]
            mzs = group.mz.values
            z = group.z.values[0]
            elements = [e.strip() for e in main_peak.element_names.values[0].split(",")]
            peak = MainPeak(id_, mz_main, rt_main, area_main, z, mzs, elements)
            peaks.append(peak)
            peak_from_id[id_] = peak

        return peaks, peak_from_id

    def _build_graph(self, peaks):
        """
        vertices in this graph connect isotope clusters which could represent the
        same adduct
        """
        graph = defaultdict(list)

        if self.mode == "negative_mode":
            adducts = emzed.adducts.negative.adducts
        else:
            adducts = emzed.adducts.positive.adducts

        adducts = [(name, delta, abs(z)) for (name, delta, z) in adducts
                                         if self.allow_acetate or name != "M+CH3COO"]

        rt_tolerance = self.rt_tolerance
        mz_tolerance = self.mz_tolerance

        for i, peak_i in enumerate(peaks):

            mz_i = peak_i.mz_main
            id_i = peak_i.id_
            for (name_i, delta_m_i, z_i) in adducts:
                if self.cl_only_as_adduct and "Cl" in peak_i.elements and "Cl" not in name_i:
                    continue
                if z_i != peak_i.z:
                    continue
                m0_i = mz_i * z_i - delta_m_i
                if m0_i < 0:
                    continue
                for j, peak_j in enumerate(peaks):
                    if i <= j:
                        continue
                    id_j = peak_j.id_
                    mz_j = peak_j.mz_main
                    if abs(peak_j.rt_main - peak_i.rt_main) < rt_tolerance:
                        for (name_j, delta_m_j, z_j) in adducts:
                            if self.cl_only_as_adduct:
                                if "Cl" in peak_j.elements and "Cl" not in name_j:
                                    continue
                            if z_j != peak_j.z:
                                continue
                            m0_j = mz_j * z_j - delta_m_j
                            if m0_j < 0:
                                continue
                            if abs(m0_i - m0_j) <= mz_tolerance:
                                graph[id_i].append((id_j, name_i, name_j))
                                graph[id_j].append((id_i, name_j, name_i))  # make graph symmetric
        return graph

    @staticmethod
    def _decompose(graph):
        """
        decomposes graph in connected components, asserts a symmetric graph
        as built above.
        """
        groups = []

        to_start = set(graph.keys())
        while to_start:
            i = to_start.pop()
            stack = [i]
            group = set()
            while stack:
                i0 = stack.pop()
                if i0 not in group:
                    group.add(i0)
                    if i0 in to_start:
                        to_start.remove(i0)
                    for j, __, __ in graph[i0]:
                        if j not in stack and j not in group:
                            stack.append(j)
            groups.append(group)
        return groups

    def _resolve_adducts(self, graph, groups):
        """
        the graph may contain multiple vertices between two nodes, where each vertex
        represents an adduct assignment for theses nodes.
        this method determines all consistent adduct assignments within each group.
        """

        assigned_adducts = defaultdict(list)

        for group in groups:
            sub_graph = dict((k, values)
                             for (k, values) in graph.items()
                             if k in group and any(v in group for v, __, __ in values))

            # we only consider assignments which annotate the full group:
            full_assignments = []
            for assignment in self.find_consistent_assignments(sub_graph):
                if len(assignment) <= len(group):
                    full_assignments.append(assignment)

            # if the assignemnt is unique we add this information
            if len(full_assignments):
                for k, v in full_assignments[0].items():
                    assigned_adducts[k].append(v)

        return assigned_adducts

    def _enrich_table(self, table, groups, peak_from_id, assigned_adducts):
        """
        adds the calculated assignments as columns to the table
        """

        id_to_group_map = dict()
        for gid, group in enumerate(groups):
            for i in group:
                id_to_group_map[i] = gid


        class AdductGroupAssigner(object):

            """mimmics stateful function"""

            def __init__(self, next_id=len(groups)):
                self.next_id = next_id

            def __call__(self, id_):
                group_id = id_to_group_map.get(id_)
                if group_id is None:
                    group_id = self.next_id
                    id_to_group_map[id_] = group_id
                    self.next_id += 1
                return group_id

        def assign_adducts(id_):
            return ", ".join(assigned_adducts.get(id_, ""))

        table.addColumn("adduct_group",
                        table.isotope_cluster_id.apply(AdductGroupAssigner()),
                        insertBefore="element_names")

        table.addColumn("possible_adducts",
                        table.isotope_cluster_id.apply(assign_adducts),
                        insertBefore="element_names")


if __name__ == "__main__":

    #table = emzed.io.loadTable("S9_isotope_clustered.table")
    #cnames1 = table.getColNames()
    import glob
    #for p in glob.glob("201311*.table"):
    p = "b5_isotope_grouped.table"
    if p:
        print p
        table = emzed.io.loadTable(p)
        #emzed.gui.inspect(table)
        #table.dropColumns("adduct_group", "possible_adducts")
        AdductAssigner("negative_mode").process(table)
        emzed.gui.inspect(table)
        #emzed.io.storeTable(table, p, True)
