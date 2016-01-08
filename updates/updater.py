# encoding: utf-8
from __future__ import print_function

def version():
    return (0, 0, 1)


def description():
    msg = """
    this is a test for development of the prototype. New Feature:
        - first version of new version
        - not the last version of new version
        - bla bla bla
    """
    return msg


def run_update(locally=True):
    import pip
    pip.main("install -U requests".split())
    raw_input("press enter !")


if __name__ == "__main__":
    import os
    is_venv = os.getenv("VIRTUAL_ENV") is not None
    run_update(locally=not is_venv)


