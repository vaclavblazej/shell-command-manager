import sys

from shcmdmgr import config, cio
from shcmdmgr.args import ArgumentGroup

def remove_first_argument():
    sys.argv = [sys.argv[0]] + sys.argv[2:]

class Parser:
    def __init__(self, arguments, helpme):
        self.arguments = arguments
        self.help = helpme

    def peek(self):
        if len(self.arguments) != 0:
            return self.arguments[0]
        return None

    def get_rest(self):
        if self.help.print:
            sys.exit(config.SUCCESSFULL_EXECUTION)
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
            raise Exception('unexpected parameter ' + cio.quote(cur))

    # def expect(self, name, description):
    #     cur = self.peek()
    #     if not cur:
    #         if self.help.print:
    #             pass # todo

    def may_have(self, groups: [ArgumentGroup]):
        current = self.peek()
        if current:
            for args in [group.arguments for group in groups if group.arguments]:
                for arg in args:
                    if current in [arg.arg_name, arg.short_arg_name]:
                        self.shift()
                        arg.function()
                        return True
        elif self.help.print:
            # print_str(ArgumentGroup.to_str(groups), end='') #fixme
            sys.exit(config.SUCCESSFULL_EXECUTION)
        return False

    def load_all(self, groups: [ArgumentGroup]):
        while self.may_have(groups): pass
