import sys

if not getattr(sys, "frozen", False):
    import pkg_resources
    version = pkg_resources.require("emzed")[0].version.split(".")
    if version[-1].startswith("post"):
        version[-1] = version[-1][4:]
    for i, vi in enumerate(version):
        try:
            vi = int(vi)
        except ValueError:
            pass
        version[i] = vi

    if len(version) < 4:
        version.append(0)
    version = tuple(version)

else:
    version = (0, 0, 0)
