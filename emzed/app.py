
import pkg_resources
import sys
reload(pkg_resources)  # migh be loaded already and is not up to date

_loaded = []

for ep in pkg_resources.iter_entry_points("emzed_package", name="main"):
    try:
        runner = ep.load()
    except:
        continue
    _loaded.append(ep.module_name)
    name = ep.module_name.split(".")[0]
    #print "$$$ loaded emzed.app.%s from %s " % (name, runner)
    exec "%s=runner" % name
    sys.modules["emzed.app.%s" % name] = runner
    del ep
    del runner
    del name

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

