# encoding: utf-8
from __future__ import print_function

import types

from PyQt4.QtCore import (Qt, QRectF, QPointF, pyqtSignal)
from PyQt4.QtGui import (QPainter, QPixmap)
from PyQt4.Qwt5 import (QwtScaleDraw, QwtText)

import numpy as np
import scipy.ndimage.morphology

import pylab


from guiqwt.builder import make
from guiqwt.config import CONF
from guiqwt.events import (KeyEventMatch, QtDragHandler, PanHandler, MoveHandler, ZoomHandler,)
from guiqwt.image import ImagePlot, RGBImageItem, RawImageItem
from guiqwt.label import ObjectInfo
from guiqwt.plot import ImageWidget
from guiqwt.shapes import RectangleShape
from guiqwt.signals import (SIG_MOVE, SIG_START_TRACKING, SIG_STOP_NOT_MOVING, SIG_STOP_MOVING,)
from guiqwt.tools import SelectTool, InteractiveTool

from emzed_optimizations.sample import sample_image

from lru_cache import lru_cache

from helpers import protect_signal_handler, set_rt_formatting_on_x_axis


def get_range(peakmap, peakmap2):
    rtmin, rtmax = peakmap.rtRange()
    mzmin, mzmax = full_mz_range(peakmap)
    if peakmap2 is not None:
        rtmin2, rtmax2 = peakmap2.rtRange()
        mzmin2, mzmax2 = full_mz_range(peakmap2)
        rtmin = min(rtmin, rtmin2)
        rtmax = max(rtmax, rtmax2)
        mzmin = min(mzmin, mzmin2)
        mzmax = max(mzmax, mzmax2)
    return rtmin, rtmax, mzmin, mzmax


def set_y_axis_scale_draw(widget):
    """ sets minimum extent for aligning chromatogram and peakmap plot """
    drawer = QwtScaleDraw()
    drawer.setMinimumExtent(50)
    widget.plot.setAxisScaleDraw(widget.plot.yLeft, drawer)


def full_mz_range(pm):
    mzranges = [s.mzRange() for s in pm.spectra]
    mzranges = [r for r in mzranges if r != (None, None)]
    if len(mzranges) == 0:
        return (None, None)
    mzmin = min(mzmin for (mzmin, mzmax) in mzranges if mzmin is not None)
    mzmax = max(mzmax for (mzmin, mzmax) in mzranges if mzmax is not None)
    return mzmin, mzmax


def dilate(data, mzmax, mzmin):
    """dilate image (here this means: paint big pixels) depending on the given mz range
    """
    dmz = mzmax - mzmin
    # above dmz > 100.0 we will have n == 2, for dmz < .0 we have n == 4, inbetween
    # we do linear inerpolation:
    dmz_max = 200.0
    dmz_min = .001
    smax = 4.0
    smin = 2.0
    n = round(smax - (dmz - dmz_min) / (dmz_max - dmz_min) * (smax - smin))
    n = max(smin, min(smax, n))
    # we use moving max here, no moving sum, because this lead to strong local peaks which
    # dominate the final imager after rescaling from max intensity to 1.0:
    dilated = scipy.ndimage.morphology.grey_dilation(data, int(n))
    return dilated


class PeakMapImageBase(object):

    def __init__(self, peakmaps):
        self.peakmaps = peakmaps
        rtmins, rtmaxs = zip(*[pm.rtRange() for pm in peakmaps])
        mzmins, mzmaxs = zip(*[full_mz_range(pm) for pm in peakmaps])
        self.rtmin = min(rtmins)
        self.rtmax = max(rtmaxs)
        self.mzmin = min(mzmins)
        self.mzmax = max(mzmaxs)

        self.bounds = QRectF(QPointF(self.rtmin, self.mzmin), QPointF(self.rtmax, self.mzmax))

        self.total_imin = 0.0
        maxi = [np.max(s.peaks[:, 1]) for pm in peakmaps for s in pm.spectra if len(s.peaks)]
        if maxi:
            self.total_imax = max(maxi)
        else:
            self.total_imax = 1.0

        self.imin = self.total_imin
        self.imax = self.total_imax

        self.gamma = 1.0
        self.is_log = 1

    def get_peakmap_bounds(self):
        return self.rtmin, self.rtmax, self.mzmin, self.mzmax

    def get_gamma(self):
        return self.gamma

    def get_total_imax(self):
        return self.total_imax

    def _set(self, field, value):
        if getattr(self, field) != value:
            self.compute_image.invalidate_cache()
        setattr(self, field, value)

    def set_imin(self, v):
        self._set("imin", v)

    def set_imax(self, v):
        self._set("imax", v)

    def set_gamma(self, v):
        self._set("gamma", v)

    def set_logarithmic_scale(self, v):
        self._set("is_log", v)

    @lru_cache(maxsize=100)
    def compute_image(self, idx, NX, NY, rtmin, rtmax, mzmin, mzmax):

        if rtmin >= rtmax or mzmin >= mzmax:
            dilated = np.zeros((1, 1))
        else:
            # optimized:
            # one additional row / col as we loose one row and col during smoothing:

            # sample_image only works on level1, therefore we have to use getDominatingPeakmap()
            pm = self.peakmaps[idx].getDominatingPeakmap()
            data = sample_image(pm, rtmin, rtmax, mzmin, mzmax, NX + 1, NY + 1)

            imin = self.imin
            imax = self.imax

            if self.is_log:
                data = np.log(1.0 + data)
                imin = np.log(1.0 + imin)
                imax = np.log(1.0 + imax)

            # set values out of range to black:
            overall_max = np.max(data)
            data[data < imin] = 0
            data[data > imax] = 0

            data /= overall_max

            # enlarge peak pixels depending on the mz range in the image:
            dilated = dilate(data, mzmax, mzmin)

        # turn up/down
        dilated = dilated[::-1, :]

        # apply gamma
        dilated = dilated ** (self.gamma) * 255
        return dilated.astype(np.uint8)


class PeakMapImageItem(PeakMapImageBase, RawImageItem):

    """ draws peakmap 2d view dynamically based on given limits """

    def __init__(self, peakmap):

        RawImageItem.__init__(self, data=np.zeros((1, 1), np.uint8))
        PeakMapImageBase.__init__(self, [peakmap])

        self.update_border()
        self.IMAX = 255
        self.set_lut_range([0, self.IMAX])
        self.set_color_map("hot")

        self.last_canvas_rect = None
        self.last_src_rect = None
        self.last_dst_rect = None
        self.last_xmap = None
        self.last_ymap = None

    def paint_pixmap(self, widget):
        assert self.last_canvas_rect is not None
        x1, y1 = self.last_canvas_rect.left(), self.last_canvas_rect.top()
        x2, y2 = self.last_canvas_rect.right(), self.last_canvas_rect.bottom()

        NX = x2 - x1
        NY = y2 - y1
        pix = QPixmap(NX, NY)
        painter = QPainter(pix)
        painter.begin(widget)
        try:
            self.draw_border(painter, self.last_xmap, self.last_ymap, self.last_canvas_rect)
            self.draw_image(painter, self.last_canvas_rect, self.last_src_rect, self.last_dst_rect,
                            self.last_xmap, self.last_xmap)
            # somehow guiqwt paints a distorted border at left/top, so we remove it:
            return pix.copy(2, 2, NX - 2, NY - 2)
        finally:
            painter.end()

    #  ---- QwtPlotItem API ------------------------------------------------------
    def draw_image(self, painter, canvasRect, srcRect, dstRect, xMap, yMap):

        # normally we use this method indirectly from quiqwt which takes the burden of constructing
        # the right parameters. if we want to call this method manually, eg for painting on on a
        # QPixmap for saving the image, we just use the last set of parmeters passed to this
        # method, this is much easier than constructing the params seperatly, and so we get the
        # exact same result as we see on screen:
        self.last_canvas_rect = canvasRect
        self.last_src_rect = srcRect
        self.last_dst_rect = dstRect
        self.last_xmap = xMap
        self.last_ymap = yMap

        x1, y1, x2, y2 = canvasRect.getCoords()
        NX = x2 - x1
        NY = y2 - y1
        rtmin, mzmax, rtmax, mzmin = srcRect
        self.data = self.compute_image(0, NX, NY, rtmin, rtmax, mzmin, mzmax)

        # draw
        srcRect = (0, 0, NX, NY)
        # x1, y1, x2, y2 = canvasRect.getCoords()
        RawImageItem.draw_image(self, painter, canvasRect, srcRect, (x1, y1, x2, y2), xMap, yMap)


class RGBPeakMapImageItem(PeakMapImageBase, RGBImageItem):

    """ draws peakmap 2d view dynamically based on given limits """

    def __init__(self, peakmap, peakmap2):
        PeakMapImageBase.__init__(self, [peakmap, peakmap2])
        self.xmin = self.rtmin
        self.xmax = self.rtmax
        self.ymin = self.mzmin
        self.ymax = self.mzmax
        RawImageItem.__init__(self, data=np.zeros((1, 1, 3), np.uint32))
        self.update_border()

    def paint_pixmap(self, widget):
        assert self.last_canvas_rect is not None
        x1, y1 = self.last_canvas_rect.left(), self.last_canvas_rect.top()
        x2, y2 = self.last_canvas_rect.right(), self.last_canvas_rect.bottom()

        NX = x2 - x1
        NY = y2 - y1
        pix = QPixmap(NX, NY)
        painter = QPainter(pix)
        painter.begin(widget)
        try:
            self.draw_border(painter, self.last_xmap, self.last_ymap, self.last_canvas_rect)
            self.draw_image(painter, self.last_canvas_rect, self.last_src_rect, self.last_dst_rect,
                            self.last_xmap, self.last_xmap)
            # somehow guiqwt paints a distorted border at left/top, so we remove it:
            return pix.copy(2, 2, NX - 2, NY - 2)
        finally:
            painter.end()

    #  ---- QwtPlotItem API ------------------------------------------------------
    def draw_image(self, painter, canvasRect, srcRect, dstRect, xMap, yMap):

        # normally we use this method indirectly from quiqwt which takes the burden of constructing
        # the right parameters. if we want to call this method manually, eg for painting on on a
        # QPixmap for saving the image, we just use the last set of parmeters passed to this
        # method, this is much easier than constructing the params seperatly, and so we get the
        # exact same result as we see on screen:
        self.last_canvas_rect = canvasRect
        self.last_src_rect = srcRect
        self.last_dst_rect = dstRect
        self.last_xmap = xMap
        self.last_ymap = yMap

        rtmin, mzmax, rtmax, mzmin = srcRect

        x1, y1 = canvasRect.left(), canvasRect.top()
        x2, y2 = canvasRect.right(), canvasRect.bottom()
        NX = x2 - x1
        NY = y2 - y1
        rtmin, mzmax, rtmax, mzmin = srcRect

        image = self.compute_image(0, NX, NY, rtmin, rtmax, mzmin, mzmax)[::-1, :]
        image2 = self.compute_image(1, NX, NY, rtmin, rtmax, mzmin, mzmax)[::-1, :]

        dilated = dilate(image.astype(np.int32), mzmax, mzmin)
        dilated2 = dilate(image2.astype(np.int32), mzmax, mzmin)

        self.data = np.zeros_like(dilated, dtype=np.uint32)[::-1, :]
        # add image as rgb(255, 255, 0): first we add red, then green which yields yellow:
        self.data += dilated * 256 * 256
        # plus red:
        self.data += dilated * 256
        # add image2 as rgb(0, 0, 256) which is blue:
        self.data += dilated2
        self.data |= 255 << 24

        self.bounds = QRectF(rtmin, mzmin, rtmax - rtmin, mzmax - mzmin)

        RGBImageItem.draw_image(self, painter, canvasRect, srcRect, dstRect, xMap, yMap)


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


class PeakmapZoomTool(InteractiveTool):

    """ selects rectangle from peakmap """

    TITLE = "Selection"
    ICON = "selection.png"
    CURSOR = Qt.CrossCursor

    def setup_filter(self, baseplot):
        filter = baseplot.filter
        # Initialisation du filtre

        start_state = filter.new_state()

        key_left_handler = lambda *a: baseplot.KEY_LEFT.emit()
        key_right_handler = lambda *a: baseplot.KEY_RIGHT.emit()
        key_end_handler = lambda *a: baseplot.KEY_END.emit()
        key_backspace_handler = lambda *a: baseplot.KEY_BACKSPACE.emit()

        key_left_and_aliases = [(Qt.Key_Z, Qt.ControlModifier), Qt.Key_Left]
        filter.add_event(start_state,
                         KeyEventMatch(key_left_and_aliases),
                         key_left_handler,
                         start_state)

        key_right_and_aliases = [(Qt.Key_Y, Qt.ControlModifier), Qt.Key_Right]
        filter.add_event(start_state,
                         KeyEventMatch(key_right_and_aliases),
                         key_right_handler,
                         start_state)

        filter.add_event(start_state,
                         KeyEventMatch((Qt.Key_Backspace, Qt.Key_Escape, Qt.Key_Home)),
                         key_backspace_handler,
                         start_state)

        filter.add_event(start_state,
                         KeyEventMatch((Qt.Key_End,)),
                         key_end_handler,
                         start_state)

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
        PanHandler(filter, Qt.LeftButton, mods=Qt.AltModifier, start_state=start_state)
        # AutoZoomHandler(filter, Qt.MidButton, start_state=start_state)

        # Bouton droit
        ZoomHandler(filter, Qt.RightButton, start_state=start_state)
        ZoomHandler(filter, Qt.LeftButton, mods=Qt.ControlModifier, start_state=start_state)
        # MenuHandler(filter, Qt.RightButton, start_state=start_state)

        # Autres (touches, move)
        MoveHandler(filter, start_state=start_state)
        MoveHandler(filter, start_state=start_state, mods=Qt.ShiftModifier)
        MoveHandler(filter, start_state=start_state, mods=Qt.AltModifier)

        return start_state


class ModifiedImagePlot(ImagePlot):

    """ special handlers for dragging selection, source is PeakmapZoomTool """

    NEW_IMAGE_LIMITS = pyqtSignal(float, float, float, float)
    KEY_LEFT = pyqtSignal()
    KEY_RIGHT = pyqtSignal()
    KEY_BACKSPACE = pyqtSignal()
    KEY_END = pyqtSignal()
    CURSOR_MOVED = pyqtSignal(float, float)

    # as this class is used for patching, the __init__ is never called, so we set default
    # values as class atributes:

    rtmin = rtmax = mzmin = mzmax = None
    peakmap_range = (None, None, None, None)
    dragging = False

    def mouseDoubleClickEvent(self, evt):
        if evt.button() == Qt.RightButton:
            self.key_left()

    def set_limits(self, rtmin, rtmax, mzmin, mzmax):
        self.rtmin = rtmin = max(rtmin, self.peakmap_range[0])
        self.rtmax = rtmax = min(rtmax, self.peakmap_range[1])
        self.mzmin = mzmin = min(max(mzmin, self.peakmap_range[2]), self.peakmap_range[3])
        self.mzmax = mzmax = max(min(mzmax, self.peakmap_range[3]), self.peakmap_range[2])
        if mzmin == mzmax:
            mzmin *= (1.0 - 1e-5)  # - 10 ppm
            mzmax *= (1.0 + 1e-5)  # + 10 ppm
        if rtmin == rtmax:
            rtmin += -.1
            rtmax += .1
        self.set_plot_limits(rtmin, rtmax, mzmin, mzmax, "bottom", "right")
        self.set_plot_limits(rtmin, rtmax, mzmin, mzmax, "top", "left")

        # only rgb plot needs update of bounds:
        peakmap_item = self.get_unique_item(RGBPeakMapImageItem)
        if peakmap_item is not None:
            peakmap_item.bounds = QRectF(QPointF(rtmin, mzmin), QPointF(rtmax, mzmax))

        self.replot()
        self.NEW_IMAGE_LIMITS.emit(rtmin, rtmax, mzmin, mzmax)

    def set_rt_limits(self, rtmin, rtmax):
        if self.mzmin is not None and self.mzmax is not None:
            self.set_limits(rtmin, rtmax, self.mzmin, self.mzmax)

    def set_mz_limits(self, mzmin, mzmax):
        if self.rtmin is not None and self.rtmax is not None:
            self.set_limits(self.rtmin, self.rtmax, mzmin, mzmax)

    def set_limits_no_sig(self, rtmin, rtmax, mzmin, mzmax):
        self.blockSignals(True)
        self.set_limits(rtmin, rtmax, mzmin, mzmax)
        self.blockSignals(False)

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
        rt = self.invTransform(self.xBottom, pos.x())
        mz = self.invTransform(self.yLeft, pos.y())
        self.CURSOR_MOVED.emit(rt, mz)

    def set_rt(self, rt):
        self.cross_marker.setValue(rt, self.cross_marker.yValue())
        self.replot()

    def set_mz(self, mz):
        self.cross_marker.setValue(self.cross_marker.xValue(), mz)
        self.replot()

    @protect_signal_handler
    def start_drag_mode(self, filter_, evt):
        self.start_at = self.get_coords(evt)
        self.moved = False
        self.dragging = True
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
        if self.dragging:
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

        self.dragging = False

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

            self.set_limits(rtmin, rtmax, mzmin, mzmax)
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
                vmin = max(vmin, self.peakmap_range[0])
                vmax = min(vmax, self.peakmap_range[1])
                rtmin = vmin
                rtmax = vmax
            elif axis_id in axis_ids_vertical:
                vmin = max(vmin, self.peakmap_range[2])
                vmax = min(vmax, self.peakmap_range[3])
                mzmin = vmin
                mzmax = vmax

            self.set_axis_limits(axis_id, vmin, vmax)

        self.setAutoReplot(auto)
        self.NEW_IMAGE_LIMITS.emit(rtmin, rtmax, mzmin, mzmax)
        self.replot()

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
                vmin = max(vmin, self.peakmap_range[0])
                vmax = min(vmax, self.peakmap_range[1])
                rtmin = vmin
                rtmax = vmax
            elif axis_id in axis_ids_vertical:
                vmin = max(vmin, self.peakmap_range[2])
                vmax = min(vmax, self.peakmap_range[3])
                mzmin = vmin
                mzmax = vmax
            self.set_axis_limits(axis_id, vmin, vmax)

        self.setAutoReplot(auto)
        self.replot()
        self.NEW_IMAGE_LIMITS.emit(rtmin, rtmax, mzmin, mzmax)


def set_image_plot(widget, image_item, peakmap_range):
    widget.plot.peakmap_range = peakmap_range
    widget.plot.del_all_items()
    widget.plot.add_item(image_item)
    create_peakmap_labels(widget.plot)
    # for zooming and panning with mouse drag:
    t = widget.add_tool(SelectTool)
    widget.set_default_tool(t)
    t.activate()
    # for selecting zoom window
    t = widget.add_tool(PeakmapZoomTool)
    t.activate()


def create_peakmap_labels(plot):
    rect_marker = RectangleShape()
    rect_label = make.info_label("TR", [PeakmapCursorRangeInfo(rect_marker)], title=None)
    rect_label.labelparam.label = ""
    rect_label.labelparam.font.size = 12
    rect_label.labelparam.update_label(rect_label)
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
        "marker/cross/line/style": "DashLine",
        "marker/cross/symbol/marker": "NoSymbol",
        "marker/cross/markerstyle": "Cross",
    }
    CONF.update_defaults(dict(plot=params))
    cross_marker.markerparam.read_config(CONF, "plot", "marker/cross")
    cross_marker.markerparam.update_marker(cross_marker)


class PeakMapPlottingWidget(ImageWidget):

    def __init__(self, parent=None):
        super(PeakMapPlottingWidget, self).__init__(parent, lock_aspect_ratio=False,
                                                    xlabel="rt", ylabel="m/z")
        self.peakmap_item = None
        # patch memeber's methods:
        self.plot.__class__ = ModifiedImagePlot

        # take over events:
        self.NEW_IMAGE_LIMITS = self.plot.NEW_IMAGE_LIMITS
        self.KEY_LEFT = self.plot.KEY_LEFT
        self.KEY_RIGHT = self.plot.KEY_RIGHT
        self.KEY_BACKSPACE = self.plot.KEY_BACKSPACE
        self.KEY_END = self.plot.KEY_END
        self.CURSOR_MOVED = self.plot.CURSOR_MOVED

        self.plot.set_axis_direction("left", False)
        self.plot.set_axis_direction("right", False)

        set_rt_formatting_on_x_axis(self.plot)
        set_y_axis_scale_draw(self)
        self.plot.enableAxis(self.plot.colormap_axis, False)

    def set_peakmaps(self, peakmap, peakmap2):

        self.peakmap = peakmap
        self.peakmap2 = peakmap2

        # only makes sense for gamma, after reload imin/imax and rt/mz bounds will not be
        # valid any more

        if self.peakmap_item is not None:
            gamma_before = self.peakmap_item.get_gamma()
        else:
            gamma_before = None
        if peakmap2 is not None:
            self.peakmap_item = RGBPeakMapImageItem(peakmap, peakmap2)
        else:
            self.peakmap_item = PeakMapImageItem(peakmap)
        set_image_plot(self, self.peakmap_item, get_range(peakmap, peakmap2))
        if gamma_before is not None:
            self.peakmap_item.set_gamma(gamma_before)

    def replot(self):
        self.plot.replot()

    def __getattr__(self, name):
        if hasattr(self, "plot"):
            return getattr(self.plot, name)

    def get_plot(self):
        return self.plot

    def paint_pixmap(self):
        return self.peakmap_item.paint_pixmap(self)

    def set_logarithmic_scale(self, flag):
        self.peakmap_item.set_logarithmic_scale(flag)

    def set_gamma(self, gamma):
        self.peakmap_item.set_gamma(gamma)

    def set_imin(self, imin):
        self.peakmap_item.set_imin(imin)

    def set_imax(self, imax):
        self.peakmap_item.set_imax(imax)

    def get_total_imax(self):
        return self.peakmap_item.get_total_imax()

    def set_cursor_rt(self, rt):
        self.plot.set_rt(rt)

    def set_cursor_mz(self, mz):
        self.plot.set_mz(mz)

    def blockSignals(self, flag):
        super(PeakMapPlottingWidget, self).blockSignals(flag)
        self.plot.blockSignals(flag)
