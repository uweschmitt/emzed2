import sys


class ProgressCounter(object):

    def __init__(self, nmax):
        self.nmax = nmax
        self.last_percent = -1
        self.n = 0

    def count_up(self, step_size=1):
        self.n += step_size
        percent = round(100.0 * self.n / self.nmax, -1)  # round to tens
        if percent != self.last_percent:
            print "%.f%%" % percent,
            sys.stdout.flush()
            self.last_percent = percent

    def done(self):
        print
