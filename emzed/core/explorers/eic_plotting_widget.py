# encoding: utf-8
from __future__ import print_function

import new

from PyQt4.QtCore import pyqtSignal
from PyQt4.Qwt5 import QwtScaleDraw, QwtText

from guiqwt.plot import CurveWidget, PlotManager
from guiqwt.builder import make
from guiqwt.label import ObjectInfo
from guiqwt.shapes import Marker

from modified_guiqwt import RtPlot, RtSelectionTool, SnappingRangeSelection, UnselectableCurveItem

from helpers import protect_signal_handler


def _setup_item(param_item, settings):
    for name, value in settings.items():
        sub_item = param_item
        sub_names = name.split(".")
        for field in sub_names[:-1]:
            sub_item = getattr(sub_item, field)
        setattr(sub_item, sub_names[-1], value)


def setup_label_param(item, settings):
    _setup_item(item.labelparam, settings)
    item.labelparam.update_label(item)


def setup_marker_param(item, settings):
    _setup_item(item.markerparam, settings)
    item.markerparam.update_marker(item)


def getColor(i):
    colors = "bgrkm"
    return colors[i % len(colors)]


def formatSeconds(seconds):
    return "%.2fm" % (seconds / 60.0)


class RtRangeSelectionInfo(ObjectInfo):

    def __init__(self, range_):
        ObjectInfo.__init__(self)
        self.range_ = range_

    def get_text(self):
        rtmin, rtmax = sorted(self.range_.get_range())
        if rtmin != rtmax:
            return u"<pre>RT: %s ... %s</pre>" % (formatSeconds(rtmin), formatSeconds(rtmax))
        else:
            return u"<pre>RT: %s</pre>" % formatSeconds(rtmin)


class RtCursorInfo(ObjectInfo):

    def __init__(self, marker):
        ObjectInfo.__init__(self)
        self.marker = marker

    def get_text(self):
        rt = self.marker.xValue()
        txt = "<pre>%.2fm</pre>" % (rt / 60.0)
        return txt


class EICPlotterWidget(CurveWidget):

    SIG_RANGE_SELECTION_CHANGED = pyqtSignal(float, float)

    def __init__(self, parent=None):
        super(EICPlotterWidget, self).__init__(parent, xlabel="RT", ylabel="I")
        self.plot.__class__ = RtPlot
        self._setup_plot()

    def _setup_plot(self):
        self.pm = PlotManager(self)
        self.pm.add_plot(self.plot)

        t = self.pm.add_tool(RtSelectionTool)
        t.activate()
        self.pm.set_default_tool(t)

        self._setup_cursor()
        self._setup_range_selector()
        self._setup_label()
        self._setup_axes()

    def _setup_cursor(self):
        marker = Marker(label_cb=self.plot.label_info,
                        constraint_cb=self.plot.on_plot)
        marker.rts = [0]
        setup_marker_param(marker, {"symbol.size": 0,
                                    "symbol.alpha": 0.0,
                                    "sel_symbol.size": 0,
                                    "sel_symbol.alpha": 0.0,
                                    "line.color": "#909090",
                                    "line.width": 1.0,
                                    "line.style": "SolidLine",
                                    "sel_line.color": "#909090",
                                    "sel_line.width": 1.0,
                                    "sel_line.style": "SolidLine",
                                    "markerstyle": "VLine"})
        marker.attach(self.plot)
        self.marker = marker

        self.cursor_info = RtCursorInfo(marker)

    def _setup_range_selector(self):
        self.range_ = SnappingRangeSelection(0, 0)

        # you have to register item to plot before you can register the
        # rtSelectionHandler:
        self.plot.add_item(self.range_)
        self.range_.SIG_RANGE_CHANGED.connect(self._range_selection_handler)

        cc = make.info_label("TR", [RtRangeSelectionInfo(self.range_)], title=None)
        setup_label_param(cc, {"label": "", "font.size": 12})
        self.plot.add_item(cc)

    def _setup_label(self):
        label = make.info_label("T", [self.cursor_info], title=None)
        setup_label_param(label, {"label": "", "font.size": 12, "border.color": "#ffffff"})
        self.label = label

    def _setup_axes(self):
        # render tic labels in modfied format:
        def label(self, v):
            return QwtText(formatSeconds(v))
        a = QwtScaleDraw()
        a.label = new.instancemethod(label, self.plot, QwtScaleDraw)
        self.plot.setAxisScaleDraw(self.plot.xBottom, a)
        self.plot.set_axis_title("bottom", "RT")

    def plot_(self, eics):
        self.add_eics(eics)

    def add_eics(self, data, labels=None, configs=None):
        """ do not forget to call replot() after calling this function ! """
        allrts = list()

        unique_labels = set()
        legend_items = []
        seen = set()
        for i, (rts, chromatogram) in enumerate(data):
            # we do not plot duplicates, which might happen if multiple lines in the
            # table explorer are sellected !
            if (id(rts), id(chromatogram)) in seen:
                continue
            seen.add((id(rts), id(chromatogram)))
            config = None
            if configs is not None:
                config = configs[i]
            if config is None:
                config = dict(color=getColor(i))
            if labels:
                label = "<pre>%s</pre>" % labels[i]
            else:
                label = ""
            unique_labels.add(label)
            curve = make.curve(rts, chromatogram, title=label, **config)
            # we patch the object:
            curve.__class__ = UnselectableCurveItem
            allrts.extend(rts)
            self.plot.add_item(curve)

        self.plot.add_item(self.label)
        allrts = sorted(set(allrts))
        self.marker.rts = allrts
        # no idea why guiqwt needs double registration here:
        self.marker.attach(self.plot)
        self.plot.add_item(self.marker)

        unique_labels -= set((None,))
        unique_labels -= set(("",))
        if unique_labels:
            legend = make.legend("TL", restrict_items=legend_items)
            setup_label_param(legend, {"font.size": 12})
            self.plot.add_item(legend)

        self.plot.add_item(self.range_)

    def set_visible(self, visible):
        self.plot.setVisible(visible)

    def getRangeSelectionLimits(self):
        return sorted((self.range_._min, self.range_._max))

    def set_range_selection_limits(self, xleft, xright):
        self.range_.move_point_to(0, (xleft, 0))
        self.range_.move_point_to(1, (xright, 0))

    @protect_signal_handler
    def _range_selection_handler(self, left, right):
        min_, max_ = sorted((left, right))
        self.SIG_RANGE_SELECTION_CHANGED.emit(min_, max_)

    def set_rt_axis_limits(self, xmin, xmax):
        self.plot.update_plot_xlimits(xmin, xmax)

    def updateAxes(self):
        self.plot.updateAxes()

    def set_intensity_axis_limits(self, ymin, ymax):
        self.plot.update_plot_ylimits(ymin, ymax)

    def reset_rt_limits(self, rt_min=None, rt_max=None, fac=1.1):
        self.plot.reset_x_limits(rt_min, rt_max, fac)

    def reset_intensitiy_limits(self, i_min=None, i_max=None, fac=1.1, rt_min=None, rt_max=None):
        self.plot.reset_y_limits(i_min, i_max, fac, rt_min, rt_max)

    def set_limit(self, ix, value):
        self.plot.set_limit(ix, value)

    def getLimits(self):
        return self.plot.get_plot_limits()

    def replot(self):
        self.plot.replot()

    def reset(self):
        """empties plot"""
        self.plot.del_all_items()
        self.replot()
