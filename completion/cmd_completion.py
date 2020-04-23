#!/usr/bin/env python3

import sys

def shift():
    if len(sys.argv)==0: return None
    arg = sys.argv[0]
    sys.argv = sys.argv[1:]
    return arg

def find_comp():
    pass

def save_comp():
    pass

if __name__ == '__main__':
    shift() # ignore the completion's program's call
    shift() # ignore the program's call
    cmds={'save':save_comp,'find':find_comp}
    cmd=shift()
    if cmd is not None:
        if cmd in cmds:
            cmds[cmd]()
    else:
        for c in cmds:
            print(c)

