import distutils.config

def patched(self):
    return dict(realm="pypi",
                username="uschmitt",
                password="pillepalle",
                repository="http://127.0.0.1:3142/root/dev/",
                server="local",
                )
distutils.config.PyPIRCCommand._read_pypirc = patched

from setuptools import setup

import emzed
version_str = ".".join(map(str, emzed.__version__))

setup(name="emzed",
      packages=[ "emzed"],
      version=version_str,
      entry_points = {
          "console_scripts":
          [
              "emzed.workbench = emzed.workbench.modified_spyder_main:main",
          ]
          },
      package_data = {
          "emzed.core.r_connect": [ "*.txt"]
          },
     )
