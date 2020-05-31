import sys

from shcmdmgr.args import ArgumentGroup

class Parser:
    def __init__(self, arguments, print_help):
        self.arguments = arguments
        self.print_help = print_help

    def peek(self):
        if len(self.arguments) != 0:
            return self.arguments[0]
        return None

    def get_rest(self):
        if self.print_help:
            sys.exit(SUCCESSFULL_EXECUTION)
        res = self.arguments
        self.arguments = []
        return res

    def shift(self):
        res = self.peek()
        self.arguments = self.arguments[1:]
        return res

    def expect_nothing(self):
        cur = self.peek()
        if cur:
            raise Exception('unexpected parameter ' + quote(cur))

    def may_have(self, groups: [ArgumentGroup]):
        current = self.peek()
        if current:
            for args in [group.arguments for group in groups if group.arguments]:
                for arg in args:
                    if current in [arg.arg_name, arg.short_arg_name]:
                        self.shift()
                        arg.function()
                        return True
        elif self.print_help:
            print_str(ArgumentGroup.to_str(groups), end='')
            sys.exit(SUCCESSFULL_EXECUTION)
        return False

    def load_all(self, groups: [ArgumentGroup]):
        while self.may_have(groups): pass
