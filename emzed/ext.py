import pkg_resources
reload(pkg_resources)  # migh be loaded already and is not up to date

for ep in pkg_resources.iter_entry_points("emzed_package", name="extension"):
    pkg = ep.load()
    print "!!! loaded", pkg
    exec "%s=pkg" % ep.module_name
    del ep
    del pkg

del pkg_resources

