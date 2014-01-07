from subprocess import *


p = Popen("python x.py", bufsize=0, stdin=PIPE, stdout=PIPE, stderr=PIPE)
print p.communicate("print 42")[0]
