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


def compute_distribution_of_labeling(intensities, n):
    mat = generate_matrix(n)
    # modify matrix and rhs for constraint that solution vec sums up to 1.0:
    mat_modified = mat[:, 1:] - mat[:, :1]
    rhs_modified= intensities - mat[:, 0]
    corrected, error = nnls(mat_modified, rhs_modified)
    return corrected, error


if __name__ == "__main__":
    n = 20
    p = np.zeros((n + 1,))
    p[:3] = 1.0
    p /= np.sum(p)
    rhs = np.dot(generate_matrix(n), p)
    corr, err = compute_distribution_of_labeling(rhs, n)
    print corr, err



