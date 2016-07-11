import sys

if not getattr(sys, "frozen", False):
    import pkg_resources
    version = tuple(map(str, pkg_resources.require("emzed")[0].version.split(".")))
else:
    version = (0, 0, 0)
