var('p1,p2,n1,n2,n')
fac(n) = gamma(n+1)
binom(n, m) = fac(n) / fac(m) / fac(n-m)
p = fac(n) / fac(n1) / fac(n2) / fac(n-n1-n2) * p1 * p2 * (1 -p1-p2)^(n-2)
#df = diff(p, n)
#print solve(df, n)

p(n) = n * p1 * (1 - p1) ^(n-1)
df = diff(p, n)
nmax = solve(df, n)[0].rhs()
print nmax
print p(nmax)

