# -*- coding: utf-8 -*-

import os

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import guidata

from plotting_widgets import RtPlotter, MzPlotter

from ..data_types import Table, PeakMap, CallBack

from table_explorer_model import *

from helpers import protect_signal_handler

from inspectors import has_inspector, inspector

from emzed_dialog import EmzedDialog

from .widgets import (FilterCriteria, ChooseFloatRange, ChooseIntRange, ChooseValue,
                      ChooseTimeRange, StringFilterPattern, ColumnMultiSelectDialog)

from ...gui.file_dialogs import askForSave


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
    if light:
        c = tuple([min(ii + 50, 255) for ii in c])

    # create hex string  "#rrggbb":
    return "#" + "".join("%02x" % v for v in c)


def configsForEics(eics):
    n = len(eics)
    return [dict(linewidth=1.5, color=getColors(i)) for i in range(n)]


def configsForSmootheds(smootheds):
    n = len(smootheds)
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

            def clicked(__):
                cell.callback(row, parent)

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
        if (evt.modifiers(), evt.key()) == (Qt.ControlModifier, Qt.Key_F):
            if self.model.selectedIndexes():
                column = self.model.selectedIndexes()[0].column()
            else:
                column = self.model().current_sort_col_idx

            # some columns are invisible, so we need a lookup:
            col_name = self.model().getShownColumnName(column)
            look_for, ok = QInputDialog.getText(self, "Search Column %s" % col_name,
                                                "Lookup Column %s for :" % col_name)
            if ok:
                look_for = unicode(look_for).strip()
                if look_for:
                    row = self.model().lookup(look_for, col_name)
                    if row is not None:
                        ix = self.model().index(row, column)
                        self.setCurrentIndex(ix)
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
        self.wasIntegrated = None

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
        self.chooseSpectrum = QComboBox()
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
                    except:
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

    def setupIntegrationWidgets(self):
        self.intLabel = QLabel("Integration")
        self.chooseIntMethod = QComboBox()
        from ... import _algorithm_configs
        for name, _ in _algorithm_configs.peakIntegrators:
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
        vsplitter.addWidget(self.chooseSpectrum)  # 2

        extra = self.create_additional_widgets(vsplitter)
        if extra is not None:
            vsplitter.addWidget(extra)

        self.table_view_container = QStackedWidget(self)
        for view in self.tableViews:
            self.table_view_container.addWidget(view)

        vsplitter.addWidget(self.table_view_container)  # 3

        vsplitter.addWidget(self.layoutToolWidgets())  # 4

        self.filter_widgets_container = QStackedWidget(self)
        for w in self.filterWidgets:
            self.filter_widgets_container.addWidget(w)

        self.filter_widgets_container.setVisible(False)
        vsplitter.addWidget(self.filter_widgets_container)  # 5

        di = 1 if extra is not None else 0

        vsplitter.setStretchFactor(0, 1.0)   # menubar
        vsplitter.setStretchFactor(1, 3.0)   # plots + integration
        vsplitter.setStretchFactor(2, 1.0)   # ms2 spec chooser
        vsplitter.setStretchFactor(3 + di, 5.0)   # table
        vsplitter.setStretchFactor(4 + di, 1.0)   # tools
        vsplitter.setStretchFactor(5 + di, 2.0)   # filters

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

    def layoutPlottingAndIntegrationWidgets(self):

        hsplitter = QSplitter()
        hsplitter.setOpaqueResize(False)

        integrationLayout = QVBoxLayout()
        integrationLayout.setSpacing(10)
        integrationLayout.setMargin(5)
        integrationLayout.addWidget(self.intLabel)
        integrationLayout.addWidget(self.chooseIntMethod)
        integrationLayout.addWidget(self.choosePostfix)
        integrationLayout.addWidget(self.reintegrateButton)
        integrationLayout.addStretch()
        integrationLayout.setAlignment(self.intLabel, Qt.AlignTop)
        integrationLayout.setAlignment(self.chooseIntMethod, Qt.AlignTop)
        integrationLayout.setAlignment(self.reintegrateButton, Qt.AlignTop)

        self.integrationFrame = QFrame()
        self.integrationFrame.setLayout(integrationLayout)

        plot_widgets = self.setup_plot_widgets([self.rt_plotter.widget, self.integrationFrame,
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

    def set_window_title(self, table, visible):
        model_title = self.model.getTitle()
        title = "%d out of %d rows from %s" % (len(visible), len(table), model_title)
        self.setWindowTitle(title)

    def setupModelDependendLook(self):
        hasFeatures = self.model.hasFeatures()
        isIntegrated = self.model.isIntegrated()
        self.hasFeatures = hasFeatures
        self.isIntegrated = isIntegrated
        self.hasEIConly = False
        if not self.hasFeatures and not self.isIntegrated and self.model.hasEIC():
            self.hasEIConly = True


        self.chooseSpectrum.setVisible(False)
        if hasFeatures != self.hadFeatures:
            self.setPlotVisibility(hasFeatures)
            self.hadFeatures = hasFeatures
            # default: invisible, only activated when row clicked and
            # level >= 2 spectra are available
        if isIntegrated != self.wasIntegrated:
            self.setIntegrationPanelVisiblity(isIntegrated)
            self.wasIntegrated = isIntegrated
        if hasFeatures:
            self.rt_plotter.setEnabled(True)
            self.resetPlots()
        elif self.hasEIConly:
            self.rt_plotter.setEnabled(True)
            self.rt_plotter.widget.setVisible(True)
            self.mz_plotter.widget.setVisible(False)
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
        self.integrationFrame.setVisible(doShow)

    @protect_signal_handler
    def handleClick(self, index, model):
        content = model.data(index)
        if isUrl(content):
            QDesktopServices.openUrl(QUrl(content))

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

            self.connect_additional_widgets(model)

        self.connect(self.reintegrateButton, SIGNAL("clicked()"), self.doIntegrate)
        self.connect(self.chooseSpectrum, SIGNAL("activated(int)"), self.spectrumChosen)

        if self.offerAbortOption:
            self.connect(self.okButton, SIGNAL("clicked()"), self.ok)
            self.connect(self.abortButton, SIGNAL("clicked()"), self.abort)

        self.choose_visible_columns_button.clicked.connect(self.choose_visible_columns)

        self.filter_on_button.clicked.connect(self.filter_toggle)
        self.remove_filtered_button.clicked.connect(self.remove_filtered)
        self.restrict_to_filtered_button.clicked.connect(self.restrict_to_filtered)
        self.export_table_button.clicked.connect(self.export_table)

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
        dlg = ColumnMultiSelectDialog(col_names, is_currently_visible)
        dlg.exec_()
        if dlg.column_settings is None:
            return

        hide_names = [n for (n, col_idx, visible) in dlg.column_settings if not visible]
        self.update_hidden_columns(hide_names)

    def update_hidden_columns(self, hide_names):
        self.model.hide_columns(hide_names)
        self.set_delegates()
        self.setup_choose_group_column_widget(hide_names)
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
            print(extra_args)

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

        self.connect(self.chooseGroupColumn, SIGNAL("activated(int)"), self.group_column_selected)

        self.model.DATA_CHANGE.connect(self.set_window_title)

    def group_column_selected(self, idx):
        multi_select_available = (idx == 0)  # entry labeled "- manual multi select -"
        if multi_select_available:
            self.tableView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        else:
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
        self.connectModelSignals()
        self.updateMenubar()

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

    @protect_signal_handler
    def handle_model_reset(self):
        for name in self.model.table.getColNames():
            self.current_filter_widget.update(name)

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

        # first entry is approx "manual selection"
        if group_by_idx == 0:
            to_select = [idx.row() for idx in self.tableView.selectionModel().selectedRows()]
        else:
            col_name = str(self.chooseGroupColumn.currentText())
            widget_rows = self.model.rows_with_same_value(col_name, widget_row_idx)
            to_select = widget_rows[:40]  # avoid to many rows

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

    def setupSpectrumChooser(self):
        # delete QComboBox:
        while self.chooseSpectrum.count():
            self.chooseSpectrum.removeItem(0)

        postfixes, spectra = [], []
        for idx in self.model.selected_data_rows:
            pf, s = self.model.getLevelNSpectra(idx, minLevel=2)
            postfixes.extend(pf)
            spectra.extend(s)

        self.currentLevelNSpecs = []

        if not len(spectra):
            self.chooseSpectrum.setVisible(False)
            return

        self.chooseSpectrum.setVisible(True)
        self.chooseSpectrum.addItem("Show only Level 1 spectra")
        for postfix, s in zip(postfixes, spectra):
            if postfix != "":
                txt = postfix + ", "
            else:
                txt = ""
            txt += "rt=%.2fm, level=%d" % (s.rt / 60.0, s.msLevel)
            mzs = [mz for (mz, I) in s.precursors]
            precursors = ", ".join("%.6f" % mz for mz in mzs)
            if precursors:
                txt += ", precursor mzs=[%s]" % precursors
            self.chooseSpectrum.addItem(txt)
            self.currentLevelNSpecs.append(s)

    def updatePlots(self, reset=False):

        curves = []
        smoothed_curves = []
        mzmins, mzmaxs, rtmins, rtmaxs = [], [], [], []

        if self.hasEIConly:
            for idx in self.model.selected_data_rows:
                eics, rtmin, rtmax, allrts = self.model.getEICs(idx)
                if rtmin is not None:
                    rtmins.append(rtmin)
                if rtmax is not None:
                    rtmaxs.append(rtmax)
                curves.extend(eics)

        else:
            for idx in self.model.selected_data_rows:
                eics, mzmin, mzmax, rtmin, rtmax, allrts = self.model.extractEICs(idx)
                if mzmin is not None:
                    mzmins.append(mzmin)
                if rtmin is not None:
                    rtmins.append(rtmin)
                if mzmax is not None:
                    mzmaxs.append(mzmax)
                if rtmax is not None:
                    rtmaxs.append(rtmax)
                curves.extend(eics)
                if self.isIntegrated:
                    smootheds = self.model.getSmoothedEics(idx, allrts)
                    if smootheds is not None:
                        smoothed_curves.extend(smootheds)

        rtmin = min(rtmins) if rtmins else None
        rtmax = max(rtmaxs) if rtmaxs else None
        mzmin = min(mzmins) if mzmins else None
        mzmax = max(mzmaxs) if mzmaxs else None

        if not reset:
            rtmin, rtmax = self.rt_plotter.getRangeSelectionLimits()
            xmin, xmax, ymin, ymax = self.rt_plotter.getLimits()

        configs = configsForEics(curves)

        curves += smoothed_curves
        configs += configsForSmootheds(smoothed_curves)

        self.rt_plotter.plot(curves, configs=configs, titles=None, withmarker=True)

        # allrts are sorted !
        if rtmin is not None and rtmax is not None:
            w = rtmax - rtmin
            if w == 0:
                w = 30.0  # seconds
            self.rt_plotter.setRangeSelectionLimits(rtmin, rtmax)
            self.rt_plotter.setXAxisLimits(rtmin - w, rtmax + w)
            self.rt_plotter.replot()

            if not reset:
                self.rt_plotter.setXAxisLimits(xmin, xmax)
                self.rt_plotter.setYAxisLimits(ymin, ymax)
                self.rt_plotter.updateAxes()

        reset = reset and mzmin is not None and mzmax is not None
        limits = (mzmin, mzmax) if reset else None
        if not self.hasEIConly:
            self.plotMz(resetLimits=limits)

    @protect_signal_handler
    def spectrumChosen(self, idx):
        if idx == 0:
            self.rt_plotter.setEnabled(True)
            self.chooseIntMethod.setEnabled(True)
            self.reintegrateButton.setEnabled(True)
            self.plotMz()
        else:
            self.rt_plotter.setEnabled(False)
            self.chooseIntMethod.setEnabled(False)
            self.reintegrateButton.setEnabled(False)
            self.mz_plotter.plot([self.currentLevelNSpecs[idx - 1].peaks])
            self.mz_plotter.resetAxes()
            self.mz_plotter.replot()

    def plotMz(self, resetLimits=None):
        """ this one is used from updatePlots and the rangeselectors
            callback """
        rtmin = self.rt_plotter.minRTRangeSelected
        rtmax = self.rt_plotter.maxRTRangeSelected
        peakmaps = [pm for idx in self.model.selected_data_rows for pm in self.model.getPeakmaps(idx)]
        mzmin = mzmax = None
        if resetLimits:
            mzmin, mzmax = resetLimits
            data = [(pm, rtmin, rtmax, mzmin, mzmax, 3000) for pm in peakmaps]
        else:
            data = []
            for pm in peakmaps:
                mzmin, mzmax = pm.mzRange()
                data.append((pm, rtmin, rtmax, mzmin, mzmax, 3000))

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
