from  .elements import MonoIsotopicElements
import re

def monoisotopicMass(mf, **kw):
    elements = MonoIsotopicElements()
    sum_ = 0.0
    for sym, n in re.findall("([A-Z][a-z]?)(\d*)", mf):
        m0 = elements.getProperty(sym, "m0") # (elements.getRowFor(a), "m0")
        overRideData = kw.get(sym)
        if overRideData is not None:
            m0 = overRideData.get("mass", m0)
        if m0 is None:
            return None
        if n == "":
            sum_ += m0
        else:
            sum_ += m0*int(n)
    return sum_


def formulaTable(min_mass, max_mass, C=(0, None),
                                     H=(0, None),
                                     N=(0, None),
                                     O=(0, None),
                                     P=(0, None),
                                     S=(0, None),
                                     prune=True):

    """
    This is a reduced Python version of HR2 formula generator,
    see http://fiehnlab.ucdavis.edu/projects/Seven_Golden_Rules/Software/

    This function generates a table containing molecular formulas consisting of
    elements C, H, N, O, P and S having a mass in range
    [**min_mass**, **max_mass**].
    For each element one can provide an given count or an inclusive range of
    atom counts considered in this process.

    If **prune** is *True*, mass ratio rules (from "seven golden rules") and valence
    bond checks are used to avoid unrealistic compounds in the table, else all formulas explaining
    the given mass range are generated.

    Putting some restrictions on atomcounts, eg **C=(0, 100)**, can speed up
    the process tremendously.

    """
    from ... import mass
    import math
    import collections
    from ..data_types import Table

    if isinstance(C, collections.Sequence):
        cmin, cmax = C
    else:
        cmin = cmax = C

    if isinstance(H, collections.Sequence):
        hmin, hmax = H
    else:
        hmin = hmax = H

    if isinstance(N, collections.Sequence):
        nmin, nmax = N
    else:
        nmin = nmax = N

    if isinstance(O, collections.Sequence):
        omin, omax = O
    else:
        omin = omax = O

    if isinstance(P, collections.Sequence):
        pmin, pmax = P
    else:
        pmin = pmax = P

    if isinstance(S, collections.Sequence):
        smin, smax = S
    else:
        smin = smax = S

    cmax = math.ceil(max_mass / mass.C) if cmax is None else cmax
    hmax = math.ceil(max_mass / mass.H) if hmax is None else hmax
    nmax = math.ceil(max_mass / mass.N) if nmax is None else nmax
    omax = math.ceil(max_mass / mass.O) if omax is None else omax
    pmax = math.ceil(max_mass / mass.P) if pmax is None else pmax
    smax = math.ceil(max_mass / mass.S) if smax is None else smax


    # upper bounds for  x/C ratios:
    hcmax = 6  # 3
    ncmax = 4  # 2
    ocmax = 3  # 1.2
    pcmax = 6  # 0.32
    scmax = 2  # 0.65

    # valence values for bound checks:
    valh = -1
    valc = +2
    valn = 1
    valo = 0
    valp = 3
    vals = 4

    int_range = lambda a, b: xrange(int(a), int(b))

    rows = []

    for c in int_range(cmin, cmax+1):

        resmc_max = max_mass - c*mass.C
        s1 = min(smax, math.floor(resmc_max/mass.S))
        if prune and c > 0:
            s1 = min(s1, scmax * c)

        for s in int_range(smin, s1+1):
            resms_max = resmc_max - s*mass.S
            p1 = min(pmax, math.floor(resms_max/mass.P))
            if prune and c > 0:
                p1 = min(p1, pcmax * c)

            for p in int_range(pmin, p1+1):
                resmp_max = resms_max - p*mass.P
                o1 = min(omax, math.floor(resmp_max/mass.O))
                if prune and c > 0:
                    o1 = min(o1, ocmax * c)

                for o in int_range(omin,o1+1):
                    resmo_max = resmp_max - o*mass.O
                    n1 = min(nmax, math.floor(resmo_max/mass.N))
                    if prune and c > 0:
                        n1 = min(n1, ncmax * c)

                    for n in int_range(nmin, n1+1):
                        resmn_max = resmo_max - n*mass.N
                        h1 = min(hmax, math.floor(resmn_max/mass.H))
                        if prune and c > 0:
                            h1 = min(h1, hcmax * c)

                        for h in int_range(hmin, h1+1):
                            resmh_max = resmn_max - h*mass.H
                            if 0 <= resmh_max <= max_mass-min_mass:
                                bond = (2.0+c*valc+n*valn+o*valo+p*valp \
                                           +s*vals+h*valh)/2.0
                                if not prune or (bond>= 0 and bond % 1 != 0.5):
                                    mf = "C%d.H%d.N%d.O%d.P%d.S%d."  \
                                       % (c, h, n, o, p, s)
                                    mf = mf.replace("C0.", ".")
                                    mf = mf.replace("H0.", ".")
                                    mf = mf.replace("N0.", ".")
                                    mf = mf.replace("O0.", ".")
                                    mf = mf.replace("P0.", ".")
                                    mf = mf.replace("S0.", ".")
                                    mf = mf.replace("C1.", "C.")
                                    mf = mf.replace("H1.", "H.")
                                    mf = mf.replace("N1.", "N.")
                                    mf = mf.replace("O1.", "O.")
                                    mf = mf.replace("P1.", "P.")
                                    mf = mf.replace("S1.", "S.")
                                    mf = mf.replace(".", "")

                                    rows.append([mf, max_mass - resmh_max])
    return Table(["mf", "m0"],[str, float], ["%s", "%.5f"], rows)

