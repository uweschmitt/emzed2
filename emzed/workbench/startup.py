# -*- coding: utf-8 -*-
#
# Copyright © 2009-2011 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see spyderlib/__init__.py for details)

"""Startup file used by ExternalPythonShell exclusively for IPython sessions
(see spyderlib/widgets/externalshell/pythonshell.py)"""

import sys
import os
import os.path as osp

print "run patched startup"

os.environ["QT_API"] = "pyqt"


###########################################################################
#
# modification emzed
#
# on win only ipython 0.10 supports all features of the variable
# explorer, so we have to utilize easy_install to install 0.10
# at least. In order to get the right version in case of other
# other intstalled ipytho versions we have to:
###########################################################################
if sys.platform == "win32":
    import pkg_resources
    pkg_resources.require("ipython==0.10")
###########################################################################

# fix for mac:
sys.path.insert(0, osp.dirname(osp.abspath(__file__)))
from install import install_emzed
sys.path.pop(0)

import sitecustomize
print "loaded sitecustomize from", sitecustomize.__file__
print "spyder encoding is set to", os.environ.get('SPYDER_ENCODING')

# Remove this module's path from sys.path:
try:
    sys.path.remove(osp.dirname(__file__))
except ValueError:
    pass


locals().pop('__file__')
__doc__ = ''
__name__ = '__main__'


if os.environ.get('IPYTHON_KERNEL', False):

    # IPython >=v0.11 Kernel

    # Fire up the kernel instance.
    from IPython.zmq.ipkernel import IPKernelApp
    ipk_temp = IPKernelApp.instance()
    ipk_temp.initialize(sys.argv[1:])
    __ipythonshell__ = ipk_temp.shell

    # Issue 977: Since kernel.initialize() has completed execution,
    # we can now allow the monitor to communicate the availablility of
    # the kernel to accept front end connections.
    __ipythonkernel__ = ipk_temp
    del ipk_temp

    # Start the (infinite) kernel event loop.
    __ipythonkernel__.start()

elif os.environ.get('IPYTHON', False):

    sys.path.insert(0, '')
    if os.name == 'nt':
        # Windows platforms: monkey-patching *pyreadline* module
        # to make IPython work in a remote process
        from pyreadline import unicode_helper
        unicode_helper.pyreadline_codepage = "ascii"
        # For pyreadline >= v1.7:
        from pyreadline import rlmain
        class Readline(rlmain.Readline):
            def __init__(self):
                super(Readline, self).__init__()
                self.console = None
        rlmain.Readline = Readline
        # For pyreadline v1.5-1.6 only:
        import pyreadline
        pyreadline.GetOutputFile = lambda: None



    ###########################################################################
    #       modification eMZed # ##############################################
    ###########################################################################
    user_ns = dict()
    install_emzed(user_ns)
    user_ns["emzed"].updaters.interactive_update()
    # ipython does not like __builtins__ in namespace:
    if "__builtins__" in user_ns:
        del user_ns["__builtins__"]

    ###########################################################################
    # end of       modification ###############################################
    ###########################################################################

    try:
        # IPython >=v0.11
        # Support for these recent versions of IPython is limited:
        # command line options are not parsed yet since there are still
        # major issues to be fixed on Windows platforms regarding pylab
        # support.
        from IPython.frontend.terminal.embed import InteractiveShellEmbed
        banner2 = None
        if os.name == 'nt':
            # Patching IPython to avoid enabling readline:
            # we can't simply disable readline in IPython options because
            # it would also mean no text coloring support in terminal
            from IPython.core.interactiveshell import InteractiveShell, io
            def patched_init_io(self):
                io.stdout = io.IOStream(sys.stdout)
                io.stderr = io.IOStream(sys.stderr)
            InteractiveShell.init_io = patched_init_io
            banner2 = """Warning:
Spyder does not support GUI interactions with IPython >=v0.11
on Windows platforms (only IPython v0.10 is fully supported).

"""
        # second modification eMZed: user_ns arg ##########################
        __ipythonshell__ = InteractiveShellEmbed(banner2=banner2,
                                                 user_ns=user_ns)
        __ipythonshell__.stdin_encoding = os.environ['SPYDER_ENCODING']
        del banner2
    except ImportError:
        # IPython v0.10

        #######################################################################
        # modification eMZEd, somehow it is important that the fix for
        # path happens here:
        # (path exception due to regression of python 2.7.4, which was not
        # fixed in IPython 0.10)
        #######################################################################

        # we keep ipython for spyder seperate from other ipython installations and
        # on win we put it to appdata so that it is available for roaming
        if sys.platform == "win32":
            base_dir = os.environ.get("APPDATA", "")
            ipython_dir = os.path.join(base_dir, "_emzed2_ipython")
        else:
            base_dir = os.environ.get("HOME", "")
            ipython_dir = os.path.join(base_dir, ".emzed2_ipython")

        os.environ["IPYTHONDIR"] = ipython_dir
        import IPython.external.path
        IPython.external.path.path.isdir = lambda self: osp.isdir(self)
        import IPython.Shell
        user_ns["__emzed_project__"] = None
        __ipythonshell__ = IPython.Shell.start(user_ns=user_ns)
        # modification eMZEd end ##############################################

        __ipythonshell__.IP.stdin_encoding = os.environ.get('SPYDER_ENCODING', 'latin-1')
        __ipythonshell__.IP.autoindent = 0


        # emzed 2 ###########################################################

        def cwd_filt2(depth):
            """Return the last depth elements of the current working directory.

            $HOME is always replaced with '~'.
            If depth==0, the full path is returned."""

            HOME = os.environ.get("HOME", "")
            if not HOME:
                HOME = os.environ.get("USERPROFILE", "")  # for win32

            full_cwd = os.getcwd()
            if HOME:
                full_cwd = full_cwd.replace(HOME, "~")
            cwd = full_cwd.split(os.sep)
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
                print "cwd =", cwd_filt2(5),
                proj = vars(__builtins__).get("__emzed_project__")
                if proj:
                    proj = "\x01\x1b[0;35;47m(project=%s)\x01\x1b[0m" % proj
                    print
                    print proj,
            from IPython.ipapi import TryNext
            raise TryNext()

        __ipythonshell__.IP.set_hook("generate_prompt", hook)
        # emzed 2 end #######################################################


    ###########################################################################
    # modification eMZed # #
    ###########################################################################
    ip = None
    try:
        ip = IPython.ipapi.get()
    except:
        try:
            ip = IPython.core.interactiveshell.InteractiveShell.instance()
        except:
            pass

    if ip is not None:

        ip.ex("os.unsetenv('PYTHONPATH')")
        for name in ["e", "pi", "path"]:
            try:
                ip.ex("del %s" % name)
            except:
                pass
    __ipythonshell__.mainloop()

    ###########################################################################
    # end of  modification       ##############################################
    ###########################################################################


else: # standard shell
    ###########################################################################
    install_emzed(locals())
    ###########################################################################

