# encoding: latin-1

import locale
import os
import string
import sys

import guidata
import guidata.dataset.datatypes as dt
import guidata.dataset.dataitems as di

from guidata.qt.QtGui import QMessageBox
from guidata.dataset.qtwidgets import DataSetEditDialog

# monkey patch following Items, else dt.DataSet.check() raises
# exceptions. They are assumed to be valid in any case:


def _true(*a, **kw):
    return True

di.BoolItem.check_value = _true
di.ChoiceItem.check_value = _true
di.MultipleChoiceItem.check_value = _true
di.ButtonItem.check_value = _true

# patch ok / cancel: never check if needed fields are present ?!
# DataSetEditDialog.check = _true


def _patched_get(self, instance, klass):
    if instance is not None:
        value = getattr(instance, "_" + self._name, self._default)
        if isinstance(value, unicode):
            return value.encode(locale.getdefaultlocale()[1])
        return value
    return self


di.StringItem.__get__ = _patched_get
di.TextItem.__get__ = _patched_get

if sys.platform == "win32":
    # replace needed for network pathes like "//gram/omics/...."
    def _conv(s):
        return s.encode(sys.getfilesystemencoding()).replace("/", "\\")
else:
    def _conv(s):
        return s.encode(sys.getfilesystemencoding())


def _patched_get_for_pathes(self, instance, klass, _conv=_conv):
    if instance is not None:
        value = getattr(instance, "_" + self._name, self._default)
        if isinstance(value, unicode):
            value = _conv(value)
        elif isinstance(value, (list, tuple)):
            for i, item in enumerate(value):
                if isinstance(item, unicode):
                    value[i] = _conv(item)
        return value
    return self


def _patch_files_open():
    """new for FilesOpenItem: notempty option"""

    def _init(self, label, formats='*', default=None, basedir=None, all_files_first=False, help='',
              notempty=True):
        if isinstance(default, basestring):  # python 2 !
            default = [default]
        FileSaveItem.__init__(self, label, formats=formats,
                              default=default, basedir=basedir, all_files_first=all_files_first,
                              help=help)
        self.set_prop("data", notempty=notempty)

    def _check_value(self, value):
        """Override DataItem method"""
        allexist = True
        value = value or []
        for path in value:
            allexist = allexist and os.path.exists(path) and os.path.isfile(path)
        """
        notetmpy  value   ok
        T         []      F
        T         [x]     T
        F         []      T
        F         [x]     T
        """
        notempty = self.get_prop("data", "notempty")
        ok = allexist and (not notempty or len(value))
        return ok

    di.FilesOpenItem.__init__ = _init
    di.FilesOpenItem.check_value = _check_value


_patch_files_open()


di.FilesOpenItem.__get__ = _patched_get_for_pathes
di.FileSaveItem.__get__ = _patched_get_for_pathes
di.FileOpenItem.__get__ = _patched_get_for_pathes
di.DirectoryItem.__get__ = _patched_get_for_pathes


def _translateLabelToFieldname(label):
    # translate label strings to python variable names
    invalid = r"""^°!"\§$%&/()=?´``+*~#'-.:,;<>|@$"""
    trtable = string.maketrans(invalid, " " * len(invalid))
    return label.lower().translate(trtable)\
                .replace("  ", " ")\
                .replace("  ", " ")\
                .replace(" ", "_")


def showWarning(message, title="Warning"):
    """
    shows a warning dialog with given message
    """

    app = guidata.qapplication()
    QMessageBox.warning(None, title, message)


def showInformation(message, title="Information"):
    """
    shows a information dialog with given message
    """

    app = guidata.qapplication()
    QMessageBox.information(None, title, message)


def askYesNo(message, allow_cancel=False, title="Question"):
    """shows message and asks for "yes" or "no" (or "cancel" if allow_cancel is True).
       returns True, False (or None).
    """

    app = guidata.qapplication()
    flags = QMessageBox.Yes | QMessageBox.No
    if allow_cancel:
        flags |= QMessageBox.Cancel

    reply = QMessageBox.question(None, title, message, flags)

    if reply == QMessageBox.Cancel:
        return None
    else:
        return reply == QMessageBox.Yes


class _Stub(object):

    def __init__(self, item, outer):
        self.item = item
        self.outer = outer

    def __call__(self, label, *a, **kw):
        # this function registers corresponding subclass of
        #    DataItem
        fieldName = _translateLabelToFieldname(label)
        # check if fieldName is valid in Python:
        try:
            exec("%s=0" % fieldName) in dict()
        except:
            raise Exception("converted label %r to field name %r "
                            "which is not allowed in python"
                            % (label, fieldName))
        # get DataItem subclass
        # construct item
        dd = dict((n, v) for (n, v) in kw.items() if n in ["col", "colspan"])
        horizontal = kw.get("horizontal")
        if horizontal is not None:
            del kw["horizontal"]
        vertical = kw.get("vertical")
        if vertical is not None:
            del kw["vertical"]
        if "col" in kw:
            del kw["col"]
        if "colspan" in kw:
            del kw["colspan"]
        item = self.item(label, *a, **kw)
        if dd:
            item.set_pos(**dd)
        if horizontal:
            item.horizontal(horizontal)
        if vertical:
            item.vertical(vertical)

        # regiter item and fieldname
        self.outer.items.append(item)
        self.outer.fieldNames.append(fieldName)
        return self.outer


class DialogBuilder(object):

    # dynamic creation of __doc__
    _docStrings = []
    for _itemName, _item in di.__dict__.items():
        if _itemName.endswith("Item"):
            _docString = getattr(_item, "__doc__")
            if _docString is None:
                _docString = ""
            _dynamicMethodName = "        add" + _itemName[:-4]
            _docStrings.append(_dynamicMethodName + "(...):\n" + _docString)

    __doc__ = "\n".join(_docStrings)

    def __init__(self, title="Dialog"):

        self.attrnum = 0
        self.title = title
        self.items = []
        self.instructions = []
        self.fieldNames = []
        self.buttonCounter = 0

    def __getattr__(self, name):
        """dynamically provides methods which start with "add...", eg
        "addInt(....)".

        If one calls

               b = Builder()
               b.addInt(params)

        then

               b.addInt

        is a stub function which is constructed and returned some
        lines below. Then

               b.addInt(params)

        calls this stub function, which registers the corresponding
        IntItem with the given params.

        """
        if name.startswith("add"):
            try:
                item = getattr(di, name[3:] + "Item")
            except:
                raise AttributeError("%r has no attribute '%s'" % (self, name))

            stub = _Stub(item, self)

            # add docstring dynamically
            item = getattr(di, name[3:] + "Item")
            docString = getattr(item, "__doc__")
            docString = "" if docString is None else docString
            docString = "-\n\n" + name + "(...):\n" + docString
            stub.__doc__ = docString
            return stub
        raise AttributeError("%r has no attribute '%s'" % (self, name))

    def addInstruction(self, what):
        self.instructions.append(what)
        return self

    def addFilesOpen(self, label, formats="*", default=None, basedir=None, all_files_first=False,
                     help="", notempty=True):
        item = di.FilesOpenItem(label, formats, default, basedir, all_files_first, help,
                                notempty)
        fieldName = _translateLabelToFieldname(label)
        self.items.append(item)
        self.fieldNames.append(fieldName)
        return self

    def addButton(self, label, callback, help=None):
        """ addButton is not handled by __getattr__, as it needs special
            handling.

            In contrast to the other DateItem subclasses, ButtonItem
            gets a callback which has to be constructed in a special
            way, see below.
        """

        # the signature of 'wrapped' is dictated by the guidata
        # framework:
        def wrapped(ds, it, value, parent):
            # check inputs before callback is executed
            invalidFields = ds.check()
            if len(invalidFields):
                msg = "The following fields are invalid: \n"
                msg += "\n".join(invalidFields)
                QMessageBox.warning(parent, "Error", msg)
                return
            callback(ds)
        # register ButtomItem in the same way other DataItem subclass
        # instances are registered in the "stub" function in
        # __getattr__:
        item = di.ButtonItem(label, wrapped, help=help)
        self.items.append(item)
        self.fieldNames.append("_button%d" % self.buttonCounter)
        self.buttonCounter += 1
        return self

    def show(self):
        """ opens the constructed dialog.

            In order to do so we construct sublcass of DataSet on the fly.

            the docstring of the class is the title of the dialog,
            class level attributes are instances of sublcasses of
            DataItem, eg IntItem.

            For more info see the docs of guidata how those classes
            are declared to get the wanted dialog.

        """
        import guidata
        app = guidata.qapplication()

        # put the class level attributes in a dict
        attributes = dict(zip(self.fieldNames, self.items))
        # construct class "Dialog" which is a sublcass of "dt.DataSet"
        # with the  given attributes:
        clz = type("Dialog", (dt.DataSet,), attributes)
        # as said: the docstring is rendered as the dialogues title:
        clz.__doc__ = self.title + "\n" + "\n".join(self.instructions)
        # open dialog now !!!
        instance = clz()
        if instance.edit() == 0:
            raise Exception("dialog aborted by user")
        # return the values a tuple according to the order of the
        # declared input widgets:
        result = [getattr(instance, name) for name in self.fieldNames]
        result = tuple(result)
        if len(result) == 1:
            result = result[0]
        return result

# import guidata DataItems into current namespace
for _itemName, _item in di.__dict__.items():
    if _itemName.endswith("Item"):
        exec ("%s = di.%s" % (_itemName, _itemName))


def RunJobButton(label, method_name=None):
    item = di.ButtonItem(label, None)
    item._run_method = method_name
    return item


class WorkflowFrontend(dt.DataSet):

    def __init__(self):
        import guidata
        self.app = guidata.qapplication()
        for item in self._items:
            if hasattr(item, "_run_method"):
                name = item._run_method or "run_" + item._name
                target = getattr(self, name)

                def inner(ds, it, value, parent, target=target):
                    invalidFields = ds.check()
                    if len(invalidFields):
                        msg = "The following fields are invalid: \n"
                        msg += "\n".join(invalidFields)
                        QMessageBox.warning(parent, "Error", msg)
                        return
                    target()
                setattr(self, "_emzed_run_" + name, inner)
                item.set_prop("display", callback=inner)
        dt.DataSet.__init__(self)

    show = dt.DataSet.edit
