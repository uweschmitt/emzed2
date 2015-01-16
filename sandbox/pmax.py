import numpy as np
import pylab as pl


p1 = np.linspace(0, 1.0, 100)


#-1/log(-p1 + 1)
#-p1*(-p1 + 1)^(-1/log(-p1 + 1) - 1)/log(-p1 + 1)

def p(n, p1):
    return n * p1 * (1.0 -p1) ** (n-1)

def global_nmax(p1):
    n_float = -1.0 / np.log(1.0 - p1)
    n1 = math.floor(n1)
    n2 = math.floor(n2)
    if p(n1, p1) > p(n2, p2):
        return n1
    return n2

def pmax(p1, nmax):
    return p(min(nmax, global_nmax(p1)), p1)


"""

print nmax(1.0 - 0.03)
print pmax(1.0 - 0.03)

pl.subplot(211)
pl.plot(p1, nmax(p1))


pl.subplot(212)
pl.plot(p1, pmax(p1))
pl.show()

"""

# todo
# for all chnops : determine upper bound
#

