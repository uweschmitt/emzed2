import pkg_resources

for ep in pkg_resources.iter_entry_points("emzed_plugin", name="package"):
    print ep
    package = ep.load()
    exec "%s=package" % package.__name__
    del package
    del ep
del pkg_resources

