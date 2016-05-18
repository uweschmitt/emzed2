# -*- coding: utf-8 -*-
import os

import contextlib
from collections import defaultdict
import itertools
import traceback

from PyQt4.QtGui import *
from PyQt4.QtCore import *


import guidata

from eic_plotting_widget import EicPlottingWidget
from mz_plotting_widget import MzPlottingWidget
from ts_plotting_widget import TimeSeriesPlottingWidget

from ..data_types import Table, PeakMap, CallBack, CheckState
from ..data_types.hdf5_table_proxy import Hdf5TableProxy

from .table_explorer_model import (TableModel, isUrl, IntegrateAction)
from .helpers import timethis

from helpers import protect_signal_handler

from inspectors import has_inspector, inspector

from emzed_dialog import EmzedDialog

from .widgets import FilterCriteriaWidget, ColumnMultiSelectDialog, IntegrationWidget

from ...gui.file_dialogs import askForSave
from ... import algorithm_configs

from .async_runner import AsyncRunner

import time


@timethis
def time_series_curves(model):
    rtmins, rtmaxs, curves = [], [], []
    for idx in model.selected_data_rows:
        # filter valid time series
        tsi = [tsi for tsi in model.getTimeSeries(idx) if tsi is not None]
        # extract all valid x values from all time series
        xi = [xi for ts in tsi for xi in ts.x if xi is not None]
        if xi:
            rtmins.append(min(xi))
            rtmaxs.append(max(xi))
            curves.extend(tsi)
    if not rtmins:
        return None, None, []
    return min(rtmins), max(rtmaxs), curves


def _eic_fetcher(model, fetcher):
    for idx in model.selected_data_rows:
        eics, rtmin, rtmax, allrts = fetcher(idx)
        for eic in eics:
            yield rtmin, rtmax, eic


def current_rt_limits(model):
    rtmins = []
    rtmaxs = []
    for idx in model.selected_data_rows:
        windows = model.getEICWindows(idx)
        rtmin = min(w[0] for w in windows)
        rtmax = max(w[1] for w in windows)
        rtmins.append(rtmin)
        rtmaxs.append(rtmax)
    if rtmins:
        return min(rtmins), max(rtmaxs)
    else:
        return None, None


@timethis
def compute_eics(model):
    return _eic_fetcher(model, model.computeEics)


@timethis
def eic_curves(model):
    return _eic_fetcher(model, model.getEics)


@timethis
def fit_shapes(model):
    fit_shapes = []
    for idx in model.selected_data_rows:
        eics, rtmin, rtmax, allrts = model.getEics(idx)
        fitted_shapes = model.getFittedPeakshapes(idx, allrts)
        fit_shapes.extend(fitted_shapes)
    return fit_shapes


def button(txt=None, parent=None):
    btn = QPushButton(parent=parent)
    if txt is not None:
        btn.setText(txt)
    btn.setAutoDefault(False)
    btn.setDefault(False)
    return btn


def getColors(i, light=False):
    colors = [(0, 0, 200), (70, 70, 70), (0, 150, 0), (200, 0, 0), (200, 200, 0), (100, 70, 0)]
    c = colors[i % len(colors)]
    color = "#" + "".join("%02x" % v for v in c)
    if light:
        color = turn_light(color)
    return color


def turn_light(color):
    rgb = [int(color[i:i + 2], 16) for i in range(1, 6, 2)]
    rgb_light = [min(ii + 50, 255) for ii in rgb]
    return "#" + "".join("%02x" % v for v in rgb_light)


def configsForEics(eics):
    return [configForEic(i) for i in range(len(eics))]


def configForEic(i):
    return dict(linewidth=1.5, color=getColors(i))


def configsForTimeSeries(eics):
    n = len(eics)
    return [dict(linewidth=1,
                 color=getColors(i),
                 marker="Ellipse",
                 markersize=4,
                 markerfacecolor=getColors(i),
                 markeredgecolor=getColors(i)
                 ) for i in range(n)]


def configs_for_fitted_peakshapes(smootheds):
    n = len(smootheds)
    return [dict(shade=0.75, linewidth=3, color=getColors(i, light=True)) for i in range(n)]
    return [dict(shade=0.35, linestyle="NoPen", color=getColors(i, light=True)) for i in range(n)]


def configsForSpectra(n):
    return [dict(color=getColors(i), linewidth=1) for i in range(n)]


class ButtonDelegate(QItemDelegate):

    """
    A delegate that places a fully functioning QPushButton in every
    cell of the column to which it's applied

    we have to distinguis view and parent here: using the view as parent does not work
    in connection with modal dialogs opened in the click handler !
    """

    def __init__(self, view, parent):
        QItemDelegate.__init__(self, parent)
        self.view = view

    def paint(self, painter, option, index):
        if not self.view.indexWidget(index):
            # we find the mode using the view, as the current model might change if one explores
            # more than one table wit the table explorer:
            model = self.view.model()
            cell = model.cell_value(index)
            label = model.data(index)
            row = model.row(index)

            parent = self.parent()   # this is the table explorer

            def clicked(__, index=index):
                parent.model.beginResetModel()
                cell.callback(row, parent)
                parent.model.endResetModel()
                parent.model.emit_data_change()

            button = QPushButton(label, self.parent(), clicked=clicked)
            self.view.setIndexWidget(index, button)


class EmzedTableView(QTableView):

    def __init__(self, dialog):
        super(EmzedTableView, self).__init__()
        self.dialog = dialog

    @protect_signal_handler
    def showEvent(self, evt):
        if not self.isSortingEnabled():
            self.setSortingEnabled(True)
            self.resizeColumnsToContents()
            self.model().emptyActionStack()
            self.dialog.updateMenubar(None, None)

    @protect_signal_handler
    def keyPressEvent(self, evt):
        if evt.key() in (Qt.Key_Up, Qt.Key_Down):
            rows = set(idx.row() for idx in self.selectedIndexes())
            if rows:
                min_row = min(rows)
                max_row = max(rows)
                if evt.key() == Qt.Key_Up:
                    row = min_row - 1
                else:
                    row = max_row + 1
                row = min(max(row, 0), self.model().rowCount() - 1)
                ix = self.model().index(row, 0)
                self.setCurrentIndex(ix)
                self.selectRow(row)
                self.verticalHeader().sectionClicked.emit(row)
                # skip event handling:
                return
        return super(EmzedTableView, self).keyPressEvent(evt)


class TableExplorer(EmzedDialog):

    def __init__(self, tables, offerAbortOption, parent=None, close_callback=None):
        super(TableExplorer, self).__init__(parent)

        # function which is called when window is closed. the arguments passed are boolean
        # flags indication for every table if it was modified:
        self.close_callback = close_callback

        # Destroying the C++ object right after closing the dialog box,
        # otherwise it may be garbage-collected in another QThread
        # (e.g. the editor's analysis thread in Spyder), thus leading to
        # a segmentation fault on UNIX or an application crash on Windows
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowFlags(Qt.Window)  # | Qt.WindowStaysOnTopHint)

        self.offerAbortOption = offerAbortOption

        self.models = [TableModel.table_model_for(table, parent=self) for table in tables]
        self.model = None
        self.tableView = None

        self.hadFeatures = None

        self.async_runner = AsyncRunner(self)

        self.setupWidgets()
        self.setupLayout()
        self.connectSignals()

        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setSizePolicy(sizePolicy)
        self.setSizeGripEnabled(True)

        self.setupViewForTable(0)

    def reject(self):
        super(TableExplorer, self).reject()
        modified = [len(m.actions) > 0 for m in self.models]
        if self.close_callback is not None:
            try:
                self.close_callback(*modified)
            except Exception:
                traceback.print_exc()

    def keyPressEvent(self, e):
        if e.key() != Qt.Key_Escape:
            super(TableExplorer, self).keyPressEvent(e)

    def setupWidgets(self):
        self.setupMenuBar()
        self.setupTableViews()
        self.setupPlottingAndIntegrationWidgets()
        self.setupToolWidgets()
        if self.offerAbortOption:
            self.setupAcceptButtons()

    def setupPlottingAndIntegrationWidgets(self):
        self.setupPlottingWidgets()
        self.setupIntegrationWidgets()

    def setupMenuBar(self):
        self.menubar = QMenuBar(self)
        menu = self.buildEditMenu()
        self.menubar.addMenu(menu)
        self.chooseTableActions = []
        if len(self.models) > 1:
            menu = self.buildChooseTableMenu()
            self.menubar.addMenu(menu)

    def buildEditMenu(self):
        self.undoAction = QAction("Undo", self)
        self.undoAction.setShortcut(QKeySequence("Ctrl+Z"))
        self.redoAction = QAction("Redo", self)
        self.redoAction.setShortcut(QKeySequence("Ctrl+Y"))
        menu = QMenu("Edit", self.menubar)
        menu.addAction(self.undoAction)
        menu.addAction(self.redoAction)
        return menu

    def setupTableViews(self):
        self.tableViews = []
        self.filterWidgets = []
        self.filters_enabled = False
        for i, model in enumerate(self.models):
            self.tableViews.append(self.setupTableViewFor(model))
            self.filterWidgets.append(self.setupFilterWidgetFor(model))

    def setupFilterWidgetFor(self, model):
        t = model.table
        w = FilterCriteriaWidget(self)
        w.configure(t)
        w.LIMITS_CHANGED.connect(self.limits_changed)
        return w

    def limits_changed(self, filters):
        with self.execute_blocked(self):
            timethis(self.model.limits_changed)(filters)

    def set_delegates(self):
        bd = ButtonDelegate(self.tableView, self)
        types = self.model.table.getColTypes()
        for i, j in self.model.widgetColToDataCol.items():
            if types[j] == CallBack:
                self.tableView.setItemDelegateForColumn(i, bd)

    def remove_delegates(self):
        types = self.model.table.getColTypes()
        for i, j in self.model.widgetColToDataCol.items():
            if types[j] in (bool, CallBack):
                self.tableView.setItemDelegateForColumn(i, None)

    def setupTableViewFor(self, model):

        tableView = EmzedTableView(self)

        tableView.setModel(model)
        tableView.horizontalHeader().setResizeMode(QHeaderView.Interactive)
        tableView.horizontalHeader().setMovable(1)
        pol = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        tableView.setSizePolicy(pol)
        tableView.setVisible(False)
        # before filling the table, disabling sorting accelerates table
        # construction, sorting is enabled in TableView.showEvent, which is
        # called after construction
        tableView.setSortingEnabled(False)
        return tableView

    def buildChooseTableMenu(self):
        menu = QMenu("Choose Table", self.menubar)
        for i, model in enumerate(self.models):
            action = QAction(" [%d]: %s" % (i, model.getTitle()), self)
            menu.addAction(action)
            self.chooseTableActions.append(action)
        return menu

    def setupPlottingWidgets(self):

        self.eic_plotter = EicPlottingWidget()
        self.mz_plotter = MzPlottingWidget()
        self.ts_plotter = TimeSeriesPlottingWidget()

        pol = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        pol.setVerticalStretch(5)

        self.eic_plotter.setSizePolicy(pol)
        self.mz_plotter.setSizePolicy(pol)
        self.ts_plotter.setSizePolicy(pol)

        self.spec_label = QLabel("plot spectra:")
        self.choose_spec = QListWidget()
        self.choose_spec.setFixedHeight(90)
        self.choose_spec.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def setupIntegrationWidgets(self):

        self.integration_widget = IntegrationWidget(self)
        names = [name for (name, __) in algorithm_configs.peakIntegrators]
        self.integration_widget.set_integration_methods(names)

    def setupToolWidgets(self):

        self.chooseGroubLabel = QLabel("Expand selection:", parent=self)
        self.chooseGroupColumn = QComboBox(parent=self)
        self.chooseGroupColumn.setMinimumWidth(150)

        self.choose_visible_columns_button = button("Visible columns")

        # we introduced this invisible button else qt makes the filter_on_button always
        # active on mac osx, that means that as soon we press enter in one of the filter
        # widgets the button is triggered !
        # problem does not occur on windows.
        # self.dummy = QPushButton()
        # self.dummy.setVisible(False)

        self.filter_on_button = button("Filter rows")

        self.sort_label = QLabel("sort by:", parent=self)

        self.sort_fields_widgets = []
        self.sort_order_widgets = []
        for i in range(3):
            w = QComboBox(parent=self)
            w.setMinimumWidth(100)
            self.sort_fields_widgets.append(w)
            w = QComboBox(parent=self)
            w.addItems(["asc", "desc"])
            w.setMaximumWidth(60)
            self.sort_order_widgets.append(w)

        self.restrict_to_filtered_button = button("Restrict to filter result")
        self.remove_filtered_button = button("Remove filter result")
        self.export_table_button = button("Export table")

        self.restrict_to_filtered_button.setEnabled(False)
        self.remove_filtered_button.setEnabled(False)

    def setupAcceptButtons(self):
        self.okButton = button("Ok", parent=self)
        self.abortButton = button("Abort", parent=self)
        self.result = 1  # default for closing

    def create_additional_widgets(self, vsplitter):
        # so that derived classes can add widgets above table !
        return None

    def connect_additional_widgets(self, model):
        pass

    def setupLayout(self):
        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        vsplitter = QSplitter()
        vsplitter.setOrientation(Qt.Vertical)
        vsplitter.setOpaqueResize(False)

        vsplitter.addWidget(self.menubar)  # 0
        vsplitter.addWidget(self.layoutPlottingAndIntegrationWidgets())   # 1

        extra = self.create_additional_widgets(vsplitter)
        if extra is not None:
            vsplitter.addWidget(extra)

        self.table_view_container = QStackedWidget(self)
        for view in self.tableViews:
            self.table_view_container.addWidget(view)

        vsplitter.addWidget(self.table_view_container)  # 2

        vsplitter.addWidget(self.layoutToolWidgets())  # 3

        # self.filter_widgets_box = QScrollArea(self)
        self.filter_widgets_container = QStackedWidget(self)
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.filter_widgets_container.setSizePolicy(sizePolicy)
        for w in self.filterWidgets:
            self.filter_widgets_container.addWidget(w)

        self.filter_widgets_container.setVisible(False)
        self.filter_widgets_container.setFrameStyle(QFrame.Plain)
        vsplitter.addWidget(self.filter_widgets_container)

        di = 1 if extra is not None else 0

        vsplitter.setStretchFactor(0, 1.0)   # menubar
        vsplitter.setStretchFactor(1, 3.0)   # plots + integration
        # vsplitter.setStretchFactor(2, 1.0)   # ms2 spec chooser
        vsplitter.setStretchFactor(2 + di, 5.0)   # table
        vsplitter.setStretchFactor(3 + di, 1.0)   # tools
        vsplitter.setStretchFactor(4 + di, 2.0)   # filters

        vlayout.addWidget(vsplitter)

        if self.offerAbortOption:
            vlayout.addLayout(self.layoutButtons())

    def layoutButtons(self):
        hbox = QHBoxLayout()
        hbox.addWidget(self.abortButton)
        hbox.setAlignment(self.abortButton, Qt.AlignVCenter)
        hbox.addWidget(self.okButton)
        hbox.setAlignment(self.okButton, Qt.AlignVCenter)
        return hbox

    def enable_integration_widgets(self, flag=True):
        self.integration_widget.setEnabled(flag)

    def enable_spec_chooser_widgets(self, flag=True):
        self.spec_label.setEnabled(flag)
        self.choose_spec.setEnabled(flag)

    def layoutPlottingAndIntegrationWidgets(self):

        hsplitter = QSplitter()
        hsplitter.setOpaqueResize(False)

        middleLayout = QVBoxLayout()
        middleLayout.setSpacing(5)
        middleLayout.setMargin(5)
        middleLayout.addWidget(self.integration_widget)
        middleLayout.addStretch()

        middleLayout.addWidget(self.spec_label)
        middleLayout.addWidget(self.choose_spec)
        middleLayout.addStretch()
        middleLayout.addStretch()

        self.middleFrame = QFrame()
        self.middleFrame.setLayout(middleLayout)
        self.middleFrame.setMaximumWidth(250)

        plot_widgets = self.setup_plot_widgets([self.ts_plotter, self.eic_plotter, self.middleFrame,
                                                self.mz_plotter])

        for widget in plot_widgets:
            hsplitter.addWidget(widget)
        return hsplitter

    def setup_plot_widgets(self, widgets):
        return widgets

    def layoutToolWidgets(self):
        frame = QFrame(parent=self)
        layout = QGridLayout()
        row = 0
        column = 0
        layout.addWidget(self.chooseGroubLabel, row, column,  alignment=Qt.AlignLeft)
        column += 1
        layout.addWidget(self.chooseGroupColumn, row, column, alignment=Qt.AlignLeft)
        column += 1
        layout.addWidget(self.choose_visible_columns_button, row, column, alignment=Qt.AlignLeft)

        h_layout = QHBoxLayout()
        h_layout.addWidget(self.sort_label)

        for sort_field_w, sort_order_w in zip(self.sort_fields_widgets, self.sort_order_widgets):
            h_layout.addWidget(sort_field_w)
            h_layout.addWidget(sort_order_w)

        column += 1
        layout.addLayout(h_layout, row, column, alignment=Qt.AlignLeft)

        row = 1
        column = 0
        layout.addWidget(self.filter_on_button, row, column, alignment=Qt.AlignLeft)
        column += 1
        layout.addWidget(self.restrict_to_filtered_button, row, column, alignment=Qt.AlignLeft)
        column += 1
        layout.addWidget(self.remove_filtered_button, row, column, alignment=Qt.AlignLeft)
        column += 1
        layout.addWidget(self.export_table_button, row, column, alignment=Qt.AlignLeft)
        column += 1

        # layout.addWidget(self.dummy, row, column, alignment=Qt.AlignLeft)
        layout.setColumnStretch(column, 1)
        layout.setVerticalSpacing(2)

        frame.setLayout(layout)
        return frame

    def set_window_title(self, n_rows_total, n_rows_visible):
        model_title = self.model.getTitle()
        title = "%d out of %d rows from %s" % (n_rows_visible, n_rows_total, model_title)
        self.setWindowTitle(title)

    def setup_model_dependent_look(self):

        hasFeatures = self.model.hasFeatures()
        isIntegrated = self.model.isIntegrated()
        hasEIC = self.model.hasEIC()
        hasTimeSeries = self.model.hasTimeSeries()
        hasSpectra = self.model.hasSpectra()

        self.eic_only_mode = hasEIC and not hasFeatures  # includes: not isIntegrated !
        self.has_eic = hasEIC
        self.has_chromatograms = hasFeatures
        self.allow_integration = isIntegrated and self.model.implements("integrate")
        self.has_time_series = hasTimeSeries
        self.has_spectra = hasSpectra or hasFeatures

        self.eic_plotter.setVisible(self.eic_only_mode or self.has_chromatograms)
        self.eic_plotter.enable_range(not self.eic_only_mode)

        if self.has_chromatograms or self.has_spectra:
            show_mz = True
        else:
            show_mz = False

        self.mz_plotter.setVisible(show_mz)
        self.ts_plotter.setVisible(self.has_time_series)

        self.enable_integration_widgets(self.allow_integration)
        self.enable_spec_chooser_widgets(self.has_spectra or self.has_chromatograms)

        self.enable_integration_widgets(self.allow_integration)
        self.enable_spec_chooser_widgets(self.has_chromatograms or self.has_spectra)

        self.middleFrame.setVisible(self.allow_integration or self.has_spectra)

        self.choose_spec.clear()

    @protect_signal_handler
    def handleClick(self, index, model):
        content = model.data(index)
        if isUrl(content):
            QDesktopServices.openUrl(QUrl(content))

    @protect_signal_handler
    def cell_pressed(self, index):
        self.tableView.selectRow(index.row())
        self.tableView.verticalHeader().sectionClicked.emit(index.row())

    def connectSignals(self):
        for i, action in enumerate(self.chooseTableActions):

            handler = lambda i=i: self.setupViewForTable(i)
            handler = protect_signal_handler(handler)
            self.menubar.connect(action, SIGNAL("triggered()"), handler)

        for view in self.tableViews:
            vh = view.verticalHeader()
            vh.setContextMenuPolicy(Qt.CustomContextMenu)
            vh.customContextMenuRequested.connect(self.openContextMenuVerticalHeader)
            vh.sectionClicked.connect(self.rowClicked)

            hh = view.horizontalHeader()
            hh.setContextMenuPolicy(Qt.CustomContextMenu)
            hh.customContextMenuRequested.connect(self.openContextMenuHorizontalHeader)

            model = view.model()
            handler = lambda idx, model=model: self.handleClick(idx, model)
            handler = protect_signal_handler(handler)
            model.ACTION_LIST_CHANGED.connect(self.updateMenubar)
            view.clicked.connect(handler)
            view.doubleClicked.connect(self.handle_double_click)

            view.pressed.connect(self.cell_pressed)

            self.connect_additional_widgets(model)

        self.integration_widget.TRIGGER_INTEGRATION.connect(self.do_integrate)
        self.choose_spec.itemSelectionChanged.connect(self.spectrumChosen)

        if self.offerAbortOption:
            self.connect(self.okButton, SIGNAL("clicked()"), self.ok)
            self.connect(self.abortButton, SIGNAL("clicked()"), self.abort)

        self.choose_visible_columns_button.clicked.connect(self.choose_visible_columns)

        self.filter_on_button.clicked.connect(self.filter_toggle)
        self.remove_filtered_button.clicked.connect(self.remove_filtered)
        self.restrict_to_filtered_button.clicked.connect(self.restrict_to_filtered)
        self.export_table_button.clicked.connect(self.export_table)

        for sort_field_w in self.sort_fields_widgets:
            sort_field_w.currentIndexChanged.connect(self.sort_fields_changed)

        for sort_order_w in self.sort_order_widgets:
            sort_order_w.currentIndexChanged.connect(self.sort_fields_changed)

        self.eic_plotter.SELECTED_RANGE_CHANGED.connect(self.eic_selection_changed)

    @protect_signal_handler
    def sort_fields_changed(self, __):
        sort_data = [(str(f0.currentText()),
                      str(f1.currentText())) for f0, f1 in zip(self.sort_fields_widgets,
                                                               self.sort_order_widgets)]
        sort_data = [(f0, f1) for (f0, f1) in sort_data if f0 != "-" and f0 != ""]
        if sort_data:
            self.model.sort_by(sort_data)
            main_name, main_order = sort_data[0]
            idx = self.model.widget_col(main_name)
            if idx is not None:
                header = self.tableView.horizontalHeader()
                header.blockSignals(True)
                header.setSortIndicator(
                    idx, Qt.AscendingOrder if main_order.startswith("asc") else Qt.DescendingOrder)
                header.blockSignals(False)

    @protect_signal_handler
    def filter_toggle(self, *a):
        self.filters_enabled = not self.filters_enabled
        for model in self.models:
            model.setFiltersEnabled(self.filters_enabled)
        self.filter_widgets_container.setVisible(self.filters_enabled)
        self.restrict_to_filtered_button.setEnabled(self.filters_enabled)
        self.remove_filtered_button.setEnabled(self.filters_enabled)
        if self.filters_enabled:
            # we add spaces becaus on mac the text field cut when rendered
            self.filter_on_button.setText("Disable row filtering")
            self.export_table_button.setText("Export filtered")
        else:
            # we add spaces becaus on mac the text field cut when rendered
            self.filter_on_button.setText("Enable row filtering")
            self.export_table_button.setText("Export table")

    @protect_signal_handler
    def choose_visible_columns(self, *a):
        self.remove_delegates()
        col_names, is_currently_visible = self.model.columnames_with_visibility()
        if not col_names:
            return

        # zip, sort and unzip then:
        col_names, is_currently_visible = zip(*sorted(zip(col_names, is_currently_visible)))
        dlg = ColumnMultiSelectDialog(col_names, is_currently_visible)
        dlg.exec_()
        if dlg.column_settings is None:
            return

        hide_names = [n for (n, col_idx, visible) in dlg.column_settings if not visible]
        self.update_hidden_columns(hide_names)
        self.model.save_preset_hidden_column_names()

    def update_hidden_columns(self, hidden_names):
        self.model.hide_columns(hidden_names)
        self.set_delegates()
        self.setup_choose_group_column_widget(hidden_names)
        self.setup_sort_fields(hidden_names)
        self.current_filter_widget.hide_filters(hidden_names)
        self.model.table.meta["hide_in_explorer"] = hidden_names
        self.setup_sort_fields(hidden_names)

    @protect_signal_handler
    def remove_filtered(self, *a):
        self.model.remove_filtered()

    @protect_signal_handler
    def restrict_to_filtered(self, *a):
        self.model.restrict_to_filtered()

    @protect_signal_handler
    def export_table(self, *a):
        n = len(self.model)
        if n > 1000:
            answer = QMessageBox.question(self, "Are you sure ?", "the final table would contain "
                                                "%d lines. Are you sure to continue ?" % n,
                                                QMessageBox.Ok | QMessageBox.Cancel)
            if answer == QMessageBox.Cancel:
                return
        path = askForSave(extensions=["csv"])
        if path is not None:
            self.model.store_table_as_csv(path)

    @protect_signal_handler
    def handle_double_click(self, idx):
        row, col = self.model.table_index(idx)
        cell_value = self.model.cell_value(idx)
        extra_args = dict()
        if isinstance(cell_value, PeakMap):
            col_name = self.model.column_name(idx)
            if "__" in col_name:
                prefix, __, __ = col_name.partition("__")
                full_prefix = prefix + "__"
            else:
                full_prefix = ""
            for n in "rtmin", "rtmax", "mzmin", "mzmax", "mz":
                full_n = full_prefix + n
                value = self.model.table.getValue(self.model.table.rows[row], full_n, None)
                extra_args[n] = value
            if extra_args["mzmin"] is None and extra_args["mzmax"] is None:
                mz = extra_args["mz"]
                if mz is not None:
                    mzmin = mz - 10 * 1e-6 * mz   # -10 ppm
                    mzmax = mz + 10 * 1e-6 * mz   # +19 ppm
                    extra_args["mzmin"] = mzmin
                    extra_args["mzmax"] = mzmax
            del extra_args["mz"]

        insp = inspector(cell_value, modal=False, parent=self, **extra_args)
        if insp is not None:
            insp()

    def disconnectModelSignals(self):
        self.disconnect(self.model, SIGNAL("dataChanged(QModelIndex,QModelIndex,PyQt_PyObject)"),
                        self.dataChanged)
        self.model.modelReset.disconnect(self.handle_model_reset)
        self.menubar.disconnect(self.undoAction, SIGNAL("triggered()"),
                                protect_signal_handler(self.model.undoLastAction))
        self.menubar.disconnect(self.redoAction, SIGNAL("triggered()"),
                                protect_signal_handler(self.model.redoLastAction))

    def connectModelSignals(self):
        self.connect(self.model, SIGNAL("dataChanged(QModelIndex,QModelIndex,PyQt_PyObject)"),
                     self.dataChanged)
        self.model.modelReset.connect(self.handle_model_reset)
        self.menubar.connect(self.undoAction, SIGNAL("triggered()"),
                             protect_signal_handler(self.model.undoLastAction))
        self.menubar.connect(self.redoAction, SIGNAL("triggered()"),
                             protect_signal_handler(self.model.redoLastAction))

        self.model.VISIBLE_ROWS_CHANGE.connect(self.set_window_title)
        self.model.SORT_TRIGGERED.connect(self.sort_by_click_in_header)

    @protect_signal_handler
    def sort_by_click_in_header(self, name, is_ascending):

        for f in self.sort_fields_widgets:
            f.blockSignals(True)
        for f in self.sort_order_widgets:
            f.blockSignals(True)

        main_widget = self.sort_fields_widgets[0]
        idx = main_widget.findText(name)
        main_widget.setCurrentIndex(idx)
        self.sort_order_widgets[0].setCurrentIndex(bool(is_ascending))
        for i in range(1, len(self.sort_fields_widgets)):
            self.sort_fields_widgets[i].setCurrentIndex(0)

        for f in self.sort_fields_widgets:
            f.blockSignals(False)
        for f in self.sort_order_widgets:
            f.blockSignals(False)

    def group_column_selected(self, idx):
        self.tableView.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def updateMenubar(self, undoInfo, redoInfo):
        self.undoAction.setEnabled(undoInfo is not None)
        self.redoAction.setEnabled(redoInfo is not None)
        if undoInfo:
            self.undoAction.setText("Undo: %s" % undoInfo)
        if redoInfo:
            self.redoAction.setText("Redo: %s" % redoInfo)

    def setupViewForTable(self, i):
        for j, action in enumerate(self.chooseTableActions):
            txt = unicode(action.text())  # QString -> Python unicode
            if txt.startswith("*"):
                txt = " " + txt[1:]
                action.setText(txt)
            if i == j:
                action.setText("*" + txt[1:])

        self.table_view_container.setCurrentIndex(i)
        self.filter_widgets_container.setCurrentIndex(i)

        if self.model is not None:
            self.disconnectModelSignals()
        self.model = self.models[i]
        self.current_filter_widget = self.filterWidgets[i]
        self.tableView = self.tableViews[i]

        hidden = self.model.table.meta.get("hide_in_explorer", ())
        self.update_hidden_columns(hidden)
        try:
            shown = self.model.load_preset_hidden_column_names()
            hidden = list(set(self.model.table.getColNames()) - shown)
            self.update_hidden_columns(hidden)
        except Exception:
            pass

        self.setup_model_dependent_look()
        if self.model.implements("setNonEditable"):
            self.model.setNonEditable("method", ["area", "rmse", "method", "params"])

        if self.model.implements("addNonEditable"):
            for col_name in self.model.table.getColNames():
                t = self.model.table.getColType(col_name)
                if t in (list, tuple, object, dict, set) or t is None or has_inspector(t):
                    self.model.addNonEditable(col_name)

        mod = self.model
        postfixes = mod.table.supportedPostfixes(mod.integrationColNames())
        self.integration_widget.set_postfixes(postfixes)

        self.setup_choose_group_column_widget(hidden)
        self.setup_sort_fields(hidden)
        self.connectModelSignals()
        self.updateMenubar(None, None)
        self.set_window_title(len(self.model.table), len(self.model.table))

    def setup_choose_group_column_widget(self, hidden_names):
        before = None
        if self.chooseGroupColumn.currentIndex() >= 0:
            before = str(self.chooseGroupColumn.currentText())
        self.chooseGroupColumn.clear()
        t = self.model.table
        candidates = [n for (n, f) in zip(t.getColNames(), t.getColFormats()) if f is not None]
        visible_names = [n for n in candidates if n not in hidden_names]
        all_choices = ["- manual multi select -"] + sorted(visible_names)
        self.chooseGroupColumn.addItems(all_choices)
        if before is not None and before in all_choices:
            idx = all_choices.index(before)
            self.chooseGroupColumn.setCurrentIndex(idx)

    def setup_sort_fields(self, hidden_names):
        before = []
        for field in self.sort_fields_widgets:
            if field.currentIndex() >= 0:
                before.append(str(field.currentText()))
            else:
                before.append(None)

        t = self.model.table
        candidates = [n for (n, f) in zip(t.getColNames(), t.getColFormats()) if f is not None]
        visible_names = [n for n in candidates if n not in hidden_names]

        all_choices = ["-"] + visible_names

        for field in self.sort_fields_widgets:
            field.clear()
            field.addItems(all_choices)

        for choice_before, field in zip(before, self.sort_fields_widgets):
            if choice_before is not None and choice_before in all_choices:
                idx = all_choices.index(choice_before)
                field.setCurrentIndex(idx)

    @protect_signal_handler
    def handle_model_reset(self):
        for name in self.model.table.getColNames():
            self.current_filter_widget.update(name)

    def reset_sort_fields(self):
        for field in self.sort_fields_widgets:
            field.setCurrentIndex(0)

    @protect_signal_handler
    def dataChanged(self, ix1, ix2, src):
        minr, maxr = sorted((ix1.row(), ix2.row()))
        minc, maxc = sorted((ix1.column(), ix2.column()))
        for r in range(minr, maxr + 1):
            for c in range(minc, maxc + 1):
                idx = self.model.createIndex(r, c)
                self.tableView.update(idx)

        minc = self.model.widgetColToDataCol[minc]
        maxc = self.model.widgetColToDataCol[maxc]
        minr = self.model.widgetRowToDataRow[minr]
        maxr = self.model.widgetRowToDataRow[maxr]

        for name in self.model.table.getColNames()[minc:maxc + 1]:
            self.current_filter_widget.update(name)

        if self.has_chromatograms:
            # minr, maxr = sorted((ix1.row(), ix2.row()))
            if any(minr <= index <= maxr for index in self.model.selected_data_rows):
                if isinstance(src, IntegrateAction):
                    self.plot_chromatograms(reset=False)
                else:
                    self.plot_chromatograms(reset=True)

        self.reset_sort_fields()

    @protect_signal_handler
    def abort(self):
        self.result = 1
        self.close()

    @protect_signal_handler
    def ok(self):
        self.result = 0
        self.close()

    @protect_signal_handler
    def openContextMenuHorizontalHeader(self, point):
        widget_col_index = self.tableView.horizontalHeader().logicalIndexAt(point)

        if self.model.column_type(widget_col_index) is CheckState:
            menu = QMenu()
            check_all_action = menu.addAction("check all")
            uncheck_all_action = menu.addAction("uncheck all")
            appearAt = self.tableView.horizontalHeader().mapToGlobal(point)

            chosen = menu.exec_(appearAt)
            if chosen == check_all_action:
                self.async_runner.run_async(self.model.set_all, (widget_col_index, CheckState(True)), blocked=True)
            if chosen == uncheck_all_action:
                self.async_runner.run_async(self.model.set_all, (widget_col_index, CheckState(False)), blocked=True)


    @protect_signal_handler
    def openContextMenuVerticalHeader(self, point):
        index = self.tableView.verticalHeader().logicalIndexAt(point)
        menu = QMenu()

        if self.model.implements("cloneRow"):
            cloneAction = menu.addAction("Clone row")
        else:
            cloneAction = None

        if self.model.implements("removeRows"):
            removeAction = menu.addAction("Delete row")
        else:
            removeAction = None

        undoInfo = self.model.infoLastAction()
        redoInfo = self.model.infoRedoAction()

        if undoInfo is not None:
            undoAction = menu.addAction("Undo %s" % undoInfo)
        if redoInfo is not None:
            redoAction = menu.addAction("Redo %s" % redoInfo)
        appearAt = self.tableView.verticalHeader().mapToGlobal(point)
        choosenAction = menu.exec_(appearAt)
        if choosenAction == removeAction:
            self.model.removeRows([index])
        elif choosenAction == cloneAction:
            self.model.cloneRow(index)
        elif undoInfo is not None and choosenAction == undoAction:
            self.model.undoLastAction()
        elif redoInfo is not None and choosenAction == redoAction:
            self.model.redoLastAction()

    @protect_signal_handler
    def do_integrate(self, method, postfix):
        # QString -> Python str:
        method = str(method)
        postfix = str(postfix)
        rtmin, rtmax = self.eic_plotter.get_range_selection_limits()
        for data_row_idx in self.model.selected_data_rows:
            self.model.integrate(data_row_idx, postfix, method, rtmin, rtmax)

    @protect_signal_handler
    def rowClicked(self, widget_row_idx):

        start = time.time()
        print
        print "row clicked !"
        print

        group_by_idx = self.chooseGroupColumn.currentIndex()
        if group_by_idx > 0:
            self.select_rows_in_group(widget_row_idx, group_by_idx)
            print
            print "row click done"
            print
            return

        @timethis
        def handle_row_click():
            to_select = [idx.row() for idx in self.tableView.selectionModel().selectedRows()]
            self.model.set_selected_widget_rows(to_select)
            return to_select

        def update(to_select, start=start):

            if to_select is not None:
                self.model.set_selected_widget_rows(to_select)
            if not self.has_time_series:
                self.choose_spec.blockSignals(True)
                try:
                    self.setup_spectrum_chooser()
                finally:
                    self.choose_spec.blockSignals(False)

            if self.eic_only_mode:
                self.plot_eics_only()
            elif self.has_chromatograms:
                self.plot_chromatograms()
            if self.has_time_series:
                self.plot_time_series()
            if self.has_spectra:
                self.plot_spectra()

            # self.setCursor(Qt.ArrowCursor)
            needed = time.time() - start
            print
            print "row click done, needed %.2f s" % needed
            print

        # we need to keep gui responsive to handle key clicks:
        self.async_runner.run_async(handle_row_click, (),
                                    id_="select_rows",
                                    blocked=True,
                                    only_one_worker=True, call_back=update)

    @timethis
    def select_rows_in_group(self, widget_row_idx, group_by_idx):

        col_name = str(self.chooseGroupColumn.currentText())

        def find_rows():
            self.tableView.blockSignals(True)
            try:
                to_select = timethis(self.model.rows_with_same_value)(col_name, widget_row_idx)
                return to_select
            finally:
                self.tableView.blockSignals(False)

        def mark_rows(to_select):
            N = 50
            if len(to_select) > N:
                QMessageBox.warning(self, "Warning", "multiselect would mark %d lines. "
                                        "reduced number of lines to %d" % (len(to_select), N))
                to_select = to_select[:N]

            # expand selection

            self.setEnabled(False)
            # self.tableView.blockSignals(True)
            # self.setCursor(Qt.WaitCursor)
            try:
                mode_before = self.tableView.selectionMode()
                scrollbar_before = self.tableView.verticalScrollBar().value()

                self.tableView.setSelectionMode(QAbstractItemView.MultiSelection)
                for i in to_select:
                    if i != widget_row_idx:      # avoid "double click !" wich de-selects current row
                        self.tableView.selectRow(i)
                self.tableView.setSelectionMode(mode_before)
                self.tableView.verticalScrollBar().setValue(scrollbar_before)

                self.model.set_selected_widget_rows(to_select)

                if to_select is not None:
                    self.model.set_selected_widget_rows(to_select)
                if not self.has_time_series:
                    self.choose_spec.blockSignals(True)
                    try:
                        self.setup_spectrum_chooser()
                    finally:
                        self.choose_spec.blockSignals(False)

                if self.eic_only_mode:
                    self.plot_eics_only()
                elif self.has_chromatograms:
                    self.plot_chromatograms()
                if self.has_time_series:
                    self.plot_time_series()
                if self.has_spectra:
                    self.plot_spectra()
            finally:
                self.setEnabled(True)
                self.tableView.blockSignals(False)

        self.async_runner.run_async(find_rows, (),
                                    id_="select_rows",
                                    blocked=True,
                                    only_one_worker=True, call_back=mark_rows)

    def setup_spectrum_chooser(self):
        self.choose_spec.clear()

        spectra = []
        labels = []

        if self.has_chromatograms:
            labels.append("spectra from peak")
            spectra.append(None)   # place holder as ms1 spec is computed from peakmap on demand !
            self.first_spec_in_choser_is_ms1 = True
        else:
            self.first_spec_in_choser_is_ms1 = False

        num_extra_spectra = 0
        for idx in self.model.selected_data_rows:
            pf, s = self.model.getMS2Spectra(idx)
            for pfi, si in zip(pf, s):
                if si is not None:
                    for sii in si:
                        label = "spectra%s rt=%.2fm" % (pfi, sii.rt / 60.0)
                        if sii.precursors:
                            mz, I = sii.precursors[0]
                            label += " pre=(%.5f, %.2e)" % (mz, I)
                        labels.append(label)
                        spectra.append(sii)
                        num_extra_spectra += 1

        self.spectra_listed_in_chooser = spectra
        self.choose_spec.setVisible(len(spectra) > 0)

        for label in labels:
            self.choose_spec.addItem(label)

        if self.first_spec_in_choser_is_ms1:
            self.choose_spec.setCurrentRow(0)
        else:
            self.choose_spec.selectAll()

    @timethis
    def plot_time_series(self):
        rtmin, rtmax, time_series = time_series_curves(self.model)
        ts_configs = configsForTimeSeries(time_series)
        self.ts_plotter.del_all_items()
        self.ts_plotter.reset()
        self.ts_plotter.add_time_series(time_series, ts_configs)
        self.ts_plotter.replot()

    def plot_eics_only(self):
        rtmin, rtmax, curves = eic_curves(self.model)
        configs = configsForEics(curves)
        self.eic_plotter.reset()
        self.eic_plotter.add_eics(curves, configs=configs, labels=None)
        self.eic_plotter.replot()

    @timethis
    def plot_chromatograms(self, reset=True):

        # todo: plot chromatograms async for huge tables !
        self.eic_plotter.del_all_items()
        if self.has_eic:
            source = eic_curves(self.model)
        elif self.has_chromatograms:
            source  = compute_eics(self.model)
        else:
            return

        overall_rtmin, overall_rtmax = current_rt_limits(self.model)

        plotter = self.eic_plotter.eic_plotter()
        plotter.next()
        w = (overall_rtmax - overall_rtmin) / 2.0
        timethis(self.eic_plotter.set_rt_axis_limits)(overall_rtmin - w, overall_rtmax + w)

        n = len(self.model.selected_data_rows)
        if n > 3:
            dlg = QProgressDialog("compute chromatograms", QString(""), 0, n, parent=self)
            dlg.setCancelButton(None)
            dlg.show()
        else:
            dlg = None

        try:
            for i, (rtmin, rtmax, curve) in itertools.izip(itertools.count(), source):
                config = configForEic(i)
                plotter.send((None, curve, config))
                if dlg is not None:
                    dlg.setValue(i)

        finally:
            if dlg is not None:
                dlg.close()

        plotter.send(None)
        plotter.close()

        f_shapes = fit_shapes(self.model)

        for (chromo, baseline), i in zip(f_shapes, itertools.count()):
            if chromo is None:
                continue
            rts, iis = chromo
            if baseline is None:
                baseline = 0.0

            config = configForEic(i)
            eic_color = config["color"]
            color = turn_light(eic_color)
            timethis(self.eic_plotter.add_eic_filled)(rts, iis, baseline, color)

        # allrts are sorted !
        if overall_rtmin is not None and overall_rtmax is not None:
            w = (overall_rtmax - overall_rtmin) / 2.0
            if w == 0:
                w = 30.0  # seconds
            if reset:
                timethis(self.eic_plotter.set_rt_axis_limits)(overall_rtmin - w, overall_rtmax + w)

            timethis(self.eic_plotter.set_range_selection_limits)(rtmin, rtmax, True)

            timethis(self.eic_plotter.reset_intensity_limits)(fac=1.1, rtmin=overall_rtmin - w,
                                                              rtmax=overall_rtmax + w)

        timethis(self.eic_plotter.replot)()

    @protect_signal_handler
    def spectrumChosen(self):
        spectra = [self.spectra_listed_in_chooser[idx.row()]
                   for idx in self.choose_spec.selectedIndexes()]
        labels = [str(item.data(0).toString()) for item in self.choose_spec.selectedItems()]
        ms2_data = [(l, s) for (l, s) in zip(labels, spectra) if s is not None and l is not None]
        if ms2_data:
            labels, spectra = zip(*ms2_data)  # unzip, works only if ms2_data is not empty
            self.mz_plotter.plot_spectra([s.peaks for s in spectra], labels)
            self.mz_plotter.resetAxes()
            self.mz_plotter.replot()
        else:
            self.plot_ms1_spectra()

    def eic_selection_changed(self, rtmin, rtmax):
        if self.has_time_series or not self.first_spec_in_choser_is_ms1:
            return
        self.choose_spec.setCurrentRow(0)
        peakmaps = [
            pm for idx in self.model.selected_data_rows for pm in self.model.getPeakmaps(idx)]
        windows = []
        for idx in self.model.selected_data_rows:
            for (__, __, mzmin, mzmax) in self.model.getEICWindows(idx):
                window = (rtmin, rtmax, mzmin, mzmax)
                windows.append(window)
        if not self.has_time_series:
            timethis(self.plot_spectra_from_peakmaps)(peakmaps, windows)

    def plot_spectra(self):
        peakmaps = [pm for idx in self.model.selected_data_rows for pm in self.model.getPeakmaps(idx)]
        windows = []
        for idx in self.model.selected_data_rows:
            windows.extend(self.model.getEICWindows(idx))
        timethis(self.plot_spectra_from_peakmaps)(peakmaps, windows)

    def plot_ms1_spectra(self):
        peakmaps = [
            pm for idx in self.model.selected_data_rows for pm in self.model.getPeakmaps(idx)]
        windows = [
            w for idx in self.model.selected_data_rows for w in self.model.getEICWindows(idx)]
        if not self.has_time_series:
            self.plot_spectra_from_peakmaps(peakmaps, windows)

    def plot_ms2_spectra(self, spectra, labels):
        self.mz_plotter.plot_spectra([s.peaks for s in spectra], labels)
        self.mz_plotter.resetAxes()
        self.mz_plotter.replot()

    def plot_spectra_from_peakmaps(self, peakmaps, windows):

        if not peakmaps or not windows:
            print("empty peakmaps or windows")
            return

        data = []
        mzs = []
        for (rtmin, rtmax, mzmin, mzmax), pm in zip(windows, peakmaps):
            mzs.append(mzmin)
            mzs.append(mzmax)
            data.append((pm, rtmin, rtmax, mzmin, mzmax, 3000))

        if not mzs:
            return
        mzmin = min(mzs)
        mzmax = max(mzs)

        configs = configsForSpectra(len(peakmaps))
        postfixes = self.model.table.supportedPostfixes(self.model.eicColNames())
        titles = map(repr, postfixes)

        n = len(data)
        if n < 5:
            self.mz_plotter.plot_peakmaps(data, configs, titles if len(titles) > 1 else None)
            self.mz_plotter.reset_mz_limits(mzmin, mzmax)
            self.mz_plotter.replot()
            return

        dlg = QProgressDialog("extract spectra", QString(""), 0, n, parent=self)
        dlg.setCancelButton(None)
        dlg.show()
        try:
            plot_iter = self.mz_plotter.plot_peakmaps_iter(data, configs,
                                                           titles if len(titles) > 1 else None)
            for i, _ in itertools.izip(itertools.count(), plot_iter):
                dlg.setValue(i)
                guidata.qapplication().processEvents()

        finally:
            dlg.close()

        self.mz_plotter.replot()


def inspect(what, offerAbortOption=False, modal=True, parent=None, close_callback=None):
    """
    allows the inspection and editing of simple or multiple
    tables.

    """
    if isinstance(what, (Table, Hdf5TableProxy)):
        what = [what]
    app = guidata.qapplication()  # singleton !
    explorer = TableExplorer(what, offerAbortOption, parent=parent, close_callback=close_callback)
    if modal:
        explorer.raise_()
        explorer.exec_()
        # partial cleanup
        modified = len(explorer.models[0].actions) > 0
        del explorer.models
        if offerAbortOption:
            if explorer.result == 1:
                raise Exception("Dialog aborted by user")
        return modified
    else:
        explorer.show()
    del app
