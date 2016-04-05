# encoding: utf-8, division
from __future__ import print_function, division


try:
    profile
except NameError:
    def profile(fun):
        return fun
else:
    # sonst kann man profile nicht mit "from install_profile import profile" importieren:
    profile = profile
