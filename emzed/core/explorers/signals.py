# encoding: utf-
from __future__ import print_function

try:
    from guiqwt.signals import *
except ImportError:
    # new guiqwt
    from guiqwt.events import QtDragHandler
    from guiqwt.curve import CurvePlot
    from guiqwt.baseplot import BasePlot

    # we import some signals defined within classes to module scope:
    for clz in (BasePlot, CurvePlot, QtDragHandler):
        _signals = dict((n, h) for n, h in vars(clz).items() if n.startswith("SIG_"))
        vars().update(_signals)


