import contextlib
import functools
import time


@contextlib.contextmanager
def timer(name=""):
    started = time.time()
    yield
    needed = time.time() - started
    print name, "needed %.5fs" % needed


def timethis(function):

    @functools.wraps(function)
    def inner(*a, **kw):
        txt = "%s(args=%s, kw=%s)" % (function.__name__, a, kw)
        with timer(txt):
            return function(*a, **kw)
    return inner
