import time
import sys


class ScreenWriter(object):

    WIDTH = 78


class SectionPrinter(ScreenWriter):

    @classmethod
    def print_(clz, what):
        print
        print (" %s " % what).center(clz.WIDTH, "=")
        print


class TimedPrinter(ScreenWriter):

    def __init__(self, start_message="start calculation"):
        self.startat = time.time()
        self.print_(start_message)

    def print_(self, what):
        appendix = "%7.1f seconds" % (time.time() - self.startat)
        print what.ljust(self.WIDTH - len(appendix) - 1, "."),
        print appendix


class ProgressIndicator(ScreenWriter):

    def __init__(self, maxn):
        self.maxn = maxn
        self.last_x = -1
        self.i = -1

    def set(self, i):
        x = int((self.WIDTH - 5) * i / self.maxn)
        if x != self.last_x:
            line = ["_"] * (self.WIDTH - 5)
            line[x] = "/-\|/-\|"[x % 8]
            percent = int(100.0 * i / self.maxn)
            sys.stdout.write("%3d  " % percent)
            sys.stdout.write("".join(line))
            sys.stdout.write(chr(13))
            self.last_x = x
        sys.stdout.flush()

    def next(self):
        self.set(self.i)
        self.i += 1

    def finish(self):
        sys.stdout.write("100  ")
        sys.stdout.write((self.WIDTH - 5) * ".")
        sys.stdout.flush()
