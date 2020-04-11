#!/usr/bin/env python3
# Keep the program in a single file with at most 1000 lines, if possible.

# This script provides management for custom scripts from a central location

# It IS designed to
# * make a clear overview of custom-made commands
# * provide a common user interface for the commands
# * provide a clear way to create a command which works well with this tool
# * basic / advanced mode, basic has only save and find

# It IS NOT designed to
# * provide standard functions or libraries to be used in the commands
# * check correctness or analyse the commands

# === TODOS ===
# * improve search (not only one whole regex)
# * print text into proper logging level
# * make help generated, not hardcoded
# * (seems hard) copy the command into command line instead of executing it

import os, sys, argparse, logging, subprocess, enum, json, datetime, re
import readline # enables arrows in the input() method
from os.path import *

SUCCESSFULL_EXECUTION = 0
USER_ERROR = 1 # argument format is fine, but content is wrong
INVALID_ARGUMENT = 129 # argument format is wrong

VERBOSE_LEVEL = 15
QUIET_LEVEL = 60

class ArgumentParser(argparse.ArgumentParser):  # bad argument exit code override
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(INVALID_ARGUMENT, '%s: error: %s\n' % (self.prog, message))

parser = ArgumentParser(
        description='Manage custom scripts from a central location',
        epilog='Run without arguments to get information about available commands',
        add_help=False,
        )
parser.add_argument('-h', '--help', dest='help', action='store_true', help='show this help message and exit')
parser.add_argument('--version', dest='version', action='store_true', help='prints out version information')
parser.add_argument('-q', '--quiet', dest='logging_level', const=QUIET_LEVEL, action='store_const', help='no output will be shown')
parser.add_argument('-v', '--verbose', dest='logging_level', const=VERBOSE_LEVEL, action='store_const', help='more detailed info')
parser.add_argument('-d', '--debug', dest='logging_level', const=logging.DEBUG, action='store_const', help='very detailed messages of script\'s inner workings')
parser.add_argument('command', nargs=argparse.REMAINDER, help='command with parameters')

conf = { 'logging_level': logging.INFO, }  # logging is set up before config loads
script_path = dirname(realpath(__file__))
working_directory = os.getcwd()
global_config_folder = join(script_path, 'config.json')
local_config_folder = join(script_path, 'config_local.json')
cmd_script_directory_name = ".cmd"
version = '0.0.1'
simple_commands_file_location = join(script_path, 'commands.json')
time_format = '%Y-%m-%d %H:%M:%S'


# == Main Logic ==================================================================

def main():
    configure()
    global args
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

    if args.version:
        print('cmd version ' + version)
        return SUCCESSFULL_EXECUTION

    if args.help:
        print_help()
        return SUCCESSFULL_EXECUTION

    if len(args.command) == 0:
        logger.warning('No command given')
        print_help()
        return USER_ERROR

    global commands
    commands = {}
    commands['save']=cmd_save
    commands['find']=cmd_find
    current_command = args.command[0]
    current_arguments = args.command[1:]
    if current_command in commands:
        commands[current_command](current_arguments)

    return SUCCESSFULL_EXECUTION

# == Formatting ==================================================================

def uv(to_print):
    return '"' + str(to_print) + '"'

def print_help():
    if is_in_advanced_mode():
        print('usage: cmd [--version] [--help] [-q] [-v] [-d] <command> [<args>]')
        print('')
        print('Manage custom commands from a central location')
        print('')
        print('commands:')
        print('   save         saves command which is passed as further arguments')
        print('   find         opens an interactive search for saved commands')
        print('')
        print('optional arguments:')
        print('  --version     prints out version information')
        print('  --help        show this help message and exit')
        print('  -q, -v, -d    quiet/verbose/debug output information')
        print('')
        print('Enable advanced mode for more features, see documentation')
    else:
        print('usage: cmd [--version] [--help] [-q] [-v] [-d] <command> [<args>]')
        print('')
        print('Manage custom commands from a central location')
        print('')
        print('commands:')
        print('   save         saves command which is passed as further arguments')
        print('   find         opens an interactive search for saved commands')
        print('')
        print('optional arguments:')
        print('  --version     prints out version information')
        print('  --help        show this help message and exit')
        print('  -q, -v, -d    quiet/verbose/debug output information')
        print('')
        print('Enable advanced mode for more features, see documentation')

def search_and_format(pattern:str, text:str) -> (int, str):
    if text is None:
        return (0, "")
    priority = 0
    occurences = list(re.finditer(pattern, text))
    color_format = '\033[{0}m'
    color_str = color_format.format(31) # red color
    reset_str = color_format.format(0)
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
def input_with_prefill(prompt, text):
    def hook():
        readline.insert_text(text)
        readline.redisplay()
    readline.set_pre_input_hook(hook)
    result = input(prompt)
    readline.set_pre_input_hook()
    return result

# == Commands ====================================================================

def cmd_save(arguments):
    command_to_save = ' '.join(arguments)
    if command_to_save == '':
        history_command_in_binary = subprocess.check_output(['tail','-1',join(os.environ['HOME'],'.bash_history')])
        history_command = history_command_in_binary[:-1].decode("utf-8")
        command_to_save = input_with_prefill('The command to be saved: ', history_command)

    if not exists(simple_commands_file_location):
        save_json_file([], simple_commands_file_location)
    description=input('Short description: ')
    commands_db = load_commands()
    commands_db += [Command(command_to_save, description)]
    save_json_file(commands_db, simple_commands_file_location)

def cmd_find(arguments):
    commands_db = load_commands()
    selected_commands = []
    try:
        while True:
            print((40 * '='))
            if len(arguments) != 0:
                query = ' '.join(arguments)
                arguments = []
            else:
                query = input('query $ ')
            try:
                idx = int(query)
                if idx not in range(1,len(selected_commands)+1):
                    print('invalid index')
                    continue
                command_string = selected_commands[idx-1].command
                run_string_command(command_string)
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
            results = sorted(results, reverse=True) # by priority
            selected_commands = []
            for result in results:
                (_, text, command) = result
                selected_commands += [command]
                print('--- ' + str(index) + ' ' + (30 * '-'))
                print(text, end='')
                index = index+1
            if len(results)==0:
                print('No results found')
    except EOFError as e:
        print()

def load_commands():
    commands_db = load_json_file(simple_commands_file_location)
    return list(map(Command.from_json, commands_db))

# == Structure ===================================================================

class Command:
    def __init__(self, command:str, description:str = None, alias:str = None, creation_time:str = None):
        self.command = command
        if description=='': description = None
        self.description = description
        if alias=='': alias = None
        self.alias = alias
        if creation_time is None: creation_time = str(datetime.datetime.now().strftime(time_format))
        self.creation_time = creation_time

    @classmethod
    def from_json(cls, data):
        return cls(**data)

    def info_string(self):
        ans = ''
        ans += 'com: ' + self.command + '\n'
        if self.alias is not None:
            ans += 'ali: ' + self.alias + '\n'
        if self.description is not None:
            ans += 'des: ' + self.description + '\n'
        if self.creation_time is not None:
            ans += 'ctm: ' + self.creation_time + '\n'
        return ans

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

class Project:
    def __init__(self, search_directory):
        self.directory = self.find_project_location(search_directory)
        if self.is_present():
            self.name = basename(self.directory)
            self.cmd_script_directory = join(self.directory, cmd_script_directory_name)
            self.commands_directory = join(self.cmd_script_directory, 'commands')
            self.completion_script = join(self.cmd_script_directory, 'completion.py')
            self.help_script = join(self.cmd_script_directory, 'help.py')
            if exists(self.commands_directory):
                self.command_files = list(os.listdir(self.commands_directory))

    def find_project_location(self, search_directory):
        currently_checked_folder = search_directory
        while True:
            possible_project_command_folder = join(currently_checked_folder, cmd_script_directory_name)
            if exists(possible_project_command_folder):
                return currently_checked_folder
            if currently_checked_folder == dirname(currently_checked_folder):
                return None # we are in the root directory
            currently_checked_folder = dirname(currently_checked_folder)

    def is_present(self):
        return self.directory is not None

    def print_help(self):
        if exists(self.help_script):
            run_script([self.help_script])
        else:
            print('You are in project: ' + self.name)
            print('This project has no explicit help')
            print('Add it by creating a script in \'{project dir}/.cmd/help.py\' which will be printed instead of this message')

# == Configuration ===============================================================

def is_in_advanced_mode():
    return 'mode' in conf and conf['mode'] == 'advanced'

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

# == File Manipulation ===========================================================

def save_json_file(json_content_object, file_location):
    file_string = json.dumps(json_content_object, default=lambda o: o.__dict__, ensure_ascii=False, indent=4)
    # fail-safe when JSON-serialization fails
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

def run_string_command(command_string):
    print('run command:',command_string)
    os.system(command_string)

def run_script(command_with_arguments):
    try:
        os.environ["project_root"] = project.directory
        p = subprocess.Popen(command_with_arguments)
        try:
            # timeout_seconds = 60
            # p.wait(timeout_seconds)
            p.wait()
        except subprocess.TimeoutExpired as ex:
            p.kill()
            raise ex
    except PermissionError:
        print('Script: '+str(command_with_arguments))
        print('could not be run, because the file is not executable')
    except KeyboardInterrupt:
        print()

# == Main invocation =============================================================

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        logger.critical('Manually interrupted!')

