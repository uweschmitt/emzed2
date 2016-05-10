from guiqwt.plot import CurveWidget, PlotManager
from guiqwt.builder import make
from guiqwt.label import ObjectInfo

from modified_guiqwt import *
from config import setupStyleRangeMarker, setupCommonStyle, setupStyleRtMarker

from PyQt4.Qwt5 import QwtScaleDraw, QwtText

import numpy as np
import new

from datetime import datetime

from helpers import protect_signal_handler


def find_datetime_split_pos(datetimes):
    if len(datetimes) == 0:
        return None
    dtstrs = [str(dt).split(".")[0] for dt in datetimes if dt is not None]
    date_time_tuples = [dtstr.split(" ") for dtstr in dtstrs]
    dates, times = zip(*date_time_tuples)
    if len(set(times)) == 1:
        return 1
    return 2


def format_datetime_value(pos, dt):
    if isinstance(dt, (int, long, float)):
        dt = datetime.fromordinal(int(dt))
    dt = str(dt)
    if pos is None:
        return dt
    dtstr = dt.split(".")[0]
    date_time_str = " ".join(dtstr.split(" ")[:pos])
    return date_time_str


def getColor(i):
    colors = "bgrkm"
    return colors[i % len(colors)]


class PlotterBase(object):

    def __init__(self, xlabel, ylabel):
        self.widget = CurveWidget(xlabel=xlabel, ylabel=ylabel)

    def set_rt_axis_limits(self, xmin, xmax):
        self.widget.plot.update_plot_xlimits(xmin, xmax)

    def updateAxes(self):
        self.widget.plot.updateAxes()

    def set_intensity_axis_limits(self, ymin, ymax):
        self.widget.plot.update_plot_ylimits(ymin, ymax)

    def setMinimumSize(self, a, b):
        self.widget.setMinimumSize(a, b)

    def reset_x_limits(self, xmin=None, xmax=None, fac=1.1):
        self.widget.plot.reset_x_limits(xmin, xmax, fac)

    def reset_y_limits(self, ymin=None, ymax=None, fac=1.1, xmin=None, xmax=None):
        self.widget.plot.reset_y_limits(ymin, ymax, fac, xmin, xmax)

    def _x_set_limit(self, ix, value):
        self.widget.plot.set_limit(ix, value)

    def get_limits(self):
        return self.widget.plot.get_plot_limits()

    def replot(self):
        self.widget.plot.replot()


class RtPlotter(PlotterBase):

    def __init__(self, parent=None, rangeSelectionCallback=None):

        PlotterBase.__init__(self, "RT", "I")

        self.rangeSelectionCallback = rangeSelectionCallback

        widget = self.widget
        widget.plot.__class__ = RtPlot

        self.pm = PlotManager(widget)
        self.pm.add_plot(widget.plot)

        t = self.pm.add_tool(RtSelectionTool)
        t.activate()
        self.pm.set_default_tool(t)

        marker = Marker(label_cb=self.widget.plot.label_info,
                        constraint_cb=self.widget.plot.on_plot)
        marker.rts = [0]
        setupStyleRtMarker(marker)
        marker.attach(self.widget.plot)
        self.marker = marker

        self.cursor_info = RtCursorInfo(marker)
        label = make.info_label("T", [self.cursor_info], title=None)
        label.labelparam.label = ""
        label.labelparam.font.size = 12
        label.labelparam.border.color = "#ffffff"
        label.labelparam.update_label(label)
        self.label = label

        self.minRTRangeSelected = None
        self.maxRTRangeSelected = None

    def _set_rt_x_axis_labels(self):
        # todo: refactor as helper
        a = QwtScaleDraw()
        # render tic labels in modfied format:
        label = lambda self, v: QwtText(formatSeconds(v))
        a.label = new.instancemethod(label, self.widget.plot, QwtScaleDraw)
        self.widget.plot.setAxisScaleDraw(self.widget.plot.xBottom, a)

    def _set_ts_x_axis_labels(self, data):
        # todo: refactor as helper
        all_ts = [tsi for ts in data for tsi in ts.x]
        pos = find_datetime_split_pos(all_ts)
        a = QwtScaleDraw()
        # render tic labels in modfied format:
        label = lambda self, v, pos=pos: QwtText(format_datetime_value(pos, v)) # QwtText(str(v))
        a.label = new.instancemethod(label, self.widget.plot, QwtScaleDraw)
        self.widget.plot.setAxisScaleDraw(self.widget.plot.xBottom, a)


    def reset(self):
        """empties plot"""
        self.plot([])
        self.marker.rts = [0]
        self.replot()

    def plot(self, data, is_time_series=False, titles=None, configs=None,
             withmarker=False):
        """ do not forget to call replot() after calling this function ! """
        allrts = []
        self.widget.plot.del_all_items()

        if is_time_series:
            self._set_ts_x_axis_labels(data)
            self.widget.plot.set_axis_title("bottom", "time")
        else:
            self._set_rt_x_axis_labels()
            self.widget.plot.set_axis_title("bottom", "RT")

        labels = set()
        legend_items = []
        if is_time_series:
            seen = set()
            for i, ts in enumerate(data):
                # we do not plot duplicates, which might happen if multiple lines in the
                # table explorer are sellected !
                if id(ts) in seen:
                    continue
                seen.add(id(ts))
                config = None
                if configs is not None:
                    config = configs[i]
                if config is None:
                    config = dict(color=getColor(i))
                title = ts.label
                labels.add(title)
                for j, (x, y) in enumerate(ts.for_plotting()):
                    x = [xi.toordinal() if isinstance(xi, datetime) else xi for xi in x]
                    allrts.extend(x)
                    curve = make.curve(x, y, title="<pre>%s</pre>" % title, **config)
                    curve.__class__ = ModifiedCurveItem
                    self.widget.plot.add_item(curve)
                    self.cursor_info.is_time_series = True
                    if j == 0:
                        legend_items.append(curve)
        else:
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
                if titles:
                    title = "<pre>%s</pre>" % titles[i]
                else:
                    title = ""
                labels.add(title)
                curve = make.curve(rts, chromatogram, title=title, **config)
                curve.__class__ = ModifiedCurveItem
                allrts.extend(rts)
                self.widget.plot.add_item(curve)
                self.cursor_info.is_time_series = False


        if withmarker:
            self.widget.plot.add_item(self.label)
            allrts = sorted(set(allrts))
            self.marker.rts = allrts
            self.marker.attach(self.widget.plot)
            self.widget.plot.add_item(self.marker)

        labels -= set((None,))
        labels -= set(("",))
        if labels:
            legend = make.legend("TL", restrict_items=legend_items)
            legend.labelparam.font.size = 12
            legend.labelparam.update_label(legend)
            self.widget.plot.add_item(legend)
        if not is_time_series:
            self._add_range_selector(allrts)

    def setEnabled(self, enabled):
        self.widget.plot.setVisible(enabled)

    def _add_range_selector(self, rtvalues):

        self.rtvalues = rtvalues
        self.minRTRangeSelected = 0
        self.maxRTRangeSelected = 0

        range_ = SnappingRangeSelection(self.minRTRangeSelected,
                                        self.maxRTRangeSelected, self.rtvalues)
        setupStyleRangeMarker(range_)
        self.range_ = range_

        # you have to register item to plot before you can register the
        # rtSelectionHandler:
        self.widget.plot.add_item(range_)
        range_.SIG_RANGE_CHANGED.connect(self._range_selection_handler)
        #self.widget.disconnect(range_.plot(), SIG_RANGE_CHANGED,
                               #self._range_selection_handler)
        #self.widget.connect(range_.plot(), SIG_RANGE_CHANGED,
                            #self._range_selection_handler)

        cc = make.info_label("TR", [RtRangeSelectionInfo(range_)], title=None)
        cc.labelparam.label = ""
        cc.labelparam.font.size = 12
        cc.labelparam.update_label(cc)
        self.widget.plot.add_item(cc)

    def getRangeSelectionLimits(self):
        return sorted((self.range_._min, self.range_._max))

    def setRangeSelectionLimits(self, xleft, xright):
        saved = self.rangeSelectionCallback
        self.rangeSelectionCallback = None
        self.minRTRangeSelected = xleft
        self.maxRTRangeSelected = xright
        # left and right bar of range marker
        self.range_.move_point_to(0, (xleft, 0))
        self.range_.move_point_to(1, (xright, 0))
        self.rangeSelectionCallback = saved

    @protect_signal_handler
    def _range_selection_handler(self, obj, left, right):
        min_, max_ = sorted((left, right))
        self.minRTRangeSelected = min_
        self.maxRTRangeSelected = max_
        if self.rangeSelectionCallback is not None:
            self.rangeSelectionCallback()

    reset_rt_limits = PlotterBase.reset_x_limits
    reset_intensity_limits = PlotterBase.reset_y_limits
