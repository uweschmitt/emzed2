# encoding: utf-8
from __future__ import print_function

def version():
    return (2, 26, 19)


def description():
    msg = """
    release 2.26.19:
       - hdf5 based table stores
       - performance improvements
       - atomic writes
       - more responsive table explorer for large files and hdf5 files
       - small bug fixes
    """
    return msg


def run_update(locally=True):
    import pip
                    "pycryptodome<=3.3",
                    "xlwt",
                    "xlrd",
                    "openpyxl",

    pip.main("install pycryptodome<=3.3".split())
    pip.main("install emzed_optimizations>=0.6.0".split())

    pip.main("install xlwt".split())
    pip.main("install xlrd".split())

    pip.main("install jdcal".split())
    pip.main("install et-xmlfile".split())
    pip.main("install openpyxl".split())

    pip.main("install emzed==2.26.19".split())


if __name__ == "__main__":
    import os
    is_venv = os.getenv("VIRTUAL_ENV") is not None
    run_update(locally=not is_venv)


