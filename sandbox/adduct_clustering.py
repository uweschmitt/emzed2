import pdb
import emzed
import sys
import numpy as np

from collections import Counter

table = emzed.io.loadTable("isotope_clustered.table")


try:
    profile
except:
    profile = lambda x: x


delta_C = emzed.mass.C13 - emzed.mass.C12


class IsotopeCluster(object):

    def __init__(self, id_, rts, mzs, mass_trace_ids, iso_ranks, z):
        # assert: iso_ranks sorted in ascending order
        assert len(rts) == len(mzs) == len(mass_trace_ids) == len(iso_ranks)
        assert z in range(5)
        self.id_ = id
        self.rts = np.array(rts)
        self.mzs = np.array(mzs)
        self.mass_trace_ids = mass_trace_ids
        self.z = z
        self.iso_ranks = np.array(iso_ranks)
        if len(iso_ranks)>1:
            if np.max(self.iso_ranks[1:]-self.iso_ranks[:-1]) > 1:
                print id_, mass_trace_ids, iso_ranks

        self.min_rt = min(rts)
        self.max_rt = max(rts)
        self.min_mz = min(mzs)
        self.max_mz = max(mzs)
        self.len_ = len(self.rts)

    def __len__(self):
        return self.len_


class AdductHypothese(object):

    def __init__(self, adduct_i, adduct_j, c_13_shift):
        self.adduct_i = adduct_i
        self.adduct_j = adduct_j
        self.c_13_shift = c_13_shift
        self.name_i, self.mass_shift_i, self.z_i = adduct_i
        self.name_j, self.mass_shift_j, self.z_j = adduct_j

    def matches(self, isocluster_i, isocluster_j):
        m0_i = isocluster_i.mzs * self.z_i - self.mass_shift_i - (isocluster_i.iso_ranks + self.c_13_shift) * delta_C
        m0_j = isocluster_j.mzs * self.z_j - self.mass_shift_j - isocluster_j.iso_ranks * delta_C
        dist_matrix = np.abs(m0_i[:, None] - m0_j[None, :])
        pdb.set_trace() ############################## Breakpoint ##############################
        return np.max(dist_matrix) < 5e-4



table.sortBy("isotope_cluster_id", "isotope_rank")

isotope_clusters = []
for subt in table.splitBy("isotope_cluster_id"):

    id_ = subt.isotope_cluster_id.uniqueValue()
    z = subt.z.uniqueValue()
    rts = subt.rt.values
    mzs = subt.mz.values
    mass_trace_ids = subt.id.values
    iso_ranks = subt.isotope_rank.values
    isotope_clusters.append(IsotopeCluster(id_, rts, mzs, mass_trace_ids, iso_ranks, z))

print "got", len(isotope_clusters), "isotope clusters"

isotope_clusters.sort(key=lambda c: len(c), reverse=True)

adducts = emzed.adducts.negative.adducts

for i, isocluster_i in enumerate(isotope_clusters):
    for j, isocluster_j in enumerate(isotope_clusters):
        if i >= j:
            continue
        hypotheses = []
        for add_i in adducts:
            for add_j in adducts:
                for c_13_shift in [-1, 0, 1]:
                    hypothese = AdductHypothese(add_i, add_j, c_13_shift)
                    if hypothese.matches(isocluster_i, isocluster_j):
                        hypotheses.append(hypothese)
        if len(hypotheses) >= 1:
            print isocluster_i.id_, isocluster_j.id_
            for h in hypothese:
                print "   ", h.add_i, h.add_j, shift







