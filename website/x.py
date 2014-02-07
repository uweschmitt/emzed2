import sys
from code import InteractiveInterpreter

def run():
    inp=sys.stdin.read()
    print ">>>", inp
    InteractiveInterpreter().runsource(inp)

if __name__ == "__main__":
    run()
