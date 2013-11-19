# encoding: utf-8

import numpy as _np


def _findMzMatches(hypot, table, tol):
    rtfit = table.rt.inRange(hypot.rtmin, hypot.rtmax)
    mzfit = table.mz.approxEqual(hypot.mz_hypot, tol)
    matched = table.join(hypot, rtfit & mzfit)
    print len(matched), "MATCHED UNIV METABOLITES"
    matched = matched.extractColumns("mz", "mz_hypot__0", "rt", "rtmin__0", "rtmax__0",
                                     "name__0", "polarity__0")
    matched.renameColumns(mz_hypot__0="mz_exact", rtmin__0="rtmin",
                          rtmax__0="rtmax", name__0="name", polarity__0="polarity")
    matched.sortBy("mz")
    real = _np.array(matched.mz.values)
    tobe = _np.array(matched.mz_exact.values)
    return real, tobe, matched


def _fitLp(A, b, p, N=10):
    """ IRLS iterations:  for minimizing ||Ax-b||_p

        iterative weighting maxtrix is

                 w_ii = resid_i^[(p-2)/2
    """
    # we do not need to store full diagonal matrix, just its entries:
    W = _np.ones(len(b))
    lastParam = None
    for i in range(N):  # 2 iterations seem to be enough
        WA = (A.T * W).T   # calculates np.dot(np.diag(W), A)
        Wb = W * b         # calculates np.dot(np.diag(W), b).flatten()
        param, _, _, _ = _np.linalg.lstsq(WA, Wb)
        resid = _np.abs(_np.dot(A, param) - b)
        W = (1e-8 + resid) ** (p - 2.0) / 2.0
        if lastParam is None:
            lastParam = param
        else:
            delta = _np.linalg.norm(param - lastParam) / _np.linalg.norm(lastParam)
            lastParam = param
            if delta < 1e-3:
                break
    else:
        print "WARNING: IRLS did not converge within %d iterations" % N

    return param


def _removeValue(vec, idx):
    return _np.hstack((vec[:idx], vec[idx + 1:]))


def _findParametersAutomatically(tobe, real, minR2, maxTol, minPoints):
    while len(real) >= minPoints:
        transform, r2, imax, _, resid = _calculateParameters(real, tobe)
        print "NUMPOINTS=%3d  goodness=%.3f" % (len(real), r2)
        if r2 >= minR2 or max(resid) <= maxTol:
            break
        # remove match which fits worst:
        real = _removeValue(real, imax)
        tobe = _removeValue(tobe, imax)
    else:
        raise Exception("could only reach R^2=%f" % r2)

    return transform, (real, tobe)


def _calculateParameters(real, tobe, p=1.01):
    # robust fit real vs (tobe-real) with p < 2
    A = _np.ones((len(real), 2))
    A[:, 0] = real
    shifts = tobe - real
    (a, b) = _fitLp(A, shifts, p)
    fittedShift = a * real + b
    resid = _np.abs(fittedShift - shifts.flatten())
    # replacement for perason r in case of m-estimators:
    nom = _np.linalg.norm(fittedShift - shifts, ord=p)
    denom = _np.linalg.norm(shifts - _np.median(shifts), ord=p)
    r = 1.0 - nom / denom
    imax = _np.argmax(resid)
#    valmax = resid[imax]
    fitted = fittedShift + real
    a = float(a)
    b = float(b)
    transform = lambda x: a * x + b + x
    return transform, r, imax, fitted, resid


def _plotAndSaveMatch(tobe, real, used, transform, path):
    import matplotlib
    matplotlib.use("Agg")
    import pylab
    fitted = transform(real)
    pylab.subplot(2, 1, 1)
    pylab.title("$mz$ vs $\Delta mz$")
    pylab.plot(real, tobe - real, "ro")
    pylab.plot(real, fitted - real)
    # pylab.subplot(2,1,1)
    realUsed, tobeUsed = used
    fittedUsed = transform(realUsed)
    pylab.plot(realUsed, tobeUsed - realUsed, "go")
    pylab.gca().set_xlabel("$mz$")
    pylab.gca().set_ylabel("$\Delta mz$")

    pylab.subplot(2, 1, 2)
    pylab.plot([_np.min(real), _np.max(real)], [0, 0])
    pylab.title("$residuals$")
    for (rr, rs) in zip(real, tobe - fitted):
        pylab.plot([rr, rr], [0, rs], "b")
    pylab.plot(real, tobe - fitted, "ro")
    # pylab.subplot(2,1,2)
    pylab.plot(realUsed, tobeUsed - fittedUsed, "go")
    pylab.gca().set_xlabel("$mz$")

    pylab.gca().set_ylabel("$\Delta mz$")
    pylab.tight_layout()

    pylab.savefig(path)
    pylab.close()

from PyQt4.QtCore import *
from PyQt4.QtGui import *


class _MatchSelector(QDialog):

    activeColor = "r"
    inactiveColor = "b"

    def __init__(self, tobe, real):
        QDialog.__init__(self)
        self.setWindowFlags(Qt.Window)
        self.setWindowTitle("Matched Feature Selector")
        self.real = _np.array(real)
        self.tobe = _np.array(tobe)
        self.savedReal = self.real.copy()
        self.savedTobe = self.tobe.copy()
        self.exitCode = 1  # abort is default for closing
        self.setupMainFrame()
        self.indexOfActivePoint = -1
        self.update()
        self.onDraw()

    def onPick(self, event):
        # do not delete point if only two are left, fitting a line to
        # one point does not make sense
        if len(self.real) <= 2:
            return

        pointIndex = event.ind[0]
        self.real = _removeValue(self.real, pointIndex)
        self.tobe = _removeValue(self.tobe, pointIndex)
        self.indexOfActivePoint = -1
        self.update()
        self.onDraw()

    def update(self):
        transform, r2, imax, fitted, resid = _calculateParameters(self.real,
                                                                  self.tobe)
        self.fitted = fitted
        self.r2 = r2
        self.transform = transform

    def reset(self):
        self.real = self.savedReal.copy()
        self.tobe = self.savedTobe.copy()
        self.update()
        self.onDraw()

    def onDraw(self):
        """ Redraws the figure
        """

        self.upper.clear()
        self.lower.clear()

        self.upper.grid(True)
        self.lower.grid(False)

        real = self.real
        tobe = self.tobe
        fitted = self.fitted

        title = "$R^2$ = %.3f" % self.r2
        self.upper.set_title(title)

        self.upper.plot(real, tobe - real, "o", picker=5,
                        color=self.inactiveColor)
        self.upper.plot(real, fitted - real)

        self.lower.plot([_np.min(real), _np.max(real)], [0, 0])
        for (rr, rs) in zip(real, tobe - fitted):
            self.lower.plot([rr, rr], [0, abs(rs)], "b")
        self.lower.plot(real, _np.abs(tobe - fitted), "o")
        self.canvas.draw()

    def finish(self):
        self.exitCode = 0
        self.close()

    def abort(self):
        self.exitCode = 1
        self.close()

    def onMove(self, evt):
        if not evt.inaxes is self.upper:
            return

        pts = _np.array([(x, y - x) for x, y in zip(self.real, self.tobe)])
        maxvals = _np.max(pts, axis=0)  # max along vertical axis
        minvals = _np.min(pts, axis=0)  # min alogn vertical axis
        range_ = maxvals - minvals    # is now of shape (1,2)

        # mouse coordinates in coordinates in respect of plotted data:
        x = evt.xdata
        y = evt.ydata
        # we have to scale distances, due to different ranges on x and y
        # axis:
        range_ += 1 - 6  # avoids zero division in next step
        distmatrix = (pts - _np.array((x, y))) / range_

        # find next point in plot:
        distances = _np.sqrt(_np.sum(distmatrix ** 2, axis=1))
        i = _np.argmin(distances)
        bestdist = distances[i]

        def deactivatePoint(x, y):
            self.upper.plot(x, y - x, "o", color=self.inactiveColor)
            self.canvas.draw()
            self.indexOfActivePoint = -1

        def activatePoint(x, y):
            self.upper.plot(x, y - x, "o", color=self.activeColor)
            self.canvas.draw()

        if bestdist > 0.15:  # no point in neighbourhood of mouse cursor
            if self.indexOfActivePoint > -1:
                x = self.real[self.indexOfActivePoint]
                y = self.tobe[self.indexOfActivePoint]
                deactivatePoint(x, y)
        elif i != self.indexOfActivePoint and bestdist <= 0.15:
            if self.indexOfActivePoint > -1:
                x = self.real[self.indexOfActivePoint]
                y = self.tobe[self.indexOfActivePoint]
                deactivatePoint(x, y)
            x = self.real[i]
            y = self.tobe[i]
            activatePoint(x, y)
            self.indexOfActivePoint = i

    def setupMainFrame(self):
        from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
        from matplotlib.figure import Figure

        # self.mainFrame = QWidget()
        # plot widget
        self.dpi = 80
        self.fig = Figure((8.0, 6.0), dpi=self.dpi)
        self.canvas = FigureCanvasQTAgg(self.fig)
        # self.canvas.setParent(self.mainFrame)
        self.upper = self.fig.add_subplot(211)
        self.lower = self.fig.add_subplot(212)

        # buttons
        self.abortButton = QPushButton("Abort")
        self.finishButton = QPushButton("Ok")
        self.resetButton = QPushButton("Start again")

        # connect signals
        self.canvas.mpl_connect('pick_event', self.onPick)
        # self.canvas.mpl_connect('motion_notify_event', self.onMove)
        self.connect(self.abortButton, SIGNAL('clicked()'), self.abort)
        self.connect(self.finishButton, SIGNAL('clicked()'), self.finish)
        self.connect(self.resetButton, SIGNAL('clicked()'), self.reset)

        # layout
        hbox = QHBoxLayout()

        for w in [self.abortButton, self.finishButton, self.resetButton]:
            hbox.addWidget(w)
            hbox.setAlignment(w, Qt.AlignVCenter)

        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addLayout(hbox)

        self.setLayout(vbox)
        # self.setCentralWidget(self.mainFrame)


def _findParametersManually(tobe, real):
    m = _MatchSelector(tobe, real)
    m.raise_()
    m.exec_()
    if m.exitCode != 0:
        return None, None
    return m.transform, (m.real, m.tobe)


def _applyTransform(table, transform):
    import copy
    # as we modify peakmaps below we need a real deepcopy here:
    table = copy.deepcopy(table)
    table.replaceColumn("mz", table.mz.apply(transform))
    table.replaceColumn("mzmin", table.mzmin.apply(transform))
    table.replaceColumn("mzmax", table.mzmax.apply(transform))

    peakmaps = set(table.peakmap.values)
    assert len(peakmaps) == 1, "can only align features from one single peakmap"
    peakmap = peakmaps.pop()
    for spec in peakmap.spectra:
        spec.peaks[:, 0] = transform(spec.peaks[:, 0])
    table.replaceColumn("peakmap", peakmap)
    table.meta["mz_aligned"] = True
    return table
