from exceptions import Exception
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QPainter
from guiqwt.curve import CurvePlot, CurveItem
from guiqwt.events import ObjectHandler, KeyEventMatch, setup_standard_tool_filter, QtDragHandler
from guiqwt.signals import *
from guiqwt.tools import InteractiveTool

from guiqwt.shapes import Marker, SegmentShape, XRangeSelection
import numpy as np

from helpers import protect_signal_handler

class ModifiedCurveItem(CurveItem):
    """ modification(s):
          selection (which plots a square at each (x,y) ) is turned off
    """

    def can_select(self):
        return False


class RtSelectionTool(InteractiveTool):
    """
        modified event handling:
            - enter, space, backspace, lift crsr and right crsr keys trigger handlers in baseplot
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
        ObjectHandler(filter, Qt.LeftButton, mods=Qt.ControlModifier,
                      start_state=start_state, multiselection=True)

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
                         KeyEventMatch((Qt.Key_Backspace,)),
                         baseplot.do_backspace_pressed, start_state)

        return setup_standard_tool_filter(filter, start_state)


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

        #start_state = filter.new_state()
        handler = QtDragHandler(filter, Qt.LeftButton, start_state=start_state)

        filter.add_event(start_state,
                         KeyEventMatch((Qt.Key_Space,)),
                         baseplot.do_space_pressed, start_state)
        filter.add_event(start_state,
                         KeyEventMatch((Qt.Key_Backspace,)),
                         baseplot.do_backspace_pressed, start_state)

        filter.add_event(start_state,
                         KeyEventMatch((Qt.Key_C,)),
                         baseplot.do_c_pressed, start_state)

        self.connect(handler, SIG_MOVE, baseplot.move_in_drag_mode)
        self.connect(handler, SIG_START_TRACKING, baseplot.start_drag_mode)
        self.connect(handler, SIG_STOP_NOT_MOVING, baseplot.stop_drag_mode)
        self.connect(handler, SIG_STOP_MOVING, baseplot.stop_drag_mode)

        #self.connect(handler, SIGNAL("doubleClicked()"), baseplot.do_c_pressed)
        return setup_standard_tool_filter(filter, start_state)

# now done in emzed patches:
#
#   remove __del__ as we get unbreakable dependency cycles
#   if we plot a lot.
#   del CurvePlot.__del__

class ModifiedCurvePlot(CurvePlot):
    """ modifications:
            - zooming preserves x asix at bottom of plot
            - panning is only in x direction
            - handler for backspace, called by RtSelectionTool and MzSelectionTool
    """

    def do_zoom_view(self, dx, dy, lock_aspect_ratio=False):
        """ modified do_zoom_view such that y=0 stays at bottom of plot """

        dy = dy[0], dy[1], self.transform(0, 0), dy[3]
        return super(ModifiedCurvePlot, self).do_zoom_view(dx, dy, lock_aspect_ratio)

    def do_pan_view(self, dx, dy):
        """ modified do_zoom_view such that only panning in x-direction happens """

        dy = dy[2], dy[2], dy[2], dy[3]
        return super(ModifiedCurvePlot, self).do_pan_view(dx, dy)


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

    def reset_x_limits(self, xmin=None, xmax=None, fac=1.0):
        xvals = []
        for item in self.items:
            if isinstance(item, CurveItem):
                x, _ = item.get_data()
                xvals.extend(list(x))
        if xmin is None:
            if len(xvals):
                xmin = min(xvals)/fac
            else:
                xmin = 0
        if xmax is None:
            if len(xvals):
                xmax = max(xvals)*fac
            else:
                xmax = 1.0
        self.update_plot_xlimits(xmin, xmax)

    def reset_y_limits(self, ymin=None, ymax=None, fac=1.2):
        yvals = []
        #xmin, xmax, _, _ = self.get_plot_limits()

        for item in self.items:
            if isinstance(item, CurveItem):
                x, y = item.get_data()
                yvals.extend(y)
        if ymin is None:
            if len(yvals)>0:
                ymin = min(yvals)/fac
            else:
                ymin = 0
        if ymax is None:
            if len(yvals)>0:
                ymax = max(yvals)*fac
            else:
                ymax = 1.0
        self.update_plot_ylimits(ymin, ymax)

    def update_plot_xlimits(self, xmin, xmax):
        _, _, ymin, ymax = self.get_plot_limits()
        self.set_plot_limits(xmin, xmax, ymin, ymax)
        self.setAxisAutoScale(self.yLeft) # y-achse
        self.updateAxes()
        self.replot()

    def update_plot_ylimits(self, ymin, ymax):
        xmin, xmax, _, _ = self.get_plot_limits()
        self.set_plot_limits(xmin, xmax, ymin, ymax)
        self.updateAxes()
        self.replot()


class RtPlot(ModifiedCurvePlot):
    """ modified behavior:
            - space zooms to selected rt range
            - enter puts range marker to middle of currenct rt plot view
            - right crsr + left csrs + shift and alt modifiers move
              boundaries of selection tool
    """

    @protect_signal_handler
    def do_space_pressed(self, filter, evt):
        """ zoom to limits of snapping selection tool """

        item = self.get_unique_item(SnappingRangeSelection)
        if item._min != item._max:
            min_neu = min(item._min, item._max)
            max_neu = max(item._min, item._max)
            self.update_plot_xlimits(min_neu, max_neu)

    @protect_signal_handler
    def do_enter_pressed(self, filter, evt):
        """ set snapping selection tool to center of actual x-range """

        xmin, xmax, _, _ = self.get_plot_limits()
        mid = (xmin + xmax) / 2.0

        item = self.get_unique_item(SnappingRangeSelection)
        item.move_point_to(0, (mid, 0), None, emitsignal=False)
        item.move_point_to(1, (mid, 0), None)
        filter.plot.replot()

    @protect_signal_handler
    def do_move_marker(self, evt):
        marker = self.get_unique_item(Marker)
        if marker is not None:
            marker.move_local_point_to(0, evt.pos())
            marker.setVisible(True)
            self.replot()

    def move_selection_bounds(self, evt, filter_, selector):
        shift_pressed = evt.modifiers() == Qt.ShiftModifier
        alt_pressed = evt.modifiers() == Qt.AltModifier

        item = self.get_unique_item(SnappingRangeSelection)
        neu1 = neu0 = None
        if not alt_pressed:
            neu1 = selector(item.get_neighbour_xvals(item._max))
        if not shift_pressed:
            neu0 = selector(item.get_neighbour_xvals(item._min))

        _min, _max = sorted((item._min, item._max))
        if neu0 is not None and (neu0 <= _max or neu0 == neu1):
            item.move_point_to(0, (neu0, 0), True)
        if neu1 is not None and (neu1 >= _min or neu0 == neu1):
            item.move_point_to(1, (neu1, 0), True)

        filter_.plot.replot()

    @protect_signal_handler
    def do_left_pressed(self, filter_, evt):
        self.move_selection_bounds(evt, filter_, lambda (a, b): a)

    @protect_signal_handler
    def do_right_pressed(self, filter_, evt):
        self.move_selection_bounds(evt, filter_, lambda (a, b): b)

    def label_info(self, x, y):
        # label next to cursor turned off:
        return None

    @protect_signal_handler
    def on_plot(self, x, y):
        """ callback for marker: determine marked point based on cursors coordinates """
        marker = self.get_unique_item(Marker)
        rts = np.array(marker.rts)
        if len(rts)==0:
            return x, y
        distances = np.abs(x-rts)
        imin = np.argmin(distances)
        self.current_peak = rts[imin], 0
        return self.current_peak

class MzPlot(ModifiedCurvePlot):

    """ modifications:
            - showing marker at peak next to mouse cursor
            - mouse drag handling for measuring distances between peaks
            - showing information about current peak and distances if in drag mode
    """

    def label_info(self, x, y):
        # label next to cursor turned off:
        return None

    @protect_signal_handler
    def on_plot(self, x, y):
        """ callback for marker: determine marked point based on cursors coordinates """
        self.current_peak = self.next_peak_to(x, y)
        return self.current_peak

    def next_peak_to(self, mz, I):

        if self.all_peaks.shape[0] == 0: 
            return mz,I

        all_peaks = self.all_peaks-np.array((mz,I))

        # scale according to zooms axis proportions:
        mzmin, mzmax, Imin, Imax = self.get_plot_limits()
        all_peaks /= np.array((mzmax-mzmin, Imax-Imin))
        # find minimal distacne
        distances = all_peaks[:,0] ** 2 + all_peaks[:,1]** 2
        imin = np.argmin(distances)
        return self.all_peaks[imin]

    @protect_signal_handler
    def do_move_marker(self, evt):
        marker = self.get_unique_item(Marker)
        marker.move_local_point_to(0, evt.pos())
        marker.setVisible(True)
        self.replot()

    @protect_signal_handler
    def do_space_pressed(self, filter, evt):
        """ finds 10 next (distance in mz) peaks tu current marker
            and zooms to them
        """

        if not hasattr(self, "centralMz") or self.centralMz is None:
            mz = self.get_unique_item(Marker).xValue()
        else:
            mz = self.centralMz

        self.update_plot_xlimits(mz-self.halfWindowWidth,\
                                 mz+self.halfWindowWidth)

    def set_half_window_width(self, w2):
        self.halfWindowWidth = w2

    def set_central_mz(self, mz):
        self.centralMz = mz

    def register_c_callback(self, cb):
        self.c_call_back = cb

    @protect_signal_handler
    def do_c_pressed(self, filter, evt):
        self.current_peak
        self.c_call_back
        self.c_call_back(self.current_peak)

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
        line.set_rect(self.start_coord[0], self.start_coord[1], current_coord[0], current_coord[1])
        line.setVisible(1)

        self.replot()

    @protect_signal_handler
    def stop_drag_mode(self, filter_, evt):
        line = self.get_unique_item(SegmentShape)
        line.setVisible(0)
        self.replot()




class ModifiedSegment(SegmentShape):
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
        # of the line, which is the last tuple, I moved this point to the beginning:

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

    def __init__(self, min_, max_, xvals):
        super(SnappingRangeSelection, self).__init__(min_, max_)

    def move_local_point_to(self, hnd, pos, ctrl=None):
        """ had to rewrite this function as the orginal does not give
            the ctrl parameter value to self.move_point_to method
        """
        val = self.plot().invTransform(self.xAxis(), pos.x())
        self.move_point_to(hnd, (val, 0), ctrl)

    def get_xvals(self):
        xvals = []
        for item in self.plot().get_items():
            if isinstance(item, CurveItem):
                xvals.append(np.array(item.get_data()[0]))
        return np.sort(np.hstack(xvals))

    def move_point_to(self, hnd, pos, ctrl=True, emitsignal=True):
        xvals = self.get_xvals()
        x,y = pos

        # modify pos to the next x-value
        # fast enough
        if len(xvals) > 0:
            val, y = pos
            imin = np.argmin(np.fabs(val-xvals))
            x = xvals[imin]

        if self._min == self._max and not ctrl:
            self._min = x
            self._max = x
        else:
            if hnd == 0:
                self._min = x
            elif hnd == 1:
                self._max =  x
            elif hnd == 2:
                move = val-(self._max+self._min)/2
                self._min += move
                self._max += move

        if emitsignal:
            self.plot().emit(SIG_RANGE_CHANGED, self, self._min, self._max)

    def get_neighbour_xvals(self, x):
        """ used for moving boundaries """

        xvals = self.get_xvals()
        imin = np.argmin(np.fabs(x-xvals))
        if imin == 0: return xvals[0], xvals[1]
        if imin == len(xvals)-1 : return xvals[imin-1], xvals[imin]
        return xvals[imin-1], xvals[imin+1]

    def move_shape(self, old_pos, new_pos):
        # disabled, that is: do nothing !
        return
