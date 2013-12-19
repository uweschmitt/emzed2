from scipy.optimize import nnls
import numpy as np
import math
import emzed

def fac(n):
    return int(math.gamma(n+1))

def binom(n, m):
    return fac(n) / fac(m) / fac(n - m)

def pc(m, l, n, p13):
    """
    p(n_13 = m | n_l = l) for n C-atoms and natural abundance p13 of C13
    """
    if l > m:
        return 0.0
    return binom(n - l, m - l) * p13 ** (m - l) * (1.0 - p13) ** (n - m)

def generate_matrix(n):
    p13 = emzed.abundance.C13
    mat = np.zeros((n+1, n+1))
    for i in range(n + 1):
        for j in range(n + 1):
            mat[i, j] = pc(i, j, n, p13)
    return mat


def bin_dist(n, p):
    rv = np.zeros((n + 1,))
    for i in range(n + 1):
        rv[i] = binom(n, i) * p ** i * (1.0 - p) ** (n - i)
    return rv


def compute_distribution_of_labeling(intensities, n):
    intensities = np.array(intensities)
    intensities /= np.sum(intensities)
    mat = generate_matrix(n)
    # modify matrix and rhs for constraint that solution vec sums up to 1.0:
    mat_modified = mat[:, 1:] - mat[:, :1]
    rhs_modified= intensities - mat[:, 0]
    corrected, error = nnls(mat_modified, rhs_modified)
    corrected = np.hstack((1.0 - np.sum(corrected), corrected))
    return corrected, error


if __name__ == "__main__":
    n = 20
    p = np.zeros((n + 1,))

    p[:10] = 1.0
    p = bin_dist(n, 0.2)

    p /= np.sum(p)
    rhs = np.dot(generate_matrix(n), p)
    rhs *= (1.0 + 0.0015 * np.random.randn(n + 1))
    last = None
    import pylab
    corr, fit_err = compute_distribution_of_labeling(rhs, n)
    #print p
    #print rhs
    print fit_err
    print corr

    fit_errs = []

    for nsub in range(1, n+10):
        rhs_sub = np.hstack((rhs, np.zeros(100)))[:nsub+1]
        corr, fit_err = compute_distribution_of_labeling(rhs_sub, nsub)
        fit_errs.append(fit_err)
        p_sub = np.hstack((p, np.zeros(100)))[:nsub+1]

        res_err = np.linalg.norm(corr[:nsub+1] - p_sub) / len(corr)

        if nsub == n:
            print "*",
            corr_opt = corr
        else:
            print " ",
        print "%2d" % nsub, "%e" % fit_err,
        pylab.subplot(211)
        pylab.plot(nsub, fit_err, "o")
        if last != None:
            res =  np.polyfit(np.arange(len(fit_errs)), fit_errs, 1)
            print "%+e" % (fit_err - last),
            print "   %+e" % res_err,
            pylab.subplot(212)
            pylab.plot(nsub, fit_err-last, "o")
        print
        last = fit_err

    pylab.figure()
    pylab.bar(np.arange(len(corr_opt)), corr_opt, 0.1, color="g")
    pylab.bar(np.arange(len(corr))+0.1, corr, 0.1, color="r")
    pylab.show()



