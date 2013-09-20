# -*- coding: utf-8 -*-

import os
import types
import numpy as np

from PyQt4.QtGui import (QDialog, QGridLayout, QSlider, QLabel, QCheckBox,
                         QComboBox)
from PyQt4.QtCore import Qt, SIGNAL, QRectF, QPointF
from PyQt4.Qwt5 import QwtScaleDraw, QwtText

import guidata

from guiqwt.builder import make
from guiqwt.config import CONF
from guiqwt.events import (KeyEventMatch, QtDragHandler, PanHandler, MoveHandler, ZoomHandler,)
from guiqwt.image import RawImageItem, ImagePlot
from guiqwt.label import ObjectInfo
from guiqwt.plot import ImageWidget, CurveWidget, CurvePlot
from guiqwt.shapes import RectangleShape
from guiqwt.signals import (SIG_MOVE, SIG_START_TRACKING, SIG_STOP_NOT_MOVING, SIG_STOP_MOVING,
                            SIG_PLOT_AXIS_CHANGED, )
from guiqwt.tools import SelectTool, InteractiveTool

from emzed_optimizations.sample import sample_image

from plotting_widgets import MzPlotter

from helpers import protect_signal_handler


SIG_HISTORY_CHANGED = SIGNAL('plot_history_changed(PyQt_PyObject)')


def set_x_axis_scale_draw(widget):
    """ formats ticks on time axis as minutes """
    drawer = QwtScaleDraw()
    formatSeconds = lambda v: "%.2fm" % (v / 60.0)
    format_label = lambda self, v: QwtText(formatSeconds(v))
    drawer.label = types.MethodType(format_label, widget.plot, QwtScaleDraw)
    widget.plot.setAxisScaleDraw(widget.plot.xBottom, drawer)


def set_y_axis_scale_draw(widget):
    """ sets minimum extent for aligning chromatogram and peakmap plot """
    drawer = QwtScaleDraw()
    drawer.setMinimumExtent(50)
    widget.plot.setAxisScaleDraw(widget.plot.yLeft, drawer)


class PeakMapImageItem(RawImageItem):

    """ draws peakmap 2d view dynamically based on given limits """

    def __init__(self, peakmap):
        super(PeakMapImageItem, self).__init__(np.zeros((1, 1), np.uint8))

        self.peakmap = peakmap

        rtmin, rtmax = self.peakmap.rtRange()
        mzmin, mzmax = self.peakmap.mzRange()

        self.bounds = QRectF(QPointF(rtmin, mzmin),
                             QPointF(rtmax, mzmax))
        self.update_border()
        self.IMAX = 255
        self.set_lut_range([0, self.IMAX])
        self.set_color_map("hot")

        self.total_imin = 0.0
        self.total_imax = max(np.max(s.peaks[:, 1]) for s in peakmap.spectra)

        self.imin = self.total_imin
        self.imax = self.total_imax

        self.gamma = 1.0

        self.is_log = 1

    def set_imin(self, imin):
        self.imin = imin

    def set_imax(self, imax):
        self.imax = imax

    def set_gamma(self, gamma):
        self.gamma = gamma

    def get_total_imax(self):
        return self.total_imax

    def set_logarithmic_scale(self, is_log):
        self.is_log = is_log

    #---- QwtPlotItem API ------------------------------------------------------
    def draw_image(self, painter, canvasRect, srcRect, dstRect, xMap, yMap):
        x1, y1 = canvasRect.left(), canvasRect.top()
        x2, y2 = canvasRect.right(), canvasRect.bottom()
        i1, j1, i2, j2 = srcRect

        NX = x2 - x1
        NY = y2 - y1
        rtmin, rtmax = i1, i2
        mzmin, mzmax = j2, j1

        # optimized:
        data = sample_image(self.peakmap, rtmin, rtmax, mzmin, mzmax, NX, NY)

        # turn up/down
        data = data[::-1, :]
        imin = self.imin
        imax = self.imax

        if self.is_log:
            data = np.log(1.0 + data)
            imin = np.log(1.0 + imin)
            imax = np.log(1.0 + imax)

        data[data < imin] = imin
        data[data > imax] = imax
        data -= imin

        # enlarge single pixels to 2 x 2 pixels:
        smoothed = data[:-1, :-1] + data[:-1, 1:] + data[1:, :-1] + data[1:, 1:]

        # scale to 1.0
        maxd = np.max(smoothed)
        if maxd:
            smoothed /= maxd

        # apply gamma
        smoothed = smoothed ** (self.gamma) * 256
        self.data = smoothed

        # draw
        srcRect = (0, 0, NX, NY)
        x1, y1, x2, y2 = canvasRect.getCoords()
        RawImageItem.draw_image(self, painter, canvasRect, srcRect, (x1, y1, x2, y2), xMap, yMap)


class PeakmapCursorRangeInfo(ObjectInfo):

    def __init__(self, marker):
        ObjectInfo.__init__(self)
        self.marker = marker

    def get_text(self):
        rtmin, mzmin, rtmax, mzmax = self.marker.get_rect()
        if not np.isnan(rtmax):
            rtmin, rtmax = sorted((rtmin, rtmax))
        if not np.isnan(mzmax):
            mzmin, mzmax = sorted((mzmin, mzmax))
        if not np.isnan(rtmax):
            delta_mz = mzmax - mzmin
            delta_rt = rtmax - rtmin
            line0 = "mz: %10.5f ..  %10.5f (delta=%5.5f)" % (mzmin, mzmax, delta_mz)
            line1 = "rt:  %6.2fm   ..   %6.2fm   (delta=%.1fs)" % (rtmin / 60.0,
                                                                   rtmax / 60.0,
                                                                   delta_rt)
            return "<pre>%s</pre>" % "<br>".join((line0, line1))
        else:
            return """<pre>mz: %9.5f<br>rt: %6.2fm</pre>""" % (mzmin, rtmin / 60.0)


class RtCursorInfo(ObjectInfo):

    def __init__(self):
        ObjectInfo.__init__(self)
        self.rt = None

    def set_rt(self, rt):
        self.rt = rt

    def get_text(self):
        if self.rt is None:
            return ""
        return "<pre>rt: %.1f sec<br>  = %.2fm</pre>" % (self.rt, self.rt / 60.0)


class PeakmapZoomTool(InteractiveTool):

    """ selects rectangle from peakmap """

    TITLE = "Selection"
    ICON = "selection.png"
    CURSOR = Qt.CrossCursor

    def setup_filter(self, baseplot):
        filter = baseplot.filter
        # Initialisation du filtre

        start_state = filter.new_state()

        hist_back_keys = [(Qt.Key_Z, Qt.ControlModifier), Qt.Key_Left]
        filter.add_event(start_state, KeyEventMatch(hist_back_keys),
                         baseplot.go_back_in_history, start_state)

        hist_forward_keys = [(Qt.Key_Y, Qt.ControlModifier), Qt.Key_Right]
        filter.add_event(start_state, KeyEventMatch(hist_forward_keys),
                         baseplot.go_forward_in_history, start_state)

        filter.add_event(start_state,
                         KeyEventMatch((Qt.Key_Backspace, Qt.Key_Escape, Qt.Key_Home)),
                         baseplot.go_to_beginning_of_history, start_state)

        filter.add_event(start_state,
                         KeyEventMatch((Qt.Key_End,)),
                         baseplot.go_to_end_of_history, start_state)

        handler = QtDragHandler(filter, Qt.LeftButton, start_state=start_state)
        self.connect(handler, SIG_MOVE, baseplot.move_in_drag_mode)
        self.connect(handler, SIG_START_TRACKING, baseplot.start_drag_mode)
        self.connect(handler, SIG_STOP_NOT_MOVING, baseplot.stop_drag_mode)
        self.connect(handler, SIG_STOP_MOVING, baseplot.stop_drag_mode)

        handler = QtDragHandler(
            filter, Qt.LeftButton, start_state=start_state, mods=Qt.ShiftModifier)
        self.connect(handler, SIG_MOVE, baseplot.move_in_drag_mode)
        self.connect(handler, SIG_START_TRACKING, baseplot.start_drag_mode)
        self.connect(handler, SIG_STOP_NOT_MOVING, baseplot.stop_drag_mode)
        self.connect(handler, SIG_STOP_MOVING, baseplot.stop_drag_mode)

        # Bouton du milieu
        PanHandler(filter, Qt.MidButton, start_state=start_state)
        # AutoZoomHandler(filter, Qt.MidButton, start_state=start_state)

        # Bouton droit
        ZoomHandler(filter, Qt.RightButton, start_state=start_state)
        # MenuHandler(filter, Qt.RightButton, start_state=start_state)

        # Autres (touches, move)
        MoveHandler(filter, start_state=start_state)
        MoveHandler(filter, start_state=start_state, mods=Qt.ShiftModifier)
        MoveHandler(filter, start_state=start_state, mods=Qt.AltModifier)

        return start_state


class History(object):

    def __init__(self):
        self.position = -1
        self.items = []

    def new_head(self, item):
        del self.items[self.position + 1:]
        self.items.append(item)
        self.position += 1

    def go_back(self):
        if self.position > 0:
            self.position -= 1
            return self.items[self.position]
        return None

    def go_forward(self):
        if self.position < len(self.items) - 1:
            self.position += 1
            return self.items[self.position]
        return None

    def skip_to_beginning(self):
        if self.position > 0:
            self.position = 0
            return self.items[self.position]
        return None

    def skip_to_end(self):
        if self.position < len(self.items) - 1:
            self.position = len(self.items) - 1
            return self.items[self.position]
        return None

    def set_position(self, position):
        if 0 <= position < len(self.items) and position != self.position:
            self.position = position
            return self.items[self.position]
        return None


class ChromatogramPlot(CurvePlot):

    def label_info(self, x, y):
        return "label_info"

    def on_plot(self, x, y):
        return (x, y)

    @protect_signal_handler
    def do_move_marker(self, event):
        pos = event.pos()
        self.set_marker_axes()
        self.cross_marker.setZ(self.get_max_z() + 1)
        self.cross_marker.setVisible(True)
        self.cross_marker.move_local_point_to(0, pos)
        self.replot()

    def do_zoom_view(self, dx, dy, lock_aspect_ratio=False):
        """ disables zoom """
        pass

    def do_pan_view(self, dx, dy):
        """ disables panning """
        pass

    def plot_chromatogram(self, rts, chroma):
        self.del_all_items()
        curve = make.curve(rts, chroma, linewidth=1.5, color="#666666")
        self.add_item(curve)
        self.add_item(self.rt_label)
        rtmin = min(rts)
        rtmax = max(rts)
        self.set_plot_limits(rtmin, rtmax, 0, max(chroma) if len(chroma) else 1.0)
        self.updateAxes()
        self.replot()


class ModifiedImagePlot(ImagePlot):

    """ special handlers for dragging selection, source is PeakmapZoomTool """

    # as this class is used for patching, the __init__ is never called, so we set default
    # values as class atributes:

    rtmin = rtmax = mzmin = mzmax = None
    coords = (None, None)

    history = History()

    def set_limits(self, rtmin, rtmax, mzmin, mzmax, add_to_history):
        self.rtmin = rtmin
        self.rtmax = rtmax
        self.mzmin = mzmin
        self.mzmax = mzmax
        self.set_plot_limits(rtmin, rtmax, mzmin, mzmax, "bottom", "right")
        self.set_plot_limits(rtmin, rtmax, mzmin, mzmax, "top", "left")

        if add_to_history:
            self.history.new_head((rtmin, rtmax, mzmin, mzmax))
            self.emit(SIG_HISTORY_CHANGED, self.history)

    @protect_signal_handler
    def go_back_in_history(self, filter_, evt):
        item = self.history.go_back()
        if item is not None:
            rtmin, rtmax, mzmin, mzmax = item
            self.set_limits(rtmin, rtmax, mzmin, mzmax, add_to_history=False)
            self.replot()
            self.emit(SIG_PLOT_AXIS_CHANGED, self)
            self.emit(SIG_HISTORY_CHANGED, self.history)

    @protect_signal_handler
    def go_forward_in_history(self, filter_, evt):
        item = self.history.go_forward()
        if item is not None:
            rtmin, rtmax, mzmin, mzmax = item
            self.set_limits(rtmin, rtmax, mzmin, mzmax, add_to_history=False)
            self.replot()
            self.emit(SIG_PLOT_AXIS_CHANGED, self)
            self.emit(SIG_HISTORY_CHANGED, self.history)

    @protect_signal_handler
    def go_to_beginning_of_history(self, filter_, evt):
        """ resets zoom """
        item = self.history.skip_to_beginning()
        if item is not None:
            rtmin, rtmax, mzmin, mzmax = item
            self.set_limits(rtmin, rtmax, mzmin, mzmax, add_to_history=False)
            self.replot()
            self.emit(SIG_PLOT_AXIS_CHANGED, self)
            self.emit(SIG_HISTORY_CHANGED, self.history)

    @protect_signal_handler
    def go_to_end_of_history(self, filter_, evt):
        item = self.history.skip_to_end()
        if item is not None:
            rtmin, rtmax, mzmin, mzmax = item
            self.set_limits(rtmin, rtmax, mzmin, mzmax, add_to_history=False)
            self.replot()
            self.emit(SIG_PLOT_AXIS_CHANGED, self)
            self.emit(SIG_HISTORY_CHANGED, self.history)

    def set_history_position(self, idx):
        item = self.history.set_position(idx)
        if item is not None:
            rtmin, rtmax, mzmin, mzmax = item
            self.set_limits(rtmin, rtmax, mzmin, mzmax, add_to_history=False)
            self.replot()
            self.emit(SIG_PLOT_AXIS_CHANGED, self)

    def get_coords(self, evt):
        return self.invTransform(self.xBottom, evt.x()), self.invTransform(self.yLeft, evt.y())

    def get_items_of_class(self, clz):
        for item in self.items:
            if isinstance(item, clz):
                yield item

    def get_unique_item(self, clz):
        items = set(self.get_items_of_class(clz))
        if len(items) == 0:
            return None
        if len(items) != 1:
            raise Exception("%d instance(s) of %s among CurvePlots items !" % (len(items), clz))
        return items.pop()

    @protect_signal_handler
    def do_move_marker(self, event):
        pos = event.pos()
        self.set_marker_axes()
        self.cross_marker.setZ(self.get_max_z() + 1)
        self.cross_marker.setVisible(True)
        self.cross_marker.move_local_point_to(0, pos)
        self.replot()

    @protect_signal_handler
    def start_drag_mode(self, filter_, evt):
        self.start_at = self.get_coords(evt)
        self.moved = False
        marker = self.get_unique_item(RectangleShape)
        marker.set_rect(self.start_at[0], self.start_at[1], self.start_at[0], self.start_at[1])
        self.cross_marker.setVisible(False)  # no cross marker when dragging
        self.rect_label.setVisible(1)
        self.with_shift_key = evt.modifiers() == Qt.ShiftModifier
        self.replot()

    @protect_signal_handler
    def move_in_drag_mode(self, filter_, evt):
        now = self.get_coords(evt)
        rect_marker = self.get_unique_item(RectangleShape)
        rect_marker.setVisible(1)
        now_rt = max(self.rtmin, min(now[0], self.rtmax))
        now_mz = max(self.mzmin, min(now[1], self.mzmax))
        rect_marker.set_rect(self.start_at[0], self.start_at[1], now_rt, now_mz)
        self.moved = True
        self.replot()

    def mouseReleaseEvent(self, evt):
        # stop drag mode is not called immediatly when dragging and releasing shift
        # during dragging.
        self.stop_drag_mode(None, evt)

    @protect_signal_handler
    def stop_drag_mode(self, filter_, evt):
        stop_at = self.get_coords(evt)
        rect_marker = self.get_unique_item(RectangleShape)
        rect_marker.setVisible(0)

        # reactivate cursor
        self.cross_marker.set_pos(stop_at[0], stop_at[1])
        self.cross_marker.setZ(self.get_max_z() + 1)

        # passing None here arives as np.nan if you call get_rect later, so we use
        # np.nan here:
        rect_marker.set_rect(stop_at[0], stop_at[1], np.nan, np.nan)

        if self.moved and not self.with_shift_key:
            rtmin, rtmax = self.start_at[0], stop_at[0]
            # be sure that rtmin <= rtmax:
            rtmin, rtmax = min(rtmin, rtmax), max(rtmin, rtmax)

            mzmin, mzmax = self.start_at[1], stop_at[1]
            # be sure that mzmin <= mzmax:
            mzmin, mzmax = min(mzmin, mzmax), max(mzmin, mzmax)

            # keep coordinates in peakmap:
            rtmin = max(self.rtmin, min(self.rtmax, rtmin))
            rtmax = max(self.rtmin, min(self.rtmax, rtmax))
            mzmin = max(self.mzmin, min(self.mzmax, mzmin))
            mzmax = max(self.mzmin, min(self.mzmax, mzmax))

            self.set_limits(rtmin, rtmax, mzmin, mzmax, add_to_history=True)

            # first replot, then emit signal is important, so that new axis are avail in
            # signal handler
            self.replot()
            self.emit(SIG_PLOT_AXIS_CHANGED, self)
        else:
            self.replot()

    @protect_signal_handler
    def do_zoom_view(self, dx, dy, lock_aspect_ratio=False):
        """
        modified version of do_zoom_view from base class,
        we restrict zooming and panning to ranges of peakmap.

        Change the scale of the active axes (zoom/dezoom) according to dx, dy
        dx, dy are tuples composed of (initial pos, dest pos)
        We try to keep initial pos fixed on the canvas as the scale changes
        """
        # See guiqwt/events.py where dx and dy are defined like this:
        #   dx = (pos.x(), self.last.x(), self.start.x(), rct.width())
        #   dy = (pos.y(), self.last.y(), self.start.y(), rct.height())
        # where:
        #   * self.last is the mouse position seen during last event
        #   * self.start is the first mouse position (here, this is the
        #     coordinate of the point which is at the center of the zoomed area)
        #   * rct is the plot rect contents
        #   * pos is the current mouse cursor position
        auto = self.autoReplot()
        self.setAutoReplot(False)
        dx = (-1,) + dx  # adding direction to tuple dx
        dy = (1,) + dy  # adding direction to tuple dy
        if lock_aspect_ratio:
            direction, x1, x0, start, width = dx
            F = 1 + 3 * direction * float(x1 - x0) / width
        axes_to_update = self.get_axes_to_update(dx, dy)

        axis_ids_horizontal = (self.get_axis_id("bottom"), self.get_axis_id("top"))
        axis_ids_vertical = (self.get_axis_id("left"), self.get_axis_id("right"))

        for (direction, x1, x0, start, width), axis_id in axes_to_update:
            lbound, hbound = self.get_axis_limits(axis_id)
            if not lock_aspect_ratio:
                F = 1 + 3 * direction * float(x1 - x0) / width
            if F * (hbound - lbound) == 0:
                continue
            if self.get_axis_scale(axis_id) == 'lin':
                orig = self.invTransform(axis_id, start)
                vmin = orig - F * (orig - lbound)
                vmax = orig + F * (hbound - orig)
            else:  # log scale
                i_lbound = self.transform(axis_id, lbound)
                i_hbound = self.transform(axis_id, hbound)
                imin = start - F * (start - i_lbound)
                imax = start + F * (i_hbound - start)
                vmin = self.invTransform(axis_id, imin)
                vmax = self.invTransform(axis_id, imax)

            # patch for not "zooming out"
            if axis_id in axis_ids_horizontal:
                vmin = max(vmin, self.rtmin)
                vmax = min(vmax, self.rtmax)
            elif axis_id in axis_ids_vertical:
                vmin = max(vmin, self.mzmin)
                vmax = min(vmax, self.mzmax)

            self.set_axis_limits(axis_id, vmin, vmax)

        self.setAutoReplot(auto)
        # the signal MUST be emitted after replot, otherwise
        # we receiver won't see the new bounds (don't know why?)
        self.replot()
        self.emit(SIG_PLOT_AXIS_CHANGED, self)

    @protect_signal_handler
    def do_pan_view(self, dx, dy):
        """
        modified version of do_pan_view from base class,
        we restrict zooming and panning to ranges of peakmap.

        Translate the active axes by dx, dy
        dx, dy are tuples composed of (initial pos, dest pos)
        """
        auto = self.autoReplot()
        self.setAutoReplot(False)
        axes_to_update = self.get_axes_to_update(dx, dy)
        axis_ids_horizontal = (self.get_axis_id("bottom"), self.get_axis_id("top"))
        axis_ids_vertical = (self.get_axis_id("left"), self.get_axis_id("right"))

        for (x1, x0, _start, _width), axis_id in axes_to_update:
            lbound, hbound = self.get_axis_limits(axis_id)
            i_lbound = self.transform(axis_id, lbound)
            i_hbound = self.transform(axis_id, hbound)
            delta = x1 - x0
            vmin = self.invTransform(axis_id, i_lbound - delta)
            vmax = self.invTransform(axis_id, i_hbound - delta)
            # patch for not "panning out"
            if axis_id in axis_ids_horizontal:
                vmin = max(vmin, self.rtmin)
                vmax = min(vmax, self.rtmax)
            elif axis_id in axis_ids_vertical:
                vmin = max(vmin, self.mzmin)
                vmax = min(vmax, self.mzmax)
            self.set_axis_limits(axis_id, vmin, vmax)

        self.setAutoReplot(auto)
        # the signal MUST be emitted after replot, otherwise
        # we receiver won't see the new bounds (don't know why?)
        self.replot()
        self.emit(SIG_PLOT_AXIS_CHANGED, self)


def create_image_widget():  # rtmin, rtmax, mzmin, mzmax):
    # patched plot in widget
    widget = ImageWidget(lock_aspect_ratio=False, xlabel="rt", ylabel="m/z")

    # patch memeber's methods:
    widget.plot.__class__ = ModifiedImagePlot
    widget.plot.set_axis_direction("left", False)
    widget.plot.set_axis_direction("right", False)
    return widget


def create_chromatogram_widget():
    widget = CurveWidget(ylabel="I")
    t = widget.add_tool(SelectTool)
    widget.set_default_tool(t)
    t.activate()

    plot = widget.plot
    plot.__class__ = ChromatogramPlot

    plot.set_antialiasing(True)
    plot.cross_marker.setZ(plot.get_max_z() + 1)
    plot.cross_marker.setVisible(True)
    plot.canvas_pointer = True  # x-cross marker on

    cursor_info = RtCursorInfo()
    label = make.info_label("TL", [cursor_info], title="None")
    label.labelparam.label = ""
    label.setVisible(1)
    plot.rt_label = label

    # we hack label_cb for updating legend:
    def label_cb(rt, mz):
        # passing None here arives as np.nan if you call get_rect later, so we use
        # np.nan here:
        cursor_info.set_rt(rt)
        return ""
    cross_marker = plot.cross_marker
    cross_marker.label_cb = label_cb
    params = {
        "marker/cross/line/color": "#cccccc",
        "marker/cross/line/width": 1.5,
        "marker/cross/line/alpha": 0.4,
        "marker/cross/markerstyle": "VLine",
        "marker/cross/symbol/marker": "NoSymbol",
    }
    CONF.update_defaults(dict(plot=params))
    cross_marker.markerparam.read_config(CONF, "plot", "marker/cross")
    cross_marker.markerparam.update_marker(cross_marker)

    return widget


def create_peakmap_labels(plot):
    rect_marker = RectangleShape()
    rect_label = make.info_label("TR", [PeakmapCursorRangeInfo(rect_marker)], title=None)
    rect_label.labelparam.label = ""
    rect_label.setVisible(1)
    plot.rect_label = rect_label
    plot.add_item(rect_label)

    params = {
        "shape/drag/symbol/size": 0,
        "shape/drag/line/color": "#cccccc",
        "shape/drag/line/width": 1.5,
        "shape/drag/line/alpha": 0.4,
        "shape/drag/line/style": "SolidLine",

    }
    CONF.update_defaults(dict(plot=params))
    rect_marker.shapeparam.read_config(CONF, "plot", "shape/drag")
    rect_marker.shapeparam.update_shape(rect_marker)
    rect_marker.setVisible(0)
    rect_marker.set_rect(0, 0, np.nan, np.nan)
    plot.add_item(rect_marker)

    plot.canvas_pointer = True  # x-cross marker on
    # we hack label_cb for updating legend:

    def label_cb(rt, mz):
        # passing None here arives as np.nan if you call get_rect later, so we use
        # np.nan here:
        rect_marker.set_rect(rt, mz, np.nan, np.nan)
        return ""

    cross_marker = plot.cross_marker
    cross_marker.label_cb = label_cb
    params = {
        "marker/cross/line/color": "#cccccc",
        "marker/cross/line/width": 1.5,
        "marker/cross/line/alpha": 0.4,
        "marker/cross/symbol/marker": "NoSymbol",
        "marker/cross/markerstyle": "Cross",
    }
    CONF.update_defaults(dict(plot=params))
    cross_marker.markerparam.read_config(CONF, "plot", "marker/cross")
    cross_marker.markerparam.update_marker(cross_marker)


class PeakMapPlotter(object):

    def __init__(self, peakmap):

        self.widget = create_image_widget()  # rtmin, rtmax, mzmin, mzmax)

        self.peakmap = peakmap

        set_x_axis_scale_draw(self.widget)
        set_y_axis_scale_draw(self.widget)

        self.pmi = PeakMapImageItem(peakmap)
        self.widget.plot.add_item(self.pmi)
        self.widget.plot.enableAxis(self.widget.plot.colormap_axis, False)

        # for zooming and panning with mouse drag:
        t = self.widget.add_tool(SelectTool)
        self.widget.set_default_tool(t)
        t.activate()
        # for selecting zoom window
        t = self.widget.add_tool(PeakmapZoomTool)
        t.activate()

        create_peakmap_labels(self.widget.plot)

    def replot(self):
        self.widget.plot.replot()


class PeakMapExplorer(QDialog):

    def __init__(self):
        QDialog.__init__(self)
        self.setWindowFlags(Qt.Window)
        # Destroying the C++ object right after closing the dialog box,
        # otherwise it may be garbage-collected in another QThread
        # (e.g. the editor's analysis thread in Spyder), thus leading to
        # a segmentation fault on UNIX or an application crash on Windows
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowFlags(Qt.Window)

        self.gamma_min = 0.05
        self.gamma_max = 2.0
        self.gamma_start = 1.0

    def keyPressEvent(self, e):
        if e.key() != Qt.Key_Escape:
            super(PeakMapExplorer, self).keyPressEvent(e)

    def setup(self, peakmap):
        self.process_peakmap(peakmap)
        self.setup_input_widgets()
        self.setup_plot_widgets()
        self.setup_layout()
        self.connect_signals_and_slots()
        self.plot_peakmap()

    def process_peakmap(self, peakmap):
        levels = peakmap.getMsLevels()
        if len(levels) == 1 and levels[0] > 1:
            self.levelNSpecs = []
        else:
            self.levelNSpecs = [s for s in peakmap.spectra if s.msLevel > 1]

        self.peakmap = peakmap.getDominatingPeakmap()

        title = os.path.basename(peakmap.meta.get("source", ""))
        self.setWindowTitle(title)

    def setup_input_widgets(self):
        self.log_label = QLabel("Logarithmic Scale:")
        self.log_check_box = QCheckBox()
        self.log_check_box.setCheckState(1)
        self.log_check_box.setTristate(0)

        self.gamma_label = QLabel("Contrast Value:")
        self.gamma_slider = QSlider(Qt.Horizontal)
        self.gamma_slider.setMinimum(0)
        self.gamma_slider.setMaximum(50)

        rel_pos = (self.gamma_start - self.gamma_min) / (self.gamma_max - self.gamma_min)
        self.gamma_slider.setSliderPosition(50 * rel_pos)

        self.imin_label = QLabel("Minimal Intensity:")
        self.imin_slider = QSlider(Qt.Horizontal)
        self.imin_slider.setMinimum(0)
        self.imin_slider.setMaximum(100)
        self.imin_slider.setSliderPosition(0)

        self.imax_label = QLabel("Maximal Intensity:")
        self.imax_slider = QSlider(Qt.Horizontal)
        self.imax_slider.setMinimum(0)
        self.imax_slider.setMaximum(100)
        self.imax_slider.setSliderPosition(100)

        self.history_list_label = QLabel("History:")
        self.history_list = QComboBox()

    def setup_plot_widgets(self):
        self.peakmap_plotter = PeakMapPlotter(self.peakmap)

        self.chromatogram_widget = create_chromatogram_widget()

        set_x_axis_scale_draw(self.chromatogram_widget)
        set_y_axis_scale_draw(self.chromatogram_widget)

        self.mz_plotter = MzPlotter(None)

        self.peakmap_plotter.pmi.set_logarithmic_scale(1)
        self.peakmap_plotter.pmi.set_gamma(self.gamma_start)

    def setup_layout(self):
        layout = QGridLayout()
        layout.addWidget(self.chromatogram_widget, 0, 0)

        layout.addWidget(self.peakmap_plotter.widget, 1, 0)
        self.peakmap_plotter.widget.setMinimumSize(450, 250)

        controls_layout = QGridLayout()
        controls_layout.setSpacing(15)
        controls_layout.setMargin(20)

        row = 0
        controls_layout.addWidget(self.log_label, row, 0)
        controls_layout.addWidget(self.log_check_box, row, 1)

        row += 1
        controls_layout.addWidget(self.gamma_label, row, 0)
        controls_layout.addWidget(self.gamma_slider, row, 1)

        row += 1
        controls_layout.addWidget(self.imin_label, row, 0)
        controls_layout.addWidget(self.imin_slider, row, 1)

        row += 1
        controls_layout.addWidget(self.imax_label, row, 0)
        controls_layout.addWidget(self.imax_slider, row, 1)

        row += 1
        controls_layout.addWidget(self.history_list_label, row, 0)
        controls_layout.addWidget(self.history_list, row, 1)

        layout.addLayout(controls_layout, 0, 1)

        layout.addWidget(self.mz_plotter.widget, 1, 1)

        layout.setRowStretch(0, 2)
        layout.setRowStretch(1, 5)
        layout.setColumnStretch(0, 3)
        layout.setColumnStretch(1, 2)

        self.setLayout(layout)

    def connect_signals_and_slots(self):
        self.connect(self.gamma_slider, SIGNAL("valueChanged(int)"), self.gamma_changed)
        self.connect(self.imin_slider, SIGNAL("valueChanged(int)"), self.imin_changed)
        self.connect(self.imax_slider, SIGNAL("valueChanged(int)"), self.imax_changed)
        self.connect(self.log_check_box, SIGNAL("stateChanged(int)"), self.log_changed)
        self.connect(self.peakmap_plotter.widget.plot, SIG_PLOT_AXIS_CHANGED, self.changed_axis)
        self.connect(self.peakmap_plotter.widget.plot, SIG_HISTORY_CHANGED, self.history_changed)
        self.connect(self.history_list, SIGNAL("activated(int)"), self.history_item_selected)

    @protect_signal_handler
    def history_changed(self, history):
        self.history_list.clear()
        for item in history.items:
            rtmin, rtmax, mzmin, mzmax = item
            str_item = "%10.5f .. %10.5f %6.2fm...%6.2fm" % (mzmin, mzmax, rtmin / 60.0,
                                                             rtmax / 60.0)
            self.history_list.addItem(str_item)
        self.history_list.setCurrentIndex(history.position)

    @protect_signal_handler
    def history_item_selected(self, index):
        self.peakmap_plotter.widget.plot.set_history_position(index)

    @protect_signal_handler
    def changed_axis(self, evt=None):
        if evt is not None:
            rtmin, rtmax = evt.get_axis_limits("bottom")
            mzmin, mzmax = evt.get_axis_limits("left")
        else:
            rtmin, rtmax = self.peakmap.rtRange()
            mzmin, mzmax = self.peakmap.mzRange()

        rts, chroma = self.peakmap.chromatogram(rtmin=rtmin, rtmax=rtmax, mzmin=mzmin, mzmax=mzmax)

        p = self.chromatogram_widget.plot
        p.plot_chromatogram(rts, chroma)

        peaks = self.peakmap.extract(rtmin, rtmax, mzmin, mzmax).all_peaks(msLevel=1)
        self.mz_plotter.plot_peaks(peaks)
        self.mz_plotter.widget.plot.reset_x_limits()
        self.mz_plotter.widget.plot.reset_y_limits()
        self.mz_plotter.updateAxes()
        self.mz_plotter.replot()

    @protect_signal_handler
    def log_changed(self, is_log):
        self.peakmap_plotter.pmi.set_logarithmic_scale(is_log)
        self.peakmap_plotter.replot()

    @protect_signal_handler
    def gamma_changed(self, value):
        self.set_range_limits()

    @protect_signal_handler
    def imin_changed(self, value):
        if value >= self.imax_slider.value():
            self.imax_slider.setSliderPosition(value)
        self.set_range_limits()

    @protect_signal_handler
    def imax_changed(self, value):
        if value <= self.imin_slider.value():
            self.imin_slider.setSliderPosition(value)
        self.set_range_limits()

    def set_range_limits(self):
        value = self.imin_slider.value()
        rel_imin = value / 1.0 / self.imin_slider.maximum()
        rel_imin = rel_imin ** 4

        value = self.imax_slider.value()
        rel_imax = value / 1.0 / self.imax_slider.maximum()
        rel_imax = rel_imax ** 4

        pmi = self.peakmap_plotter.pmi
        pmi.set_imin(rel_imin * pmi.get_total_imax())
        pmi.set_imax(rel_imax * pmi.get_total_imax())

        value = self.gamma_slider.value()
        gamma = value / 1.0 / self.gamma_slider.maximum() * (self.gamma_max -
                                                             self.gamma_min) + self.gamma_min
        pmi.set_gamma(gamma)
        self.peakmap_plotter.replot()

    def plot_peakmap(self):
        rtmin, rtmax = self.peakmap.rtRange()
        mzmin, mzmax = self.peakmap.mzRange()
        self.peakmap_plotter.widget.plot.set_limits(rtmin, rtmax, mzmin, mzmax, add_to_history=True)
        self.peakmap_plotter.replot()
        self.changed_axis(evt=None)


def inspectPeakMap(peakmap):
    """
    allows the visual inspection of a peakmap
    """

    if len(peakmap) == 0:
        raise Exception("empty peakmap")

    app = guidata.qapplication()  # singleton !
    win = PeakMapExplorer()
    win.setup(peakmap)
    win.raise_()
    win.exec_()

if __name__ == "__main__":
    import emzed.io
    peakmap = emzed.io.loadPeakMap("peakmap.mzML")
    inspectPeakMap(peakmap)
