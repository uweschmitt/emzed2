
import pkg_resources
reload(pkg_resources)  # migh be loaded already and is not up to date

for ep in pkg_resources.iter_entry_points("emzed_package", name="main"):
    runner = ep.load()
    print "$$$ loaded", runner
    exec "%s=runner" % ep.module_name.split(".")[0]
    del ep
    del runner

del pkg_resources

