#encoding:utf-8

from ..core.chemistry.tools import formulaTable

formulaTable.__doc__ += """

    Examples:

    .. pycon::

       import emzed
       m0 = emzed.mass.of("C6H12O3")

       mmin, mmax = m0 - 0.01, m0 + 0.01
       print mmin, mmax
       tab = emzed.utils.formulaTable(mmin, mmax)
       print tab

       # reduce output by putting restrictions on atom counts:
       tab = emzed.utils.formulaTable(mmin, mmax, C=6, N=0, P=(0,3), S=0)
       print tab

       # generating all hydrocarbons with a neutral mass below 30:
       tab = emzed.utils.formulaTable(1, 30, C=(1, 100), H=(1,100), N=0, O=0, P=0, S=0, prune=False)
       print tab    !shortentable

    """
