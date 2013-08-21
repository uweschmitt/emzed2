# -*- coding: utf-8 -*-

from PyQt4.QtGui import  *
from PyQt4.QtCore import *

import guidata

from plotting_widgets import RtPlotter, MzPlotter

from ..data_types import Table

from table_explorer_model import *

from helpers import protect_signal_handler

def getColors(i, light=False):
     colors = [(0, 0, 200), (70, 70, 70), (0,150,0),
                (200, 0, 0), (200, 200, 0), (100, 70, 0)]
     c = colors[i % len(colors)]
     if light:
         c = tuple([min(i+50,  255) for i in c])

     # create hex string  "#rrggbb":
     return "#"+"".join( "%02x" % v  for v in c)

def configsForEics(eics):
    n = len(eics)
    return [dict(linewidth=1.5, color=getColors(i)) for i in range(n)]

def configsForSmootheds(smootheds):
    n = len(smootheds)
    return [dict(shade=0.35, linestyle="NoPen",
                 color=getColors(i, light=True)) for i in range(n)]

def configsForSpectra(spectra):
    return [dict(color=getColors(i), linewidth=1)\
                                      for i in range(len(spectra))]
class TableExplorer(QDialog):

    def __init__(self, tables, offerAbortOption):
        QDialog.__init__(self)

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

        self.currentRowIdx = -1
        self.hadFeatures = None
        self.wasIntegrated = None

        self.setupWidgets()
        self.setupLayout()
        self.connectSignals()

        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setSizePolicy(sizePolicy)
        self.setSizeGripEnabled(True)

        self.setupViewForTable(0)

    def setupWidgets(self):
        self.setupMenuBar()
        self.setupTableViews()
        self.setupPlottingWidgets()
        self.chooseSpectrum = QComboBox()
        self.setupIntegrationWidgets()
        if self.offerAbortOption:
            self.setupAcceptButtons()

    def setupMenuBar(self):
        self.menubar = QMenuBar(self)
        menu = self.buildEditMenu()
        self.menubar.addMenu(menu)
        self.chooseTableActions = []
        if len(self.models)>1:
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
        tableView = QTableView(self)

        @protect_signal_handler
        def handler(evt, view=tableView, model=model, self=self):
            if not view.isSortingEnabled():
                view.setSortingEnabled(True)
                view.resizeColumnsToContents()
                model.emptyActionStack()
                self.updateMenubar()
        tableView.showEvent = handler

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
            action = QAction(" [%d]: %s" % (i,model.getTitle()), self)
            menu.addAction(action)
            self.chooseTableActions.append(action)
        return menu

    def setupPlottingWidgets(self):
        self.plotconfigs = (None, dict(shade=0.35, linewidth=1, color="g") )
        self.rtPlotter = RtPlotter(rangeSelectionCallback=self.plotMz)
        self.rtPlotter.setMinimumSize(300, 100)
        self.mzPlotter = MzPlotter()
        self.mzPlotter.setMinimumSize(300, 100)
        pol = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        pol.setVerticalStretch(5)
        self.rtPlotter.widget.setSizePolicy(pol)
        self.mzPlotter.widget.setSizePolicy(pol)

    def setupIntegrationWidgets(self):
        self.intLabel = QLabel("Integration")
        self.chooseIntMethod = QComboBox()
        import algorithm_configs
        for name, _ in algorithm_configs.peakIntegrators:
            self.chooseIntMethod.addItem(name)

        self.choosePostfix = QComboBox()

        self.reintegrateButton = QPushButton()
        self.reintegrateButton.setText("Integrate")

    def setupAcceptButtons(self):
        self.okButton = QPushButton("Ok")
        self.abortButton = QPushButton("Abort")
        self.result = 1 # default for closing

    def setupLayout(self):
        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        vsplitter = QSplitter()
        vsplitter.setOrientation(Qt.Vertical)
        vsplitter.setOpaqueResize(False)

        vsplitter.addWidget(self.menubar)
        vsplitter.addWidget(self.layoutWidgetsAboveTable())
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
        hsplitter.addWidget(self.rtPlotter.widget)

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
        hsplitter.addWidget(self.mzPlotter.widget)
        return hsplitter

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
            self.rtPlotter.setEnabled(True)
            self.resetPlots()

    def setPlotVisibility(self, doShow):
        self.rtPlotter.widget.setVisible(doShow)
        self.mzPlotter.widget.setVisible(doShow)

    def resetPlots(self):
        self.rtPlotter.reset()
        self.mzPlotter.reset()

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
            self.connect(vh, SIGNAL("customContextMenuRequested(QPoint)"),\
                         self.openContextMenu)

            self.connect(vh, SIGNAL("sectionClicked(int)"), self.rowClicked)

            model = view.model()
            handler = lambda idx, model=model: self.handleClick(idx, model)
            handler = protect_signal_handler(handler)
            self.connect(view, SIGNAL("clicked(QModelIndex)"), handler)

        self.connect(self.reintegrateButton, SIGNAL("clicked()"),
                     self.doIntegrate)

        self.connect(self.chooseSpectrum, SIGNAL("activated(int)"),
                     self.spectrumChosen)

        if self.offerAbortOption:
            self.connect(self.okButton, SIGNAL("clicked()"), self.ok)
            self.connect(self.abortButton, SIGNAL("clicked()"), self.abort)

    def disconnectModelSignals(self):
        self.disconnect(self.model,
                   SIGNAL("dataChanged(QModelIndex,QModelIndex,PyQt_PyObject)"),
                   self.dataChanged)
        self.menubar.disconnect(self.undoAction, SIGNAL("triggered()"),\
                             protect_signal_handler(self.model.undoLastAction))
        self.menubar.disconnect(self.redoAction, SIGNAL("triggered()"),\
                             protect_signal_handler(self.model.redoLastAction))

    def connectModelSignals(self):
        self.connect(self.model,
                   SIGNAL("dataChanged(QModelIndex,QModelIndex,PyQt_PyObject)"),
                   self.dataChanged)
        self.menubar.connect(self.undoAction, SIGNAL("triggered()"),\
                             protect_signal_handler(self.model.undoLastAction))
        self.menubar.connect(self.redoAction, SIGNAL("triggered()"),\
                             protect_signal_handler(self.model.redoLastAction))

    def updateMenubar(self):
        undoInfo = self.model.infoLastAction()
        redoInfo = self.model.infoRedoAction()
        self.undoAction.setEnabled(undoInfo != None)
        self.redoAction.setEnabled(redoInfo != None)
        if undoInfo:
            self.undoAction.setText("Undo: %s" % undoInfo)
        if redoInfo:
            self.redoAction.setText("Redo: %s" % redoInfo)

    def setupViewForTable(self, i):
        for j, action in enumerate(self.chooseTableActions):
            txt = str(action.text()) # QString -> Python str
            if txt.startswith("*"):
                txt = " "+txt[1:]
                action.setText(txt)
            if i==j:
                action.setText("*"+txt[1:])

        for j in range(len(self.models)):
            self.tableViews[j].setVisible(i==j)

        if self.model is not None:
            self.disconnectModelSignals()
        self.model = self.models[i]
        self.tableView = self.tableViews[i]
        self.setupModelDependendLook()
        if self.isIntegrated:
            self.model.setNonEditable("method", ["area", "rmse", "method",\
                                                 "params"])
        self.choosePostfix.clear()
        mod = self.model
        for p in mod.table.supportedPostfixes(mod.integrationColNames()):
            self.choosePostfix.addItem(repr(p))

        if len(self.choosePostfix) == 1:
            self.choosePostfix.setVisible(False)

        self.connectModelSignals()
        self.updateMenubar()

    @protect_signal_handler
    def dataChanged(self, ix1, ix2, src):
        minr, maxr = sorted((ix1.row(), ix2.row()))
        minc, maxc = sorted((ix1.column(), ix2.column()))
        for r in range(minr, maxr+1):
            for c in range(minc, maxc+1):
                idx = self.model.createIndex(r, c)
                self.tableView.update(idx)

        if self.hasFeatures:
            minr, maxr = sorted((ix1.row(), ix2.row()))
            if minr <= self.currentRowIdx <= maxr:
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
        if self.currentRowIdx < 0:
            return # no row selected

        # QString -> Python str:
        method = str(self.chooseIntMethod.currentText())
        # Again QString -> Python str.
        # For better readibilty we put single quotes around the postfix
        # entry in the QComboBox which we have to remove now:
        postfix = str(self.choosePostfix.currentText()).strip("'")
        rtmin, rtmax = self.rtPlotter.getRangeSelectionLimits()
        self.model.integrate(postfix, self.currentRowIdx, method, rtmin, rtmax)

    @protect_signal_handler
    def rowClicked(self, rowIdx):
        if not self.hasFeatures:
            return
        self.currentRowIdx = rowIdx
        self.rtPlotter.setEnabled(True)
        self.updatePlots(reset=True)
        if self.hasFeatures:
            self.setupSpectrumChooser()


    def setupSpectrumChooser(self):
        # delete QComboBox:
        while self.chooseSpectrum.count():
            self.chooseSpectrum.removeItem(0)

        # get current spectra
        rowidx = self.currentRowIdx
        postfixes, spectra = self.model.getLevelNSpectra(rowidx, minLevel=2)
        self.currentLevelNSpecs = []

        if not len(spectra):
            self.chooseSpectrum.setVisible(False)
            return

        self.chooseSpectrum.setVisible(True)
        self.chooseSpectrum.addItem("Show only Level 1 spectra")
        for postfix, s in zip(postfixes, spectra):
            if postfix != "":
                txt = postfix+", "
            else:
                txt = ""
            txt += "rt=%.2fm, level=%d" % (s.rt/60.0, s.msLevel)
            mzs = [ mz for (mz, I) in s.precursors ]
            precursors = ", ".join("%.6f" % mz for mz in mzs)
            if precursors:
                txt += ", precursor mzs=[%s]" % precursors
            self.chooseSpectrum.addItem(txt)
            self.currentLevelNSpecs.append(s)

    def updatePlots(self, reset=False):
        rowIdx = self.currentRowIdx
        eics, mzmin, mzmax, rtmin, rtmax, allrts = self.model.getEics(rowIdx)

        curves = eics
        configs = configsForEics(eics)
        if self.isIntegrated:
            smootheds = self.model.getSmoothedEics(rowIdx, allrts)
            if smootheds is not None:
                curves += smootheds
                configs += configsForSmootheds(smootheds)

        if not reset:
            rtmin, rtmax = self.rtPlotter.getRangeSelectionLimits()
            xmin, xmax, ymin, ymax = self.rtPlotter.getLimits()

        self.rtPlotter.plot(curves, configs=configs, titles=None,
                            withmarker=True)

        # allrts are sorted !
        w = rtmax - rtmin
        if w == 0:
            w = 30.0 # seconds
        self.rtPlotter.setRangeSelectionLimits(rtmin, rtmax)
        self.rtPlotter.setXAxisLimits(rtmin -w, rtmax + w)
        self.rtPlotter.replot()
        if not reset:
            self.rtPlotter.setXAxisLimits(xmin, xmax)
            self.rtPlotter.setYAxisLimits(ymin, ymax)
            self.rtPlotter.updateAxes()

        reset = reset and mzmin is not None and mzmax is not None
        limits = (mzmin, mzmax) if reset else None
        self.plotMz(resetLimits=limits)

    @protect_signal_handler
    def spectrumChosen(self, idx):
        if idx==0:
            self.rtPlotter.setEnabled(True)
            self.chooseIntMethod.setEnabled(True)
            self.reintegrateButton.setEnabled(True)
            self.plotMz()
        else:
            self.rtPlotter.setEnabled(False)
            self.chooseIntMethod.setEnabled(False)
            self.reintegrateButton.setEnabled(False)
            self.mzPlotter.plot([self.currentLevelNSpecs[idx-1].peaks])
            self.mzPlotter.resetAxes()
            self.mzPlotter.replot()

    def plotMz(self, resetLimits=None):
        """ this one is used from updatePlots and the rangeselectors
            callback """
        rtmin=self.rtPlotter.minRTRangeSelected
        rtmax=self.rtPlotter.maxRTRangeSelected

        # get spectra for current row in given rt-range:
        peakmaps = self.model.getPeakmaps(self.currentRowIdx)

        peaks = [pm.getDominatingPeakmap().ms1Peaks(rtmin, rtmax) for pm in peakmaps]

        # plot peaks
        configs = configsForSpectra(peaks)
        postfixes = self.model.table.supportedPostfixes(self.model.eicColNames())
        titles = map(repr, postfixes)
        self.mzPlotter.plot(peaks, configs, titles if len(titles)>1 else None)

        if resetLimits:
            mzmin, mzmax = resetLimits
            Imaxes = []
            for p  in peaks:
                imin = p[:,0].searchsorted(mzmin)
                imax = p[:,0].searchsorted(mzmax, side='right')
                found = p[imin:imax,1]
                if len(found):
                    Imaxes.append(found.max())

            if len(Imaxes) == 0:
                Imax = 1.0
            else:
                Imax = max(Imaxes) * 1.2
            self.mzPlotter.setXAxisLimits(mzmin, mzmax)
            self.mzPlotter.reset_y_limits(0, Imax)
        # plot() needs replot() afterwards !
        self.mzPlotter.replot()

def inspect(what, offerAbortOption=False):
    """
    allows the inspection and editing of simple or multiple
    tables.

    """
    if isinstance(what, Table):
        what = [what]
    app = guidata.qapplication() # singleton !
    explorer = TableExplorer(what, offerAbortOption)
    explorer.raise_()
    explorer.exec_()
    # partial cleanup
    del explorer.models
    if offerAbortOption:
        if explorer.result == 1:
            raise Exception("Dialog aborted by user")
