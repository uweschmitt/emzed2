# -*- coding: utf-8 -*-

import os
import types
import math
import numpy as np

from scipy.signal import convolve2d

from PyQt4.QtGui import (QDialog, QGridLayout, QSlider, QLabel, QCheckBox,
                         QComboBox, QLineEdit, QDoubleValidator, QFrame,
                         QHBoxLayout, QPushButton, QMenuBar, QAction, QMenu,
                         QKeySequence, QVBoxLayout, QPixmap, QPainter,
                         QMessageBox, QTableWidget, QTableWidgetItem, QSplitter, QHeaderView)

from PyQt4.QtCore import (Qt, SIGNAL, QRectF, QPointF)
from PyQt4.QtWebKit import (QWebView, QWebSettings)
from PyQt4.Qwt5 import (QwtScaleDraw, QwtText)

import guidata

from guiqwt.builder import make
from guiqwt.config import CONF
from guiqwt.events import (KeyEventMatch, QtDragHandler, PanHandler, MoveHandler, ZoomHandler,)
from guiqwt.image import ImagePlot, RGBImageItem, RawImageItem
from guiqwt.label import ObjectInfo
from guiqwt.plot import ImageWidget, CurveWidget, CurvePlot
from guiqwt.shapes import RectangleShape
from guiqwt.signals import (SIG_MOVE, SIG_START_TRACKING, SIG_STOP_NOT_MOVING, SIG_STOP_MOVING,
                            SIG_PLOT_AXIS_CHANGED, )
from guiqwt.tools import SelectTool, InteractiveTool

from pkg_resources import resource_string

from emzed_optimizations.sample import sample_image

from modified_guiqwt import ModifiedCurveItem

from plotting_widgets import MzPlotter

from helpers import protect_signal_handler

from lru_cache import lru_cache

from ...io.load_utils import loadPeakMap

from ...gui.file_dialogs import askForSave, askForSingleFile

from emzed_dialog import EmzedDialog


def read_float(widget):
    try:
        value = float(widget.text())
        return value
    except ValueError:
        return None


def smooth(data, mzmax, mzmin):
    dmz = mzmax - mzmin
    # above dmz > 100.0 we will have n == 2, for dmz < .0 we have n == 4, inbetween
    # we do linear inerpolation:
    dmz_max = 200.0
    dmz_min = .001
    smax = 5.0
    smin = 2.0
    n = round(smax - (dmz - dmz_min) / (dmz_max - dmz_min) * (smax - smin))
    n = max(smin, min(smax, n))
    mask = np.ones((n, n), dtype=np.uint32)
    smoothed = convolve2d(data, mask, mode="full") # / np.sum(mask)
    return smoothed


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


def full_mz_range(pm):
    mzranges = [s.mzRange() for s in pm.spectra]
    mzranges = [r for r in mzranges if r != (None, None)]
    if len(mzranges) == 0:
        return (None, None)
    mzmin = min(mzmin for (mzmin, mzmax) in mzranges if mzmin is not None)
    mzmax = max(mzmax for (mzmin, mzmax) in mzranges if mzmax is not None)
    return mzmin, mzmax


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

    def set_imin(self, imin):
        if self.imin != imin:
            self.compute_image.invalidate_cache()
        self.imin = imin

    def set_imax(self, imax):
        if self.imax != imax:
            self.compute_image.invalidate_cache()
        self.imax = imax

    def set_gamma(self, gamma):
        if self.gamma != gamma:
            self.compute_image.invalidate_cache()
        self.gamma = gamma

    def set_logarithmic_scale(self, is_log):
        if self.is_log != is_log:
            self.compute_image.invalidate_cache()
        self.is_log = is_log

    @lru_cache(maxsize=100)
    def compute_image(self, idx, NX, NY, rtmin, rtmax, mzmin, mzmax):

        if rtmin >= rtmax or mzmin >= mzmax:
            smoothed = np.zeros((1, 1))
        else:
            # optimized:
            # one additional row / col as we loose one row and col during smoothing:

            # sample_image only works on level1, therefore we have to use getDominatingPeakmap()
            pm = self.peakmaps[idx].getDominatingPeakmap()
            data = sample_image(pm, rtmin, rtmax, mzmin, mzmax, NX + 1, NY + 1)

            smoothed = smooth(data, mzmax, mzmin)
            # enlarge single pixels depending on the mz range in the image:

        # turn up/down
        smoothed = smoothed[::-1, :]
        imin = self.imin
        imax = self.imax

        if self.is_log:
            smoothed = np.log(1.0 + smoothed)
            imin = np.log(1.0 + imin)
            imax = np.log(1.0 + imax)

        smoothed[smoothed < imin] = imin
        smoothed[smoothed > imax] = imax
        smoothed -= imin

        # scale to 1.0
        maxd = np.max(smoothed)
        if maxd:
            smoothed /= maxd

        # apply gamma
        smoothed = smoothed ** (self.gamma) * 255
        return smoothed.astype(np.uint8)


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

        x1, y1 = canvasRect.left(), canvasRect.top()
        x2, y2 = canvasRect.right(), canvasRect.bottom()
        NX = x2 - x1
        NY = y2 - y1
        rtmin, mzmax, rtmax, mzmin = srcRect

        self.data = self.compute_image(0, NX, NY, rtmin, rtmax, mzmin, mzmax)

        # draw
        srcRect = (0, 0, NX, NY)
        x1, y1, x2, y2 = canvasRect.getCoords()
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

        smoothed = smooth(image, mzmax, mzmin)
        smoothed2 = smooth(image2, mzmax, mzmin)

        self.data = np.zeros_like(smoothed, dtype=np.uint32)[::-1, :]
        self.data[:] = 255 << 24  # alpha = 1.0
        # add image as rgb(255, 255, 0)
        self.data += smoothed * 256 * 256
        self.data += smoothed * 256
        # add image2 as rgb(0, 0, 256)
        self.data += smoothed2

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

        history_back_keys = [(Qt.Key_Z, Qt.ControlModifier), Qt.Key_Left]
        filter.add_event(start_state, KeyEventMatch(history_back_keys),
                         baseplot.go_back_in_history, start_state)

        history_forward_keys = [(Qt.Key_Y, Qt.ControlModifier), Qt.Key_Right]
        filter.add_event(start_state, KeyEventMatch(history_forward_keys),
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


class History(object):

    def __init__(self):
        self.position = -1
        self.items = []

    def new_head(self, item, max_len=20):
        del self.items[self.position + 1:]
        self.items.append(item)
        if len(self.items) > max_len:
            # keep head !
            self.items = [self.items[0]] + self.items[-max_len - 1:]
            self.position = len(self.items) - 1
        else:
            self.position += 1

    def current_position_is_beginning(self):
        return self.position == 0

    def current_position_is_end(self):
        return self.position == len(self.items) - 1

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

    # as we use this class for patching by setting this class as super class of a given
    # CurvePlot instance, we do not call __init__, instead we set defaults here:

    image_plot = None

    def label_info(self, x, y):
        return "label_info"

    def on_plot(self, x, y):
        return (x, y)

    @protect_signal_handler
    def do_move_marker(self, event):
        pos = event.pos()
        rt = self.invTransform(self.xBottom, pos.x())
        if self.image_plot:
            self.image_plot.set_rt(rt)
        self.set_marker_axes()
        self.cross_marker.setZ(self.get_max_z() + 1)
        self.cross_marker.setVisible(True)
        self.cross_marker.move_local_point_to(0, pos)
        self.replot()

    def set_rt(self, rt):
        self.cross_marker.setValue(rt, self.cross_marker.yValue())
        self.replot()

    def do_zoom_view(self, dx, dy, lock_aspect_ratio=False):
        """ disables zoom """
        pass

    def do_pan_view(self, dx, dy):
        """ disables panning """
        pass

    def plot_chromatograms(self, rts, chroma, rts2, chroma2):
        self.del_all_items()
        if rts2 is None:
            curve = make.curve(rts, chroma, linewidth=1.5, color="#666666")
            curve.__class__ = ModifiedCurveItem
            self.add_item(curve)
        else:
            curve = make.curve(rts, chroma, linewidth=1.5, color="#aaaa00")
            curve.__class__ = ModifiedCurveItem
            self.add_item(curve)
            curve = make.curve(rts2, chroma2, linewidth=1.5, color="#0000aa")
            curve.__class__ = ModifiedCurveItem
            self.add_item(curve)

        def mmin(seq, default=1.0):
            return min(seq) if len(seq) else default

        def mmax(seq, default=1.0):
            return max(seq) if len(seq) else default

        self.add_item(self.rt_label)
        rtmin = mmin(rts, default=0.0)
        rtmax = mmax(rts)
        maxchroma = mmax(chroma)
        if rts2 is not None:
            rtmin = min(rtmin, mmin(rts2, rtmin))
            rtmax = max(rtmax, mmax(rts2, rtmax))
            maxchroma = max(maxchroma, mmax(chroma2, maxchroma))
        self.set_plot_limits(rtmin, rtmax, 0, maxchroma)
        self.updateAxes()
        self.replot()


class ModifiedImagePlot(ImagePlot):

    """ special handlers for dragging selection, source is PeakmapZoomTool """

    # as this class is used for patching, the __init__ is never called, so we set default
    # values as class atributes:

    rtmin = rtmax = mzmin = mzmax = None
    peakmap_range = (None, None, None, None)
    coords = (None, None)
    dragging = False

    chromatogram_plot = None
    mz_plot = None

    history = None

    def reset_history(self):
        self.history = History()
        self.emit(SIG_HISTORY_CHANGED, self.history)

    def mouseDoubleClickEvent(self, evt):
        if evt.button() == Qt.RightButton:
            self.go_back_in_history()

    def set_limits(self, rtmin, rtmax, mzmin, mzmax, add_to_history):
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

        if add_to_history:
            self.history.new_head((rtmin, rtmax, mzmin, mzmax))
            self.emit(SIG_HISTORY_CHANGED, self.history)

        self.replot()
        self.emit(SIG_PLOT_AXIS_CHANGED, self)

    @protect_signal_handler
    def go_back_in_history(self, filter_=None, evt=None):
        item = self.history.go_back()
        if item is not None:
            rtmin, rtmax, mzmin, mzmax = item
            self.set_limits(rtmin, rtmax, mzmin, mzmax, add_to_history=False)
            self.emit(SIG_HISTORY_CHANGED, self.history)

    @protect_signal_handler
    def go_forward_in_history(self, filter_=None, evt=None):
        item = self.history.go_forward()
        if item is not None:
            rtmin, rtmax, mzmin, mzmax = item
            self.set_limits(rtmin, rtmax, mzmin, mzmax, add_to_history=False)
            self.emit(SIG_HISTORY_CHANGED, self.history)

    @protect_signal_handler
    def go_to_beginning_of_history(self, filter_=None, evt=None):
        """ resets zoom """
        item = self.history.skip_to_beginning()
        if item is not None:
            rtmin, rtmax, mzmin, mzmax = item
            self.set_limits(rtmin, rtmax, mzmin, mzmax, add_to_history=False)
            self.emit(SIG_HISTORY_CHANGED, self.history)

    @protect_signal_handler
    def go_to_end_of_history(self, filter_=None, evt=None):
        item = self.history.skip_to_end()
        if item is not None:
            rtmin, rtmax, mzmin, mzmax = item
            self.set_limits(rtmin, rtmax, mzmin, mzmax, add_to_history=False)
            self.emit(SIG_HISTORY_CHANGED, self.history)

    def set_history_position(self, idx):
        item = self.history.set_position(idx)
        if item is not None:
            rtmin, rtmax, mzmin, mzmax = item
            self.set_limits(rtmin, rtmax, mzmin, mzmax, add_to_history=False)

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
        if self.chromatogram_plot is not None:
            rt = self.invTransform(self.xBottom, pos.x())
            self.chromatogram_plot.set_rt(rt)
        if self.mz_plot is not None:
            mz = self.invTransform(self.yLeft, pos.y())
            self.mz_plot.set_mz(mz)

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

            self.set_limits(rtmin, rtmax, mzmin, mzmax, add_to_history=True)
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
            elif axis_id in axis_ids_vertical:
                vmin = max(vmin, self.peakmap_range[2])
                vmax = min(vmax, self.peakmap_range[3])

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
                vmin = max(vmin, self.peakmap_range[0])
                vmax = min(vmax, self.peakmap_range[1])
            elif axis_id in axis_ids_vertical:
                vmin = max(vmin, self.peakmap_range[2])
                vmax = min(vmax, self.peakmap_range[3])
            self.set_axis_limits(axis_id, vmin, vmax)

        self.setAutoReplot(auto)
        # the signal MUST be emitted after replot, otherwise
        # we receiver won't see the new bounds (don't know why?)
        self.replot()
        self.emit(SIG_PLOT_AXIS_CHANGED, self)


def create_table_widget(table, parent):
    formats = table.getColFormats()
    names = table.getColNames()
    indices_of_visible_columns = [j for (j, f) in enumerate(formats) if f is not None]
    headers = ["ok"] + [names[j] for j in indices_of_visible_columns]
    n_rows = len(table)

    widget = QTableWidget(n_rows, 1 + len(indices_of_visible_columns), parent=parent)
    widget.setHorizontalHeaderLabels(headers)
    widget.setMinimumSize(200, 200)

    widget.horizontalHeader().setResizeMode(QHeaderView.Interactive)

    for i, row in enumerate(table.rows):
        item = QTableWidgetItem()
        item.setCheckState(Qt.Unchecked)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)
        widget.setItem(i, 0, item)
        for j0, j in enumerate(indices_of_visible_columns):
            value = row[j]
            formatter = table.colFormatters[j]
            item = QTableWidgetItem(formatter(value))
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            widget.setItem(i, j0 + 1, item)
    return widget


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


def create_image_widget():
    # patched plot in widget
    widget = ImageWidget(lock_aspect_ratio=False, xlabel="rt", ylabel="m/z")

    # patch memeber's methods:
    widget.plot.__class__ = ModifiedImagePlot
    widget.plot.set_axis_direction("left", False)
    widget.plot.set_axis_direction("right", False)

    set_x_axis_scale_draw(widget)
    set_y_axis_scale_draw(widget)
    widget.plot.enableAxis(widget.plot.colormap_axis, False)

    return widget


def set_image_plot(widget, image_item, peakmap_range):
    widget.plot.peakmap_range = peakmap_range
    widget.plot.del_all_items()
    widget.plot.add_item(image_item)
    widget.plot.reset_history()
    create_peakmap_labels(widget.plot)
    # for zooming and panning with mouse drag:
    t = widget.add_tool(SelectTool)
    widget.set_default_tool(t)
    t.activate()
    # for selecting zoom window
    t = widget.add_tool(PeakmapZoomTool)
    t.activate()


def create_chromatogram_widget(image_plot):
    widget = CurveWidget(ylabel="I")
    t = widget.add_tool(SelectTool)
    widget.set_default_tool(t)
    t.activate()

    plot = widget.plot
    plot.__class__ = ChromatogramPlot
    plot.image_plot = image_plot
    image_plot.chromatogram_plot = plot

    plot.set_antialiasing(True)
    plot.cross_marker.setZ(plot.get_max_z() + 1)
    plot.cross_marker.setVisible(True)
    plot.canvas_pointer = True  # x-cross marker on

    cursor_info = RtCursorInfo()
    label = make.info_label("TR", [cursor_info], title="None")
    label.labelparam.label = ""
    label.labelparam.font.size = 12
    label.setVisible(1)
    label.labelparam.update_label(label)
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
        "marker/cross/line/style": "DashLine",
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


class PeakMapPlotter(object):

    def __init__(self):
        self.widget = create_image_widget()
        self.peakmap_item = None

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
        set_image_plot(self.widget, self.peakmap_item, get_range(peakmap, peakmap2))
        if gamma_before is not None:
            self.peakmap_item.set_gamma(gamma_before)

    def replot(self):
        self.widget.plot.replot()

    def __getattr__(self, name):
        if hasattr(self, "widget"):
            return getattr(self.widget.plot, name)

    def get_plot(self):
        return self.widget.plot

    def paint_pixmap(self):
        return self.peakmap_item.paint_pixmap(self.widget)

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


class ChromatogramPlotter(object):

    def __init__(self, image_plot):
        self.widget = create_chromatogram_widget(image_plot)
        set_x_axis_scale_draw(self.widget)
        set_y_axis_scale_draw(self.widget)

    def plot(self, rts, chroma, rts2=None, chroma2=None):
        self.widget.plot.plot_chromatograms(rts, chroma, rts2, chroma2)
        self.widget.plot.updateAxes()


class PeakMapExplorer(EmzedDialog):

    def __init__(self, ok_rows_container=[], parent=None):
        super(PeakMapExplorer, self).__init__(parent)
        self.setWindowFlags(Qt.Window)
        # Destroying the C++ object right after closing the dialog box,
        # otherwise it may be garbage-collected in another QThread
        # (e.g. the editor's analysis thread in Spyder), thus leading to
        # a segmentation fault on UNIX or an application crash on Windows
        self.ok_rows = ok_rows_container

        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowFlags(Qt.Window)

        self.gamma_min = 0.05
        self.gamma_max = 4.0
        self.gamma_start = 3.0

        self.last_used_directory_for_load = None
        self.last_used_directory_for_save = None

    def keyPressEvent(self, e):
        # avoid closing of dialog when Esc key pressed:
        if e.key() != Qt.Key_Escape:
            return super(PeakMapExplorer, self).keyPressEvent(e)

    def setWindowTitle(self):
        if self.peakmap2 is None:
            title = os.path.basename(self.peakmap.meta.get("source", ""))
        else:
            p1 = os.path.basename(self.peakmap.meta.get("source", ""))
            p2 = os.path.basename(self.peakmap2.meta.get("source", ""))
            title = "yellow=%s, blue=%s" % (p1, p2)
        super(PeakMapExplorer, self).setWindowTitle(title)

    def setup(self, peakmap, peakmap2=None, table=None):
        self.table = table

        def collect_precursor_mz(pm):
            for s in pm:
                if s.precursors:
                    if s.msLevel > 1:
                        yield s.precursors[0][0]

        self.ms_levels = set(peakmap.getMsLevels())
        self.precursor_mz = set(collect_precursor_mz(peakmap))
        if peakmap2 is not None:
            self.ms_levels &= set(peakmap2.getMsLevels())
            self.precursor_mz &= set(collect_precursor_mz(peakmap2))

        self.ms_levels = sorted(self.ms_levels)
        self.precursor_mz = sorted(self.precursor_mz)

        self.setup_table_widgets()
        self.setup_input_widgets()

        self.setup_ms2_widgets()
        self.full_pm = peakmap
        self.full_pm2 = peakmap2
        self.dual_mode = self.full_pm2 is not None

        self.setup_for_ms_level(min(self.ms_levels))
        self.rtmin, self.rtmax, self.mzmin, self.mzmax = get_range(self.peakmap, self.peakmap2)

        self.setup_plot_widgets()
        self.setup_menu_bar()
        self.setup_layout()
        self.connect_signals_and_slots()
        self.setup_initial_values()
        self.plot_peakmap()

    def setup_for_ms_level(self, ms_level):
        self.process_peakmap(ms_level)
        self.precursor_mz_min.setEnabled(ms_level > 1)
        self.precursor_mz_max.setEnabled(ms_level > 1)
        self.precursor.setEnabled(ms_level > 1)
        self.current_ms_level = ms_level

    def setup_ms2_widgets(self):
        self.precursor.clear()
        self.precursor.addItem("- use range -")
        for mz in self.precursor_mz:
            self.precursor.addItem("%.5f" % mz)

        for level in self.ms_levels:
            self.ms_level.addItem(str(level))

        if self.precursor_mz:
            self.precursor_mz_min.setText("%.5f" % min(self.precursor_mz))
            self.precursor_mz_max.setText("%.5f" % max(self.precursor_mz))

    def setup_table_widgets(self):
        if self.table is not None:
            self.table_widget = create_table_widget(self.table, self)
            self.select_all_peaks = QPushButton("Select all peaks", self)
            self.unselect_all_peaks = QPushButton("Unselect all peaks", self)
            self.done_button = QPushButton("Done", self)

    def setup_menu_bar(self):
        self.menu_bar = QMenuBar(self)
        menu = QMenu("Peakmap Explorer", self.menu_bar)
        self.menu_bar.addMenu(menu)
        if not self.dual_mode:
            self.load_action = QAction("Load Peakmap", self)
            self.load_action.setShortcut(QKeySequence("Ctrl+L"))
            self.load_action2 = None
            menu.addAction(self.load_action)
        else:
            self.load_action = QAction("Load Yellow Peakmap", self)
            self.load_action2 = QAction("Load Blue Peakmap", self)
            menu.addAction(self.load_action)
            menu.addAction(self.load_action2)

        self.save_action = QAction("Save selected range as image", self)
        self.save_action.setShortcut(QKeySequence("Ctrl+S"))
        menu.addAction(self.save_action)

        menu = QMenu("Help", self.menu_bar)
        self.help_action = QAction("Help", self)
        self.help_action.setShortcut(QKeySequence("F1"))
        menu.addAction(self.help_action)
        self.menu_bar.addMenu(menu)

    def process_peakmap(self, ms_level, pre_mz_min=None, pre_mz_max=None):

        peakmap = self.full_pm.filter(lambda s: s.msLevel == ms_level)
        if ms_level > 1 and pre_mz_min is not None:
            peakmap = peakmap.filter(lambda s: s.precursors[0][0] >= pre_mz_min)
        if ms_level > 1 and pre_mz_max is not None:
            peakmap = peakmap.filter(lambda s: s.precursors[0][0] <= pre_mz_max)

        if self.full_pm2 is not None:
            peakmap2 = self.full_pm2.filter(lambda s: s.msLevel == ms_level)

        self.peakmap = peakmap
        if self.dual_mode:
            self.peakmap2 = peakmap2
        else:
            self.peakmap2 = None

        for i, msl in enumerate(self.ms_levels):
            if msl == ms_level:
                self.ms_level.setCurrentIndex(i)

        self.setWindowTitle()

    def setup_initial_values(self):
        self.imin_input.setText("0")

        imax = self.peakmap_plotter.get_total_imax()
        imax = 10 ** math.ceil(math.log10(imax))
        self.imax_input.setText("%g" % imax)

        self.set_range_value_fields(self.rtmin, self.rtmax, self.mzmin, self.mzmax)

    def set_range_value_fields(self, rtmin, rtmax, mzmin, mzmax):
        is_ppm = self.dmz_is_ppm.isChecked()
        self.rtmin_input.setText("%.2f" % (rtmin / 60.0))
        self.rtmax_input.setText("%.2f" % (rtmax / 60.0))
        self.mzmin_input.setText("%.5f" % mzmin)
        self.mzmax_input.setText("%.5f" % mzmax)
        self.mz_middle_input.setText("%.5f" % ((mzmax + mzmin) / 2.0))
        if is_ppm:
            self.dmz_input.setText("%.1f" % ((mzmax - mzmin) / (mzmax + mzmin) * 1e6))
        else:
            self.dmz_input.setText("%.5f" % ((mzmax - mzmin) / 2.0))

    def setup_input_widgets(self):
        self.log_label = QLabel("Logarithmic Scale:", self)
        self.log_check_box = QCheckBox(self)
        self.log_check_box.setCheckState(1)
        self.log_check_box.setTristate(0)

        self.gamma_label = QLabel("Contrast:", self)
        self.gamma_slider = QSlider(Qt.Horizontal, self)
        self.gamma_slider.setMinimum(0)
        self.gamma_slider.setMaximum(50)

        rel_pos = (self.gamma_start - self.gamma_min) / (self.gamma_max - self.gamma_min)
        self.gamma_slider.setSliderPosition(50 * rel_pos)

        self.i_range_label = QLabel("Intensity:", self)

        self.imin_input = QLineEdit(self)
        self.imin_slider = QSlider(Qt.Horizontal, self)
        self.imin_slider.setMinimum(0)
        self.imin_slider.setMaximum(100)
        self.imin_slider.setSliderPosition(0)

        self.imax_slider = QSlider(Qt.Horizontal, self)
        self.imax_slider.setMinimum(0)
        self.imax_slider.setMaximum(100)
        self.imax_slider.setSliderPosition(1000)
        self.imax_input = QLineEdit(self)

        self.imax_input.setValidator(QDoubleValidator())
        self.imin_input.setValidator(QDoubleValidator())

        self.ms_level_label = QLabel("Choose MS Level:", self)
        self.ms_level = QComboBox(self)
        self.precursor_label = QLabel("Choose Precursor:", self)
        self.precursor = QComboBox(self)

        self.precursor_range_label = QLabel("MZ Range Precursor:")
        self.precursor_mz_min = QLineEdit(self)
        self.precursor_mz_min.setValidator(QDoubleValidator())
        self.precursor_mz_max = QLineEdit(self)
        self.precursor_mz_max.setValidator(QDoubleValidator())

        self.rt_range_label = QLabel("Retention Time [minutes]:", self)
        self.rtmin_input = QLineEdit(self)
        self.rtmin_input.setValidator(QDoubleValidator())
        self.rtmax_input = QLineEdit(self)
        self.rtmax_input.setValidator(QDoubleValidator())

        self.mz_middle_label = QLabel("Mass To Charge center + width:", self)
        self.dmz_is_ppm_label = QLabel("width in ppm ?")
        self.dmz_is_ppm = QCheckBox(self)
        self.mz_middle_input = QLineEdit(self)
        self.mz_middle_input.setValidator(QDoubleValidator())
        self.dmz_input = QLineEdit(self)
        self.dmz_input.setValidator(QDoubleValidator())
        self.dmz_input.setText("0.001")

        self.mz_range_label = QLabel("Mass to Charge range [Da]:", self)
        self.mzmin_input = QLineEdit(self)
        self.mzmin_input.setValidator(QDoubleValidator())
        self.mzmax_input = QLineEdit(self)
        self.mzmax_input.setValidator(QDoubleValidator())

        # self.history_list_label = QLabel("History:", self)
        self.history_list = QComboBox(self)

    def setup_plot_widgets(self):
        self.peakmap_plotter = PeakMapPlotter()
        self.peakmap_plotter.set_peakmaps(self.peakmap, self.peakmap2)
        image_plot = self.peakmap_plotter.widget.plot
        self.chromatogram_plotter = ChromatogramPlotter(image_plot=image_plot)
        self.mz_plotter = MzPlotter(None, image_plot=image_plot)
        self.peakmap_plotter.widget.plot.mz_plot = self.mz_plotter.widget.plot

        self.peakmap_plotter.set_logarithmic_scale(1)
        self.peakmap_plotter.set_gamma(self.gamma_start)

    def setup_layout(self):
        outer_layout = QVBoxLayout()
        outer_layout.addWidget(self.menu_bar)
        outer_layout.setStretch(0, 1)

        h_splitter = QSplitter(self)
        h_splitter.setOrientation(Qt.Horizontal)

        # FIRST COLUMN of h_splitter is chromatogram + peakmap:  ############################

        v_splitter1 = QSplitter(self)
        v_splitter1.setOrientation(Qt.Vertical)
        v_splitter1.addWidget(self.chromatogram_plotter.widget)
        v_splitter1.addWidget(self.peakmap_plotter.widget)
        self.peakmap_plotter.widget.setMinimumSize(250, 200)
        v_splitter1.setStretchFactor(0, 1)
        v_splitter1.setStretchFactor(1, 3)

        h_splitter.addWidget(v_splitter1)
        h_splitter.setStretchFactor(0, 2)

        # SECOND COLUMN of h_splittier holds controlx boxes + mz plot #######################

        frame1, frame2 = self.layout_control_boxes()

        v_splitter2 = QSplitter(self)
        v_splitter2.setOrientation(Qt.Vertical)

        v_splitter2.addWidget(frame1)
        v_splitter2.addWidget(frame2)
        v_splitter2.addWidget(self.mz_plotter.widget)

        v_splitter2.setStretchFactor(0, 1)
        v_splitter2.setStretchFactor(1, 1)
        v_splitter2.setStretchFactor(2, 2)

        h_splitter.addWidget(v_splitter2)
        h_splitter.setStretchFactor(1, 1)

        # THIRD COLUMN of h_splittier holds control table + buttons ##########################
        if self.table:
            frame = QFrame(self)
            layout = QVBoxLayout(frame)
            frame.setLayout(layout)
            layout.addWidget(self.table_widget)

            button_row_layout = QHBoxLayout(frame)
            button_row_layout.addWidget(self.select_all_peaks)
            button_row_layout.addWidget(self.unselect_all_peaks)
            button_row_layout.addWidget(self.done_button)

            layout.addLayout(button_row_layout)
            h_splitter.addWidget(frame)
            h_splitter.setStretchFactor(2, 2)

        outer_layout.addWidget(h_splitter)
        self.setLayout(outer_layout)
        outer_layout.setStretch(1, 99)

    def layout_control_boxes(self):

        controls_layout = QGridLayout()
        controls_layout.setSpacing(5)
        controls_layout.setMargin(5)

        row = 0
        controls_layout.addWidget(self.log_label, row, 0)
        controls_layout.addWidget(self.log_check_box, row, 1)
        controls_layout.addWidget(self.gamma_label, row, 2)
        controls_layout.addWidget(self.gamma_slider, row, 3)

        row += 1
        controls_layout.addWidget(self.i_range_label, row, 0, 1, 4)

        row += 1
        controls_layout.addWidget(self.imin_input, row, 0)
        controls_layout.addWidget(self.imin_slider, row, 1)
        controls_layout.addWidget(self.imax_slider, row, 2)
        controls_layout.addWidget(self.imax_input, row, 3)

        frame = QFrame(self)
        frame.setLineWidth(1)
        frame.setFrameStyle(QFrame.Box | QFrame.Plain)
        frame.setLayout(controls_layout)

        controls_layout = QGridLayout()
        controls_layout.setSpacing(5)
        controls_layout.setMargin(5)

        row = 0
        controls_layout.addWidget(self.ms_level_label, row, 0, 1, 2)
        controls_layout.addWidget(self.ms_level, row, 2, 1, 2)

        row += 1
        controls_layout.addWidget(self.precursor_label, row, 0, 1, 2)
        controls_layout.addWidget(self.precursor, row, 2, 1, 2)

        row += 1
        controls_layout.addWidget(self.precursor_range_label, row, 0, 1, 4)
        row += 1
        controls_layout.addWidget(self.precursor_mz_min, row, 0, 1, 2)
        controls_layout.addWidget(self.precursor_mz_max, row, 2, 1, 2)

        row += 1
        controls_layout.addWidget(self.rt_range_label, row, 0, 1, 4)

        row += 1
        controls_layout.addWidget(self.rtmin_input, row, 0, 1, 2)
        controls_layout.addWidget(self.rtmax_input, row, 2, 1, 2)

        row += 1
        controls_layout.addWidget(self.mz_middle_label, row, 0, 1, 2)
        controls_layout.addWidget(self.dmz_is_ppm_label, row, 2, 1, 1)
        controls_layout.addWidget(self.dmz_is_ppm, row, 3)

        row += 1
        controls_layout.addWidget(self.mz_middle_input, row, 0, 1, 2)
        controls_layout.addWidget(self.dmz_input, row, 2, 1, 2)

        row += 1
        controls_layout.addWidget(self.mz_range_label, row, 0, 1, 4)

        row += 1
        controls_layout.addWidget(self.mzmin_input, row, 0, 1, 2)
        controls_layout.addWidget(self.mzmax_input, row, 2, 1, 2)

        row += 1
        controls_layout.addWidget(self.history_list, row, 0, 1, 4)

        frame2 = QFrame(self)
        frame2.setLineWidth(1)
        frame2.setFrameStyle(QFrame.Box | QFrame.Plain)
        frame2.setLayout(controls_layout)

        return frame, frame2

    def connect_signals_and_slots(self):
        self.connect(self.log_check_box, SIGNAL("stateChanged(int)"), self.log_changed)
        self.connect(self.gamma_slider, SIGNAL("valueChanged(int)"), self.gamma_changed)

        self.connect(self.imin_input, SIGNAL("editingFinished()"), self.imin_edited)
        self.connect(self.imax_input, SIGNAL("editingFinished()"), self.imax_edited)

        self.connect(self.imin_slider, SIGNAL("valueChanged(int)"), self.imin_slider_changed)
        self.connect(self.imax_slider, SIGNAL("valueChanged(int)"), self.imax_slider_changed)

        self.connect(self.ms_level, SIGNAL("activated(int)"), self.ms_level_chosen)
        self.connect(self.precursor, SIGNAL("activated(int)"), self.precursor_chosen)
        self.connect(self.precursor_mz_min, SIGNAL("returnPressed()"), self.set_precursor_range)
        self.connect(self.precursor_mz_max, SIGNAL("returnPressed()"), self.set_precursor_range)


        self.connect(self.rtmin_input, SIGNAL("returnPressed()"), self.set_image_range)
        self.connect(self.rtmax_input, SIGNAL("returnPressed()"), self.set_image_range)
        self.connect(self.mzmin_input, SIGNAL("returnPressed()"), self.set_image_range)
        self.connect(self.mzmax_input, SIGNAL("returnPressed()"), self.set_image_range)

        self.connect(self.mz_middle_input, SIGNAL("returnPressed()"), self.set_image_range_from_center)
        self.connect(self.dmz_input, SIGNAL("returnPressed()"), self.set_image_range_from_center)
        self.connect(self.dmz_is_ppm, SIGNAL("stateChanged(int)"), self.dmz_mode_changed)

        self.connect(self.history_list, SIGNAL("activated(int)"), self.history_item_selected)

        self.connect(self.peakmap_plotter.get_plot(), SIG_PLOT_AXIS_CHANGED, self.changed_axis)
        self.connect(self.peakmap_plotter.get_plot(), SIG_HISTORY_CHANGED, self.history_changed)

        if self.dual_mode:
            self.connect(self.load_action, SIGNAL("triggered()"), self.do_load_yellow)
            self.connect(self.load_action2, SIGNAL("triggered()"), self.do_load_blue)
        else:
            self.connect(self.load_action, SIGNAL("triggered()"), self.do_load)
        self.connect(self.save_action, SIGNAL("triggered()"), self.do_save)
        self.connect(self.help_action, SIGNAL("triggered()"), self.show_help)

        if self.table is not None:
            self.connect(self.table_widget.verticalHeader(), SIGNAL("sectionClicked(int)"),
                         self.row_selected)
            self.connect(self.table_widget, SIGNAL("itemClicked(QTableWidgetItem*)"),
                         self.cell_clicked)
            self.connect(self.select_all_peaks, SIGNAL("pressed()"),
                         self.select_all_peaks_button_pressed)
            self.connect(self.unselect_all_peaks, SIGNAL("pressed()"),
                         self.unselect_all_peaks_button_pressed)
            self.connect(self.done_button, SIGNAL("pressed()"),
                         self.done_button_pressed)

            def key_release_handler(evt):
                tw = self.table_widget
                active_rows = set(ix.row() for ix in tw.selectionModel().selection().indexes())
                if active_rows:
                    row = active_rows.pop()
                    if evt.key() in (Qt.Key_Up, Qt.Key_Down):
                        tw.selectRow(row)
                        tw.verticalHeader().emit(SIGNAL("sectionClicked(int)"), row)
                        return
                return QTableWidget.keyPressEvent(tw, evt)

            self.table_widget.keyReleaseEvent = key_release_handler

    @protect_signal_handler
    def do_save(self):
        pix = self.peakmap_plotter.paint_pixmap()
        while True:
            path = askForSave(self.last_used_directory_for_save,
                              caption="Save Image",
                              extensions=("png", "PNG")
                              )
            if path is None:
                break
            __, ext = os.path.splitext(path)
            if ext not in (".png", ".PNG"):
                QMessageBox.warning(self, "Warning", "wrong/missing extension '.png'")
            else:
                self.last_used_directory_for_save = os.path.dirname(path)
                pix.save(path)
                break
        return

    def _do_load(self, title, attribute):
        path = askForSingleFile(self.last_used_directory_for_load,
                                caption=title,
                                extensions=("mzML", "mzData", "mzXML")
                                )
        if path is not None:
            setattr(self, attribute, loadPeakMap(path))
            self.process_peakmap()
            self.peakmap_plotter.set_peakmaps(self.peakmap, self.peakmap2)
            self.setup_initial_values()
            self.setWindowTitle()
            self.peakmap_plotter.replot()
            self.plot_peakmap()
            self.last_used_directory_for_load = os.path.dirname(path)

    @protect_signal_handler
    def do_load(self):
        self._do_load("Load Peakmap", "peakmap")

    @protect_signal_handler
    def do_load_yellow(self):
        self._do_load("Load Yellow Peakmap", "peakmap")

    @protect_signal_handler
    def do_load_blue(self):
        self._do_load("Load Blue Peakmap", "peakmap2")

    @protect_signal_handler
    def select_all_peaks_button_pressed(self):
        for row in range(self.table_widget.rowCount()):
            item = self.table_widget.item(row, 0)
            item.setCheckState(Qt.Checked)

    @protect_signal_handler
    def unselect_all_peaks_button_pressed(self):
        for row in range(self.table_widget.rowCount()):
            item = self.table_widget.item(row, 0)
            item.setCheckState(Qt.Unchecked)

    @protect_signal_handler
    def done_button_pressed(self):
        self.ok_rows[:] = [i for i in range(len(self.table))
                           if self.table_widget.item(i, 0).checkState() == Qt.Checked]
        self.accept()

    @protect_signal_handler
    def row_selected(self, row_idx):
        row = self.table.getValues(self.table.rows[row_idx])
        needed = ["rtmin", "rtmax", "mzmin", "mzmax"]
        if all(n in row for n in needed):
            rtmin, rtmax, mzmin, mzmax = [row.get(ni) for ni in needed]
            self.peakmap_plotter.set_limits(rtmin, rtmax, mzmin, mzmax, True)
        else:
            needed = ["mzmin", "mzmax"]
            if all(n in row for n in needed):
                mzmin, mzmax = [row.get(ni) for ni in needed]
                self.peakmap_plotter.set_limits(self.rtmin, self.rtmax, mzmin, mzmax, True)

    @protect_signal_handler
    def cell_clicked(self, item):
        row = item.row()
        self.table_widget.selectRow(row)
        self.table_widget.verticalHeader().emit(SIGNAL("sectionClicked(int)"), row)

    @protect_signal_handler
    def show_help(self):
        html = resource_string("emzed.core.explorers", "help_peakmapexplorer.html")
        QWebSettings.globalSettings().setFontFamily(QWebSettings.StandardFont, 'Courier')
        QWebSettings.globalSettings().setFontSize(QWebSettings.DefaultFontSize, 12)
        v = QWebView(self)
        v.setHtml(html)
        dlg = QDialog(self, Qt.Window)
        dlg.setMinimumSize(300, 300)
        l = QVBoxLayout(dlg)
        l.addWidget(v)
        dlg.setLayout(l)
        dlg.show()

    @protect_signal_handler
    def history_changed(self, history):
        self.history_list.clear()
        for item in history.items:
            rtmin, rtmax, mzmin, mzmax = item
            str_item = "%10.5f .. %10.5f %6.2fm...%6.2fm " % (mzmin, mzmax, rtmin / 60.0,
                                                              rtmax / 60.0)
            self.history_list.addItem(str_item)

        self.history_list.setCurrentIndex(history.position)

    @protect_signal_handler
    def history_item_selected(self, index):
        self.peakmap_plotter.set_history_position(index)

    @protect_signal_handler
    def changed_axis(self, evt=None):
        if evt is not None:
            rtmin, rtmax = evt.get_axis_limits("bottom")
            mzmin, mzmax = evt.get_axis_limits("left")
        else:
            rtmin, rtmax = self.peakmap.rtRange()
            mzmin, mzmax = full_range(self.peakmap)

        rts, chroma = self.peakmap.chromatogram(mzmin, mzmax, rtmin, rtmax)
        if self.dual_mode:
            rts2, chroma2 = self.peakmap2.chromatogram(mzmin, mzmax, rtmin, rtmax)
            self.chromatogram_plotter.plot(rts, chroma, rts2, chroma2)
        else:
            self.chromatogram_plotter.plot(rts, chroma)

        if self.dual_mode:
            data = [(self.peakmap, rtmin, rtmax, mzmin, mzmax, 3000),
                    (self.peakmap2, rtmin, rtmax, mzmin, mzmax, 3000)]
            configs = [dict(color="#aaaa00"), dict(color="#0000aa")]
            self.mz_plotter.plot(data, configs)
        else:
            self.mz_plotter.plot([(self.peakmap, rtmin, rtmax, mzmin, mzmax, 3000)])

        self.mz_plotter.widget.plot.reset_x_limits()
        self.mz_plotter.widget.plot.reset_y_limits()
        self.mz_plotter.updateAxes()
        self.mz_plotter.replot()
        self.set_range_value_fields(rtmin, rtmax, mzmin, mzmax)

    @protect_signal_handler
    def log_changed(self, is_log):
        self.peakmap_plotter.set_logarithmic_scale(is_log)
        self.peakmap_plotter.replot()

    @protect_signal_handler
    def ms_level_chosen(self, value):
        ms_level = self.ms_levels[value]
        if ms_level != self.current_ms_level:
            self.setup_for_ms_level(ms_level)
            self.peakmap_plotter.set_peakmaps(self.peakmap, self.peakmap2)
            self.peakmap_plotter.replot()
            self.plot_peakmap()

    @protect_signal_handler
    def precursor_chosen(self, item):
        if item > 0:
            mz_pre = self.precursor_mz[item - 1]
            self.precursor_mz_min.setText("%.5f" % (mz_pre - 0.01))
            self.precursor_mz_max.setText("%.5f" % (mz_pre + 0.01))
            self.process_peakmap(self.current_ms_level, mz_pre - 0.01, mz_pre + 0.01)
            self.peakmap_plotter.set_peakmaps(self.peakmap, self.peakmap2)
            self.peakmap_plotter.replot()
            self.plot_peakmap()
        else:
            self.set_precursor_range()

    @protect_signal_handler
    def set_precursor_range(self):
        pre_mz_min = read_float(self.precursor_mz_min)
        pre_mz_max = read_float(self.precursor_mz_max)
        if pre_mz_min is None or pre_mz_max is None:
            return

        self.precursor.setCurrentIndex(0)
        self.process_peakmap(self.current_ms_level, pre_mz_min, pre_mz_max)
        self.peakmap_plotter.set_peakmaps(self.peakmap, self.peakmap2)
        self.peakmap_plotter.replot()
        self.plot_peakmap()


    @protect_signal_handler
    def gamma_changed(self, value):

        value = self.gamma_slider.value()
        gamma = value / 1.0 / self.gamma_slider.maximum() * (self.gamma_max -
                                                             self.gamma_min) + self.gamma_min
        self.peakmap_plotter.set_gamma(gamma)
        self.peakmap_plotter.replot()

    # ---- handle intensity text field edits

    def _i_edited(self, inp, setter, slider):
        abs_value = read_float(inp)
        if abs_value is None:
            return
        setter(abs_value)

        slider_value = (
            abs_value / self.peakmap_plotter.get_total_imax()) ** 0.3333333 * slider.maximum()

        slider.blockSignals(True)
        slider.setSliderPosition(slider_value)
        slider.blockSignals(False)
        self.peakmap_plotter.replot()

    @protect_signal_handler
    def imin_edited(self):
        self._i_edited(self.imin_input, self.peakmap_plotter.set_imin, self.imin_slider)

    @protect_signal_handler
    def imax_edited(self):
        self._i_edited(self.imax_input, self.peakmap_plotter.set_imax, self.imax_slider)

    # ---- handle intensity slider change

    def _i_slider_changed(self, value, slider, setter, text_field):
        i_rel = value / 1.0 / slider.maximum()
        i_rel = i_rel ** 4
        i_abs = i_rel * self.peakmap_plotter.get_total_imax()  # total_imax !
        if i_abs > 0:
            # only keep signifcant first digit:
            tens = 10 ** int(math.log10(i_abs))
            i_abs = round(i_abs / tens) * tens
        setter(i_abs)
        text_field.setText("%g" % i_abs)
        self.peakmap_plotter.replot()

    @protect_signal_handler
    def imin_slider_changed(self, value):
        if value > self.imax_slider.value():
            self.imax_slider.setSliderPosition(value)
        self._i_slider_changed(
            value, self.imin_slider, self.peakmap_plotter.set_imin, self.imin_input)
        return

    @protect_signal_handler
    def imax_slider_changed(self, value):
        if value < self.imin_slider.value():
            self.imin_slider.setSliderPosition(value)
        self._i_slider_changed(
            value, self.imax_slider, self.peakmap_plotter.set_imax, self.imax_input)
        return

    def _read_rt_values(self):
        rtmin = read_float(self.rtmin_input)
        rtmax = read_float(self.rtmax_input)
        if rtmin is None or rtmax is None:
            guidata.qapplication().beep()
            return self.rtmin, self.rtmax
        return rtmin, rtmax

    @protect_signal_handler
    def set_image_range(self):
        rtmin, rtmax = self._read_rt_values()
        mzmin = read_float(self.mzmin_input)
        mzmax = read_float(self.mzmax_input)
        if mzmin is None or mzmax is None:
            guidata.qapplication().beep()
            return
        mzmean = (mzmin + mzmax) / 2.0
        dmz = (mzmax - mzmin) / 2.0
        is_ppm = self.dmz_is_ppm.isChecked()
        if is_ppm:
            dmz = dmz / mzmean * 1e6
            self.dmz_input.setText("%.1f" % dmz)
        else:
            self.dmz_input.setText("%.5f" % dmz)
        self.mz_middle_input.setText("%.5f" % mzmean)
        self.update_image_range(rtmin, rtmax, mzmin, mzmax)

    @protect_signal_handler
    def set_image_range_from_center(self):
        middle = read_float(self.mz_middle_input)
        dmz = read_float(self.dmz_input)
        if middle is None or dmz is None:
            return

        is_ppm = self.dmz_is_ppm.isChecked()
        if is_ppm:
            dmz = dmz * middle * 1e-6

        mzmin = middle - dmz
        mzmax = middle + dmz
        # self.mzmin_input.setText("%.6f" % mzmin)
        # self.mzmax_input.setText("%.6f" % mzmax)
        rtmin, rtmax = self._read_rt_values()
        self.update_image_range(rtmin, rtmax, mzmin, mzmax)

    @protect_signal_handler
    def dmz_mode_changed(self, is_ppm):
        is_ppm = bool(is_ppm)   # current we receive int values 0 or 2 from qt
        mz_middle = read_float(self.mz_middle_input)
        dmz = read_float(self.dmz_input)
        if is_ppm:
            # dalton -> ppm
            dmz = "%.1f" % (1e6 * dmz / mz_middle)
        else:
            dmz = "%.5f" % (dmz * mz_middle * 1e-6)
        self.dmz_input.setText(dmz)

    @protect_signal_handler
    def update_image_range(self, rtmin, rtmax, mzmin, mzmax):

        rtmin *= 60.0
        rtmax *= 60.0

        if rtmin < self.rtmin:
            rtmin = self.rtmin
        if rtmax > self.rtmax:
            rtmax = self.rtmax
        if mzmin < self.mzmin:
            mzmin = self.mzmin
        if mzmax > self.mzmax:
            mzmax = self.mzmax
        rtmin, rtmax = sorted((rtmin, rtmax))
        mzmin, mzmax = sorted((mzmin, mzmax))

        self.set_range_value_fields(rtmin, rtmax, mzmin, mzmax)
        self.peakmap_plotter.set_limits(rtmin, rtmax, mzmin, mzmax, add_to_history=True)

    def plot_peakmap(self):
        self.peakmap_plotter.set_limits(self.rtmin, self.rtmax, self.mzmin, self.mzmax,
                                        add_to_history=True)


def inspectPeakMap(peakmap, peakmap2=None, table=None, modal=True, parent=None, rtmin=None,
                   rtmax=None, mzmin=None, mzmax=None):
    """
    allows the visual inspection of a peakmap
    """

    peakmap = peakmap.cleaned()

    if len(peakmap) == 0:
        raise Exception("empty peakmap")

    app = guidata.qapplication()  # singleton !
    ok_rows = []
    win = PeakMapExplorer(ok_rows, parent=parent)
    win.setup(peakmap, peakmap2, table)

    if modal:
        win.raise_()
        win.exec_()
        return ok_rows
    else:
        win.show()

    return ok_rows

if __name__ == "__main__":
    import emzed.io
    peakmap = emzed.io.loadPeakMap("peakmap.mzML")
    inspectPeakMap(peakmap)
