# encoding: utf-8
from __future__ import print_function

import new

from PyQt4.QtCore import pyqtSignal, Qt
from PyQt4.Qwt5 import QwtScaleDraw, QwtText

from PyQt4.QtGui import QPen

from guiqwt.plot import CurveWidget, PlotManager
from guiqwt.builder import make
from guiqwt.label import ObjectInfo
from guiqwt.shapes import Marker

from guiqwt.shapes import PolygonShape

from modified_guiqwt import EicPlot, RtSelectionTool, SnappingRangeSelection
from modified_guiqwt import make_unselectable_curve, patch_inner_plot_object

from helpers import protect_signal_handler, set_rt_formatting_on_x_axis


import numpy as np


def create_borderless_polygon(points, color):
    shape = PolygonShape(points, closed=True)
    shape.set_selectable(False)
    shape.set_movable(False)
    shape.set_resizable(False)
    shape.set_rotatable(False)
    setup_shape_param(shape, {"fill.alpha": 0.3, "fill.color": color})
    # paint no border:
    shape.pen = QPen(Qt.NoPen)
    return shape


def create_closed_shape(rts, iis, baseline, color):
    rts = np.array(rts)
    iis = np.array(iis)
    perm = np.argsort(rts)
    rts = rts[perm][:, None]  # column vector
    iis = iis[perm][:, None]
    points = np.hstack((rts, iis))  # we need two columns not two rows
    points = points[points[:, 1] >= baseline]
    if len(points):
        rt0 = points[0][0]
        rt1 = points[-1][0]
        points = np.vstack(((rt0, baseline), points, (rt1, baseline)))
        shape = create_borderless_polygon(points, color)
        return shape
    return None


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


def setup_shape_param(item, settings):
    _setup_item(item.shapeparam, settings)
    item.shapeparam.update_shape(item)


def getColor(i):
    colors = "bgrkm"
    return colors[i % len(colors)]



class RangeSelectionInfo(ObjectInfo):

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


class EicPlottingWidget(CurveWidget):

    SELECTED_RANGE_CHANGED = pyqtSignal(float, float)

    def __init__(self, parent=None, with_range=True):
        super(EicPlottingWidget, self).__init__(parent, xlabel="RT", ylabel="I")
        patch_inner_plot_object(self, EicPlot)
        self._setup_plot(with_range)

    def _setup_plot(self, with_range):
        self.pm = PlotManager(self)
        self.pm.add_plot(self.plot)

        t = self.pm.add_tool(RtSelectionTool)
        t.activate()
        self.pm.set_default_tool(t)

        self._setup_cursor()
        self._setup_range_selector(with_range)
        self._setup_label()
        self._setup_axes()

    def _setup_cursor(self):
        marker = Marker(label_cb=self.plot.label_info, constraint_cb=self.plot.on_plot)
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

    def _setup_range_selector(self, with_range):

        if not with_range:
            self.range_ = None
            return

        self.range_ = SnappingRangeSelection(0, 0)

        # you have to register item to plot before you can register the
        # rtSelectionHandler:
        self.plot.add_item(self.range_)
        self.range_.SELECTED_RANGE_CHANGED.connect(self._range_selection_handler)

        cc = make.info_label("TR", [RangeSelectionInfo(self.range_)], title=None)
        setup_label_param(cc, {"label": "", "font.size": 12})
        self.plot.add_item(cc)

    def _setup_label(self):
        label = make.info_label("T", [self.cursor_info], title=None)
        setup_label_param(label, {"label": "", "font.size": 12, "border.color": "#ffffff"})
        self.label = label

    def _setup_axes(self):
        # render tic labels in modfied format:
        set_rt_formatting_on_x_axis(self.plot)
        self.plot.set_axis_title("bottom", "RT")

    def plot_(self, eics):
        self.add_eics(eics)

    def set_cursor_pos(self, rt):
        self.plot.set_rt(rt)

    def add_eics(self, data, labels=None, configs=None):
        """ do not forget to call replot() after calling this function ! """
        allrts = list()

        if configs is None:
            configs = [{"color": getColor(i)} for i in range(len(data))]
        if labels is None:
            labels = [""] * len(data)

        unique_labels = set()
        # items_with_label = []
        seen = set()
        for i, (rts, chromatogram) in enumerate(data):
            # we do not plot duplicates, which might happen if multiple lines in the
            # table explorer are sellected !
            if (id(rts), id(chromatogram)) in seen:
                continue
            seen.add((id(rts), id(chromatogram)))
            config = configs[i]
            label = "<pre>%s</pre>" % labels[i]
            unique_labels.add(label)
            curve = make_unselectable_curve(rts, chromatogram, title=label, **config)
            allrts.extend(rts)
            self.plot.add_item(curve)

        self.plot.add_item(self.label)
        self.plot.set_rts(sorted(set(allrts)))
        # no idea why guiqwt needs double registration here:
        self.marker.attach(self.plot)
        self.plot.add_item(self.marker)

        # self._add_legend(unique_labels, items_with_label)
        if self.range_ is not None:
            self.plot.add_item(self.range_)

    def _add_legend(self, unique_labels, items_with_label):
        # überbleibsel von zeitreihen plott
        unique_labels -= set((None,))
        unique_labels -= set(("",))
        if unique_labels:
            legend = make.legend("TL", restrict_items=items_with_label)
            setup_label_param(legend, {"font.size": 12})
            self.plot.add_item(legend)

    def add_eic_filled(self, rts, iis, baseline, color):
        shape = create_closed_shape(rts, iis, baseline, color)
        if shape is not None:
            self.plot.add_item(shape)

    def set_visible(self, visible):
        self.plot.setVisible(visible)

    def get_range_selection_limits(self):
        if self.range_ is None:
            return None, None
        return sorted((self.range_._min, self.range_._max))

    def set_range_selection_limits(self, xleft, xright):
        if self.range_ is None:
            return
        self.range_.move_point_to(0, (xleft, 0))
        self.range_.move_point_to(1, (xright, 0))

    def reset_intensity_limits(self, imin=None, imax=None, fac=1.1, rtmin=None, rtmax=None):
        self.plot.reset_y_limits(imin, imax, fac, rtmin, rtmax)

    @protect_signal_handler
    def _range_selection_handler(self, left, right):
        min_, max_ = sorted((left, right))
        self.SELECTED_RANGE_CHANGED.emit(min_, max_)

    def set_rt_axis_limits(self, xmin, xmax):
        self.plot.update_plot_xlimits(xmin, xmax)

    def get_limits(self):
        return self.plot.get_plot_limits()

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

    def del_all_items(self):
        self.plot.del_all_items()

    def reset(self):
        """empties plot"""
        self.del_all_items()
        self.replot()

    def shrink_and_replot(self):
        self.plot.replot()
        self.plot.reset_x_limits()
        self.plot.reset_y_limits()
        self.plot.updateAxes()
        self.plot.replot()