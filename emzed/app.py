
import pkg_resources
import sys
reload(pkg_resources)  # migh be loaded already and is not up to date

_loaded = []

for _ep in pkg_resources.iter_entry_points("emzed_package", name="main"):
    try:
        _runner = _ep.load()
    except:
        del _ep
        import traceback
        traceback.print_exc()
        continue

    _loaded.append(_ep.module_name)
    _name = _ep.module_name.split(".")[0]
    #print "$$$ loaded emzed.app.%s from %s " % (_name, _runner)
    exec "%s=_runner" % _name
    sys.modules["emzed.app.%s" % _name] = _runner
    del _ep
    del _runner
    del _name

if _loaded:
    print
    print "LOADED EMZED APPLICATIONS: ".ljust(80, "-")
    print
    for l in _loaded:
        print "loaded", l
    print
    print "-" * 80

del pkg_resources
del sys

