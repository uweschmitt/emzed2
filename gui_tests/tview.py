# encoding: utf-8, division
from __future__ import print_function, division

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys



my_array = [['00', '01', '02'],
            ['10', '11', '12'],
            ['20', '21', '22']]


from emzed.core.data_types.hdf5_table_proxy import Hdf5TableProxy

import emzed

def main():

    import os.path

    here = os.path.dirname(os.path.abspath(__file__))
    #tproxy = Hdf5TableProxy(os.path.join(here, "test_1000000.hdf5"))
    tproxy = Hdf5TableProxy(os.path.join(here, "peaks.hdf5"))
    tproxy.info()

    # tproxy.filter_("floats_0", 400, 450)
    #print("sort")
    #tproxy.sortBy(["floats_0"], [True])

    emzed.gui.inspect(tproxy)

if __name__ == "__main__":
    main()
