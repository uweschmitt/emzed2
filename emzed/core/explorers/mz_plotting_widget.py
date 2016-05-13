# encoding: utf-8
from __future__ import print_function

import new

from PyQt4.Qwt5 import QwtScaleDraw, QwtText

from guiqwt.plot import PlotManager, CurveWidget
from guiqwt.builder import make
from guiqwt.label import ObjectInfo
from guiqwt.shapes import Marker

import numpy as np

from modified_guiqwt import MzPlot, MzSelectionTool
from modified_guiqwt import make_measurement_line, make_unselectable_curve

from config import setupCommonStyle
from eic_plotting_widget import getColor


from modified_guiqwt import patch_inner_plot_object


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
            # to avoid zero division:
            if I == 0:
                I == 1
            txt += "<br/><br/>dmz=%.6f<br/>rI=%.3e<br/>mean=%.6f" % (mz2 - mz, I2 / I, mean)

        return "<pre>%s</pre>" % txt


class MzPlottingWidget(CurveWidget):

    def __init__(self, parent=None):
        super(MzPlottingWidget, self).__init__(parent, xlabel="mz", ylabel="I")

        patch_inner_plot_object(self, MzPlot)
        self.plot.centralMz = None

        def label(self, x):
            # label with full precision:
            return QwtText(str(x))

        a = QwtScaleDraw()
        a.label = new.instancemethod(label, self.plot, QwtScaleDraw)
        self.plot.setAxisScaleDraw(self.plot.xBottom, a)

        self.pm = PlotManager(self)
        self.pm.add_plot(self.plot)
        self.curve = make_unselectable_curve([], [], color="b", curvestyle="Sticks")

        self.plot.add_item(self.curve)

        t = self.pm.add_tool(MzSelectionTool)
        self.pm.set_default_tool(t)
        t.activate()

        marker = Marker(label_cb=self.plot.label_info, constraint_cb=self.plot.on_plot)
        marker.attach(self.plot)

        line = make_measurement_line()
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

    def plot_spectra(self, all_peaks, labels):
        self.plot.del_all_items()
        self.plot.add_item(self.marker)
        self.plot.add_item(make.legend("TL"))
        self.plot.add_item(self.label)

        for i, (peaks, label) in enumerate(zip(all_peaks, labels)):
            config = dict(color=getColor(i))
            curve = make_unselectable_curve([], [], title=label, curvestyle="Sticks", **config)
            curve.set_data(peaks[:, 0], peaks[:, 1])
            self.plot.add_item(curve)
            self.plot.resample_config = []

        self.plot.add_item(self.line)
        if len(all_peaks):
            self.plot.all_peaks = np.vstack(all_peaks)
        else:
            self.plot.all_peaks = np.zeros((0, 2))

    def _setup_configs_and_titles(self, configs, titles, n):
        configs = configs if configs is not None else [None] * n
        titles = titles if titles is not None else [""] * n

        def default(i):
            return dict(color=getColor(i))
        configs = [ci if ci is not None else default(i) for (i, ci) in enumerate(configs)]
        return configs, titles

    def set_overall_range(self, mzmin, mzmax):
        self.plot.overall_x_min = mzmin
        self.plot.overall_x_max = mzmax

    def plot_peakmaps_iter(self, peakmap_ranges, configs=None, titles=None):
        has_titles = titles is not None
        configs, titles = self._setup_configs_and_titles(configs, titles, len(peakmap_ranges))

        self.plot.del_all_items()
        self.plot.add_item(self.marker)
        if has_titles:
            self.plot.add_item(make.legend("TL"))
        self.plot.add_item(self.label)

        for _ in self.plot.plot_peakmap_ranges_iter(peakmap_ranges, configs, titles):
            yield
        self.plot.add_item(self.line)


    def plot_peakmaps(self, peakmap_ranges, configs=None, titles=None):

        for _ in self.plot_peakmaps_iter(peakmap_ranges, configs, titles):
            pass

    def set_cursor_pos(self, mz):
        self.plot.set_mz(mz)

    def resetAxes(self):
        self.plot.reset_x_limits()

    def reset_mz_limits(self, xmin=None, xmax=None, fac=1.1):
        self.plot.reset_x_limits(xmin, xmax, fac)

    def reset(self):
        self.plot.del_all_items()
        self.replot()

    def replot(self):
        self.plot.replot()

    def set_visible(self, visible):
        self.plot.setVisible(visible)

    def updateAxes(self):
        self.plot.updateAxes()

    def shrink_and_replot(self, mzmin, mzmax):
        self.reset_mz_limits(mzmin, mzmax)
        self.plot.reset_y_limits()
        self.plot.replot()
