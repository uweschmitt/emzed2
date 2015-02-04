import pdb
import os.path

import numpy as np
import cPickle

import emzed.utils as utils
import emzed.io as io
import emzed._algorithm_configs
from  emzed.core.data_types import Spectrum, PeakMap
from  emzed.core.peak_integration import *


def _compare_tables(t1, t2):
    t1.sortBy("id")
    t2.sortBy("id")

    assert len(t1) == len(t2)
    assert t1.getColNames() == t2.getColNames()
    assert t1.getColTypes() == t2.getColTypes()
    assert t1.getColFormats() == t2.getColFormats()
    assert len(t1.rows) == len(t2.rows)
    assert t1.area.values == t2.area.values
    assert t1.method.values == t2.method.values
    assert t1.rmse.values == t2.rmse.values
    for v1, v2 in zip(t1.params.values, t2.params.values):
        assert cPickle.dumps(v1) == cPickle.dumps(v2)


def testIntegration(path):

    for integrator_id in ("trapez", "max", "emg_exact"):
        t1 = _testIntegration(path, 1, integrator_id, check_values=True)
        t2 = _testIntegration(path, 2, integrator_id, check_values=True)

        _compare_tables(t1, t2)

        t3 = _testIntegration(path, 4, integrator_id, check_values=True)
        _compare_tables(t1, t3)

    t1 = _testIntegration(path, 1, "no_integration", check_values=False)
    t2 = _testIntegration(path, 2, "no_integration", check_values=False)

    _compare_tables(t1, t2)

    t3 = _testIntegration(path, 4, "no_integration", check_values=False)
    _compare_tables(t1, t3)


def _testIntegration(path, n_cpus, integrator_id, check_values=True):

    # test with and without unicode:
    ft = io.loadTable(path("data/features.table"))
    # an invalid row should not stop integration, but result
    # in None values for emzed.utils.integrate generated columns
    ftr = utils.integrate(ft, integrator_id,  n_cpus=n_cpus, min_size_for_parallel_execution=1)
    assert len(ftr) == len(ft)
    assert "area" in ftr.getColNames()
    assert "rmse" in ftr.getColNames()

    if check_values:
        assert ftr.area.values[0] >= 0, ftr.area.values[0]
        assert ftr.rmse.values[0] >= 0, ftr.rmse.values[0]
        assert ftr.params.values[0] is not None
        assert ftr.method.values[0] is not None

    ft.setValue(ft.rows[0], "mzmin", None)

    ft._addColumnWithoutNameCheck("mzmin__0", ft.mzmin)
    ft._addColumnWithoutNameCheck("mzmax__0", ft.mzmax)
    ft._addColumnWithoutNameCheck("rtmin__0", ft.rtmin)
    ft._addColumnWithoutNameCheck("rtmax__0", ft.rtmax)
    ft._addColumnWithoutNameCheck("peakmap__0", ft.peakmap)

    ft.addColumn("mzminX", ft.mzmin)
    ft.addColumn("mzmaxX", ft.mzmax)
    ft.addColumn("rtminX", ft.rtmin)
    ft.addColumn("rtmaxX", ft.rtmax)
    ft.addColumn("peakmapX", ft.peakmap)

    ftr = utils.integrate(ft, integrator_id,  n_cpus=n_cpus, min_size_for_parallel_execution=1)
    assert len(ftr) == len(ft)
    assert "area" in ftr.getColNames()
    assert "rmse" in ftr.getColNames()
    assert "eic" in ftr.getColNames()
    assert "area__0" in ftr.getColNames()
    assert "rmse__0" in ftr.getColNames()
    assert "eic__0" in ftr.getColNames()
    assert "areaX" in ftr.getColNames()
    assert "rmseX" in ftr.getColNames()
    assert "rmseX" in ftr.getColNames()
    assert "eicX" in ftr.getColNames()

    if check_values:
        assert ftr.area.values[0] is None
        assert ftr.rmse.values[0] is None
        assert ftr.params.values[0] is None
        assert ftr.method.values[0] is not None
        assert ftr.eic.values[0] is None

        assert ftr.area.values[1] >= 0
        assert ftr.rmse.values[1] >= 0
        assert ftr.params.values[1] is not None
        assert ftr.method.values[1] is not None
        assert len(ftr.eic.values[1]) == 2

        assert ftr.area__0.values[0] is None
        assert ftr.rmse__0.values[0] is None
        assert ftr.params__0.values[0] is None
        assert ftr.method__0.values[0] is not None
        assert ftr.eic__0.values[0] is None

        assert ftr.area__0.values[1] >= 0
        assert ftr.rmse__0.values[1] >= 0
        assert ftr.params__0.values[1] is not None
        assert ftr.method__0.values[1] is not None
        assert len(ftr.eic__0.values[1]) == 2

        assert ftr.areaX.values[0] is None
        assert ftr.rmseX.values[0] is None
        assert ftr.paramsX.values[0] is None
        assert ftr.methodX.values[0] is not None
        assert ftr.eicX.values[0] is None

        assert ftr.areaX.values[1] >= 0
        assert ftr.rmseX.values[1] >= 0
        assert ftr.paramsX.values[1] is not None
        assert ftr.methodX.values[1] is not None
        assert len(ftr.eicX.values[1]) == 2

    # test with empty chromatograms
    s0 = ft.peakmap.values[0].spectra[0]
    rt0 = s0.rt
    pm = PeakMap([s0])
    rts, iis = pm.chromatogram(0, 10000, rt0 + 20, rt0 + 30)
    assert len(rts) == 0
    assert len(iis) == 0
    ft.replaceColumn("peakmap", pm)
    ft.replaceColumn("rtmin", rt0 + 10)
    ft.replaceColumn("rtmax", rt0 + 20)
    ftr2 = utils.integrate(ft, integrator_id,  n_cpus=n_cpus, min_size_for_parallel_execution=1)

    assert  set(ftr2.eic.values) == {None}

    return ftr



def run(integrator, areatobe, rmsetobe, eicareatobe):
    assert len(str(integrator))>0

    try:
        ds = run.ds
    except:
        here = os.path.dirname(os.path.abspath(__file__))
        ds = run.ds =  io.loadPeakMap(os.path.join(here, "data", "SHORT_MS2_FILE.mzData"))

    integrator.setPeakMap(ds)

    rtmin = ds.spectra[0].rt
    rtmax = ds.spectra[30].rt

    mzmin = ds.spectra[0].peaks[10,0]
    mzmax = ds.spectra[0].peaks[-10,0]

    result = integrator.integrate(mzmin, mzmax, rtmin, rtmax, 1)
    area=result.get("area")
    rmse=result.get("rmse")

    print "area: is=%e  tobe=%e" % (area, areatobe)
    print "rmse: is=%e  tobe=%e" % (rmse, rmsetobe)


    if area > 0:
        assert abs(area-areatobe)/areatobe < .01,  area
    else:
        assert area == 0.0, area
    if rmsetobe > 0:
        assert abs(rmse-rmsetobe)/rmsetobe < .01,  rmse
    else:
        assert rmse == 0.0, rmse

    params = result.get("params")

    x, y = result.get("eic")
    eicarea = 0.5 * np.dot(x[1:] - x[:-1], y[1:] + y[:-1])

    if eicarea > 0:
        assert abs(eicarea - eicareatobe)/ eicareatobe < 0.01, eicarea
    else:
        assert eicarea == 0.0, eicarea


def testNoIntegration():

    integrator = dict(emzed._algorithm_configs.peakIntegrators)["no_integration"]
    integrator.setPeakMap(PeakMap([]))
    result = integrator.integrate(0.0, 100.0, 0, 300, 1)
    assert result.get("area") is None
    assert result.get("rmse") is None
    assert result.get("params") is None
    assert result.get("eic") is None

    rts = range(0, 600)
    x,y = integrator.getSmoothed(rts, result.get("params"))
    assert x==[]
    assert y==[]


def testPeakIntegration():

    integrator = dict(emzed._algorithm_configs.peakIntegrators)["asym_gauss"]
    run(integrator, 1.19e5, 7.2891e3, 139984.31911294549)

    integrator = dict(emzed._algorithm_configs.peakIntegrators)["emg_exact"]

    run(integrator,  154542.79, 7.43274e3, 139984.31911294549)

    integrator = dict(emzed._algorithm_configs.peakIntegrators)["trapez"]

    run(integrator,  120481.9, 0.0, 139984.31911294549)

    integrator = dict(emzed._algorithm_configs.peakIntegrators)["std"]
    run(integrator,  119149.7, 6854.8, 139984.31911294549)

    integrator = dict(emzed._algorithm_configs.peakIntegrators)["max"]
    run(integrator,  37620.81, 0.0, 139984.31911294549)


def testTrapezIntegrationSimple():

    p0 = np.array((1.0, 1.0, 2.0, 2.0)).reshape(-1,2)
    p1 = np.array((2.0, 2.0, 3.0, 3.0)).reshape(-1,2)
    p2 = np.array((1.0, 1.0, 2.0, 2.0, 3.0, 3.0)).reshape(-1,2)
    p3 = np.array((3.0, 3.0)).reshape(-1,2)

    s0 = Spectrum(p0, 0.0, 1, '0')
    s1 = Spectrum(p1, 1.0, 1, '0')
    s2 = Spectrum(p2, 2.0, 1, '0')
    s3 = Spectrum(p3, 3.0, 1, '0')

    pm = PeakMap([s0,s1,s2,s3])

    integrator = dict(emzed._algorithm_configs.peakIntegrators)["trapez"]
    integrator.setPeakMap(pm)

    assert integrator.integrate(1.4, 2.5, 0, 3)["area"] == 5.0
    assert integrator.integrate(1.4, 2.5, 0, 2)["area"] == 4.0

    assert integrator.integrate(0.4, 2.5, 0, 3)["area"] == 6.5
    assert integrator.integrate(0.4, 2.5, 0, 2)["area"] == 5.0

    assert integrator.integrate(0.4, 3.0, 0, 3)["area"] == 14


    # one level 2 spec:
    s1 = Spectrum(p1, 1.0, 2, '0')
    pm = PeakMap([s0,s1,s2,s3])
    integrator.setPeakMap(pm)

    assert integrator.integrate(1.4, 2.5, 0, 3, msLevel=1)["area"] == 5.0
    assert integrator.integrate(1.4, 2.5, 0, 2, msLevel=1)["area"] == 4.0

    assert integrator.integrate(0.4, 2.5, 0, 3, msLevel=1)["area"] == 7.5
    assert integrator.integrate(0.4, 2.5, 0, 2, msLevel=1)["area"] == 6.0

    assert integrator.integrate(0.4, 3.0, 0, 3, msLevel=1)["area"] == 13.5

    # multiple levels shall rise exception:
    ex(lambda: integrator.integrate(0.4, 3.0, 0, 3))


def ex(f):
    e0 = None
    try:
        f()
    except Exception, e:
        e0 = e
    assert e0 is not None

def testSg():
    allrts = np.arange(10, 100)
    rts    = np.arange(1, 10)
    chromo = np.sin(allrts)
    chromo[10:]= 0

    ex(lambda: SGIntegrator(order=1, window_size=4).smooth(allrts, rts, chromo))
    ex(lambda: SGIntegrator(order=1, window_size=-1).smooth(allrts, rts, chromo))
    ex(lambda: SGIntegrator(order=4, window_size=5).smooth(allrts, rts, chromo))
