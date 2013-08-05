# -*- coding: utf-8 -*-
"""
Created on Sat Apr 13 00:04:22 2013

@author: uwe schmitt
"""
import inspect, sys

def replace( orig_func, target=None, verbose=False):
    """ monkey pathchin decorator: replaces function """

    def decorator(new_func, target=target):
        def wrapper(*a, **kw):
            return new_func(*a, **kw)

        wrapper.isPatched = True
        if inspect.ismethod(orig_func):
            if target is None:
                target =  orig_func.im_class
            setattr(target, orig_func.__name__, wrapper)
            setattr(target, "_orig_%s" % orig_func.__name__, orig_func)
        elif inspect.isfunction(orig_func):
            if target is None:
                target = sys.modules[orig_func.__module__]
            setattr(target, orig_func.func_name, wrapper)
            setattr(target, "_orig_%s" % orig_func.__name__, orig_func)
        else:
            raise Exception("can not wrap %s " % orig_func)
        return wrapper # not needed as new_func is not modified at all
    return decorator


def add(target, verbose=False):
    """ monkey pathchin decorator: adds function """

    def decorator(new_func, target=target):
        setattr(target, new_func.__name__, new_func)
    return decorator
