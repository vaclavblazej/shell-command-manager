
from shcmdmgr.command import Command

class Argument:
    def __init__(self, function, arg_name, short_arg_name, help_str):
        self.function = function
        self.arg_name = arg_name
        self.short_arg_name = short_arg_name
        self.help_str = help_str or ''

    @property
    def show_name(self):
        res = ''
        if self.short_arg_name:
            res += self.short_arg_name + ', '
        res += self.arg_name
        return res

    def to_str(self, position=16):
        (width, _) = util.get_terminal_dimensions()
        width -= 2
        offset = max(2, position - len(self.show_name))
        line = '   ' + self.show_name + (offset * ' ') + self.help_str
        total = ''
        while width > position + 10:
            total += line[:width] + '\n'
            if len(line) <= width: break
            line = '   ' + (position * ' ') + line[width:]
        return total

class CommandArgument(Argument):
    def __init__(self, command: Command):
        fun = lambda: (command.execute(PARSER.get_rest()))
        super().__init__(fun, command.alias, None, command.description)

def set_scope(scope):
    CONF['scope'] = scope

class ArgumentGroup:
    def __init__(self, group_name: str, arguments: [Argument] = None, arg_fun=None, if_empty: str = None):
        self.group_name = group_name
        self._arguments = arguments
        self.arg_fun = arg_fun
        self.if_empty = if_empty

    @property
    def arguments(self):
        if self._arguments:
            return self._arguments
        if self.arg_fun:
            return self.arg_fun()
        return None

    @staticmethod
    def to_str(groups: []):
        res = ""
        for group in groups:
            if res != '': res += '\n'
            args = group.arguments
            if not args and group.arg_fun:
                args = group.arg_fun()
            if args and len(args) != 0:
                res += group.group_name + ":\n"
                for argument in args:
                    res += argument.to_str()
            elif group.if_empty:
                res += group.group_name + ":\n"
                res += '   ' + group.if_empty + '\n'
        return res
