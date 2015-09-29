import guiqwt
# assert guiqwt.__version__ == "2.1.5", guiqwt.__version__

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

from emzed_optimizations.sample import sample_peaks


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
            return u"<pre>RT: %s ... %s</pre>" % (formatSeconds(rtmin),
                                       formatSeconds(rtmax))
        else:
            return u"<pre>RT: %s</pre>" % formatSeconds(rtmin)


class PlotterBase(object):

    def __init__(self, xlabel, ylabel):
        self.widget = CurveWidget(xlabel=xlabel, ylabel=ylabel)

    def setXAxisLimits(self, xmin, xmax):
        self.widget.plot.update_plot_xlimits(xmin, xmax)

    def updateAxes(self):
        self.widget.plot.updateAxes()

    def setYAxisLimits(self, ymin, ymax):
        self.widget.plot.update_plot_ylimits(ymin, ymax)

    def setMinimumSize(self, a, b):
        self.widget.setMinimumSize(a, b)

    def reset_x_limits(self, xmin=None, xmax=None, fac=1.1):
        self.widget.plot.reset_x_limits(xmin, xmax, fac)

    def reset_y_limits(self, ymin=None, ymax=None, fac=1.1, xmin=None, xmax=None):
        self.widget.plot.reset_y_limits(ymin, ymax, fac, xmin, xmax)

    def set_limit(self, ix, value):
        self.widget.plot.set_limit(ix, value)

    def getLimits(self):
        return self.widget.plot.get_plot_limits()

    def replot(self):
        self.widget.plot.replot()


class RtCursorInfo(ObjectInfo):
    def __init__(self, marker):
        ObjectInfo.__init__(self)
        self.marker = marker
        self.is_time_series = False

    def get_text(self):
        rt = self.marker.xValue()
        if self.is_time_series:
            try:
                txt = str(datetime.fromordinal(int(rt)))
            except:
                txt = ""
        else:
            txt = "<pre>%.2fm</pre>" % (rt / 60.0)
        return txt


class RtPlotter(PlotterBase):

    def __init__(self, rangeSelectionCallback=None):
        super(RtPlotter, self).__init__("RT", "I")

        self.rangeSelectionCallback = rangeSelectionCallback

        widget = self.widget
        widget.plot.__class__ = RtPlot

        self.pm = PlotManager(widget)
        self.pm.add_plot(widget.plot)

        t = self.pm.add_tool(RtSelectionTool)
        self.addTool(RtSelectionTool)
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
        label.labelparam.update_label(label)
        self.label = label

        self.minRTRangeSelected = None
        self.maxRTRangeSelected = None

    def set_rt_x_axis_labels(self):
        # todo: refactor as helper
        a = QwtScaleDraw()
        # render tic labels in modfied format:
        label = lambda self, v: QwtText(formatSeconds(v))
        a.label = new.instancemethod(label, self.widget.plot, QwtScaleDraw)
        self.widget.plot.setAxisScaleDraw(self.widget.plot.xBottom, a)

    def set_ts_x_axis_labels(self):
        # todo: refactor as helper
        a = QwtScaleDraw()
        # render tic labels in modfied format:
        label = lambda self, v: QwtText("") # QwtText(str(v))
        a.label = new.instancemethod(label, self.widget.plot, QwtScaleDraw)
        self.widget.plot.setAxisScaleDraw(self.widget.plot.xBottom, a)

    def addTool(self, tool):
        t = self.pm.add_tool(tool)
        t.activate()

    def reset(self):
        self.plot([])
        self.marker.rts = [0]
        self.replot()

    def plot(self, data, is_time_series=False, titles=None, configs=None,
             withmarker=False):
        """ do not forget to call replot() after calling this function ! """
        allrts = []
        self.widget.plot.del_all_items()

        if is_time_series:
            self.set_ts_x_axis_labels()
            self.widget.plot.set_axis_title("bottom", "time")
        else:
            self.set_rt_x_axis_labels()
            self.widget.plot.set_axis_title("bottom", "RT")
        # self.widget.plot.set_antialiasing(True)
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
                if titles:
                    title = titles[i]
                else:
                    title = ""
                for (x, y) in ts.segments():
                    x = [xi.toordinal() if isinstance(xi, datetime) else xi for xi in x]
                    allrts.extend(x)
                    curve = make.curve(x, y, title=title, **config)
                    curve.__class__ = ModifiedCurveItem
                    self.widget.plot.add_item(curve)
                    self.cursor_info.is_time_series = True
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
                    title = titles[i]
                else:
                    title = ""
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
        if titles is not None:
            self.widget.plot.add_item(make.legend("TL"))
        if not is_time_series:
            self.addRangeSelector(allrts)

    def setEnabled(self, enabled):
        self.widget.plot.setVisible(enabled)

    def addRangeSelector(self, rtvalues):

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
        self.widget.disconnect(range_.plot(), SIG_RANGE_CHANGED,
                               self.rangeSelectionHandler)
        self.widget.connect(range_.plot(), SIG_RANGE_CHANGED,
                            self.rangeSelectionHandler)

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
        self.range_.move_point_to(0, (xleft, 0), emitsignal=False)
        self.range_.move_point_to(1, (xright, 0))
        # calls self.rangeSelectionHandler !
        self.rangeSelectionCallback = saved

    @protect_signal_handler
    def rangeSelectionHandler(self, obj, left, right):
        min_, max_ = sorted((left, right))
        self.minRTRangeSelected = min_
        self.maxRTRangeSelected = max_
        if self.rangeSelectionCallback is not None:
            self.rangeSelectionCallback()


class MzCursorInfo(ObjectInfo):
    def __init__(self, marker, line):
        ObjectInfo.__init__(self)
        self.marker = marker
        self.line = line

    def get_text(self):
        mz, I = self.marker.xValue(), self.marker.yValue()
        txt = "mz=%.6f<br/>I=%.1e" % (mz, I)
        if self.line.isVisible():
            _, _, mz2, I2 = self.line.get_rect()
            mean = (mz + mz2) / 2.0
            txt += "<br/><br/>dmz=%.6f<br/>rI=%.3e<br/>mean=%.6f" % (mz2 - mz, I2 / I, mean)

        return "<pre>%s</pre>" % txt


class MzPlotter(PlotterBase):

    def __init__(self, c_callback=None, image_plot=None):
        super(MzPlotter, self).__init__("m/z", "I")

        self.c_callback = c_callback

        widget = self.widget

        # inject mofified behaviour of wigets plot attribute:
        widget.plot.__class__ = MzPlot
        widget.plot.register_c_callback(self.handle_c_pressed)
        widget.plot.image_plot = image_plot
        self.setHalfWindowWidth(0.05)
        self.centralMz = None

        # todo: refactor as helper
        a = QwtScaleDraw()
        label = lambda self, x: QwtText("%s" % x)
        a.label = new.instancemethod(label, widget.plot, QwtScaleDraw)
        widget.plot.setAxisScaleDraw(widget.plot.xBottom, a)

        self.pm = PlotManager(widget)
        self.pm.add_plot(widget.plot)
        self.curve = make.curve([], [], color='b', curvestyle="Sticks")
        # inject modified behaviour:
        self.curve.__class__ = ModifiedCurveItem

        self.widget.plot.add_item(self.curve)

        t = self.pm.add_tool(MzSelectionTool)
        self.pm.set_default_tool(t)
        t.activate()

        marker = Marker(label_cb=widget.plot.label_info,
                        constraint_cb=widget.plot.on_plot)
        marker.attach(self.widget.plot)

        line = make.segment(0, 0, 0, 0)
        line.__class__ = ModifiedSegment
        line.setVisible(0)

        setupCommonStyle(line, marker)
        line.shapeparam.line.color = "#555555"
        line.shapeparam.update_shape(line)

        label = make.info_label("TR", [MzCursorInfo(marker, line)], title=None)
        label.labelparam.label = ""
        label.labelparam.font.size = 12
        label.labelparam.update_label(label)

        self.marker = marker
        self.label = label
        self.line = line

    def setHalfWindowWidth(self, w2):
        self.widget.plot.set_half_window_width(w2)

    def setCentralMz(self, mz):
        self.widget.plot.set_central_mz(mz)

    def handle_c_pressed(self, p):
        if self.c_callback:
            self.c_callback(p)

    def plot_spectra(self, all_peaks, labels):
        self.widget.plot.del_all_items()
        self.widget.plot.add_item(self.marker)
        self.widget.plot.add_item(make.legend("TL"))
        self.widget.plot.add_item(self.label)

        for i, (peaks, label) in enumerate(zip(all_peaks, labels)):
            config = dict(color=getColor(i))
            curve = make.curve([], [], title=label, curvestyle="Sticks", **config)
            curve.set_data(peaks[:, 0], peaks[:, 1])
            curve.__class__ = ModifiedCurveItem
            self.widget.plot.add_item(curve)
            #self.widget.plot.curves.append(curve)
            self.widget.plot.resample_config = []

        self.widget.plot.add_item(self.line)
        if len(all_peaks):
            self.widget.plot.all_peaks = np.vstack(all_peaks)
        else:
            self.widget.plot.all_peaks = np.zeros((0, 2))


    def plot(self, data, configs=None, titles=None):
        """ do not forget to call replot() after calling this function ! """
        self.widget.plot.del_all_items()
        self.widget.plot.add_item(self.marker)
        if titles is not None:
            self.widget.plot.add_item(make.legend("TL"))
        self.widget.plot.add_item(self.label)

        all_peaks = []
        self.widget.plot.resample_config = []
        self.widget.plot.curves = []
        for i, (pm, rtmin, rtmax, mzmin, mzmax, npeaks) in enumerate(data):
            ms_level = min(pm.getMsLevels())
            if rtmin is None and rtmax is None:
                rtmin, rtmax = pm.rtRange()
            elif rtmin is None:
                rtmin, __ = pm.rtRange()
            elif rtmax is None:
                __, rtmax = pm.rtRange()
            if mzmin is None and mzmax is None:
                mzmin, mzmax = pm.mzRange(ms_level)
            elif mzmin is None:
                mzmin, __ = pm.mzRange(ms_level)
            elif mzmax is None:
                __, mzmax = pm.mzRange(ms_level)
            if npeaks is None:
                npeaks = 3000

            peaks = sample_peaks(pm, rtmin, rtmax, mzmin, mzmax, npeaks, ms_level)
            all_peaks.append(peaks)
            config = configs[i] if configs is not None else None
            if config is None:
                config = dict(color=getColor(i))
            if titles is not None:
                title = titles[i]
            else:
                title = u""
            curve = make.curve([], [], title=title, curvestyle="Sticks", **config)
            curve.set_data(peaks[:, 0], peaks[:, 1])
            curve.__class__ = ModifiedCurveItem
            self.widget.plot.add_item(curve)
            self.widget.plot.curves.append(curve)
            self.widget.plot.resample_config.append((pm, rtmin, rtmax, mzmin, mzmax, npeaks))
        self.widget.plot.add_item(self.line)
        if len(all_peaks):
            self.widget.plot.all_peaks = np.vstack(all_peaks)
        else:
            self.widget.plot.all_peaks = np.zeros((0, 2))


    def resetAxes(self):
        self.widget.plot.reset_x_limits()

    def reset(self):
        self.plot(np.ndarray((0, 2)))
        self.replot()
