from collections import defaultdict
import cPickle

f1m = cPickle.load(open("withoutfilter.bin", "rb"))
f2m = cPickle.load(open("withfilter.bin", "rb"))

cluster1s = defaultdict(list)
cluster2s = defaultdict(list)

for k, v in f1m.items():
    cluster1s[v].append(k)

for k, v in f2m.items():
    cluster2s[v].append(k)

# featuer cluster difs
diff = set(map(tuple, cluster1s.values())) - set(map(tuple, cluster2s.values()))

print diff

