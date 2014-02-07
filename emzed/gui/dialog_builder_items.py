#encoding: latin-1
import guidata.dataset.dataitems as _di
import guidata.dataset.datatypes as _dt
import inspect as _inspect

for _name, _item in _di.__dict__.items():
    if _inspect.isclass(_item):
        if issubclass(_item, _dt.DataItem):
            exec("%s=_item" % _name)
