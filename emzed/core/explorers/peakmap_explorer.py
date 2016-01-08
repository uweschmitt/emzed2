# -*- coding: utf-8 -*-

import os
import math


from PyQt4.QtGui import (QDialog, QGridLayout, QLabel, QCheckBox,
                         QComboBox, QLineEdit, QDoubleValidator, QFrame,
                         QHBoxLayout, QPushButton, QMenuBar, QAction, QMenu,
                         QKeySequence, QVBoxLayout,
                         QMessageBox, QTableWidget, QTableWidgetItem, QSplitter, QHeaderView)

from PyQt4.QtCore import (Qt, SIGNAL)
from PyQt4.QtWebKit import (QWebView, QWebSettings)

import guidata

from pkg_resources import resource_string

from ...io.load_utils import loadPeakMap
from ...gui.file_dialogs import askForSave, askForSingleFile

from .peakmap_plotting_widget import PeakMapPlottingWidget, get_range
from .mz_plotting_widget import MzPlottingWidget
from .eic_plotting_widget import EicPlottingWidget
from .helpers import protect_signal_handler
from .emzed_dialog import EmzedDialog
from .widgets.image_scaling_widget import ImageScalingWidget
from .widgets.spectra_selector_widget import SpectraSelectorWidget
from .widgets.view_range_widget import ViewRangeWidget


grey_line = dict(linewidth=1.5, color="#666666")
blue_line = dict(linewidth=1.5, color="#aaaa00")
yellow_line = dict(linewidth=1.5, color="#0000aa")


def read_float(widget):
    try:
        value = float(widget.text())
        return value
    except ValueError:
        return None


SIG_HISTORY_CHANGED = SIGNAL('plot_history_changed(PyQt_PyObject)')


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

    def go_to_beginning(self):
        if self.position > 0:
            self.position = 0
            return self.items[self.position]
        return None

    def go_to_end(self):
        if self.position < len(self.items) - 1:
            self.position = len(self.items) - 1
            return self.items[self.position]
        return None

    def set_position(self, position):
        if 0 <= position < len(self.items) and position != self.position:
            self.position = position
            return self.items[self.position]
        return None


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

        self.gamma = 3.0

        self.last_used_directory_for_load = None
        self.last_used_directory_for_save = None

        self.history = History()

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
        self.history_list = QComboBox(self)

        self.setup_ms2_widgets()
        self.full_pm = peakmap
        self.full_pm2 = peakmap2
        self.dual_mode = self.full_pm2 is not None

        self.current_ms_level = self.ms_levels[0]
        self.process_peakmap(self.current_ms_level)
        self.rtmin, self.rtmax, self.mzmin, self.mzmax = get_range(self.peakmap, self.peakmap2)

        self.setup_plot_widgets()
        self.setup_menu_bar()
        self.setup_layout()
        self.connect_signals_and_slots()
        self.setup_initial_values()
        self.plot_peakmap()

    def setup_ms2_widgets(self):
        self.spectra_selector_widget.set_data(self.ms_levels, self.precursor_mz)

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
                pass # TODO self.ms_level.setCurrentIndex(i)

        self.setWindowTitle()

    def setup_initial_values(self):

        imax = self.peakmap_plotter.get_total_imax()
        self.image_scaling_widget.set_max_intensity(imax)
        self.image_scaling_widget.set_gamma(self.gamma)

        self.view_range_widget.set_view_range(self.rtmin, self.rtmax, self.mzmin, self.mzmax)

    def setup_input_widgets(self):
        self.image_scaling_widget = ImageScalingWidget(self)
        self.spectra_selector_widget = SpectraSelectorWidget(self)
        self.view_range_widget = ViewRangeWidget(self)

    def setup_plot_widgets(self):
        self.peakmap_plotter = PeakMapPlottingWidget()
        self.peakmap_plotter.set_peakmaps(self.peakmap, self.peakmap2)
        self.eic_plotter = EicPlottingWidget(with_range=False)
        self.mz_plotter = MzPlottingWidget()

        self.peakmap_plotter.set_logarithmic_scale(1)
        self.peakmap_plotter.set_gamma(self.gamma)

        self.eic_plotter.set_overall_range(self.rtmin, self.rtmax)
        self.mz_plotter.set_overall_range(self.mzmin, self.mzmax)


    def setup_layout(self):
        outer_layout = QVBoxLayout()
        outer_layout.addWidget(self.menu_bar)
        outer_layout.setStretch(0, 1)

        h_splitter = QSplitter(self)
        h_splitter.setOrientation(Qt.Horizontal)

        # FIRST COLUMN of h_splitter is chromatogram + peakmap:  ############################

        v_splitter1 = QSplitter(self)
        v_splitter1.setOrientation(Qt.Vertical)
        v_splitter1.addWidget(self.eic_plotter)
        v_splitter1.addWidget(self.peakmap_plotter)
        self.peakmap_plotter.setMinimumSize(250, 200)
        v_splitter1.setStretchFactor(0, 1)
        v_splitter1.setStretchFactor(1, 3)

        h_splitter.addWidget(v_splitter1)
        h_splitter.setStretchFactor(0, 2)

        # SECOND COLUMN of h_splittier holds controlx boxes + mz plot #######################

        v_splitter2 = QSplitter(self)
        v_splitter2.setOrientation(Qt.Vertical)

        v_splitter2.addWidget(self.image_scaling_widget)
        v_splitter2.addWidget(self.spectra_selector_widget)
        v_splitter2.addWidget(self.view_range_widget)
        v_splitter2.addWidget(self.history_list)
        v_splitter2.addWidget(self.mz_plotter)

        v_splitter2.setStretchFactor(0, 0)
        v_splitter2.setStretchFactor(1, 0)
        v_splitter2.setStretchFactor(2, 0)
        v_splitter2.setStretchFactor(3, 0)
        v_splitter2.setStretchFactor(4, 1)

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

    def connect_signals_and_slots(self):
        self.image_scaling_widget.USE_LOG_SCALE.connect(self.use_logscale)
        self.image_scaling_widget.GAMMA_CHANGED.connect(self.gamma_changed)

        self.image_scaling_widget.IMIN_CHANGED.connect(self.set_image_min)
        self.image_scaling_widget.IMAX_CHANGED.connect(self.set_image_max)

        self.spectra_selector_widget.MS_LEVEL_CHOSEN.connect(self.ms_level_chosen)
        self.spectra_selector_widget.PRECURSOR_RANGE_CHANGED.connect(self.set_precursor_range)

        self.view_range_widget.RANGE_CHANGED.connect(self.update_image_range)

        self.connect(self.history_list, SIGNAL("activated(int)"), self.history_item_selected)

        if self.dual_mode:
            self.connect(self.load_action, SIGNAL("triggered()"), self.do_load_yellow)
            self.connect(self.load_action2, SIGNAL("triggered()"), self.do_load_blue)
        else:
            self.connect(self.load_action, SIGNAL("triggered()"), self.do_load)
        self.connect(self.save_action, SIGNAL("triggered()"), self.do_save)
        self.connect(self.help_action, SIGNAL("triggered()"), self.show_help)

        self.peakmap_plotter.NEW_IMAGE_LIMITS.connect(self.image_limits_upated_by_user)

        self.peakmap_plotter.KEY_LEFT.connect(self.user_pressed_left_key_in_plot)
        self.peakmap_plotter.KEY_RIGHT.connect(self.user_pressed_right_key_in_plot)
        self.peakmap_plotter.KEY_BACKSPACE.connect(self.user_pressed_backspace_key_in_plot)
        self.peakmap_plotter.KEY_END.connect(self.user_pressed_end_key_in_plot)
        self.peakmap_plotter.CURSOR_MOVED.connect(self.cursor_moved_in_plot)
        self.eic_plotter.CURSOR_MOVED.connect(self.eic_cursor_moved)
        self.eic_plotter.VIEW_RANGE_CHANGED.connect(self.eic_view_range_changed)
        self.mz_plotter.CURSOR_MOVED.connect(self.mz_cursor_moved)
        self.mz_plotter.VIEW_RANGE_CHANGED.connect(self.mz_view_range_changed)

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

    def cursor_moved_in_plot(self, rt, mz):
        self.eic_plotter.set_cursor_pos(rt)
        self.mz_plotter.set_cursor_pos(mz)

    def eic_cursor_moved(self, rt):
        self.peakmap_plotter.set_cursor_rt(rt)

    def eic_view_range_changed(self, rtmin, rtmax):
        """
        we want to avoid the loop   EIC_RANGE_CHANGED -> VIEW_RANGE_CHANGED -> EIC_RANGE_CHANGED
        and we do not want to fully block emitting of VIEW_RANGE_CHANGED.
        so self.peakmap_plotter.blockSignals() does not work here, instead we "cut" the last
        connection here:
        """
        self.eic_plotter.VIEW_RANGE_CHANGED.disconnect()
        self.peakmap_plotter.blockSignals(True)
        self.peakmap_plotter.set_rt_limits(rtmin, rtmax)
        self.peakmap_plotter.blockSignals(False)
        self.peakmap_plotter.replot()
        self.eic_plotter.VIEW_RANGE_CHANGED.connect(self.eic_view_range_changed)

    def mz_view_range_changed(self, mzmin, mzmax):
        """
        we want to avoid the loop  MZ_RANGE_CHANGED -> VIEW_RANGE_CHANGED -> MZ_RANGE_CHANGED
        and we do not want to fully block emitting of VIEW_RANGE_CHANGED.
        so self.peakmap_plotter.blockSignals() does not work here, instead we "cut" the last
        connection here:
        """
        self.mz_plotter.VIEW_RANGE_CHANGED.disconnect()
        self.peakmap_plotter.blockSignals(True)
        self.peakmap_plotter.set_mz_limits(mzmin, mzmax)
        self.peakmap_plotter.blockSignals(False)
        self.peakmap_plotter.replot()
        self.mz_plotter.VIEW_RANGE_CHANGED.connect(self.mz_view_range_changed)

    def mz_cursor_moved(self, mz):
        self.peakmap_plotter.set_cursor_mz(mz)

    def image_limits_upated_by_user(self, rtmin, rtmax, mzmin, mzmax):
        self.update_peakmap_projection_views(rtmin, rtmax, mzmin, mzmax)
        self.history.new_head((rtmin, rtmax, mzmin, mzmax))
        self.update_history_entries()

    def set_image_min(self, value):
        self.peakmap_plotter.set_imin(value)
        self.peakmap_plotter.replot()

    def set_image_max(self, value):
        self.peakmap_plotter.set_imax(value)
        self.peakmap_plotter.replot()

    def update_peakmap_projection_views(self, rtmin, rtmax, mzmin, mzmax):

        rts, chroma = self.peakmap.chromatogram(mzmin, mzmax)
        self.eic_plotter.del_all_items()
        if self.dual_mode:
            rts2, chroma2 = self.peakmap2.chromatogram(mzmin, mzmax, rtmin, rtmax)
            self.eic_plotter.add_eics([(rts, chroma), (rts2, chroma2)], configs=[blue_line, yellow_line])
        else:
            self.eic_plotter.add_eics([(rts, chroma)], configs=[grey_line])

        self.eic_plotter.shrink_and_replot(rtmin, rtmax)

        if self.dual_mode:
            data = [(self.peakmap, rtmin, rtmax, mzmin, mzmax, 3000),
                    (self.peakmap2, rtmin, rtmax, mzmin, mzmax, 3000)]
            configs = [dict(color="#aaaa00"), dict(color="#0000aa")]
            self.mz_plotter.plot_peakmaps(data, configs)
        else:
            self.mz_plotter.plot_peakmaps([(self.peakmap, rtmin, rtmax, mzmin, mzmax, 3000)])

        self.mz_plotter.shrink_and_replot(mzmin, mzmax)
        self.view_range_widget.set_view_range(rtmin, rtmax, mzmin, mzmax)

    def _handle_history_action(self, action):
        item = action()
        if item is not None:
            self.peakmap_plotter.set_limits_no_sig(*item)
            self.update_peakmap_projection_views(*item)
            self.update_history_entries()

    def user_pressed_left_key_in_plot(self):
        self._handle_history_action(self.history.go_back)

    def user_pressed_right_key_in_plot(self):
        self._handle_history_action(self.history.go_forward)

    def user_pressed_backspace_key_in_plot(self):
        self._handle_history_action(self.history.go_to_beginning)

    def user_pressed_end_key_in_plot(self):
        self._handle_history_action(self.history.go_to_end)

    def history_item_selected(self, index):
        self._handle_history_action(lambda index=index: self.history.set_position(index))

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
            self.peakmap_plotter.set_limits(rtmin, rtmax, mzmin, mzmax)
        else:
            needed = ["mzmin", "mzmax"]
            if all(n in row for n in needed):
                mzmin, mzmax = [row.get(ni) for ni in needed]
                self.peakmap_plotter.set_limits(self.rtmin, self.rtmax, mzmin, mzmax)

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

    def update_history_entries(self):
        self.history_list.clear()
        for item in self.history.items:
            rtmin, rtmax, mzmin, mzmax = item
            str_item = "%10.5f .. %10.5f %6.2fm...%6.2fm " % (mzmin, mzmax, rtmin / 60.0,
                                                              rtmax / 60.0)
            self.history_list.addItem(str_item)

        self.history_list.setCurrentIndex(self.history.position)

    @protect_signal_handler
    def use_logscale(self, is_log):
        self.peakmap_plotter.set_logarithmic_scale(is_log)
        self.peakmap_plotter.replot()

    @protect_signal_handler
    def ms_level_chosen(self, ms_level):
        if ms_level != self.current_ms_level:
            self.current_ms_level = ms_level
            self.process_peakmap(ms_level)
            self.peakmap_plotter.set_peakmaps(self.peakmap, self.peakmap2)
            self.peakmap_plotter.replot()
            self.plot_peakmap()

    @protect_signal_handler
    def set_precursor_range(self, pre_mz_min, pre_mz_max):
        self.process_peakmap(self.current_ms_level, pre_mz_min, pre_mz_max)
        self.peakmap_plotter.set_peakmaps(self.peakmap, self.peakmap2)
        self.peakmap_plotter.replot()
        self.plot_peakmap()

    @protect_signal_handler
    def gamma_changed(self, value):
        self.peakmap_plotter.set_gamma(value)
        self.peakmap_plotter.replot()

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

        self.peakmap_plotter.set_limits(rtmin, rtmax, mzmin, mzmax)

    def plot_peakmap(self):
        self.peakmap_plotter.set_limits(self.rtmin, self.rtmax, self.mzmin, self.mzmax)


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
