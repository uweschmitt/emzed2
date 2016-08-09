# encoding: utf-8
from __future__ import print_function, division, absolute_import

import os
import sys


def _symlink_ms(source, link_name):
    import ctypes
    csl = ctypes.windll.kernel32.CreateSymbolicLinkW
    csl.argtypes = (ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32)
    csl.restype = ctypes.c_ubyte
    flags = 1 if os.path.isdir(source) else 0
    if csl(link_name, source, flags) == 0:
        raise ctypes.WinError()


if sys.platform == "win32":
    symlink = _symlink_ms
else:
    symlink = os.symlink
