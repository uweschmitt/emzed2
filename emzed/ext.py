import sys

# rescan moudles and packages on sys.path:

import pkg_resources
reload(pkg_resources)  # migh be loaded already and is not up to date

_loaded = []

for _ep in pkg_resources.iter_entry_points("emzed_package", name="extension"):
    try:
        _pkg = _ep.load()
    except:
        del _ep
        import traceback
        traceback.print_exc()
        continue
    _loaded.append(_ep.module_name)
    exec "%s=_pkg" % _ep.module_name
    sys.modules["emzed.ext.%s" % _ep.module_name] = _pkg
    del _ep
    del _pkg

if _loaded:
    print
    print "LOADED EMZED EXTENSIONS: ".ljust(80, "-")
    print
    for l in _loaded:
        print "loaded", l
    print
    print "-" * 80

del pkg_resources
del sys
