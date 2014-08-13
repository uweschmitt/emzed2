import pkg_resources
version = tuple(map(int, pkg_resources.require("emzed")[0].version.split(".")))
