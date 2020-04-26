#!/usr/bin/env python3
# Keep the program in a single file with at most 1000 lines, if possible.

# This script provides management for custom scripts from a central location

# It IS designed to
# * make a clear overview of custom-made commands
# * provide a common user interface for the commands
# * provide a clear way to create a scripts which work well with this tool

# It IS NOT designed to
# * provide standard functions or libraries to be used in the commands
# * check correctness or analyse the commands

# === TODOS ===
# ? allow user to register project scripts
# * improve search (not only one whole regex)
# * (seems hard) copy the command into command line instead of executing it

import os, sys, argparse, logging, subprocess, enum, json, datetime, re
import readline # enables prefill for the input() method
from os.path import *

SUCCESSFULL_EXECUTION = 0
USER_ERROR = 1 # argument format is fine, but content is wrong
INVALID_ARGUMENT = 129 # argument format is wrong

VERBOSE_LEVEL = 15
TEXT_LEVEL = 30
QUIET_LEVEL = 60

conf = { 'logging_level': logging.INFO, }  # logging is set up before config loads
script_path = dirname(realpath(__file__))
working_directory = os.getcwd()
global_config_folder = join(script_path, '_config.json')
local_config_folder = join(script_path, 'config_local.json')
project_specific_subfolder = ".cmd"
version = '0.0.1'
simple_commands_file_location = join(script_path, 'commands.json')
complete = None
project_context = False # todo ?
project_root_var = 'project_root'

# == Main Logic ==================================================================

def main():
    configure()
    global args
    setup_argument_handling()
    args = parser.parse_args()
    setup_logging()
    if args.logging_level: conf['logging_level'] = args.logging_level
    logger.setLevel(conf['logging_level'])
    logger.debug('Configuration: ' + str(conf))
    logger.debug('Script folder: ' + uv(script_path))
    logger.debug('Working directory: ' + uv(working_directory))
    logger.debug('Arguments: ' + str(sys.argv))
    global project
    project = Project(working_directory)

    load_aliases()
    load_project_aliases()

    if args.flag_command is not None:
        return args.flag_command(args.command)

    if len(args.command) == 0:
        if complete: return complete_commands()
        if conf['default_command']:
            new_args = conf['default_command'].split(' ')
            if len(new_args) != 0: # prevent loop
                sys.argv += new_args
                return main()
        logger.warning('No command given')
        return USER_ERROR

    current_command = args.command[0]
    current_arguments = args.command[1:]
    if current_command in project_aliases:
        project_aliases[current_command].execute(current_arguments)
    elif current_command in aliases:
        aliases[current_command].execute(current_arguments)
    else:
        logger.warning('The given command ' + uv(current_command) + ' was not found')
        logger.info('run "cmd --help" if you are having trouble')
        return USER_ERROR

    return SUCCESSFULL_EXECUTION

# == Formatting ==================================================================

def uv(to_print):
    return '"' + str(to_print) + '"'

def print_help():
    help_str = ''
    help_str += 'usage: cmd [-q|-v|-d] <command> [<args>]\n'
    help_str += '\n'
    help_str += 'Manage custom commands from a central location\n'
    print_str(help_str)
    print_str(ArgumentGroup.to_str(), end='')
    # additional_str = ''
    # print_str(additional_str) #todo print info about very detailed peculiar options (such as --complete)

def print_str(text="", level=TEXT_LEVEL, end='\n'):
    if level >= logger.level:
        print(text, end=end)

def input_str(text="", level=TEXT_LEVEL, end=''):
    prompt = ''
    if level >= logger.level: prompt = text
    return input(prompt)

def search_and_format(pattern:str, text:str) -> (int, str):
    if text is None:
        return (0, "")
    priority = 0
    occurences = list(re.finditer(pattern, text, re.I))
    color_format = '\033[{0}m'
    color_str = color_format.format(31) # red color
    reset_str = color_format.format(0) # default color
    last_match = 0
    formatted_text = ''
    for match in occurences:
        start, end = match.span()
        formatted_text += text[last_match: start]
        formatted_text += color_str
        formatted_text += text[start: end]
        formatted_text += reset_str
        last_match = end
    formatted_text += text[last_match:]
    priority += len(occurences)
    return (priority, formatted_text)

# https://stackoverflow.com/questions/8505163/is-it-possible-to-prefill-a-input-in-python-3s-command-line-interface
def input_with_prefill(prompt, text, level=TEXT_LEVEL):
    if not level >= logger.level: prompt = ''
    def hook():
        readline.insert_text(text)
        readline.redisplay()
    readline.set_pre_input_hook(hook)
    result = input(prompt)
    readline.set_pre_input_hook()
    return result

# == Commands ====================================================================

def cmd_help(arguments):
    print_help()
    return SUCCESSFULL_EXECUTION

def cmd_version(arguments):
    if complete: return complete_nothing()
    print_str('cmd version ' + version)
    return SUCCESSFULL_EXECUTION

def cmd_save(arguments):
    command_to_save = ' '.join(arguments)
    edited = False
    if command_to_save == '':
        history_file_location = join(os.environ['HOME'],conf['history_home'])
        history_command_in_binary = subprocess.check_output(['tail','-1',history_file_location])
        history_command = history_command_in_binary[:-1].decode("utf-8")
        command_to_save = input_with_prefill('The command to be saved: ', history_command)
        edited = True
    if project_context and project.is_present() and exists(command_to_save.split(' ')[0]):
        args = command_to_save.split(' ')
        args[0] = '$' + project_root_var + '/' + os.path.relpath(join(working_directory, args[0]), project.directory) # might have problem with absolute paths
        command_to_save = ' '.join(args)
    if not edited:
        print_str('Saving command: ' + command_to_save)

    if not exists(simple_commands_file_location):
        save_json_file([], simple_commands_file_location)
    alias=input_str('Alias: ')
    description=input_str('Short description: ')
    commands_db = load_commands(simple_commands_file_location)
    commands_db += [Command(command_to_save, description, alias)]
    save_json_file(commands_db, simple_commands_file_location)
    return SUCCESSFULL_EXECUTION

def cmd_find(arguments):
    max_cmd_count = 4
    max_cmd_count_slack = 2
    commands_db = load_commands(simple_commands_file_location)
    selected_commands = []
    try:
        while True:
            print_str((40 * '='))
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
                    results += [(priority,formatted_text,command)]
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
                selected_commands += [command]
                print_str('--- ' + str(index) + ' ' + (30 * '-'))
                print_str(text, end='')
                index = index+1
            if total_results_count > cmd_showing_count:
                print_str('\nand ' + str(total_results_count-cmd_showing_count) + ' other commands')
    except EOFError as e:
        print_str()
    return SUCCESSFULL_EXECUTION

def cmd_complete(arguments):
    last_arg=sys.argv[-1]
    sys.argv=[sys.argv[0]] + sys.argv[2:-1]
    # print(sys.argv)
    global complete
    complete = Complete(last_arg)
    logger.setLevel(QUIET_LEVEL) # fix when set after main() call
    main_res=main()
    for word in complete.words:
        print(word, end=' ')
    print()
    return main_res

def load_commands(commands_file_location):
    commands_db = load_json_file(commands_file_location)
    return list(map(Command.from_json, commands_db))

def load_aliases():
    commands_db = load_commands(simple_commands_file_location)
    global aliases
    aliases = {}
    call_fun = lambda cmd : (lambda args : cmd.execute(args))
    for command in commands_db:
        if command.alias:
            aliases[command.alias]=Command(call_fun(command), command.description)
    return [CommandArgument(cmd) for cmd in commands_db if cmd.alias]

def load_project_aliases():
    global project_aliases
    project_aliases = {}
    if project.is_present():
        call_fun = lambda cmd : (lambda args : cmd.execute(args))
        for command in project.commands:
            if command.alias:
                project_aliases[command.alias]=Command(call_fun(command), command.description)
        return [CommandArgument(cmd) for cmd in project.commands if cmd.alias]
    return None

# == Structure ===================================================================

class Command:
    # command can be either str, or a function (str[]) -> None
    def __init__(self, command:any, description:str = None, alias:str = None, creation_time:str = None):
        self.command = command
        if description=='': description = None
        self.description = description
        if alias=='': alias = None
        self.alias = alias
        if creation_time is None: creation_time = str(datetime.datetime.now().strftime(conf['time_format']))
        self.creation_time = creation_time

    @classmethod
    def from_json(cls, data):
        return cls(**data)

    def find(self, query):
        to_check = [
                # {'name':'ali','field':self.alias},
                {'name':'cmd','field':self.command},
                {'name':'des','field':self.description},
                # {'name':'ctm','field':self.creation_time},
                ]
        total_priority = 0
        total_formatted_output = ""
        for check in to_check:
            (priority, formatted_output) = search_and_format(query, check['field'])
            total_priority += priority
            total_formatted_output += check['name'] + ': ' + formatted_output + '\n'
        if total_priority != 0:
            return (total_priority,total_formatted_output)
        else:
            return None

    def execute(self, args=[]):
        if project.is_present():
            os.environ[project_root_var] = project.directory
        if type(self.command) is str:
            cmd = self.command
            print_str('run command: ' + cmd)
            os.system(self.command)
        else:
            self.command(args)

class Project:
    def __init__(self, search_directory):
        self.directory = self.find_project_location(search_directory)
        if self.is_present():
            self.conf = {
                    'name': basename(self.directory),
                    'completion': None
                    }
            self.cmd_script_directory = join(self.directory, project_specific_subfolder)
            self.config_file = join(self.cmd_script_directory, 'config.json')
            conf.update(load_json_file(self.config_file))
            self.commands_file = join(self.cmd_script_directory, 'commands.json')
            self.completion_script = join(self.cmd_script_directory, 'completion.py')
            self.help_script = join(self.cmd_script_directory, 'help.py')
            if exists(self.commands_file):
                self.commands = load_commands(self.commands_file)

    def find_project_location(self, search_directory):
        currently_checked_folder = search_directory
        while True:
            possible_project_command_folder = join(currently_checked_folder, project_specific_subfolder)
            if exists(possible_project_command_folder):
                return currently_checked_folder
            if currently_checked_folder == dirname(currently_checked_folder):
                return None # we are in the root directory
            currently_checked_folder = dirname(currently_checked_folder)

    def is_present(self):
        return self.directory

    def print_help(self):
        if exists(self.help_script):
            run_script([self.help_script])
        else:
            print_str('You are in project: ' + self.name)
            print_str('This project has no explicit help')
            print_str('Add it by creating a script in \'{project dir}/.cmd/help.py\' which will be executed (to pring help) instead of this message')

# == Configuration ===============================================================

def setup_argument_handling():
    global parser
    class ArgumentParser(argparse.ArgumentParser):  # bad argument exit code override
        def error(self, message):
            self.print_usage(sys.stderr)
            self.exit(INVALID_ARGUMENT, '%s: error: %s\n' % (self.prog, message))

    parser = ArgumentParser(
            description='Manage custom scripts from a central location',
            epilog='Run without arguments to get information about available commands',
            add_help=False,
            )
    parser.add_argument('-h', '--help', dest='flag_command', const=cmd_help, action='store_const', help='Request detailed information about flags or commands')
    parser.add_argument('--version', dest='flag_command', const=cmd_version, action='store_const', help='Prints out version information')
    parser.add_argument('-s', '--save', dest='flag_command', const=cmd_save, action='store_const', help='Saves command which is passed as further arguments')
    parser.add_argument('-f', '--find', dest='flag_command', const=cmd_find, action='store_const', help='Opens an interactive search for saved commands')
    parser.add_argument('--complete', dest='flag_command', const=cmd_complete, action='store_const', help='')

    parser.add_argument('-q', '--quiet', dest='logging_level', const=QUIET_LEVEL, action='store_const', help='no output will be shown')
    parser.add_argument('-v', '--verbose', dest='logging_level', const=VERBOSE_LEVEL, action='store_const', help='more detailed info')
    parser.add_argument('-d', '--debug', dest='logging_level', const=logging.DEBUG, action='store_const', help='very detailed messages of script\'s inner workings')
    parser.add_argument('command', nargs=argparse.REMAINDER, help='command with parameters')

def setup_logging():
    logging.addLevelName(VERBOSE_LEVEL, 'VERBOSE')
    def verbose(self, message, *args, **kws):
        if self.isEnabledFor(VERBOSE_LEVEL):
            self._log(VERBOSE_LEVEL, message, args, **kws)
    logging.Logger.verbose = verbose
    global logger
    logger = logging.getLogger()
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

def configure():
    conf.update(load_json_file(global_config_folder))
    conf.update(load_json_file(local_config_folder))
    return

# == Argument parser =============================================================

class Argument:
    def to_str():
        return 'argument has undefined print'

class CommandArgument(Argument):
    def __init__(self, command:Command):
        if type(command.alias) is str:
            self.arg_name = command.alias
        self.short_arg_name = None
        self.help_str = command.description
    def to_str(self):
        res = self.arg_name
        if self.short_arg_name: res += ', ' + self.short_arg_name
        if self.help_str: res += '\t' + self.help_str
        return res

class FixedArgument(Argument,enum.Enum):
    SAVE = ('--save', '-s', cmd_save, 'Saves command which is passed as further arguments')
    FIND = ('--find', '-f', cmd_find, 'Opens an interactive search for saved commands')
    VER = ('--version', None, cmd_version, 'Prints out version information')
    HELP = ('--help', '-h', cmd_help, 'Request detailed information about flags or commands')
    COMPLETION = ('--completion', None, cmd_complete, 'Returns list of words which are supplied to the completion shell command')
    QUIET = ('--quiet', '-q', None, 'no output will be shown')
    VERBOSE = ('--verbose', '-v', None, 'more detailed output information')
    DEBUG = ('--debug', '-d', None, 'very detailed messages of script\'s inner workings')

    def __init__(self, arg_name:str, short_arg_name:str, function, help_str:str):
        self.arg_name = arg_name
        self.short_arg_name = short_arg_name
        self.function = function
        self.help_str = help_str

    def to_str(self):
        res = ''
        res += self.arg_name
        if self.short_arg_name:
            res += ', ' + self.short_arg_name
        res += '\t' + self.help_str
        return res
    
class ArgumentGroup(enum.Enum):
    PROJECT_COMMANDS = ('project commands', None, load_project_aliases)
    CUSTOM_COMMANDS = ('custom commands', None, load_aliases, 'You may add new custom commands via "cmd --save if the command is given alias, it will show up here')
    FLAG_COMMANDS = ('management commands', [FixedArgument.SAVE, FixedArgument.FIND, FixedArgument.VER, FixedArgument.HELP])
    OPTIONAL_ARGUMENTS = ('optional argument', [FixedArgument.QUIET, FixedArgument.VERBOSE, FixedArgument.DEBUG])

    def __init__(self, group_name:str, arguments:[Argument]=None, arg_fun=None, if_empty:str=None):
        self.group_name = group_name
        self.arguments = arguments
        self.arg_fun = arg_fun
        self.if_empty = if_empty

    @staticmethod
    def to_str():
        res = ""
        for group in ArgumentGroup:
            if res!='': res += '\n'
            args = group.arguments
            if not args and group.arg_fun:
                args = group.arg_fun()
            if args:
                res += group.group_name + ":\n"
                for argument in args:
                    res += '   ' + argument.to_str() + '\n'
            elif group.if_empty:
                res += group.group_name + ":\n"
                res += '   ' + group.if_empty + '\n'
        return res
        

class Parser:
    def __init__(self):
        pass

    def peek(self):
        return sys.argv[0]

    def shift(self):
        res = peek()
        sys.argv = sys.argv[1:]
        return res

    def argument_may(self, group:ArgumentGroup):
        current = self.peek()
        for arg in group:
            if current in [arg.arg_name, arg.short_arg_name]:
                arg.function()

    def argument_must(self, group:ArgumentGroup):
        argument_may()
        raise Exception('argument was expected') # todo make the exception more descriptive


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
                res_words += [word]
        return res_words

    @words.setter
    def words(self, words):
        self.__words = words

def complete_nothing():
    return SUCCESSFULL_EXECUTION

def complete_commands():
    flag_commands = ['--save','--find','--version','--help','--complete','-s','-f','-h']
    flags = ['-q','-v','-d']
    complete.words += aliases
    complete.words += flag_commands
    complete.words += flags
    return SUCCESSFULL_EXECUTION

# == File Manipulation ===========================================================

def save_json_file(json_content_object, file_location):
    # fail-safe when JSON-serialization fails
    file_string = json.dumps(json_content_object, default=lambda o: o.__dict__, ensure_ascii=False, indent=4)
    with open(file_location, 'w', encoding='utf-8') as f:
        f.write(file_string)

def load_json_file(file_location):
    try:
        with open(file_location) as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        return dict()
    return data

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

