# -*- coding: utf-8 -*-

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import guidata

from plotting_widgets import RtPlotter, MzPlotter

from ..data_types import Table

from table_explorer_model import *

from helpers import protect_signal_handler

from inspectors import has_inspector, inspector

from emzed_dialog import EmzedDialog


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

        self.currentRowIndices = []
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
        self.setupPlottingWidgets()
        self.chooseSpectrum = QComboBox()
        self.setupIntegrationWidgets()
        self.setupToolWidgets()
        if self.offerAbortOption:
            self.setupAcceptButtons()

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
        for i, model in enumerate(self.models):
            self.tableViews.append(self.setupTableViewFor(model))

    def setupTableViewFor(self, model):

        class MyView(QTableView):

            @protect_signal_handler
            def showEvent(self, evt, model=model, parent=self):
                print self, evt, parent
                if not self.isSortingEnabled():
                    self.setSortingEnabled(True)
                    self.resizeColumnsToContents()
                    model.emptyActionStack()
                    parent.updateMenubar()

            @protect_signal_handler
            def keyPressEvent(self, evt, parent=self):
                if (evt.modifiers(), evt.key()) == (Qt.ControlModifier, Qt.Key_F):
                    if self.selectedIndexes():
                        column = self.selectedIndexes()[0].column()
                    else:
                        column = parent.model.current_sort_idx
                    table = parent.model.table
                    col_name = table.getColNames()[column]
                    look_for, ok = QInputDialog.getText(self, "Search Column %s" % col_name,
                                                        "Lookup Column %s for :" % col_name)
                    if ok:
                        look_for = str(look_for).strip()
                        if look_for:
                            for row, value in enumerate(getattr(table, col_name)):
                                if str(value).strip() == look_for:
                                    ix = parent.model.index(row, column)
                                    self.setCurrentIndex(ix)


        #tableView.showEvent = handler
        tableView = MyView(self)

        tableView.setModel(model)
        tableView.horizontalHeader().setResizeMode(QHeaderView.Interactive)
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

        self.reintegrateButton = QPushButton()
        self.reintegrateButton.setText("Integrate")

    def setupToolWidgets(self):
        self.chooseGroubLabel = QLabel("Expand selection by:")
        self.chooseGroupColumn = QComboBox()
        self.chooseGroupColumn.setMinimumWidth(300)

    def setupAcceptButtons(self):
        self.okButton = QPushButton("Ok")
        self.abortButton = QPushButton("Abort")
        self.result = 1  # default for closing

    def setupLayout(self):
        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        vsplitter = QSplitter()
        vsplitter.setOrientation(Qt.Vertical)
        vsplitter.setOpaqueResize(False)

        vsplitter.addWidget(self.menubar)
        vsplitter.addWidget(self.layoutWidgetsAboveTable())
        vsplitter.addWidget(self.layoutToolWidgets())
        vsplitter.addWidget(self.chooseSpectrum)

        for view in self.tableViews:
            vsplitter.addWidget(view)
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

    def layoutWidgetsAboveTable(self):
        hsplitter = QSplitter()
        hsplitter.setOpaqueResize(False)
        hsplitter.addWidget(self.rt_plotter.widget)

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

        hsplitter.addWidget(self.integrationFrame)
        hsplitter.addWidget(self.mz_plotter.widget)
        return hsplitter

    def layoutToolWidgets(self):
        frame = QFrame()
        layout = QHBoxLayout()
        # layout.setSpacing(10)
        # layout.setMargin(5)
        layout.addWidget(self.chooseGroubLabel, stretch=1, alignment=Qt.AlignLeft)
        layout.addWidget(self.chooseGroupColumn, stretch=1, alignment=Qt.AlignLeft)
        layout.addStretch(10)
        frame.setLayout(layout)
        return frame

    def setupModelDependendLook(self):
        hasFeatures = self.model.hasFeatures()
        isIntegrated = self.model.isIntegrated()
        self.hasFeatures = hasFeatures
        self.isIntegrated = isIntegrated

        self.setWindowTitle(self.model.getTitle())

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

        self.connect(self.reintegrateButton, SIGNAL("clicked()"), self.doIntegrate)
        self.connect(self.chooseSpectrum, SIGNAL("activated(int)"), self.spectrumChosen)

        if self.offerAbortOption:
            self.connect(self.okButton, SIGNAL("clicked()"), self.ok)
            self.connect(self.abortButton, SIGNAL("clicked()"), self.abort)

    @protect_signal_handler
    def handle_double_click(self, idx):
        value = self.model.cell_value(idx)
        insp = inspector(value, modal=False, parent=self)
        if insp is not None:
            insp()

    def disconnectModelSignals(self):
        self.disconnect(self.model, SIGNAL("dataChanged(QModelIndex,QModelIndex,PyQt_PyObject)"),
                        self.dataChanged)
        self.menubar.disconnect(self.undoAction, SIGNAL("triggered()"),
                                protect_signal_handler(self.model.undoLastAction))
        self.menubar.disconnect(self.redoAction, SIGNAL("triggered()"),
                                protect_signal_handler(self.model.redoLastAction))

    def connectModelSignals(self):
        self.connect(self.model, SIGNAL("dataChanged(QModelIndex,QModelIndex,PyQt_PyObject)"),
                     self.dataChanged)
        self.menubar.connect(self.undoAction, SIGNAL("triggered()"),
                             protect_signal_handler(self.model.undoLastAction))
        self.menubar.connect(self.redoAction, SIGNAL("triggered()"),
                             protect_signal_handler(self.model.redoLastAction))

        self.connect(self.chooseGroupColumn, SIGNAL("activated(int)"), self.group_column_selected)

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
            txt = str(action.text())  # QString -> Python str
            if txt.startswith("*"):
                txt = " " + txt[1:]
                action.setText(txt)
            if i == j:
                action.setText("*" + txt[1:])

        for j in range(len(self.models)):
            self.tableViews[j].setVisible(i == j)

        if self.model is not None:
            self.disconnectModelSignals()
        self.model = self.models[i]
        self.tableView = self.tableViews[i]
        self.setupModelDependendLook()
        if self.isIntegrated:
            self.model.setNonEditable("method", ["area", "rmse", "method", "params"])

        for col_name in self.model.table.getColNames():
            t = self.model.table.getColType(col_name)
            if t is object or t is None or has_inspector(t):
                self.model.addNonEditable(col_name)

        self.choosePostfix.clear()
        mod = self.model
        for p in mod.table.supportedPostfixes(mod.integrationColNames()):
            self.choosePostfix.addItem(repr(p))

        if len(self.choosePostfix) == 1:
            self.choosePostfix.setVisible(False)

        self.chooseGroupColumn.clear()
        self.chooseGroupColumn.addItems(["- manual multi select -"] + mod.table.getColNames())

        self.connectModelSignals()
        self.updateMenubar()

    @protect_signal_handler
    def dataChanged(self, ix1, ix2, src):
        minr, maxr = sorted((ix1.row(), ix2.row()))
        minc, maxc = sorted((ix1.column(), ix2.column()))
        for r in range(minr, maxr + 1):
            for c in range(minc, maxc + 1):
                idx = self.model.createIndex(r, c)
                self.tableView.update(idx)

        if self.hasFeatures:
            minr, maxr = sorted((ix1.row(), ix2.row()))
            if any(minr <= index <= maxr for index in self.currentRowIndices):
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
            self.model.removeRow(idx)
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
        for idx in self.currentRowIndices:
            self.model.integrate(postfix, idx, method, rtmin, rtmax)

    @protect_signal_handler
    def rowClicked(self, rowIdx):

        group_by_idx = self.chooseGroupColumn.currentIndex()
        if group_by_idx == 0:
            selected_rows = [idx.row() for idx in self.tableView.selectionModel().selectedRows()]
        else:
            table = self.model.table
            col_name = table.getColNames()[group_by_idx - 1]
            selected_value = table.getValue(table.rows[rowIdx], col_name)
            selected_rows = [i for i in range(len(table))
                             if table.getValue(table.rows[i], col_name) == selected_value]
            selected_rows = selected_rows[:40]  # avoid to many rows

            mode_before = self.tableView.selectionMode()
            scrollbar_before = self.tableView.verticalScrollBar().value()

            self.tableView.setSelectionMode(QAbstractItemView.MultiSelection)
            for i in selected_rows:
                if i != rowIdx:      # avoid "double click !" wich de-selects current row
                    self.tableView.selectRow(i)
            self.tableView.setSelectionMode(mode_before)
            self.tableView.verticalScrollBar().setValue(scrollbar_before)
        if not self.hasFeatures:
            return

        self.currentRowIndices = selected_rows
        self.rt_plotter.setEnabled(True)
        self.updatePlots(reset=True)
        if self.hasFeatures:
            self.setupSpectrumChooser()

    def setupSpectrumChooser(self):
        # delete QComboBox:
        while self.chooseSpectrum.count():
            self.chooseSpectrum.removeItem(0)

        postfixes, spectra = [], []
        for idx in self.currentRowIndices:
            pf, s = self.model.getLevelNSpectra(idx, minLevel=2)
            postfixes.extend(pf)
            spectra.extend(s)

        # get current spectra
        # jjrowidx = self.currentRowIdx
        # postfixes, spectra = self.model.getLevelNSpectra(rowidx, minLevel=2)
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
        for idx in self.currentRowIndices:
            eics, mzmin, mzmax, rtmin, rtmax, allrts = self.model.getEics(idx)
            mzmins.append(mzmin)
            rtmins.append(rtmin)
            mzmaxs.append(mzmax)
            rtmaxs.append(rtmax)
            curves.extend(eics)
            if self.isIntegrated:
                smootheds = self.model.getSmoothedEics(idx, allrts)
                if smootheds is not None:
                    smoothed_curves.extend(smootheds)

        rtmin = min(rtmins)
        rtmax = max(rtmaxs)
        mzmin = min(mzmins)
        mzmax = max(mzmaxs)

        if not reset:
            rtmin, rtmax = self.rt_plotter.getRangeSelectionLimits()
            xmin, xmax, ymin, ymax = self.rt_plotter.getLimits()

        configs = configsForEics(curves)
        curves += smoothed_curves
        configs += configsForSmootheds(smoothed_curves)

        self.rt_plotter.plot(curves, configs=configs, titles=None, withmarker=True)

        # allrts are sorted !
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
        peakmaps = [pm for idx in self.currentRowIndices for pm in self.model.getPeakmaps(idx)]
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
        self.mz_plotter.plot(data, configs, titles if len(titles) > 1 else None)

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
    else:
        explorer.show()
    # partial cleanup
    del explorer.models
    if offerAbortOption:
        if explorer.result == 1:
            raise Exception("Dialog aborted by user")
