
from setuptools import setup, find_packages

# no import emzed here, causes trouble when installing on win, as missing packages
# are needed when importing emzed
version_str = "2.1.7"


setup(name="emzed",
      packages=find_packages(exclude=["tests", "sandbox"]),
      version=version_str,
      entry_points={
          "gui_scripts": ["emzed.workbench = emzed.workbench.main:main",
                          "emzed.inspect = emzed.cmdline:inspect",
                          ]

      },
      include_package_data=True,
      zip_safe=False,
      install_requires=["emzed_optimizations",
                        "guidata>=1.6.0",
                        "guiqwt>=2.3.1",
                        "requests",
                        "sphinx",
                        "pyopenms",
                        "spyder==2.1.13",
                        "html2text",
                        "pandas",
                        ]

      )
