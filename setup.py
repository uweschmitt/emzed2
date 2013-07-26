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

setup(name="emzed",
      packages=[ "emzed"],
      version="2.0.1" ,
     )
