# encoding: utf-8
from __future__ import print_function

def version():
    return (2, 27, 1)


is_experimental = False


def description():
    msg = """
    release 2.17.1
       - emzed.gui.inspect how accepts a string hold the path to a file to inspect (.table, .hdf5,
         .mzML, etc)
       - emezd.io now supports reading and writing of Excel .xls and .xlsx files
       - improvements on table explorer
       - fixed issue with plain MS2 peakmap in table explorer
       - minor fixes
    """
    return msg


def run_update(locally=True):
    import pip

    pip.main("install pycryptodome<=3.3".split())
    pip.main("install emzed_optimizations>=0.6.0".split())

    pip.main("install xlwt".split())
    pip.main("install xlrd".split())

    pip.main("install jdcal".split())
    pip.main("install et-xmlfile".split())
    pip.main("install openpyxl".split())

    pip.main("install emzed==2.27.1".split())


if __name__ == "__main__":
    import os
    is_venv = os.getenv("VIRTUAL_ENV") is not None
    run_update(locally=not is_venv)


