import datetime

import numpy as np

from PyQt4.QtCore import Qt, pyqtSignal, QObject
from PyQt4.QtGui import QPainter
from guiqwt.curve import CurvePlot, CurveItem
from guiqwt.events import ObjectHandler, KeyEventMatch, QtDragHandler
from guiqwt.signals import (SIG_MOVE, SIG_START_TRACKING, SIG_STOP_NOT_MOVING, SIG_STOP_MOVING)

from guiqwt.events import ZoomHandler, PanHandler, MoveHandler

from guiqwt.tools import InteractiveTool
from guiqwt.builder import make

from guidata import qapplication

from guiqwt.shapes import Marker, SegmentShape, XRangeSelection

from helpers import protect_signal_handler, timethis


def patch_inner_plot_object(widget, plot_clz):
    # we overwrite some methods of the given object:
    widget.plot.__class__ = plot_clz

    # we attach a signal (pyqtSignal is only usable for subclasses of QObject, and
    # deriving from QObject does not work with multiple inheritance, so we have to apply
    # some trickery):
    class _Q(QObject):
        CURSOR_MOVED = pyqtSignal(float)
        VIEW_RANGE_CHANGED = pyqtSignal(float, float)

    widget._q = _Q()
    widget.CURSOR_MOVED = widget.plot.CURSOR_MOVED = widget._q.CURSOR_MOVED
    widget.VIEW_RANGE_CHANGED = widget.plot.VIEW_RANGE_CHANGED = widget._q.VIEW_RANGE_CHANGED


class UnselectableCurveItem(CurveItem):

    """ modification(s):
          selection (which plots a square at each (x,y) ) is turned off
    """

    def can_select(self):
        return False


def make_unselectable_curve(*a, **kw):
    curve = make.curve(*a, **kw)
    curve.__class__ = UnselectableCurveItem
    return curve


def make_measurement_line():
    line = make.segment(0, 0, 0, 0)
    line.__class__ = MesaurementLine
    return line


class ImprovedPanHandler(PanHandler):

    def __init__(self, filter, btn, mods=Qt.NoModifier, start_state=0):
        super(ImprovedPanHandler, self).__init__(filter, btn, mods, start_state)
        # additionally we reset state machine if mouse is release anyhow !
        filter.add_event(self.state0, filter.mouse_release(btn),
                         self.stop_notmoving, start_state)
        filter.add_event(self.state1, filter.mouse_release(btn),
                         self.stop_moving, start_state)


class ImprovedZoomHandler(ZoomHandler):

    def __init__(self, filter, btn, mods=Qt.NoModifier, start_state=0):
        super(ImprovedZoomHandler, self).__init__(filter, btn, mods, start_state)
        # additionally we reset state machine if mouse is release anyhow !
        filter.add_event(self.state0, filter.mouse_release(btn),
                         self.stop_notmoving, start_state)
        filter.add_event(self.state1, filter.mouse_release(btn),
                         self.stop_moving, start_state)


class RtSelectionTool(InteractiveTool):

    """
        modified event handling:
            - enter, space, backspace, left crsr and right crsr keys trigger handlers in baseplot
    """
    TITLE = "Rt Selection"
    ICON = "selection.png"
    CURSOR = Qt.ArrowCursor

    def setup_filter(self, baseplot):
        filter = baseplot.filter
        # Initialisation du filtre
        start_state = filter.new_state()
        # Bouton gauche :
        ObjectHandler(filter, Qt.LeftButton, start_state=start_state)

        filter.add_event(start_state,
                         KeyEventMatch((Qt.Key_Enter, Qt.Key_Return,)),
                         baseplot.do_enter_pressed, start_state)

        filter.add_event(start_state,
                         KeyEventMatch((Qt.Key_Space,)),
                         baseplot.do_space_pressed, start_state)

        filter.add_event(start_state,
                         KeyEventMatch((Qt.Key_Right,)),
                         baseplot.do_right_pressed, start_state)

        filter.add_event(start_state,
                         KeyEventMatch((Qt.Key_Left,)),
                         baseplot.do_left_pressed, start_state)

        filter.add_event(start_state,
                         KeyEventMatch((Qt.Key_Backspace, Qt.Key_Escape)),
                         baseplot.do_backspace_pressed, start_state)

        # Bouton du milieu
        ImprovedPanHandler(filter, Qt.MidButton, start_state=start_state)
        ImprovedPanHandler(filter, Qt.LeftButton, mods=Qt.AltModifier, start_state=start_state)

        # Bouton droit
        ImprovedZoomHandler(filter, Qt.RightButton, start_state=start_state)
        ImprovedZoomHandler(filter, Qt.LeftButton, mods=Qt.ControlModifier, start_state=start_state)

        # Autres (touches, move)
        MoveHandler(filter, start_state=start_state)
        MoveHandler(filter, start_state=start_state, mods=Qt.ShiftModifier)
        MoveHandler(filter, start_state=start_state, mods=Qt.AltModifier)
        return start_state


class MzSelectionTool(InteractiveTool):

    """
       modified event handling:
           - space and backspac keys trigger handlers in baseplot
           - calling handlers for dragging with mouse
    """

    TITLE = "mZ Selection"
    ICON = "selection.png"
    CURSOR = Qt.CrossCursor

    def setup_filter(self, baseplot):
        filter = baseplot.filter
        # Initialisation du filtre
        start_state = filter.new_state()
        # Bouton gauche :

        # start_state = filter.new_state()
        handler = QtDragHandler(filter, Qt.LeftButton, start_state=start_state)

        filter.add_event(start_state,
                         KeyEventMatch((Qt.Key_Space,)),
                         baseplot.do_space_pressed, start_state)
        filter.add_event(start_state,
                         KeyEventMatch((Qt.Key_Backspace, Qt.Key_Escape)),
                         baseplot.do_backspace_pressed, start_state)

        self.connect(handler, SIG_MOVE, baseplot.move_in_drag_mode)
        self.connect(handler, SIG_START_TRACKING, baseplot.start_drag_mode)
        self.connect(handler, SIG_STOP_NOT_MOVING, baseplot.stop_drag_mode)
        self.connect(handler, SIG_STOP_MOVING, baseplot.stop_drag_mode)

        """
        filter.add_event(self.state0, filter.mouse_release(btn),
                         self.stop_notmoving, start_state)
        filter.add_event(self.state1, filter.mouse_release(btn),
                         self.stop_moving, start_state)
        """

        # Bouton du milieu
        ImprovedPanHandler(filter, Qt.MidButton, start_state=start_state)
        ImprovedPanHandler(filter, Qt.LeftButton, mods=Qt.AltModifier, start_state=start_state)

        # Bouton droit
        class ZoomHandlerWithStopingEvent(ImprovedZoomHandler):

            def stop_moving(self, filter_, event):
                x_state, y_state = self.get_move_state(filter_, event.pos())
                filter_.plot.do_finish_zoom_view(x_state, y_state)

        ZoomHandlerWithStopingEvent(filter, Qt.RightButton, start_state=start_state)
        ZoomHandlerWithStopingEvent(filter, Qt.LeftButton, mods=Qt.ControlModifier, start_state=start_state)

        # Autres (touches, move)
        MoveHandler(filter, start_state=start_state)
        MoveHandler(filter, start_state=start_state, mods=Qt.ShiftModifier)
        MoveHandler(filter, start_state=start_state, mods=Qt.AltModifier)
        return start_state


class PositiveValuedCurvePlot(CurvePlot):

    """ modifications:
            - zooming preserves x asix at bottom of plot
            - panning is only in x direction
            - handler for backspace, called by RtSelectionTool and MzSelectionTool
    """

    overall_x_min = None
    overall_x_max = None

    @protect_signal_handler
    def do_zoom_view(self, dx, dy, lock_aspect_ratio=False):
        """
        modified version of do_zoom_view from base class,
        we restrict zooming and panning to positive y-values

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

            # patch for not zooming into "negative space" ;) :
            if axis_id in axis_ids_vertical:
                vmin = 0
                if vmax < 0:
                    vmax = -vmax
            else:
                if self.overall_x_min is not None:
                    if vmin < self.overall_x_min:
                        vmin = self.overall_x_min
                        vmax = self.overall_x_max
                if self.overall_x_max is not None:
                    if vmax > self.overall_x_max:
                        vmin = self.overall_x_min
                        vmax = self.overall_x_max
                final_xmin = vmin
                final_xmax = vmax
            self.set_axis_limits(axis_id, vmin, vmax)

        self.setAutoReplot(auto)
        # the signal MUST be emitted after replot, otherwise
        # we receiver won't see the new bounds (don't know why?)
        self.replot()
        # self.emit(SIG_PLOT_AXIS_CHANGED, self)
        self.VIEW_RANGE_CHANGED.emit(final_xmin, final_xmax)

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
        axis_ids_vertical = (self.get_axis_id("left"), self.get_axis_id("right"))

        # tofix: compute range of overall spectrum, not range of shown peaks:
        for (x1, x0, _start, _width), axis_id in axes_to_update:
            lbound, hbound = self.get_axis_limits(axis_id)
            i_lbound = self.transform(axis_id, lbound)
            i_hbound = self.transform(axis_id, hbound)
            delta = x1 - x0
            vmin = self.invTransform(axis_id, i_lbound - delta)
            vmax = self.invTransform(axis_id, i_hbound - delta)
            # patch for not zooming into "negative space" ;) :
            if axis_id in axis_ids_vertical:
                vmin = 0
                if vmax < 0:
                    vmax = -vmax
            if axis_id not in axis_ids_vertical:
                if self.overall_x_min is not None:
                    if vmin < self.overall_x_min:
                        self.setAutoReplot(auto)
                        return
                if self.overall_x_max is not None:
                    if vmax > self.overall_x_max:
                        self.setAutoReplot(auto)
                        return
                final_xmin = vmin
                final_xmax = vmax
            self.set_axis_limits(axis_id, vmin, vmax)

        self.setAutoReplot(auto)
        # the signal MUST be emitted after replot, otherwise
        # we receiver won't see the new bounds (don't know why?)
        self.replot()
        self.VIEW_RANGE_CHANGED.emit(final_xmin, final_xmax)


class ExtendedCurvePlot(CurvePlot):

    @protect_signal_handler
    def do_backspace_pressed(self, filter, evt):
        """ reset axes of plot """
        self.reset_x_limits()

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

    def set_limit(self, ix, value):
        limits = list(self.get_plot_limits())
        limits[ix] = value
        self.set_plot_limits(*limits)

    def seen_yvals(self, xmin, xmax):
        yvals = []
        if isinstance(xmin, datetime.datetime):
            xmin = xmin.toordinal()
        if isinstance(xmax, datetime.datetime):
            xmax = xmax.toordinal()
        for item in self.items:
            if isinstance(item, CurveItem):
                x, y = item.get_data()
                xy = zip(x, y)
                xy = [(xi, yi) for (xi, yi) in xy if xmin is None or xi >= xmin]
                xy = [(xi, yi) for (xi, yi) in xy if xmax is None or xi <= xmax]
                if xy:
                    x, y = zip(*xy)  # unzip
                    yvals.extend(y)
        return yvals

    def reset_x_limits(self, xmin=None, xmax=None, fac=1.0):
        xvals = []
        for item in self.items:
            if isinstance(item, CurveItem):
                x, _ = item.get_data()
                xvals.extend(list(x))
        if xmin is None:
            if len(xvals):
                xmin = min(xvals) / fac
        if xmax is None:
            if len(xvals):
                xmax = max(xvals) * fac

        if xmin is not None and xmax is not None:
            if xmin == xmax:  # zoomint to same min and max limits looks strange, so we zoom a bit:
                xmin *= 0.9
                xmax *= 1.1
            self.update_plot_xlimits(xmin, xmax)

    def reset_y_limits(self, ymin=None, ymax=None, fac=1.1, xmin=None, xmax=None):

        yvals = self.seen_yvals(xmin, xmax)

        if ymin is None:
            if len(yvals) > 0:
                ymin = min(yvals) / fac
            else:
                ymin = 0
        if ymax is None:
            if len(yvals) > 0:
                ymax = max(yvals) * fac
            else:
                ymax = 1.0
        self.update_plot_ylimits(ymin, ymax)

    def update_plot_xlimits(self, xmin, xmax):
        _, _, ymin, ymax = self.get_plot_limits()
        self.set_plot_limits(xmin, xmax, ymin, ymax)
        self.VIEW_RANGE_CHANGED.emit(xmin, xmax)
        self.setAxisAutoScale(self.yLeft)  # y-achse
        self.updateAxes()
        self.replot()

    def update_plot_ylimits(self, ymin, ymax):
        xmin, xmax, _, _ = self.get_plot_limits()
        self.set_plot_limits(xmin, xmax, ymin, ymax)
        self.updateAxes()
        self.replot()


class EicPlot(PositiveValuedCurvePlot, ExtendedCurvePlot):

    """ modified behavior:
            - space zooms to selected rt range
            - enter puts range marker to middle of currenct rt plot view
            - right crsr + left csrs + shift and alt modifiers move
              boundaries of selection tool
    """

    # we use this class by patching, so we do not call __init__, instead we set defaults as
    # follows
    x_values = None

    @protect_signal_handler
    def do_space_pressed(self, filter, evt):
        """ zoom to limits of snapping selection tool """

        item = self.get_unique_item(SnappingRangeSelection)
        if item is None:
            return
        if item._min != item._max:
            min_neu = min(item._min, item._max)
            max_neu = max(item._min, item._max)
            range_ = max_neu - min_neu
            if range_ == 0.0:   # look strange in this case, so we zoom a little bit:
                mm = max_neu
                max_neu = mm * 1.1
                min_neu = mm * 0.9
            else:
                max_neu += 0.1 * range_
                min_neu -= 0.1 * range_
            self.update_plot_xlimits(min_neu, max_neu)

            yvals = self.seen_yvals(min_neu, max_neu)
            if yvals:
                ymax = max(yvals)
                if ymax > 0:
                    self.update_plot_ylimits(0, ymax * 1.1)

    @protect_signal_handler
    def do_enter_pressed(self, filter, evt):
        """ set snapping selection tool to center of actual x-range """

        xmin, xmax, _, _ = self.get_plot_limits()
        mid = (xmin + xmax) / 2.0

        item = self.get_unique_item(SnappingRangeSelection)
        if item is None:
            return

        # move_point_to always emits both limits, so we block the first signalling:
        item.set_range(mid, mid)
        filter.plot.replot()

    @protect_signal_handler
    def do_move_marker(self, evt):
        marker = self.get_unique_item(Marker)
        if marker is not None:
            marker.move_local_point_to(0, evt.pos())
            marker.setVisible(True)
            self.replot()

    def move_selection_bounds(self, evt, filter_, selector):
        shift_pressed = evt.modifiers() & Qt.ShiftModifier
        alt_pressed = evt.modifiers() & Qt.AltModifier
        ctrl_pressed = evt.modifiers() & Qt.ControlModifier

        item = self.get_unique_item(SnappingRangeSelection)
        if item is None:
            return

        n_iter = 5 if ctrl_pressed else 1

        new_max = item._max
        new_min = item._min
        for _ in range(n_iter):
            if not alt_pressed:
                new_max = selector(item.get_neighbour_xvals(new_max))
                if new_max is None:
                    break
            if not shift_pressed:
                new_min = selector(item.get_neighbour_xvals(new_min))
                if new_min is None:
                    break

        if new_min is not None and new_max is not None:
            # move_point_to always emits both limits, so we block the first signalling:
            item.set_range(new_min, new_max)

        filter_.plot.replot()

    @protect_signal_handler
    def do_left_pressed(self, filter_, evt):
        self.move_selection_bounds(evt, filter_,
                                   lambda (left_neighbour, right_neighbour): left_neighbour)

    @protect_signal_handler
    def do_right_pressed(self, filter_, evt):
        self.move_selection_bounds(evt, filter_,
                                   lambda (left_neighbour, right_neighbour): right_neighbour)

    def label_info(self, x, y):
        # label next to cursor turned off:
        return None

    def set_x_values(self, x_values):
        self.x_values = np.array(x_values)

    def set_rt(self, rt):
        # sets cursor
        marker = self.get_unique_item(Marker)
        if marker is None:
            return
        marker.setXValue(rt)
        self.replot()

    @protect_signal_handler
    def on_plot(self, x, y):
        """ callback for marker: determine marked point based on cursors coordinates """
        x_values = self.x_values
        if x_values is None or len(x_values) == 0:
            return x, y
        distances = np.abs(x - x_values)
        imin = np.argmin(distances)
        self.current_peak = x_values[imin], 0
        self.CURSOR_MOVED.emit(x_values[imin])
        return self.current_peak


class MzPlot(PositiveValuedCurvePlot, ExtendedCurvePlot):

    """ modifications:
            - showing marker at peak next to mouse cursor
            - mouse drag handling for measuring distances between peaks
            - showing information about current peak and distances if in drag mode
    """

    # as this class is used in patching we do not call __init__, so we set some defaults
    # here:
    peakmap_ranges = ()
    latest_mzmin = None
    latest_mzmax = None
    image_plot = None
    visible_peaks = ()
    overall_x_min = 0
    overall_x_max = 1000

    def label_info(self, x, y):
        # label next to cursor turned off:
        return None

    @protect_signal_handler
    def on_plot(self, x, y):
        """ callback for marker: determine marked point based on cursors coordinates """
        self.current_peak = self.next_peak_to(x, y)
        if self.image_plot is not None:
            self.image_plot.set_mz(self.current_peak[0])
        self.CURSOR_MOVED.emit(float(self.current_peak[0]))
        return self.current_peak

    def set_mz(self, mz):
        # set cursor position
        mz, I = self.next_peak_to(mz)
        if mz is not None and I is not None:
            marker = self.get_unique_item(Marker)
            if marker is None:
                return
            marker.setValue(mz, I)  # avoids sending signal
            self.replot()

    def do_finish_zoom_view(self, dx, dy):
        dx = (-1,) + dx  # adding direction to tuple dx
        dy = (1,) + dy  # adding direction to tuple dy
        axes_to_update = self.get_axes_to_update(dx, dy)

        mzmins = []
        mzmaxs = []

        axis_ids_horizontal = (self.get_axis_id("bottom"), self.get_axis_id("top"))
        for __, id_ in axes_to_update:
            if id_ in axis_ids_horizontal:
                mzmin, mzmax = self.get_axis_limits(id_)
                mzmins.append(mzmin)
                mzmaxs.append(mzmax)

        mzmin = min(mzmins)
        mzmax = max(mzmaxs)
        self.update_plot_xlimits(mzmin, mzmax, rescale_y=False)
        self.replot()

    def set_visible_peaks(self, peaks):
        if peaks is None or len(peaks) == 0:
            peaks = np.zeros((0, 2))
        else:
            peaks = np.vstack(peaks)
        self.visible_peaks = peaks

    def next_peak_to(self, mz, I=None):
        if len(self.visible_peaks) == 0:
            return mz, I
        if I is None:
            distances = (self.visible_peaks[:, 0] - mz) ** 2
            imin = np.argmin(distances)
        else:
            peaks = self.visible_peaks - np.array((mz, I))

            # scale according to zooms axis proportions:
            mzmin, mzmax, Imin, Imax = self.get_plot_limits()
            peaks /= np.array((mzmax - mzmin, Imax - Imin))
            # find minimal distance
            distances = peaks[:, 0] ** 2 + peaks[:, 1] ** 2
            imin = np.argmin(distances)
        return self.visible_peaks[imin]

    @protect_signal_handler
    def do_move_marker(self, evt):
        marker = self.get_unique_item(Marker)
        if marker is not None:
            marker.move_local_point_to(0, evt.pos())
            marker.setVisible(True)
            self.replot()

    @protect_signal_handler
    def do_space_pressed(self, filter, evt):
        """ finds 10 next (distance in mz) peaks tu current marker
            and zooms to them
        """

        if not hasattr(self, "centralMz") or self.centralMz is None:
            marker = self.get_unique_item(Marker)
            if marker is None:
                return
            mz = marker.xValue()
        else:
            mz = self.centralMz

        self.update_plot_xlimits(mz - 0.5, mz + 0.5)

    @protect_signal_handler
    def start_drag_mode(self, filter_, evt):
        mz = self.invTransform(self.xBottom, evt.x())
        I = self.invTransform(self.yLeft, evt.y())
        self.start_coord = self.next_peak_to(mz, I)

    @protect_signal_handler
    def move_in_drag_mode(self, filter_, evt):
        mz = self.invTransform(self.xBottom, evt.x())
        I = self.invTransform(self.yLeft, evt.y())
        current_coord = self.next_peak_to(mz, I)

        line = self.get_unique_item(SegmentShape)
        if line is None:
            return
        line.set_rect(self.start_coord[0], self.start_coord[1], current_coord[0], current_coord[1])
        line.setVisible(1)

        self.replot()

    @protect_signal_handler
    def stop_drag_mode(self, filter_, evt):
        line = self.get_unique_item(SegmentShape)
        if line is not None:
            line.setVisible(0)
            self.replot()

    def _extract_peaks(self, mz_limits=None):
        for i, (pm, rtmin, rtmax, mzmin, mzmax, npeaks) in enumerate(self.peakmap_ranges):
            ms_level = min(pm.getMsLevels())

            rtmin_pm, rtmax_pm = pm.rtRange()
            rtmin = rtmin if rtmin is not None else rtmin_pm
            rtmax = rtmax if rtmax is not None else rtmax_pm

            if mz_limits is not None:
                mzmin, mzmax = mz_limits
            else:
                if mzmin is None or mzmax is None:
                    mzmin_pm, mzmax_pm = pm.mzRange(ms_level)
                mzmin = mzmin if mzmin is not None else mzmin_pm
                mzmax = mzmax if mzmax is not None else mzmax_pm

            npeaks = npeaks or 3000

            peaks = timethis(pm.sample_peaks)(rtmin, rtmax, mzmin, mzmax, npeaks, ms_level)
            yield i, peaks

    def plot_peakmap_ranges_iter(self, peakmap_ranges, configs, titles):
        collected_peaks = []
        self.sticks = []
        self.peakmap_ranges = peakmap_ranges

        for i, peaks in self._extract_peaks():
            collected_peaks.append(peaks)
            config = configs[i]
            title = titles[i]
            curve = make_unselectable_curve([], [], title=title, curvestyle="Sticks", **config)
            curve.set_data(peaks[:, 0], peaks[:, 1])
            self.add_item(curve)
            self.sticks.append(curve)
            self.replot()
            yield

        self.set_visible_peaks(collected_peaks)

    def plot_peakmap_ranges(self, peakmap_ranges, configs, titles):
        for _ in self.plot_peakmap_ranges_iter(peakmap_ranges, configs, titles):
            yield
        self.replot()

    def resample_peaks(self, mzmin, mzmax):
        if mzmin == self.latest_mzmin and mzmax == self.latest_mzmax:
            return
        self.latest_mzmin = mzmin
        self.latest_mzmax = mzmax
        self._update_sticks(mz_limits=(mzmin, mzmax))

    def _update_sticks(self, mz_limits):
        collected_peaks = []
        for i, peaks in self._extract_peaks(mz_limits):
            collected_peaks.append(peaks)
            curve = self.sticks[i]
            curve.set_data(peaks[:, 0], peaks[:, 1])
            collected_peaks.append(peaks)
        self.set_visible_peaks(collected_peaks)

    def do_backspace_pressed(self, filter, evt):
        """ reset axes of plot """
        self._update_sticks(mz_limits=None)
        self.reset_x_limits()

    def update_plot_xlimits(self, xmin, xmax, rescale_y=True):
        _, _, ymin, ymax = self.get_plot_limits()
        self.set_plot_limits(xmin, xmax, ymin, ymax)
        self.resample_peaks(xmin, xmax)
        if rescale_y:
            self.setAxisAutoScale(self.yLeft)  # y-achse
        self.VIEW_RANGE_CHANGED.emit(xmin, xmax)
        self.updateAxes()
        self.replot()

    def update_plot_ylimits(self, ymin, ymax):
        xmin, xmax, _, _ = self.get_plot_limits()
        self.resample_peaks(xmin, xmax)
        self.set_plot_limits(xmin, xmax, ymin, ymax)
        self.updateAxes()
        self.replot()


class MesaurementLine(SegmentShape):

    """
        This is plottet as a line
        modifications are:
            - no point int the middle of the line
            - no antialising for the markers
    """

    def set_rect(self, x1, y1, x2, y2):
        """
        Set the start point of this segment to (x1, y1)
        and the end point of this line to (x2, y2)
        """
        # the original shape has a extra point in the middle
        # of the line, which is the last tuple, I moved this point to the starting point:

        self.set_points([(x1, y1), (x2, y2), (x1, y1)])

    def draw(self, painter, xMap, yMap, canvasRect):
        # code copied and rearanged such that line has antialiasing,
        # but symbols have not.
        pen, brush, symbol = self.get_pen_brush(xMap, yMap)

        painter.setPen(pen)
        painter.setBrush(brush)

        points = self.transform_points(xMap, yMap)
        if self.ADDITIONNAL_POINTS:
            shape_points = points[:-self.ADDITIONNAL_POINTS]
            other_points = points[-self.ADDITIONNAL_POINTS:]
        else:
            shape_points = points
            other_points = []

        for i in xrange(points.size()):
            symbol.draw(painter, points[i].toPoint())

        painter.setRenderHint(QPainter.Antialiasing)
        if self.closed:
            painter.drawPolygon(shape_points)
        else:
            painter.drawPolyline(shape_points)

        if self.LINK_ADDITIONNAL_POINTS and other_points:
            pen2 = painter.pen()
            pen2.setStyle(Qt.DotLine)
            painter.setPen(pen2)
            painter.drawPolyline(other_points)


class SnappingRangeSelection(XRangeSelection):

    """ modification:
            - only limit bars can be moved
            - snaps to given rt-values which are in general not equally spaced
    """

    class _X(QObject):
        SELECTED_RANGE_CHANGED = pyqtSignal(float, float)

    def __init__(self, min_, max_):
        XRangeSelection.__init__(self, min_, max_)
        self._can_move = False  # moving entire shape disabled, but handles are still movable

        # we have to trick a bit because pyqtSignal must be attributes of a derived class of
        # QObject and adding QObject as an additional base class does not work somehow:
        self._x = SnappingRangeSelection._X()
        self.SELECTED_RANGE_CHANGED = self._x.SELECTED_RANGE_CHANGED

        p = self.shapeparam
        p.fill = "#aaaaaa"
        p.line.color = "#888888"
        p.sel_line.color = "#888888"
        p.symbol.color = "gray"
        p.symbol.facecolor = "gray"
        p.symbol.alpha = 0.5
        p.sel_symbol.color = "gray"
        p.sel_symbol.facecolor = "gray"
        p.sel_symbol.alpha = 0.5
        p.sel_symbol.size = 8
        p.symbol.size = 8
        p.update_range(self)

    def get_xvals(self):
        xvals = []
        for item in self.plot().get_items():
            if isinstance(item, CurveItem):
                xvals.extend(np.array(item.get_data()[0]))
        return np.sort(np.unique(xvals))

    def set_range(self, xmin, xmax, block_signals=False):
        self.move_point_to(0, (xmin, 0), True)
        self.move_point_to(1, (xmax, 0), block_signals)

    def move_point_to(self, hnd, pos, block_signals=False):
        xvals = self.get_xvals()
        x, y = pos

        # modify pos to the next x-value
        # fast enough
        if len(xvals) > 0:
            val, y = pos
            imin = np.argmin(np.fabs(val - xvals))
            x = xvals[imin]
        else:
            val = x

        if hnd == 0:
            self._min = x
        elif hnd == 1:
            self._max = x
        elif hnd == 2:
            move = val - (self._max + self._min) / 2
            new_min = self._min + move
            new_max = self._max + move
            if len(xvals):
                if min(xvals) <= new_min <= max(xvals) and min(xvals) <= new_max <= max(xvals):
                    self._min = new_min
                    self._max = new_max
            else:
                self._min = new_min
                self._max = new_max

        if not block_signals:
            self.SELECTED_RANGE_CHANGED.emit(self._min, self._max)

    def get_neighbour_xvals(self, x):
        """ used for moving boundaries """

        xvals = self.get_xvals()
        if not len(xvals):
            return x, None
        imin = np.argmin(np.fabs(x - xvals))
        if imin == 0:
            return None, xvals[1]
        if imin == len(xvals) - 1:
            return xvals[imin - 1], None
        return xvals[imin - 1], xvals[imin + 1]
