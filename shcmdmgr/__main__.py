#!/usr/bin/env python3
#
#    shell-command-management
#    Tool for managing custom commands from a central location
#    Copyright (C) 2020  Václav Blažej
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os
import sys
import subprocess
import enum
from os.path import join, exists

from shcmdmgr import util, config, filemanip, structure, cmdcomplete
from shcmdmgr.cio import quote, print_str, input_str
from shcmdmgr.structure import Command, Project
from shcmdmgr.config import SCRIPT_PATH

SUCCESSFULL_EXECUTION = 0
USER_ERROR = 1 # argument format is fine, but content is wrong
INVALID_ARGUMENT = 129 # argument format is wrong

WORKING_DIRECTORY = os.getcwd()
GLOBAL_COMMANDS_FILE_LOCATION = join(SCRIPT_PATH, 'commands.json')
COMPLETE = None
PRINT_HELP = False
PROJECT_ROOT_VAR = 'project_root'
DEFAULT_COMMAND_LOAD_DEJA_VU = False
CONF = config.get_conf()
LOGGER = None
PARSER = None
PROJECT = None
PROJECT_ALIASES = None
ALIASES = None

# == Main Logic ==================================================================

def main():
    global LOGGER
    LOGGER = config.get_logger()
    global PARSER
    PARSER = Parser(sys.argv)
    PARSER.shift() # skip the program invocation
    while PARSER.may_have([FixedArgumentGroup.OUTPUT_ARGUMENTS]): pass
    LOGGER.setLevel(CONF['logging_level'])
    LOGGER.debug('Configuration: %s', str(CONF))
    LOGGER.debug('Script folder: %s', quote(SCRIPT_PATH))
    LOGGER.debug('Working directory: %s', quote(WORKING_DIRECTORY))
    LOGGER.debug('Arguments: %s', str(sys.argv))
    global PROJECT
    PROJECT = Project.retrieve_project_if_present(WORKING_DIRECTORY)
    if PROJECT: os.environ[PROJECT_ROOT_VAR] = PROJECT.directory # expose variable to subprocesses

    load_aliases()
    load_project_aliases()
    while PARSER.may_have([FixedArgumentGroup.OPTIONAL_ARGUMENTS]): pass
    if CONF['scope'] == 'auto':
        if PROJECT: CONF['scope'] = 'project'
        else: CONF['scope'] = 'global'
    return main_command()

def main_command():
    current_command = PARSER.peek()

    if not current_command:
        if COMPLETE: return complete_commands()
        if PRINT_HELP: return print_general_help()
        if CONF['default_command']:
            new_args = CONF['default_command'].split(' ')
            global DEFAULT_COMMAND_LOAD_DEJA_VU
            if len(new_args) != 0: # prevent doing nothing due to empty default command
                if DEFAULT_COMMAND_LOAD_DEJA_VU: # prevent adding default command multiple times
                    LOGGER.warning('The default command is invalid, it must include a command argument')
                    return USER_ERROR
                DEFAULT_COMMAND_LOAD_DEJA_VU = True
                sys.argv += new_args
                return main()
        LOGGER.warning('No command given')
        return USER_ERROR

    if not PARSER.may_have([FixedArgumentGroup.PROJECT_COMMANDS, FixedArgumentGroup.CUSTOM_COMMANDS, FixedArgumentGroup.CMD_COMMANDS]):
        LOGGER.warning('The argument/command %s was not found', quote(current_command))
        LOGGER.info('run "cmd --help" if you are having trouble')
        return USER_ERROR

    return SUCCESSFULL_EXECUTION

# == Formatting ==================================================================

def print_general_help():
    help_str = ''
    help_str += 'usage: cmd [-q|-v|-d] [-g|-p] <command> [<args>]\n'
    help_str += '\n'
    help_str += 'Manage custom commands from a central location\n'
    print_str(help_str)
    main_groups = [
        FixedArgumentGroup.PROJECT_COMMANDS,
        FixedArgumentGroup.CUSTOM_COMMANDS,
        FixedArgumentGroup.CMD_SHOWN_COMMANDS,
        FixedArgumentGroup.OPTIONAL_ARGUMENTS,
    ]
    print_str(ArgumentGroup.to_str(main_groups), end='')
    # additional_str = ''
    # print_str(additional_str) #todo print info including special options (such as --complete)
    return SUCCESSFULL_EXECUTION

# == Commands ====================================================================

def cmd_help():
    if COMPLETE: return main_command()
    global PRINT_HELP
    PRINT_HELP = True
    remove_first_argument()
    return main_command()

def cmd_version():
    if COMPLETE: return complete_nothing()
    print_str('cmd version ' + config.VERSION)
    PARSER.expect_nothing()
    return SUCCESSFULL_EXECUTION

def cmd_save():
    if COMPLETE: return complete_nothing()
    alias = ''
    description = ''
    other_args = [
        Argument(lambda: print('TODO'), '--alias', '-a', 'one word shortcut used to invoke the command'),
        Argument(lambda: print('TODO'), '--descr', '-d', 'few words about the command\'s functionality'),
        Argument(lambda: print('TODO'), '--', None, 'command to be saved follows'),
    ]
    while PARSER.may_have([ArgumentGroup('test', other_args)]): pass
    args = PARSER.get_rest()
    show_edit = False

    if len(args) == 0: # supply the last command from history
        history_file_location = join(os.environ['HOME'], CONF['history_home'])
        history_command_in_binary = subprocess.check_output(['tail', '-1', history_file_location])
        history_command = history_command_in_binary[:-1].decode("utf-8")
        args = history_command.split(' ')
        show_edit = True

    if len(args) > 0 and exists(args[0]): # substitute relative file path for absolute
        if CONF['scope'] == 'project':
            args[0] = '$' + PROJECT_ROOT_VAR + '/' + os.path.relpath(join(WORKING_DIRECTORY, args[0]), PROJECT.directory)
        if CONF['scope'] == 'global':
            args[0] = os.path.realpath(join(WORKING_DIRECTORY, args[0]))
        show_edit = True

    command_to_save = ' '.join(args)

    if show_edit:
        command_to_save = input_str('The command to be saved: ', prefill=command_to_save)
    else:
        print_str('Saving command: ' + command_to_save)

    if CONF['scope'] == 'project': commands_file_location = PROJECT.commands_file
    if CONF['scope'] == 'global': commands_file_location = GLOBAL_COMMANDS_FILE_LOCATION

    if not exists(commands_file_location):
        filemanip.save_json_file([], commands_file_location)
    if alias == '': alias = input_str('Alias: ')
    if description == '': description = input_str('Short description: ')
    commands_db = structure.load_commands(commands_file_location)
    commands_db.append(Command(command_to_save, description, alias))
    filemanip.save_json_file(commands_db, commands_file_location)
    return SUCCESSFULL_EXECUTION

def cmd_find():
    if COMPLETE: return complete_nothing()
    max_cmd_count = 4
    max_cmd_count_slack = 2
    commands_db = structure.load_commands(GLOBAL_COMMANDS_FILE_LOCATION)
    if PROJECT:
        commands_db += PROJECT.commands
    selected_commands = []
    try:
        while True:
            print_str(40 * '=')
            arguments = PARSER.get_rest()
            if len(arguments) != 0:
                query = ' '.join(arguments)
                arguments = []
            else:
                query = input_str('query $ ')
            try:
                idx = int(query)
                if idx not in range(1, len(selected_commands)+1):
                    print_str('invalid index')
                    continue
                selected_commands[idx-1].execute(PARSER.get_rest())
                break
            except ValueError as _:
                pass
            index = 1
            results = []
            for command in commands_db:
                result = command.find(query)
                if result is not None:
                    (priority, formatted_text) = result
                    results.append((priority, formatted_text, command))
            total_results_count = len(results)
            if total_results_count == 0:
                print_str('No results found')
            results = sorted(results, reverse=True) # by priority
            selected_commands = []
            cmd_showing_count = max_cmd_count
            if total_results_count <= cmd_showing_count + max_cmd_count_slack:
                cmd_showing_count += max_cmd_count_slack
            for result in results[:cmd_showing_count]:
                (_, text, command) = result
                selected_commands.append(command)
                print_str('--- ' + str(index) + ' ' + (30 * '-'))
                print_str(text, end='')
                index = index+1
            if total_results_count > cmd_showing_count:
                print_str('\nand ' + str(total_results_count-cmd_showing_count) + ' other commands')
    except EOFError as _:
        print_str()
    return SUCCESSFULL_EXECUTION

def cmd_edit():
    if COMPLETE: return complete_nothing()
    subprocess.run([os.path.expandvars('$EDITOR'), GLOBAL_COMMANDS_FILE_LOCATION], check=True)
    return SUCCESSFULL_EXECUTION

def cmd_complete():
    global COMPLETE
    last_arg = sys.argv[-1]
    sys.argv = sys.argv[:-1]
    remove_first_argument()
    if COMPLETE: return main()
    COMPLETE = cmdcomplete.get_complete(last_arg)
    LOGGER.setLevel(config.QUIET_LEVEL) # fix when set after main() call
    main_res = main()
    for word in COMPLETE.words:
        print(word, end=' ')
    print()
    return main_res

def load_aliases(): # todo simplify
    commands_db = structure.load_commands(GLOBAL_COMMANDS_FILE_LOCATION)
    global ALIASES
    ALIASES = {}
    for command in commands_db:
        if command.alias:
            ALIASES[command.alias] = Command(command.execute, command.description)
    return [CommandArgument(cmd) for cmd in commands_db if cmd.alias]

def load_project_aliases(): # todo push into the parser
    global PROJECT_ALIASES
    PROJECT_ALIASES = {}
    if PROJECT:
        for command in PROJECT.commands:
            if command.alias:
                PROJECT_ALIASES[command.alias] = Command(command.execute, command.description)
        return [CommandArgument(cmd) for cmd in PROJECT.commands if cmd.alias]
    return None

# == Completion ==================================================================

def complete_nothing():
    return SUCCESSFULL_EXECUTION

def complete_commands():
    cmd_commands = ['--save', '--find', '--version', '--help', '-s', '-f', '-h']
    flags = ['-q', '-v', '-d']
    COMPLETE.words += ALIASES
    COMPLETE.words += PROJECT_ALIASES
    COMPLETE.words += cmd_commands
    COMPLETE.words += flags
    return SUCCESSFULL_EXECUTION

# == Argument parser =============================================================

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

def set_function(property_name, value):
    CONF[property_name] = value

def create_set_function(property_name, value):
    return lambda: (set_function(property_name, value))

def set_scope(scope):
    CONF['scope'] = scope

class FixedArgument(Argument, enum.Enum):
    SAVE = ('--save', '-s', cmd_save, 'Saves command which is passed as further arguments')
    FIND = ('--find', '-f', cmd_find, 'Opens an interactive search for saved commands')
    EDIT = ('--edit', '-e', cmd_edit, 'Edit the command databse in text editor')
    VERSION = ('--version', '-V', cmd_version, 'Prints out version information')
    HELP = ('--help', '-h', cmd_help, 'Request detailed information about flags or commands')
    COMPLETION = ('--complete', None, cmd_complete, 'Returns list of words which are supplied to the completion shell command')
    QUIET = ('--quiet', '-q', create_set_function('logging_level', config.QUIET_LEVEL), 'No output will be shown')
    VERBOSE = ('--verbose', '-v', create_set_function('logging_level', config.VERBOSE_LEVEL), 'More detailed output information')
    DEBUG = ('--debug', '-d', create_set_function('logging_level', config.DEBUG_LEVEL), 'Very detailed messages of script\'s inner workings')
    PROJECT_SCOPE = ('--project', '-p', lambda: set_scope('project'), 'Applies the command in the project command collection')
    GLOBAL_SCOPE = ('--global', '-g', lambda: set_scope('global'), 'Applies the command in the global command collection')

    def __init__(self, arg_name: str, short_arg_name: str, function, help_str: str):
        super().__init__(function, arg_name, short_arg_name, help_str)


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


class FixedArgumentGroup(ArgumentGroup, enum.Enum):
    PROJECT_COMMANDS = ('project commands', None, load_project_aliases)
    CUSTOM_COMMANDS = ('custom commands', None, load_aliases, 'You may add new custom commands via "cmd --save if the command is given alias, it will show up here')
    CMD_COMMANDS = ('management commands', [FixedArgument.SAVE, FixedArgument.FIND, FixedArgument.EDIT, FixedArgument.VERSION, FixedArgument.HELP, FixedArgument.COMPLETION])
    CMD_SHOWN_COMMANDS = ('management commands', [FixedArgument.SAVE, FixedArgument.FIND, FixedArgument.EDIT, FixedArgument.VERSION, FixedArgument.HELP])
    OUTPUT_ARGUMENTS = ('', [FixedArgument.QUIET, FixedArgument.VERBOSE, FixedArgument.DEBUG])
    OPTIONAL_ARGUMENTS = ('optional argument', [FixedArgument.QUIET, FixedArgument.VERBOSE, FixedArgument.DEBUG, FixedArgument.PROJECT_SCOPE, FixedArgument.GLOBAL_SCOPE])

class Parser:
    def __init__(self, arguments):
        self.arguments = []
        for arg in arguments:
            add_args = [arg]
            if len(arg) >= 3 and arg[0] == '-' and arg[1] != '-':
                add_args = []
                for one_letter_arg in arg[1:]:
                    add_args.append('-' + one_letter_arg)
            self.arguments += add_args

    def peek(self):
        if len(self.arguments) != 0:
            return self.arguments[0]
        return None

    def get_rest(self):
        if PRINT_HELP:
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
            raise Exception('unexpected parameter ' + cur)

    def may_have(self, groups: [ArgumentGroup]):
        current = self.peek()
        if current:
            for args in [group.arguments for group in groups if group.arguments]:
                for arg in args:
                    if current in [arg.arg_name, arg.short_arg_name]:
                        self.shift()
                        arg.function()
                        return True
        elif PRINT_HELP:
            print_str(ArgumentGroup.to_str(groups), end='')
            sys.exit(SUCCESSFULL_EXECUTION)
        return False

def remove_first_argument():
    sys.argv = [sys.argv[0]] + sys.argv[2:]

# == Main invocation =============================================================

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print_str()
        LOGGER.critical('Manually interrupted!')
