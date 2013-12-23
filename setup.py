
from setuptools import setup, find_packages

import emzed
version_str = "%d.%d.%d" % emzed.__version__


setup(name="emzed",
      packages=find_packages(),
      version=version_str,
      entry_points={
          "console_scripts": ["emzed.workbench = emzed.workbench.main:main",
                              "emzed.inspect = emzed.workbench.inspect:main",
                              ]

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
                        "sphinx",
                        "pyopenms",
                        "spyder==2.1.13",
                        "html2text",
                        "pandas",
                        ]

      )
