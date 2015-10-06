# encoding: utf-8
from __future__ import print_function

import new

from PyQt4.Qwt5 import QwtScaleDraw, QwtText

from guiqwt.plot import PlotManager, CurveWidget
from guiqwt.builder import make
from guiqwt.label import ObjectInfo
from guiqwt.shapes import Marker

import numpy as np

from modified_guiqwt import MzPlot, UnselectableCurveItem, MzSelectionTool, MesaurementLine
from config import setupCommonStyle
from eic_plotting_widget import getColor

from emzed_optimizations.sample import sample_peaks

"""
todo: - explore and impmement needed api
      - use it with peakmaps
      - implement signal stuff
      - cleanup
      - build miminal dialog !
"""


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


class MzPlottingWidget(CurveWidget):

    def __init__(self, parent=None):
        super(MzPlottingWidget, self).__init__(parent, xlabel="mz", ylabel="I")

        # inject mofified behaviour of wigets plot attribute:
        self.plot.__class__ = MzPlot
        # self.plot.register_c_callback(self.handle_c_pressed)
        # self.plot.image_plot = image_plot
        self.setHalfWindowWidth(0.05)
        self.plot.centralMz = None

        # todo: refactor as helper
        a = QwtScaleDraw()
        label = lambda self, x: QwtText("%s" % x)
        a.label = new.instancemethod(label, self.plot, QwtScaleDraw)
        self.plot.setAxisScaleDraw(self.plot.xBottom, a)

        self.pm = PlotManager(self)
        self.pm.add_plot(self.plot)
        self.curve = make.curve([], [], color='b', curvestyle="Sticks")
        # inject modified behaviour:
        self.curve.__class__ = UnselectableCurveItem

        self.plot.add_item(self.curve)

        t = self.pm.add_tool(MzSelectionTool)
        self.pm.set_default_tool(t)
        t.activate()

        marker = Marker(label_cb=self.plot.label_info, constraint_cb=self.plot.on_plot)
        marker.attach(self.plot)

        line = make.segment(0, 0, 0, 0)
        line.__class__ = MesaurementLine
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
        self.plot.set_half_window_width(w2)

    def setCentralMz(self, mz):
        self.plot.set_central_mz(mz)

    def handle_c_pressed(self, p):
        if self.c_callback:
            self.c_callback(p)

    def plot_spectra(self, all_peaks, labels):
        self.plot.del_all_items()
        self.plot.add_item(self.marker)
        self.plot.add_item(make.legend("TL"))
        self.plot.add_item(self.label)

        for i, (peaks, label) in enumerate(zip(all_peaks, labels)):
            config = dict(color=getColor(i))
            curve = make.curve([], [], title=label, curvestyle="Sticks", **config)
            curve.set_data(peaks[:, 0], peaks[:, 1])
            curve.__class__ = UnselectableCurveItem
            self.plot.add_item(curve)
            self.plot.resample_config = []

        self.plot.add_item(self.line)
        if len(all_peaks):
            self.plot.all_peaks = np.vstack(all_peaks)
        else:
            self.plot.all_peaks = np.zeros((0, 2))

    def plot(self, data, configs=None, titles=None):
        """ do not forget to call replot() after calling this function ! """
        self.plot.del_all_items()
        self.plot.add_item(self.marker)
        if titles is not None:
            self.plot.add_item(make.legend("TL"))
        self.plot.add_item(self.label)

        all_peaks = []
        self.plot.resample_config = []
        self.plot.curves = []
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
            curve.__class__ = UnselectableCurveItem
            self.plot.add_item(curve)
            self.plot.curves.append(curve)
            self.plot.resample_config.append((pm, rtmin, rtmax, mzmin, mzmax, npeaks))
        self.plot.add_item(self.line)
        if len(all_peaks):
            self.plot.all_peaks = np.vstack(all_peaks)
        else:
            self.plot.all_peaks = np.zeros((0, 2))

    def resetAxes(self):
        self.plot.reset_x_limits()

    def reset(self):
        self.plot(np.ndarray((0, 2)))
        self.replot()

    def replot(self):
        self.plot.replot()

    def set_visible(self, visible):
        self.plot.setVisible(visible)
