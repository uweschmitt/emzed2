
import pkg_resources
reload(pkg_resources)  # migh be loaded already and is not up to date

for ep in pkg_resources.iter_entry_points("emzed_package", name="main"):
    runner = ep.load()
    name = ep.module_name.split(".")[0]
    #print "$$$ loaded emzed.app.%s from %s " % (name, runner)
    exec "%s=runner" % name
    del ep
    del runner
    del name

del pkg_resources

