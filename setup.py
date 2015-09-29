import sys

from setuptools import setup, find_packages

# no import emzed here, causes trouble when installing on win, as missing packages
# are needed when importing emzed
version = (2, 20, 3)


install_requires = ["emzed_optimizations",
                    "guidata<=1.6.2",
                    "guiqwt<=2.3.2",
                    "requests",
                    "ipython==0.10",
                    # "spyder==2.1.13",
                    "dill",
                    "sphinx",
                    "html2text",
                    "pandas",
                    "dill",
                    "pyopenms",
                    "pyRserve==0.8.2",
                    "pytest",
                    ]

# if we install pyreadline on ubuntu14 we run into trouble:
if sys.platform == "win32":
    install_requires += ["pyreadline"]
elif sys.platform != "linux2":
    install_requires += ["readline"]


setup(name="emzed",
      packages=find_packages(exclude=["tests", "sandbox"]),
      version="%d.%d.%d" % version,
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
