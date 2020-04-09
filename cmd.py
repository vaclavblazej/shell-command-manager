#!/usr/bin/env python3
# Keep the program in a single file with at most 1000 lines, if possible.

# This script provides management for custom scripts from a central location

# It IS designed to
# * make a clear overview of custom-made commands
# * provide a common user interface for the commands
# * provide a clear way to create a command which works well with this tool
# * 'cmd save {cmd}' will save the command to the general commands
# * 'cmd find' runs interactive search mode, chosen command will be paster to the terminal
# * basic / advanced mode, basic has only save and find

# It IS NOT designed to
# * provide standard functions or libraries to be used in the commands
# * check correctness or analyse the commands
# * todo ...

# === TODOS ===
# * todo ...

import os, sys, argparse, logging, subprocess, enum, json
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
parser.add_argument('command', nargs='*', help='command with parameters')

conf = { 'logging_level': logging.INFO, }  # logging is set up before config loads
script_path = dirname(realpath(__file__))
working_directory = os.getcwd()
global_config_folder = join(script_path, 'config.json')
local_config_folder = join(script_path, 'config_local.json')
cmd_script_directory_name = ".cmd"
version = '0.0.1'


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

    if args.help or len(sys.argv) == 1:
        print_help()
        return SUCCESSFULL_EXECUTION

    global commands
    commands = {}
    commands['save']=cmd_save
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
        print('advanced')
    else:
        print('usage: cmd [--version] [--help] [-q] [-v] [-d] command')
        print('')
        print('Manage custom commands from a central location')
        print('')
        print('command arguments:')
        print('   save         saves command which is passed as further arguments')
        print('   find         opens an interactive search for saved commands')
        print('')
        print('optional arguments:')
        print('  --version     prints out version information')
        print('  -h, --help    show this help message and exit')
        print('  -q, -v, -d    quiet/verbose/debug output information')
        print('')
        print('Enable advanced mode for more features, see documentation')

# == Commands ====================================================================

def cmd_save(arguments):
    command_to_save = ' '.join(arguments)
    print('todo save to json file: ' + command_to_save)

# == Structure ===================================================================

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
            run_command([self.help_script])
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
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_json_file(file_location):
    try:
        with open(file_location) as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        return dict()
    return data

# == Core Script Logic Chunks ====================================================

def load_commands(group_name, directory):
    # load commands from external files
    pass

def run_command(command_with_arguments):
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
        print('Command: '+str(command_with_arguments))
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

