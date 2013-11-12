

def patched(self):
    return dict(realm="pypi",
                username="uschmitt",
                password="pillepalle",
                repository="http://127.0.0.1:3142/root/dev/",
                server="local",
               )
# import distutils.config
# distutils.config.PyPIRCCommand._read_pypirc = patched


import os
p = os.getcwd()
os.chdir("emzed/core/explorers")
os.system("rst2html help_peakmapexplorer.rst > help_peakmapexplorer.html")
os.chdir(p)

version_str = "2.0.3"

version_tuple = tuple(map(int, version_str.split(".")))
with open("emzed/version.py", "w") as fp:
    fp.write("version = %r\n" % (version_tuple,))


from setuptools import setup, find_packages
setup(name="emzed",
      packages=find_packages(),
      version=version_str,
      entry_points={
          "console_scripts": ["emzed.workbench = emzed.workbench.main:main", ]
      },
      package_data={
          "emzed.core.r_connect": ["*.txt"],
          "emzed.core.explorers": ["*.html"],
          "emzed.workbench": ["*.png"],
      },
      zip_safe=False,
      install_requires=["emzed_optimizations",
                        "guidata>=1.6.0",
                        "guiqwt>=2.3.1",
                        "requests",
                        "numpy",
                        "scipy",
                        "matplotlib",
                        "sphinx",
                        "pyopenms",
                        "spyder==2.1.13",
                        "html2text",
                        "pandas",
                        ]

      )
