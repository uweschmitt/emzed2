# -*- coding: utf-8 -*-
import os

import numpy as np

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import guidata

from guiqwt.shapes import PolygonShape
from guiqwt.styles import ShapeParam

from plotting_widgets import RtPlotter, MzPlotter

from ..data_types import Table, PeakMap, CallBack

from table_explorer_model import *

from helpers import protect_signal_handler

from inspectors import has_inspector, inspector

from emzed_dialog import EmzedDialog

from .widgets import (FilterCriteria, ChooseFloatRange, ChooseIntRange, ChooseValue,
                      ChooseTimeRange, StringFilterPattern, ColumnMultiSelectDialog)

from ...gui.file_dialogs import askForSave


def create_peak_fit_shape(rts, iis, baseline, color):
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
        shape = PolygonShape(points, closed=True)
        shape.set_selectable(False)
        shape.set_movable(False)
        shape.set_resizable(False)
        shape.set_rotatable(False)
        param = ShapeParam()
        param.fill.alpha = 0.3
        param.fill.color = color
        # we set params this way because guiqwt has a bug if we use the shapeparam arg in
        # PolygonShapes __init__:
        param.update_shape(shape)
        shape.pen = QPen(Qt.NoPen)

        return shape
    return None


def eic_curves(model):
    rtmins, rtmaxs, curves = [], [], []
    for idx in model.selected_data_rows:
        eics, rtmin, rtmax, allrts = model.getEICs(idx)
        if rtmin is not None:
            rtmins.append(rtmin)
        if rtmax is not None:
            rtmaxs.append(rtmax)
        curves.extend(eics)
    return min(rtmins), max(rtmaxs), curves


def time_series(model):
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
    return min(rtmins), max(rtmaxs), curves


def chromatograms(model, is_integrated):
    curves = []
    fit_shapes = []
    mzmins, mzmaxs, rtmins, rtmaxs = [], [], [], []
    for idx in model.selected_data_rows:
        eics, mzmin, mzmax, rtmin, rtmax, allrts = model.extractEICs(idx)
        if mzmin is not None:
            mzmins.append(mzmin)
        if rtmin is not None:
            rtmins.append(rtmin)
        if mzmax is not None:
            mzmaxs.append(mzmax)
        if rtmax is not None:
            rtmaxs.append(rtmax)
        if is_integrated:
            fitted_shapes = model.getFittedPeakshapes(idx, allrts)
            # make sure that eics and fit shapes are in sync (needed for coloring):
            assert len(eics) == len(fitted_shapes)
            curves.extend(eics)
            fit_shapes.extend(fitted_shapes)
        else:
            curves.extend(eics)
    return min(rtmins), max(rtmaxs), min(mzmins), max(mzmaxs), curves, fit_shapes


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
    n = len(eics)
    w = 1.5
    return [dict(linewidth=w, color=getColors(i)) for i in range(n)]


def configsForTimeSeries(eics):
    n = len(eics)
    w = 1.5
    return [dict(linewidth=w, color=getColors(i)) for i in range(n)]


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
            self.dialog.updateMenubar()

    @protect_signal_handler
    def keyPressEvent(self, evt):
        if evt.key() in (Qt.Key_Up, Qt.Key_Down):
            row = self.currentIndex().row()
            column = self.currentIndex().column()
            if evt.key() == Qt.Key_Up:
                row -= 1
            else:
                row += 1
            row = min(max(row, 0), self.model().rowCount() - 1)
            ix = self.model().index(row, column)
            self.setCurrentIndex(ix)
            self.selectRow(row)
            self.verticalHeader().sectionClicked.emit(row)
            # skip event handling:
            return
        return super(EmzedTableView, self).keyPressEvent(evt)


class TableExplorer(EmzedDialog):

    def __init__(self, tables, offerAbortOption, parent=None):
        super(TableExplorer, self).__init__(parent)

        # Destroying the C++ object right after closing the dialog box,
        # otherwise it may be garbage-collected in another QThread
        # (e.g. the editor's analysis thread in Spyder), thus leading to
        # a segmentation fault on UNIX or an application crash on Windows
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowFlags(Qt.Window)

        self.offerAbortOption = offerAbortOption

        self.models = [TableModel(table, self) for table in tables]
        self.model = None
        self.tableView = None

        self.hadFeatures = None

        self.setupWidgets()
        self.setupLayout()
        self.connectSignals()

        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setSizePolicy(sizePolicy)
        self.setSizeGripEnabled(True)

        self.setupViewForTable(0)

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
        for i, model in enumerate(self.models):
            self.tableViews.append(self.setupTableViewFor(model))
            self.filterWidgets.append(self.setupFilterWidgetFor(model))

    def setupFilterWidgetFor(self, model):
        t = model.table
        w = FilterCriteria(self)
        for i, (fmt, name, type_) in enumerate(zip(t.getColFormats(),
                                                   t.getColNames(),
                                                   t.getColTypes())):
            if fmt is not None:
                ch = None
                col = t.getColumn(name)
                if type_ == float:
                    fmtter = t.colFormatters[i]
                    try:
                        txt = fmtter(0.0)
                    except Exception:
                        txt = ""
                    if txt.endswith("m"):
                        ch = ChooseTimeRange(name, t)
                    else:
                        ch = ChooseFloatRange(name, t)
                elif type_ in (bool, str, unicode, basestring, int):
                    distinct_values = sorted(set(col.values))
                    if len(distinct_values) <= 15:
                        ch = ChooseValue(name, t)
                    else:
                        if type_ == int:
                            ch = ChooseIntRange(name, t)
                        elif type_ in (str, unicode, basestring):
                            ch = StringFilterPattern(name, t)
                if ch is not None:
                    w.addChooser(ch)
        if w.number_of_choosers() > 0:
            w.add_stretch(1)
            self.filters_enabled = False
            w.setVisible(False)
            w.LIMITS_CHANGED.connect(model.limits_changed)
            return w
        else:
            return None

    def set_delegates(self):
        bd = ButtonDelegate(self.tableView, self)
        types = self.model.table.getColTypes()
        for i, j in self.model.widgetColToDataCol.items():
            if types[j] == CallBack:
                self.tableView.setItemDelegateForColumn(i, bd)

    def remove_delegates(self):
        types = self.model.table.getColTypes()
        for i, j in self.model.widgetColToDataCol.items():
            if types[j] == CallBack:
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
        self.plotconfigs = (None, dict(shade=0.35, linewidth=1, color="g"))
        self.rt_plotter = RtPlotter(rangeSelectionCallback=self.plotMz)
        self.rt_plotter.setMinimumSize(300, 100)
        self.mz_plotter = MzPlotter()
        self.mz_plotter.setMinimumSize(300, 100)
        pol = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        pol.setVerticalStretch(5)
        self.rt_plotter.widget.setSizePolicy(pol)
        self.mz_plotter.widget.setSizePolicy(pol)

        self.spec_label = QLabel("plot spectra:")
        self.choose_spec = QListWidget()
        self.choose_spec.setFixedHeight(90)
        self.choose_spec.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def setupIntegrationWidgets(self):
        self.intLabel = QLabel("Integration")
        self.chooseIntMethod = QComboBox()
        from ... import algorithm_configs
        for name, _ in algorithm_configs.peakIntegrators:
            self.chooseIntMethod.addItem(name)

        self.choosePostfix = QComboBox()

        self.reintegrateButton = button("Integrate")

    def setupToolWidgets(self):

        self.chooseGroubLabel = QLabel("Expand selection by:", parent=self)
        self.chooseGroupColumn = QComboBox(parent=self)
        self.chooseGroupColumn.setMinimumWidth(200)

        self.choose_visible_columns_button = button("Choose visible columns")

        # we introduced this invisible button else qt makes the filter_on_button always
        # active on mac osx, that means that as soon we press enter in one of the filter
        # widgets the button is triggered !
        # problem does not occur on windows.
        # self.dummy = QPushButton()
        # self.dummy.setVisible(False)

        self.filter_on_button = button("Enable row filtering")

        self.sort_label = QLabel("sort by:", parent=self)

        self.sort_fields_widgets = []
        self.sort_order_widgets = []
        for i in range(3):
            w = QComboBox(parent=self)
            w.setMinimumWidth(150)
            self.sort_fields_widgets.append(w)
            w = QComboBox(parent=self)
            w.addItems(["asc", "desc"])
            w.setMaximumWidth(70)
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

        self.filter_widgets_box = QScrollArea(self)
        self.filter_widgets_container = QStackedWidget(self)
        for w in self.filterWidgets:
            self.filter_widgets_container.addWidget(w)

        self.filter_widgets_box.setVisible(False)
        self.filter_widgets_box.setWidget(self.filter_widgets_container)  # 4
        self.filter_widgets_box.setWidgetResizable(True)
        self.filter_widgets_box.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.filter_widgets_box.setMinimumSize(QSize(self.filter_widgets_box.sizeHint().width(), 120))
        self.filter_widgets_box.setFrameStyle(QFrame.Plain)
        vsplitter.addWidget(self.filter_widgets_box)

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
        self.intLabel.setEnabled(flag)
        self.chooseIntMethod.setEnabled(flag)
        self.choosePostfix.setEnabled(flag)
        self.reintegrateButton.setEnabled(flag)

    def enable_spec_chooser_widgets(self, flag=True):
        self.spec_label.setEnabled(flag)
        self.choose_spec.setEnabled(flag)

    def layoutPlottingAndIntegrationWidgets(self):

        hsplitter = QSplitter()
        hsplitter.setOpaqueResize(False)

        middleLayout = QVBoxLayout()
        middleLayout.setSpacing(10)
        middleLayout.setMargin(5)
        middleLayout.addWidget(self.intLabel)
        middleLayout.addWidget(self.chooseIntMethod)
        middleLayout.addWidget(self.choosePostfix)
        middleLayout.addWidget(self.reintegrateButton)
        middleLayout.addStretch()

        middleLayout.addWidget(self.spec_label)
        middleLayout.addWidget(self.choose_spec)
        middleLayout.addStretch()
        middleLayout.addStretch()

        middleLayout.setAlignment(self.chooseIntMethod, Qt.AlignTop)
        middleLayout.setAlignment(self.reintegrateButton, Qt.AlignTop)

        self.middleFrame = QFrame()
        self.middleFrame.setLayout(middleLayout)

        plot_widgets = self.setup_plot_widgets([self.rt_plotter.widget, self.middleFrame,
                                                self.mz_plotter.widget])

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

        frame.setLayout(layout)
        return frame

    def set_window_title(self, table, visible=None):
        if visible is None:
            visible = table
        model_title = self.model.getTitle()
        title = "%d out of %d rows from %s" % (len(visible), len(table), model_title)
        self.setWindowTitle(title)

    def setupModelDependendLook(self):
        hasFeatures = self.model.hasFeatures()
        isIntegrated = self.model.isIntegrated()
        self.hasFeatures = hasFeatures
        self.isIntegrated = isIntegrated
        self.hasEIConly = False
        self.hasTimeSeries = False
        self.hasExtraSpectra = self.model.hasExtraSpectra()
        if self.model.hasTimeSeries():
            # overrides everything !
            self.hasTimeSeries = True
            isIntegrated = self.isIntegrated = False
            self.hasFeatures = hasFeatures = True
        elif not self.hasFeatures and not self.isIntegrated and self.model.hasEIC():
            self.hasEIConly = True

        self.setPlotVisibility(hasFeatures)
        self.enable_integration_widgets(isIntegrated)
        self.enable_spec_chooser_widgets(hasFeatures or self.hasExtraSpectra)

        show_middle = isIntegrated or hasFeatures or self.hasExtraSpectra
        self.middleFrame.setVisible(show_middle)

        self.choose_spec.clear()

        if hasFeatures:
            self.rt_plotter.setEnabled(True)
            self.resetPlots()
        elif self.hasEIConly:
            self.rt_plotter.setEnabled(True)
            self.rt_plotter.widget.setVisible(True)
            self.mz_plotter.widget.setVisible(False)
            self.resetPlots()
        elif self.hasTimeSeries:
            self.rt_plotter.setEnabled(True)
            self.mz_plotter.setEnabled(True)
            self.rt_plotter.widget.setVisible(True)
            self.mz_plotter.widget.setVisible(True)
            self.resetPlots()
        else:
            self.rt_plotter.widget.setVisible(False)
            self.mz_plotter.widget.setVisible(False)

    def setPlotVisibility(self, doShow):
        self.rt_plotter.widget.setVisible(doShow)
        self.mz_plotter.widget.setVisible(doShow)

    def resetPlots(self):
        self.rt_plotter.reset()
        self.mz_plotter.reset()

    def setIntegrationPanelVisiblity(self, doShow):
        self.middleFrame.setVisible(doShow)

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
            self.connect(vh, SIGNAL("customContextMenuRequested(QPoint)"), self.openContextMenu)

            self.connect(vh, SIGNAL("sectionClicked(int)"), self.rowClicked)

            model = view.model()
            handler = lambda idx, model=model: self.handleClick(idx, model)
            handler = protect_signal_handler(handler)
            self.connect(view, SIGNAL("clicked(QModelIndex)"), handler)
            self.connect(view, SIGNAL("doubleClicked(QModelIndex)"), self.handle_double_click)

            view.pressed.connect(self.cell_pressed)

            self.connect_additional_widgets(model)

        self.connect(self.reintegrateButton, SIGNAL("clicked()"), self.doIntegrate)
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
            header = self.tableView.horizontalHeader()
            header.blockSignals(True)
            header.setSortIndicator(idx, Qt.AscendingOrder if main_order.startswith("asc") else Qt.DescendingOrder)
            header.blockSignals(False)

    @protect_signal_handler
    def filter_toggle(self, *a):
        self.filters_enabled = not self.filters_enabled
        for model in self.models:
            model.setFiltersEnabled(self.filters_enabled)
        self.filter_widgets_box.setVisible(self.filters_enabled)
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
        dlg = ColumnMultiSelectDialog(col_names, is_currently_visible)
        dlg.exec_()
        if dlg.column_settings is None:
            return

        hide_names = [n for (n, col_idx, visible) in dlg.column_settings if not visible]
        self.update_hidden_columns(hide_names)
        self.model.save_preset_hidden_column_names()

    def update_hidden_columns(self, hide_names):
        self.model.hide_columns(hide_names)
        self.set_delegates()
        self.setup_choose_group_column_widget(hide_names)
        self.setup_sort_fields(hide_names)
        self.current_filter_widget.hide_filters(hide_names)
        self.model.table.meta["hide_in_explorer"] = hide_names

    @protect_signal_handler
    def remove_filtered(self, *a):
        self.model.remove_filtered()

    @protect_signal_handler
    def restrict_to_filtered(self, *a):
        self.model.restrict_to_filtered()

    @protect_signal_handler
    def export_table(self, *a):
        path = askForSave(extensions=["csv"])
        if path is not None:
            t = self.model.extract_visible_table()
            if os.path.exists(path):
                os.remove(path)
            t.storeCSV(path, as_printed=True)

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

        self.model.DATA_CHANGE.connect(self.set_window_title)
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

    def updateMenubar(self):
        undoInfo = self.model.infoLastAction()
        redoInfo = self.model.infoRedoAction()
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
            self.model.load_preset_hidden_column_names()
        except Exception:
            pass

        self.setupModelDependendLook()
        if self.isIntegrated:
            self.model.setNonEditable("method", ["area", "rmse", "method", "params"])

        for col_name in self.model.table.getColNames():
            t = self.model.table.getColType(col_name)
            if t in (list, tuple, object, dict, set) or t is None or has_inspector(t):
                self.model.addNonEditable(col_name)

        self.choosePostfix.clear()
        mod = self.model
        for p in mod.table.supportedPostfixes(mod.integrationColNames()):
            self.choosePostfix.addItem(repr(p))

        if len(self.choosePostfix) == 1:
            self.choosePostfix.setVisible(False)

        self.setup_choose_group_column_widget([])
        self.setup_sort_fields([])
        self.connectModelSignals()
        self.updateMenubar()
        self.set_window_title(self.model.table)

    def setup_choose_group_column_widget(self, hidden_names):
        before = None
        if self.chooseGroupColumn.currentIndex() >= 0:
            before = str(self.chooseGroupColumn.currentText())
        self.chooseGroupColumn.clear()
        t = self.model.table
        candidates = [n for (n, f) in zip(t.getColNames(), t.getColFormats()) if f is not None]
        visible_names = [n for n in candidates if n not in hidden_names]
        all_choices = ["- manual multi select -"] + visible_names
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
            field.clear()

        t = self.model.table
        candidates = [n for (n, f) in zip(t.getColNames(), t.getColFormats()) if f is not None]
        visible_names = [n for n in candidates if n not in hidden_names]

        all_choices = ["-"] + visible_names

        for field in self.sort_fields_widgets:
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

        if self.hasFeatures:
            # minr, maxr = sorted((ix1.row(), ix2.row()))
            if any(minr <= index <= maxr for index in self.model.selected_data_rows):
                if isinstance(src, IntegrateAction):
                    self.updatePlots(reset=False)
                else:
                    self.updatePlots(reset=True)

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
    def openContextMenu(self, point):
        idx = self.tableView.verticalHeader().logicalIndexAt(point)
        menu = QMenu()
        cloneAction = menu.addAction("Clone row")
        removeAction = menu.addAction("Delete row")
        undoInfo = self.model.infoLastAction()
        redoInfo = self.model.infoRedoAction()

        if undoInfo is not None:
            undoAction = menu.addAction("Undo %s" % undoInfo)
        if redoInfo is not None:
            redoAction = menu.addAction("Redo %s" % redoInfo)
        appearAt = self.tableView.verticalHeader().mapToGlobal(point)
        choosenAction = menu.exec_(appearAt)
        if choosenAction == removeAction:
            self.model.removeRows([idx])
        elif choosenAction == cloneAction:
            self.model.cloneRow(idx)
        elif undoInfo is not None and choosenAction == undoAction:
            self.model.undoLastAction()
        elif redoInfo is not None and choosenAction == redoAction:
            self.model.redoLastAction()

    @protect_signal_handler
    def doIntegrate(self):
        # QString -> Python str:
        method = str(self.chooseIntMethod.currentText())
        # Again QString -> Python str.
        # For better readibilty we put single quotes around the postfix
        # entry in the QComboBox which we have to remove now:
        postfix = str(self.choosePostfix.currentText()).strip("'")
        rtmin, rtmax = self.rt_plotter.getRangeSelectionLimits()
        for data_row_idx in self.model.selected_data_rows:
            self.model.integrate(postfix, data_row_idx, method, rtmin, rtmax)

    @protect_signal_handler
    def rowClicked(self, widget_row_idx):

        group_by_idx = self.chooseGroupColumn.currentIndex()

        # first entry is "manual selection"
        if group_by_idx == 0:
            to_select = [idx.row() for idx in self.tableView.selectionModel().selectedRows()]
        else:
            col_name = str(self.chooseGroupColumn.currentText())
            widget_rows = self.model.rows_with_same_value(col_name, widget_row_idx)
            to_select = widget_rows[:200]  # avoid to many rows

            # expand selection
            mode_before = self.tableView.selectionMode()
            scrollbar_before = self.tableView.verticalScrollBar().value()

            self.tableView.setSelectionMode(QAbstractItemView.MultiSelection)
            for i in to_select:
                if i != widget_row_idx:      # avoid "double click !" wich de-selects current row
                    self.tableView.selectRow(i)
            self.tableView.setSelectionMode(mode_before)
            self.tableView.verticalScrollBar().setValue(scrollbar_before)

        self.model.set_selected_data_rows(to_select)

        if self.hasFeatures:
            self.rt_plotter.setEnabled(True)
            self.updatePlots(reset=True)
            self.setupSpectrumChooser()
        elif self.hasEIConly:
            self.rt_plotter.setEnabled(True)
            self.updatePlots(reset=True)
            self.setupSpectrumChooser()
        elif self.hasTimeSeries:
            self.rt_plotter.setEnabled(True)
            self.updatePlots(reset=True)
            self.setupSpectrumChooser()

    def setupSpectrumChooser(self):
        self.choose_spec.blockSignals(True)
        self.choose_spec.clear()

        spectra = []
        labels = []

        if self.hasFeatures:
            labels.append("spectra from peak")
            spectra.append(None)

        for idx in self.model.selected_data_rows:
            pf, s = self.model.getExtraSpectra(idx)
            for pfi, si in zip(pf, s):
                if si is not None:
                    for sii in si:
                        label = "spectra%s rt=%.2fm" % (pfi, sii.rt / 60.0)
                        if sii.precursors:
                            mz, I = sii.precursors[0]
                            label += " pre=(%.5f, %.2e)" % (mz, I)
                        labels.append(label)
                        spectra.append(sii)

        self.spectra_from_chooser = spectra
        self.choose_spec.setVisible(len(spectra) > 0)

        for label in labels:
            self.choose_spec.addItem(label)

        if labels:
            self.choose_spec.setCurrentRow(0)
        self.choose_spec.blockSignals(False)

    def updatePlots(self, reset=False):

        mzmin = mzmax = rtmin = rtmax = None
        fit_shapes = []

        if self.hasEIConly:
            rtmin, rtmax, curves = eic_curves(self.model)
            configs = configsForEics(curves)

        elif self.hasTimeSeries:
            rtmin, rtmax, curves = time_series(self.model)
            configs = configsForTimeSeries(curves)
            self.plotMz(limits_from_rows=True)
        else:
            rtmin, rtmax, mzmin, mzmax, curves, fit_shapes = chromatograms(self.model, self.isIntegrated)
            configs = configsForEics(curves)

        if not reset:
            if not self.hasTimeSeries:
                rtmin, rtmax = self.rt_plotter.getRangeSelectionLimits()
            xmin, xmax, ymin, ymax = self.rt_plotter.getLimits()

        self.rt_plotter.plot(curves, self.hasTimeSeries, configs=configs, titles=None, withmarker=True)

        for ((rts, iis), baseline), config in zip(fit_shapes, configs):
            if baseline is None:
                baseline = 0.0

            eic_color = config["color"]
            color = turn_light(eic_color)
            shape = create_peak_fit_shape(rts, iis, baseline, color)
            if shape is not None:
                self.rt_plotter.widget.plot.add_item(shape)

        # allrts are sorted !
        if rtmin is not None and rtmax is not None:
            w = rtmax - rtmin
            if w == 0:
                w = 30.0  # seconds
            if not self.hasTimeSeries:
                self.rt_plotter.setRangeSelectionLimits(rtmin, rtmax)
                self.rt_plotter.setXAxisLimits(rtmin - w, rtmax + w)
            self.rt_plotter.replot()

            if not reset:
                self.rt_plotter.setXAxisLimits(xmin, xmax)
                self.rt_plotter.setYAxisLimits(ymin, ymax)
                self.rt_plotter.updateAxes()
            else:
                self.rt_plotter.reset_y_limits(fac=1.1, xmin=rtmin - w, xmax=rtmax + w)

        if self.hasTimeSeries and reset:
            self.rt_plotter.reset_x_limits(fac=1.0)

        reset_ = reset and mzmin is not None and mzmax is not None
        limits = (mzmin, mzmax) if reset_ else None
        if not self.hasEIConly and not self.hasTimeSeries:
            self.plotMz(resetLimits=limits)

    @protect_signal_handler
    def spectrumChosen(self):
        spectra = [self.spectra_from_chooser[idx.row()] for idx in self.choose_spec.selectedIndexes()]
        labels = [str(item.data(0).toString()) for item in self.choose_spec.selectedItems()]
        data = [(l, s) for (l, s) in zip(labels, spectra) if s is not None and l is not None]
        if data:
            labels, spectra = zip(*data)
            self.mz_plotter.plot_spectra([s.peaks for s in spectra], labels)
            self.mz_plotter.resetAxes()
            self.mz_plotter.replot()
        else:
            self.plotMz()

    def plotMz(self, resetLimits=None, limits_from_rows=False):
        """ this one is used from updatePlots and the rangeselectors
            callback """
        peakmaps = [pm for idx in self.model.selected_data_rows for pm in self.model.getPeakmaps(idx)]
        mzmin = mzmax = None
        if not limits_from_rows:
            rtmin = self.rt_plotter.minRTRangeSelected
            rtmax = self.rt_plotter.maxRTRangeSelected
            if resetLimits:
                mzmin, mzmax = resetLimits
                data = [(pm, rtmin, rtmax, mzmin, mzmax, 3000) for pm in peakmaps]
            else:
                data = []
                for pm in peakmaps:
                    mzmin, mzmax = pm.mzRange()
                    data.append((pm, rtmin, rtmax, mzmin, mzmax, 3000))
        else:
            windows = [wi for idx in self.model.selected_data_rows for wi in self.model.getEICWindows(idx)]
            data = [(pm,) + tuple(w) + (3000,) for (pm, w) in zip(peakmaps, windows)]
            if data:
                mzmin = min(wi[2] for wi in windows)
                mzmax = max(wi[3] for wi in windows)

        configs = configsForSpectra(len(peakmaps))
        postfixes = self.model.table.supportedPostfixes(self.model.eicColNames())
        titles = map(repr, postfixes)

        if data:
            self.mz_plotter.plot(data, configs, titles if len(titles) > 1 else None)
            if mzmin is not None and mzmax is not None:
                self.mz_plotter.reset_x_limits(mzmin, mzmax)
            self.mz_plotter.replot()


def inspect(what, offerAbortOption=False, modal=True, parent=None):
    """
    allows the inspection and editing of simple or multiple
    tables.

    """
    if isinstance(what, Table):
        what = [what]
    app = guidata.qapplication()  # singleton !
    explorer = TableExplorer(what, offerAbortOption, parent=parent)
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
