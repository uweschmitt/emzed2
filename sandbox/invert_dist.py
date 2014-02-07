import pdb
import math
import numpy as np
from scipy.optimize import leastsq

import emzed

c13_fac = emzed.abundance.C13 / emzed.abundance.C12


def fac(n):
    return math.gamma(n + 1)


def binom(n, m):
    return fac(n) / fac(m) / fac(n - m)


def create_matrix(p12, n):
    p13 = p12 * c13_fac
    mat = np.zeros((n + 2, n + 1))
    for m in range(0, n + 1):
        for nl in range(0, m + 1):
            mat[m, nl] = binom(n, n - m) * p12 ** (n - m) * p13 ** (m - nl)
    mat[n+1, :] = 1.0
    return mat


def resid(param, ii, n):
    p12 = param[0]
    x = param[1:]
    cm = create_matrix(p12, n)
    #print cm.shape, x.shape, ii, n
    resid = np.dot(cm, x) - ii
    return resid

p12 = emzed.abundance.C12
mat = create_matrix(p12, 3)
p13 = 1.0 - p12

# todo
# simul: full bernoulle for p12, p13, pL !
#

n = 5
rhs = np.zeros((n + 2,))
for i in range(n + 1):
    rhs[i] = binom(n, n - i) * p12 ** (n - i) * p13 ** i
rhs[n + 1] = 1.0

#x = leastsq(resid, np.ones((n+2,))/(n+1), (rhs, n))
#print x

p12 = 0.5
p13 = 0 # p12 * c13_fac
pL  = 1.0 - p12 - p13

print p12, p13, pL

n = 5
rhs = np.zeros((n + 2,))
for m in range(n + 1):
    n12 = n - m
    for nl in range(m + 1):
        n13 = m - nl
        rhs[m] += fac(n) / fac(n12) / fac(nl) / fac(n13) * p12**n12 * p13**n13 * pL**nl


rhs[n + 1] = 1.0
print rhs
x, __ = leastsq(resid, .5 * np.ones((n+2,)), (rhs, n))
print x, sum(x[1:])


