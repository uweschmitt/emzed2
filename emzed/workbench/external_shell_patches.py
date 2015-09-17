# -*- coding: utf-8 -*-
"""
Created on Sat Apr 13 00:10:11 2013

@author: uwe
"""


from patch_utils import replace


def patch_external_shell():

    from spyderlib import baseconfig

    # guiqwt leads to mem leak for long running procesess, we fix this:
    patch_guiqwt()

    # utility functions called in monitor to get status info
    # about objects in shell:
    patch_dicteditorutils()

    # oedit opens dialogs for objects, we introduce handling of
    # emzed specific types:
    patch_oedit()

    __builtins__["__emzed_patches_applied"] = True

def patch_dicteditorutils():

    from  spyderlib.widgets import dicteditorutils
    @replace(dicteditorutils.is_supported, verbose=True)
    def is_supported(value, check_all=False, filters=None, iterate=True):
        from  emzed.core.data_types import PeakMap, Table
        import numpy
        return isinstance(value, (Table, PeakMap)) \
            or dicteditorutils._orig_is_supported(value,
                                                  check_all,
                                                  filters,
                                                  iterate)\
            or numpy.number in getattr(type(value), "__mro__", [])


    @replace(dicteditorutils.get_size, verbose=True)
    def get_size( item ):
        from  emzed.core.data_types import PeakMap, Table
        if isinstance(item, (PeakMap, Table)):
            return len(item)
        return dicteditorutils._orig_get_size(item)


    @replace(dicteditorutils.get_type_string, verbose=True)
    def get_type_string( item ):
        # if you return a string with dots the part until
        # and including the first dot is ommited by
        # dicteditorutils.get_type which leads to strange results

        from  emzed.core.data_types import PeakMap, Table
        import numpy

        if isinstance(item, list) and all(isinstance(ii, Table) for ii in item):
            # here I avoid dots by using the unicode char for "...":
            return u"[Table, %s]" % unichr(0x2026)
        if isinstance(item, PeakMap):
            return "PeakMap"
        if isinstance(item, Table):
            return "Table"
        if numpy.number in getattr(type(item), "__mro__", []):
            # str(type) returns something lilke "<type 'numpy.float32'>",
            # so we cut out 'float32':
            return str(type(item))[7:-2]
        return dicteditorutils._orig_get_type_string(item)

    @replace(dicteditorutils.value_to_display, verbose=True)
    def  value_to_display(value, truncate=False, trunc_len=80, minmax=False,
                          collvalue=True):
        from  emzed.core.data_types import PeakMap, Table
        import os
        import numpy

        def trunc(what, trunc_len=trunc_len, truncate=truncate):
            if truncate and len(what)>trunc_len:
               return "..."+ res[(len(what) + 3 - trunc_len):]
            return what

        if isinstance(value, PeakMap):
            try:
                return trunc(value.meta.get("source", ""))
            except Exception, e:
                return "exception: %s" % e

        if isinstance(value, list) and\
           all(isinstance(ii, Table) for ii in value):
           names = [os.path.basename(d.title or "") for d in value
                                              if isinstance(d, Table)]
           prefix = os.path.commonprefix(names)
           if len(prefix) == 0:
               res = ", ".join(names)
           else:
               res = prefix+"*"
           return "[%s]" % trunc(res, trunc_len=trunc_len-2)

        if isinstance(value, Table):
            if value.title:
                res = value.title
            else:
                try:
                    res = os.path.basename(value.meta.get("source", ""))
                except Exception, e:
                    return "exception: %s" % e
            return trunc(res)

        if numpy.number in getattr(type(value), "__mro__", []):
            return str(value)

        return dicteditorutils._orig_value_to_display(value,
                                                      truncate,
                                                      trunc_len,
                                                      minmax,
                                                      collvalue)




def patch_guiqwt():

    import guiqwt.plot
    import guiqwt.curve

    # remove __del__ as we get unbreakable dependency cycles
    #  if we plot a lot.
    if hasattr(guiqwt.curve.CurvePlot, "__del__"):
        del guiqwt.curve.CurvePlot.__del__

    # caused by the latter patch, get_active_plot sometimes raises
    # exception (i guess) because the underlying c++ object does not
    # exist anymore.
    # so we supress this exception:

    @replace(guiqwt.plot.PlotManager.get_active_plot)
    def patch(self):
        try:
            return guiqwt.plot.PlotManaager._orig_get_active_plot(self)
        except:
            return self.default_plot



def patch_oedit():

    # runs in external console, is triggered if someone clickst at items
    # in the variable explorer (aka namespace explorer)
    from  spyderlib.widgets import objecteditor


    # modified signature of patched method: added keeper arg, as this is
    # a module global variable in objecteditor.py:

    @replace(objecteditor.oedit, verbose=True)
    def oedit(obj, modal=True, namespace=None, keeper=objecteditor.DialogKeeper()):
        """
        Edit the object 'obj' in a GUI-based editor and return the edited copy
        (if Cancel is pressed, return None)

        The object 'obj' is a container

        Supported container types:
        dict, list, tuple, str/unicode or numpy.array

        (instantiate a new QApplication if necessary,
        so it can be called directly from the interpreter)
        """
        # Local import
        from spyderlib.widgets.texteditor import TextEditor
        from spyderlib.widgets.dicteditorutils import (ndarray, FakeObject,
                                                       Image, is_known_type)
        from spyderlib.widgets.dicteditor import DictEditor
        from spyderlib.widgets.arrayeditor import ArrayEditor

        from spyderlib.utils.qthelpers import qapplication
        app = qapplication()

        # STARTMODIFICATION EMZED
        from emzed.core.data_types import PeakMap, Table
        from emzed.core.explorers  import PeakMapExplorer, TableExplorer
        # ENDMODIFICATION EMZED


        if modal:
            obj_name = ''
        else:
            assert isinstance(obj, basestring)
            obj_name = obj
            if namespace is None:
                namespace = globals()
            keeper.set_namespace(namespace)
            obj = namespace[obj_name]
            # keep QApplication reference alive in the Python interpreter:
            namespace['__qapp__'] = app

        conv_func = lambda data: data
        readonly = not is_known_type(obj)
        if isinstance(obj, ndarray) and ndarray is not FakeObject:
            dialog = ArrayEditor()
            if not dialog.setup_and_check(obj, title=obj_name,
                                          readonly=readonly):
                return
        elif isinstance(obj, Image) and Image is not FakeObject \
             and ndarray is not FakeObject:
            dialog = ArrayEditor()
            import numpy as np
            data = np.array(obj)
            if not dialog.setup_and_check(data, title=obj_name,
                                          readonly=readonly):
                return
            from spyderlib.pil_patch import Image
            conv_func = lambda data: Image.fromarray(data, mode=obj.mode)
        elif isinstance(obj, (str, unicode)):
            dialog = TextEditor(obj, title=obj_name, readonly=readonly)

        # START MODIFICATION EMZED
        elif isinstance(obj, PeakMap):
            dialog = PeakMapExplorer()
            dialog.setup(obj)
        elif isinstance(obj, Table):
            dialog = TableExplorer([obj], False)
            conv_func = lambda (x,) : x
        elif isinstance(obj, list) and all(isinstance(t, Table) for t in obj):
            dialog = TableExplorer(obj, False)
        # END MODIFICATION EMZED

        else:
            dialog = DictEditor()
            dialog.setup(obj, title=obj_name, readonly=readonly)

        def end_func(dialog):
            return conv_func(dialog.get_value())

        if modal:
            if dialog.exec_():
                return end_func(dialog)
        else:
            keeper.create_dialog(dialog, obj_name, end_func)
            import os
            qt_inputhook = os.environ.get("INSTALL_QT_INPUTHOOK",
                                          "").lower() == "true"
            if os.name == 'nt' and not qt_inputhook \
               and not os.environ.get('IPYTHON', False):
                app.exec_()

