#!/usr/bin/env python3

import os, sys, subprocess, enum, datetime, shlex
from string import Template
from os.path import *

import util, config, cio, filemanip, structure
from cio import uv, print_str, input_str, input_with_prefill, search_and_format
from structure import Command, Project

SUCCESSFULL_EXECUTION = 0
USER_ERROR = 1 # argument format is fine, but content is wrong
INVALID_ARGUMENT = 129 # argument format is wrong

script_path = dirname(dirname(realpath(__file__)))
working_directory = os.getcwd()
version = '0.0a1-dev1'
global_commands_file_location = join(script_path, 'commands.json')
complete = None
print_help = False
project_root_var = 'project_root'
default_command_load_deja_vu = False
conf = config.get_conf()

# == Main Logic ==================================================================

def main():
    config.setup_logging()
    global logger
    logger = config.get_logger()
    global parser
    parser = Parser(sys.argv)
    parser.shift() # skip the program invocation
    while parser.may_have([FixedArgumentGroup.OUTPUT_ARGUMENTS]): pass
    logger.setLevel(conf['logging_level'])
    logger.debug('Configuration: ' + str(conf))
    logger.debug('Script folder: ' + uv(script_path))
    logger.debug('Working directory: ' + uv(working_directory))
    logger.debug('Arguments: ' + str(sys.argv))
    global project
    project = Project.retrieve_project_if_present(working_directory)

    load_aliases()
    load_project_aliases()
    while parser.may_have([FixedArgumentGroup.OPTIONAL_ARGUMENTS]): pass
    if conf['scope']=='auto':
        if project: conf['scope']='project'
        else: conf['scope']='global'
    return main_command()

def main_command():
    current_command = parser.peek()

    if not current_command:
        if complete: return complete_commands()
        if print_help: return print_general_help()
        if conf['default_command']:
            new_args = conf['default_command'].split(' ')
            global default_command_load_deja_vu
            if len(new_args) != 0: # prevent doing nothing due to empty default command
                if default_command_load_deja_vu: # prevent adding default command multiple times
                    logger.warning('The default command is invalid, it must include a command argument')
                    return USER_ERROR
                default_command_load_deja_vu = True
                sys.argv += new_args
                return main()
        logger.warning('No command given')
        return USER_ERROR

    if not parser.may_have([FixedArgumentGroup.PROJECT_COMMANDS, FixedArgumentGroup.CUSTOM_COMMANDS, FixedArgumentGroup.CMD_COMMANDS]):
        logger.warning('The argument/command ' + uv(current_command) + ' was not found')
        logger.info('run "cmd --help" if you are having trouble')
        return USER_ERROR

    return SUCCESSFULL_EXECUTION

# == Formatting ==================================================================

def print_general_help():
    help_str = ''
    help_str += 'usage: cmd [-q|-v|-d] [-g|-p] <command> [<args>]\n'
    help_str += '\n'
    help_str += 'Manage custom commands from a central location\n'
    print_str(help_str)
    main_groups = [FixedArgumentGroup.PROJECT_COMMANDS,
                FixedArgumentGroup.CUSTOM_COMMANDS,
                FixedArgumentGroup.CMD_SHOWN_COMMANDS,
                FixedArgumentGroup.OPTIONAL_ARGUMENTS]
    print_str(ArgumentGroup.to_str(main_groups), end='')
    # additional_str = ''
    # print_str(additional_str) #todo print info including special options (such as --complete)
        
    return SUCCESSFULL_EXECUTION

# == Commands ====================================================================

def cmd_help():
    if complete: return main_command()
    global print_help
    print_help = True
    remove_first_argument()
    return main_command()

def cmd_version():
    if complete: return complete_nothing()
    print_str('cmd version ' + version)
    parser.expect_nothing()
    return SUCCESSFULL_EXECUTION

def cmd_save():
    if complete: return complete_nothing()
    alias = ''
    description = ''
    ar = [
        Argument(lambda:print('TODO'), '--alias', '-a', 'one word shortcut used to invoke the command'),
        Argument(lambda:print('TODO'), '--descr', '-d', 'few words about the command\'s functionality'),
        Argument(lambda:print('TODO'), '--', None, 'command to be saved follows'),
    ]
    while parser.may_have([ArgumentGroup('test', ar)]): pass
    args = parser.get_rest()
    show_edit = False

    if len(args) == 0: # supply the last command from history
        history_file_location = join(os.environ['HOME'],conf['history_home'])
        history_command_in_binary = subprocess.check_output(['tail','-1',history_file_location])
        history_command = history_command_in_binary[:-1].decode("utf-8")
        args = history_command.split(' ')
        show_edit = True

    if len(args) > 0 and exists(args[0]): # substitute relative file path for absolute 
        if conf['scope']=='project':
            args[0] = '$' + project_root_var + '/' + os.path.relpath(join(working_directory, args[0]), project.directory)
        if conf['scope']=='global':
            args[0] = os.path.realpath(join(working_directory, args[0]))
        show_edit = True

    command_to_save = ' '.join(args)

    if show_edit:
        edited_command = input_with_prefill('The command to be saved: ', command_to_save)
    else:
        print_str('Saving command: ' + command_to_save)

    if conf['scope']=='project': commands_file_location = project.commands_file
    if conf['scope']=='global': commands_file_location = global_commands_file_location

    if not exists(commands_file_location):
        filemanip.save_json_file([], commands_file_location)
    if alias=='': alias=input_str('Alias: ')
    if description=='': description=input_str('Short description: ')
    commands_db = load_commands(commands_file_location)
    commands_db.append(Command(command_to_save, description, alias))
    filemanip.save_json_file(commands_db, commands_file_location)
    return SUCCESSFULL_EXECUTION

def cmd_find():
    if complete: return complete_nothing()
    max_cmd_count = 4
    max_cmd_count_slack = 2
    commands_db = load_commands(global_commands_file_location)
    if project:
        commands_db += project.commands
    selected_commands = []
    try:
        while True:
            print_str(40 * '=')
            arguments = parser.get_rest()
            if len(arguments) != 0:
                query = ' '.join(arguments)
                arguments = []
            else:
                query = input_str('query $ ')
            try:
                idx = int(query)
                if idx not in range(1,len(selected_commands)+1):
                    print_str('invalid index')
                    continue
                selected_commands[idx-1].execute() # todo add arguments ?
                return
            except ValueError as e:
                pass
            index = 1
            results = []
            for command in commands_db:
                result = command.find(query)
                if result is not None:
                    (priority,formatted_text) = result
                    results.append((priority,formatted_text,command))
            total_results_count = len(results)
            if total_results_count==0:
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
    except EOFError as e:
        print_str()
    return SUCCESSFULL_EXECUTION

def cmd_edit():
    if complete: return complete_nothing()
    subprocess.run([os.path.expandvars('$EDITOR'), global_commands_file_location])
    return SUCCESSFULL_EXECUTION

def cmd_complete():
    global complete
    last_arg=sys.argv[-1]
    remove_first_argument()
    if complete: return main()
    complete = Complete(last_arg)
    logger.setLevel(config.QUIET_LEVEL) # fix when set after main() call
    main_res=main()
    for word in complete.words:
        print(word, end=' ')
    print()
    return main_res

def load_commands(commands_file_location):
    commands_db = filemanip.load_json_file(commands_file_location)
    return list(map(Command.from_json, commands_db))

def load_aliases(): # todo simplify
    commands_db = load_commands(global_commands_file_location)
    global aliases
    aliases = {}
    call_fun = lambda cmd : (lambda args : cmd.execute(args))
    for command in commands_db:
        if command.alias:
            aliases[command.alias]=Command(call_fun(command), command.description)
    return [CommandArgument(cmd) for cmd in commands_db if cmd.alias]

def load_project_aliases(): # todo push into the parser
    global project_aliases
    project_aliases = {}
    if project:
        call_fun = lambda cmd : (lambda args : cmd.execute(args))
        for command in project.commands:
            if command.alias:
                project_aliases[command.alias]=Command(call_fun(command), command.description)
        return [CommandArgument(cmd) for cmd in project.commands if cmd.alias]
    return None

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
        (width, height) = util.get_terminal_dimensions()
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
    def __init__(self, command:Command):
        super().__init__(lambda : (command.execute()), command.alias, None, command.description)

def set_function(property_name, value):
    conf[property_name]=value

def create_set_function(property_name, value):
    return (lambda : (set_function(property_name, value)))

def set_scope(scope):
    conf['scope']=scope

class FixedArgument(Argument,enum.Enum):
    SAVE = ('--save', '-s', cmd_save, 'Saves command which is passed as further arguments')
    FIND = ('--find', '-f', cmd_find, 'Opens an interactive search for saved commands')
    EDIT = ('--edit', '-e', cmd_edit, 'Edit the command databse in text editor')
    VERSION = ('--version', '-V', cmd_version, 'Prints out version information')
    HELP = ('--help', '-h', cmd_help, 'Request detailed information about flags or commands')
    COMPLETION = ('--complete', None, cmd_complete, 'Returns list of words which are supplied to the completion shell command')
    QUIET = ('--quiet', '-q', create_set_function('logging_level', config.QUIET_LEVEL), 'No output will be shown')
    VERBOSE = ('--verbose', '-v', create_set_function('logging_level', config.VERBOSE_LEVEL), 'More detailed output information')
    DEBUG = ('--debug', '-d', create_set_function('logging_level', config.DEBUG_LEVEL), 'Very detailed messages of script\'s inner workings')
    PROJECT_SCOPE = ('--project', '-p', lambda : set_scope('project'), 'Applies the command in the project command collection')
    GLOBAL_SCOPE = ('--global', '-g', lambda : set_scope('global'), 'Applies the command in the global command collection')

    def __init__(self, arg_name:str, short_arg_name:str, function, help_str:str):
        super().__init__(function, arg_name, short_arg_name, help_str)

    
class ArgumentGroup:
    def __init__(self, group_name:str, arguments:[Argument]=None, arg_fun=None, if_empty:str=None):
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
            if res!='': res += '\n'
            args = group.arguments
            if not args and group.arg_fun:
                args = group.arg_fun()
            if args and len(args)!=0:
                res += group.group_name + ":\n"
                for argument in args:
                    res += argument.to_str()
            elif group.if_empty:
                res += group.group_name + ":\n"
                res += '   ' + group.if_empty + '\n'
        return res


class FixedArgumentGroup(ArgumentGroup,enum.Enum):
    PROJECT_COMMANDS = ('project commands', None, load_project_aliases)
    CUSTOM_COMMANDS = ('custom commands', None, load_aliases, 'You may add new custom commands via "cmd --save if the command is given alias, it will show up here')
    CMD_COMMANDS = ('management commands', [FixedArgument.SAVE, FixedArgument.FIND, FixedArgument.EDIT, FixedArgument.VERSION, FixedArgument.HELP, FixedArgument.COMPLETION])
    CMD_SHOWN_COMMANDS = ('management commands', [FixedArgument.SAVE, FixedArgument.FIND, FixedArgument.EDIT, FixedArgument.VERSION, FixedArgument.HELP])
    OUTPUT_ARGUMENTS = ('', [FixedArgument.QUIET, FixedArgument.VERBOSE, FixedArgument.DEBUG])
    OPTIONAL_ARGUMENTS = ('optional argument', [FixedArgument.QUIET, FixedArgument.VERBOSE, FixedArgument.DEBUG, FixedArgument.PROJECT_SCOPE, FixedArgument.GLOBAL_SCOPE])

    def __init__(self, group_name:str, arguments:[Argument]=None, arg_fun=None, if_empty:str=None):
        super().__init__(group_name, arguments, arg_fun, if_empty)

class Parser:
    def __init__(self, arguments):
        self.arguments = []
        for arg in arguments:
            add_args = [arg]
            if len(arg) >= 3 and arg[0]=='-' and arg[1]!='-':
                add_args = []
                for a in arg[1:]:
                    add_args.append('-'+a)
            self.arguments += add_args

    def peek(self):
        if len(self.arguments) != 0:
            return self.arguments[0]
        return None

    def get_rest(self):
        if print_help:
            exit(SUCCESSFULL_EXECUTION)
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

    def may_have(self, groups:[ArgumentGroup]):
        current = self.peek()
        if current:
            for args in [group.arguments for group in groups if group.arguments]:
                for arg in args:
                    if current in [arg.arg_name, arg.short_arg_name]:
                        self.shift()
                        arg.function()
                        return True
        elif print_help:
            print_str(ArgumentGroup.to_str(groups), end='')
            exit(SUCCESSFULL_EXECUTION)
        return False

def remove_first_argument():
    sys.argv=[sys.argv[0]] + sys.argv[2:]

# == Completion ==================================================================

class Complete:
    def __init__(self, last_arg):
        self.last_arg = last_arg
        self.words = []

    @property
    def words(self):
        res_words = []
        for word in self.__words:
            if word.startswith(self.last_arg) and (len(self.last_arg) != 0 or '-'!=word[0]):
                res_words.append(word)
        return res_words

    @words.setter
    def words(self, words):
        self.__words = words

def complete_nothing():
    return SUCCESSFULL_EXECUTION

def complete_commands():
    cmd_commands = ['--save','--find','--version','--help','-s','-f','-h']
    flags = ['-q','-v','-d']
    complete.words += aliases
    complete.words += project_aliases
    complete.words += cmd_commands
    complete.words += flags
    return SUCCESSFULL_EXECUTION

# == Core Script Logic Chunks ====================================================

def run_script(command_with_arguments):
    try:
        os.environ[project_root_var] = project.directory
        p = subprocess.Popen(command_with_arguments)
        try:
            p.wait()
        except subprocess.TimeoutExpired as ex:
            p.kill()
            raise ex
    except PermissionError:
        print_str('Script: ' + str(command_with_arguments))
        print_str('could not be run, because the file is not executable')
    except KeyboardInterrupt:
        print_str()

# == Main invocation =============================================================

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print_str()
        logger.critical('Manually interrupted!')

