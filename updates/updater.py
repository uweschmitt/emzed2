# encoding: utf-8
from __future__ import print_function

def version():
    return (2, 24, 6)


def description():
    msg = """
    release 2.24.6:
    this release provides some bugfixes and minor performance improvements.
    """
    return msg


def run_update(locally=True):
    import pip
    pip.main("install -U pycryptodome<=3.3".split())
    pip.main("install -U emzed_optimizations>=0.5.0".split())
    pip.main("install emzed==2.24.6".split())


if __name__ == "__main__":
    import os
    is_venv = os.getenv("VIRTUAL_ENV") is not None
    run_update(locally=not is_venv)


