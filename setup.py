import sys

from setuptools import setup, find_packages

# no import emzed here, causes trouble when installing on win, as missing packages
# are needed when importing emzed
version = (2, 29, 4)


install_requires = ["guidata<=1.6.2",
                    "guiqwt<=2.3.2",
                    "requests",
                    "ipython==7.16.3",
                    "dill",
                    "html2text",
                    "pandas<0.18",
                    "dill",
                    "pyopenms",
                    "pytest",
                    "scikit-learn",
                    "emzed_optimizations>=0.6.0",
                    "sphinx",           # needed by spyder
                    "colorama>=0.3.5",  # needed by sphinx
                    "pycryptodome<=3.3",
                    "xlwt",
                    "xlrd",
                    "openpyxl",
                    ]

# if we install pyreadline on ubuntu14 we run into trouble:
if sys.platform == "win32":
    install_requires += ["pyreadline"]
elif sys.platform != "linux2":
    install_requires += ["readline"]


setup(name="emzed",
      packages=find_packages(exclude=["tests", "sandbox"]),
      version="%s.%s.%s" % version,
      keywords=["alpha", ],
      description="Rewrite of emzed framework for LCMS data analysis",
      entry_points={
          "gui_scripts": ["emzed.workbench = emzed.workbench.main:main",
                          "emzed.inspect = emzed.cmdline:inspect",
                          ],
          "console_scripts": ["emzed.console = emzed.console:main",
                              "emzed.workbench.debug = emzed.workbench.main:main",
                              ]
      },
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      )
