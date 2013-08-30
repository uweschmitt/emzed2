# -*- coding: utf-8 -*-
"""
Spyder Editor

This temporary script file is located here:
/home/uschmitt/emzed2_workbench/.temp.py
"""
import os
import sys

def cwd_filt2(depth):
    """Return the last depth elements of the current working directory.

    $HOME is always replaced with '~'.
    If depth==0, the full path is returned."""

    HOME = os.environ.get("HOME", "")

    full_cwd = os.getcwd()
    cwd = full_cwd.replace(HOME,"~").split(os.sep)
    if '~' in cwd and len(cwd) == depth+1:
        depth += 1
    drivepart = ''
    if sys.platform == 'win32' and len(cwd) > depth:
        drivepart = os.path.splitdrive(full_cwd)[0]
    out = drivepart + '/'.join(cwd[-depth:])

    if out:
        return out
    else:
        return os.sep

def hook(shell, is_continuation):
    if not is_continuation:
        print
        print cwd_filt2(5)
        proj = getattr(__builtins__, "__emzed_project__", "")
        print repr(proj)
        if proj:
            proj = "\x01\x1b[0;35;47m(%s)\x01\x1b[0m" % proj
            print proj,
            #if 0:
                #import os
                #n = _ip.IP.outputcache.prompt_count + 1
                #
                #return "%s\n(%s) In[%d]:" % (proj, os.getcwd(), n)

    from IPython.ipapi import TryNext
    raise TryNext()


import IPython.ipapi

_ip = IPython.ipapi.get()

_ip.IP.set_hook("generate_prompt", hook)


