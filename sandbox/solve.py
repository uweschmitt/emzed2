# psi(n - n1 - n2 + 1) == log(-p1 - p2 + 1) + psi(n + 1),

from scipy.special import polygamma, gamma, gammaln
from scipy.optimize import newton
from math import log, exp
import numpy as np
import pylab as pl

psi = lambda x: polygamma(0, x)
dpsi = lambda x: polygamma(1, x)

def fac(n):
    return gamma(n + 1)

def lfac(n):
    return gammaln(n + 1)

def bin(n, n1, n2):
    lbin = lfac(n) - lfac(n1) - lfac(n2) - lfac(n - n1 - n2)
    return np.exp(lbin)


def p(n, n1, n2, p1, p2):
    return bin(n, n1, n2) * p1 * p2 * (1.0 - p1 -p2) ** (n-2)
    return fac(n) / fac(n1) / fac(n2) / fac(n - n1 - n2) * p1 * p2 * (1.0 - p1 -p2) ** (n-2)
    #return fac(n) / fac(n1) / fac(n2) / fac(n - n1 - n2) * p1 * (1.0 - p1) ** (n1 -1 ) * p2 * (1.0 - p2) ** (n2 - 1) * (1.0 - p1 -p2) ** (n-n1-n2)

def fun(n, n1, n2, p1, p2):
    return log(1 - p1 -p2) + psi(n + 1) - psi(n - n1 - n2 + 1)

def dfun(n, n1, n2, p1, p2):
    return dpsi(n + 1) - dpsi(n - n1 - n2 + 1)


n1 = 4
n2 = 4
p1 = 0.01
p2 = 0.05

pmax = newton(fun, 12.0, dfun, args=(n1, n2, p1, p2))

x = np.linspace(0.1, pmax*2, 200)
y = fun(x, n1, n2, p1, p2)

print pmax

pl.subplot(211)

pl.plot(x, y)
y = p(x, n1, n2, p1, p2)
pl.subplot(212)
pl.plot(x, y)
pl.show()




