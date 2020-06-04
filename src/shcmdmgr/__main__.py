#!/usr/bin/env python3
#
#    shell-command-manager
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
from string import Template

from shcmdmgr import util, config, filemanip, command, project, complete, args, parser, cio
from shcmdmgr.command import Command, load_commands
from shcmdmgr.project import Project
from shcmdmgr.config import SCRIPT_PATH, GLOBAL_COMMANDS_FILE_LOCATION
from shcmdmgr.args import Argument, CommandArgument, ArgumentGroup
from shcmdmgr.parser import Parser

SUCCESSFULL_EXECUTION = 0
USER_ERROR = 1 # argument format is fine, but content is wrong
INVALID_ARGUMENT = 129 # argument format is wrong

WORKING_DIRECTORY = os.getcwd()
COMPLETE = None
PRINT_HELP = False
project_ROOT_VAR = 'project_root'
DEFAULT_COMMAND_LOAD_DEJA_VU = False
form = None
conf = None
logger = None
parser = None
project = None
project_ALIASES = None
ALIASES = None

# == Main Logic ==================================================================

def main():
    conf = config.get_conf()
    logger = config.get_logger()
    form = cio.Formatter(conf, logger)
    fixed_argument_group = fixed_argument_groups()
    parser = Parser(sys.argv, PRINT_HELP) # todo changes after?
    parser.shift() # skip the program invocation
    parser.load_all([fixed_argument_group['OUTPUT_ARGUMENTS']])
    logger.setLevel(conf['logging_level'])
    logger.debug('Configuration: %s', str(conf))
    logger.debug('Script folder: %s', form.quote(SCRIPT_PATH))
    logger.debug('Working directory: %s', form.quote(WORKING_DIRECTORY))
    logger.debug('Arguments: %s', str(sys.argv))
    project = Project.retrieve_project_if_present(WORKING_DIRECTORY, form)
    if project: os.environ[project_ROOT_VAR] = project.directory # expose variable to subprocesses
    # load_aliases() # todo
    # load_project_aliases()
    parser.load_all([ArgumentGroup.OPTIONAL_ARGUMENTS])
    if conf['scope'] == 'auto':
        if project: conf['scope'] = 'project'
        else: conf['scope'] = 'global'
    return App(conf, logger, form, fixed_argument_group, parser).main_command()

class App:
    def __init__(conf, logger, form, fixed_argument_group, parser):
        self.conf = conf
        self.logger = logger
        self.form = form
        self.fixed_argument_group = fixed_argument_group
        self.parser = parser

    def main_command():
        current_command = parser.peek()
        if not current_command:
            if COMPLETE: return complete_commands(ALIASES + project_ALIASES)
            if PRINT_HELP: return print_general_help()
            if self.conf['default_command']:
                new_args = self.conf['default_command'].split(' ')
                global DEFAULT_COMMAND_LOAD_DEJA_VU
                if len(new_args) != 0: # prevent doing nothing due to empty default command
                    if DEFAULT_COMMAND_LOAD_DEJA_VU: # prevent adding default command multiple times
                        logger.warning('The default command is invalid, it must include a command argument')
                        return USER_ERROR
                    DEFAULT_COMMAND_LOAD_DEJA_VU = True
                    sys.argv += new_args
                    return main()
            logger.warning('No command given')
            return USER_ERROR
        if not parser.may_have([ArgumentGroup.PROJECT_COMMANDS, ArgumentGroup.CUSTOM_COMMANDS, ArgumentGroup.CMD_COMMANDS]):
            logger.warning('The argument/command %s was not found', form.quote(current_command))
            logger.info('run "cmd --help" if you are having trouble')
            return USER_ERROR
        return SUCCESSFULL_EXECUTION

    # == Formatting ==================================================================
    def print_general_help():
        help_str = ''
        help_str += 'usage: cmd [-q|-v|-d] [-g|-p] <command> [<args>]\n'
        help_str += '\n'
        help_str += 'Manage custom commands from a central location\n'
        form.print_str(help_str)
        main_groups = [
            ArgumentGroup.PROJECT_COMMANDS,
            ArgumentGroup.CUSTOM_COMMANDS,
            ArgumentGroup.CMD_SHOWN_COMMANDS,
            ArgumentGroup.OPTIONAL_ARGUMENTS,
        ]
        form.print_str(ArgumentGroup.to_str(main_groups), end='')
        # additional_str = ''
        # form.print_str(additional_str) #todo print info including special options (such as --complete)
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
        form.print_str('cmd version ' + config.VERSION)
        parser.expect_nothing()
        return SUCCESSFULL_EXECUTION

    def cmd_save():
        alias = ''
        description = ''
        other_args = [
            Argument(lambda: print('TODO'), '--alias', '-a', 'one word shortcut used to invoke the command'),
            Argument(lambda: print('TODO'), '--descr', '-d', 'few words about the command\'s functionality'),
            Argument(lambda: print('TODO'), '--', None, 'command to be saved follows'),
        ]
        parser.load_all([ArgumentGroup('save arguments (missing will be queried)', other_args)])
        args = parser.get_rest()
        if COMPLETE: return complete_nothing()
        show_edit = False
        if len(args) == 0: # supply the last command from history
            history_file_location = join(os.environ['HOME'], self.conf['history_home'])
            history_command_in_binary = subprocess.check_output(['tail', '-1', history_file_location])
            history_command = history_command_in_binary[:-1].decode("utf-8")
            args = history_command.split(' ')
            show_edit = True
        if len(args) > 0 and exists(args[0]): # substitute relative file path for absolute
            if self.conf['scope'] == 'project':
                path_from_project_root = os.path.relpath(join(WORKING_DIRECTORY, args[0]), project.directory)
                args[0] = '${root_var}/{path}'.format(project_ROOT_VAR, path_from_project_root)
            if self.conf['scope'] == 'global':
                args[0] = os.path.realpath(join(WORKING_DIRECTORY, args[0]))
            show_edit = True
        command_to_save = ' '.join(args)
        if show_edit:
            command_to_save = input_str('The command to be saved: ', prefill=command_to_save)
        else:
            form.print_str('Saving command: ' + command_to_save)
        commands_file_location = get_context_command_file_location()
        if not exists(commands_file_location):
            filemanip.save_json_file([], commands_file_location)
        if alias == '': alias = input_str('Alias: ')
        if description == '': description = input_str('Short description: ')
        commands_db = load_commands(commands_file_location)
        commands_db.append(Command(command_to_save, description, alias))
        filemanip.save_json_file(commands_db, commands_file_location)
        return SUCCESSFULL_EXECUTION

    def get_context_command_file_location() -> str:
        if self.conf['scope'] == 'project' and project: return project.commands_file
        if self.conf['scope'] == 'global': return GLOBAL_COMMANDS_FILE_LOCATION
        return None

    def cmd_find():
        if COMPLETE: return complete_nothing()
        max_cmd_count = 4
        max_cmd_count_slack = 2
        commands_db = load_commands(GLOBAL_COMMANDS_FILE_LOCATION)
        if project:
            commands_db += project.commands
        selected_commands = []
        try:
            while True:
                form.print_str(40 * '=')
                arguments = parser.get_rest()
                if len(arguments) != 0:
                    query = ' '.join(arguments)
                    arguments = []
                else:
                    query = input_str('query $ ')
                try:
                    idx = int(query)
                    if idx not in range(1, len(selected_commands)+1):
                        form.print_str('invalid index')
                        continue
                    selected_commands[idx-1].execute(parser.get_rest())
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
                    form.print_str('No results found')
                results = sorted(results, reverse=True) # by priority
                selected_commands = []
                cmd_showing_count = max_cmd_count
                if total_results_count <= cmd_showing_count + max_cmd_count_slack:
                    cmd_showing_count += max_cmd_count_slack
                for result in results[:cmd_showing_count]:
                    (_, text, command) = result
                    selected_commands.append(command)
                    form.print_str('--- ' + str(index) + ' ' + (30 * '-'))
                    form.print_str(text, end='')
                    index = index+1
                if total_results_count > cmd_showing_count:
                    form.print_str('\nand ' + str(total_results_count-cmd_showing_count) + ' other commands')
        except EOFError as _:
            form.print_str()
        return SUCCESSFULL_EXECUTION

    def cmd_edit():
        if COMPLETE: return complete_nothing()
        editor = 'vim'
        try:
            editor = Template('$EDITOR').substitute(os.environ)
        except KeyError:
            pass
        subprocess.run([editor, get_context_command_file_location()], check=True)
        return SUCCESSFULL_EXECUTION

    def cmd_complete():
        global COMPLETE
        last_arg = sys.argv[-1]
        sys.argv = sys.argv[:-1]
        remove_first_argument()
        if COMPLETE: return main()
        COMPLETE = complete.get_complete(last_arg)
        logger.setLevel(config.QUIET_LEVEL) # fix when set after main() call
        main_res = main()
        for word in COMPLETE.words:
            print(word, end=' ')
        print()
        return main_res

    def cmd_completion():
        shell = parser.shift()
        parser.expect_nothing()
        completion_init_script_path = complete.completion_setup_script_path(shell, self.conf)
        if exists(completion_init_script_path):
            form.print_str('source {} cmd'.format(completion_init_script_path))
        else:
            raise Exception('unsuported shell {}, choose bash or zsh'.format(form.quote(shell)))
        return SUCCESSFULL_EXECUTION

    def load_aliases(): # todo simplify
        commands_db = structure.load_commands(GLOBAL_COMMANDS_FILE_LOCATION)
        global ALIASES
        ALIASES = {}
        for command in commands_db:
            if command.alias:
                ALIASES[command.alias] = Command(command.execute, command.description)
        return [CommandArgument(cmd) for cmd in commands_db if cmd.alias]

    def load_project_aliases(): # todo push into the parser
        global project_ALIASES
        project_ALIASES = {}
        if project:
            for command in project.commands:
                if command.alias:
                    project_ALIASES[command.alias] = Command(command.execute, command.description)
            return [CommandArgument(cmd) for cmd in project.commands if cmd.alias]
        return None

    # == Argument parser =============================================================
    def remove_first_argument():
        sys.argv = [sys.argv[0]] + sys.argv[2:]

    # == Arguments ===================================================================

    def command_args(self):
        res = {}
        res['SAVE'] = ('--save', '-s', self.cmd_save, 'Saves command which is passed as further arguments')
        res['FIND'] = ('--find', '-f', self.cmd_find, 'Opens an interactive search for saved commands')
        res['EDIT'] = ('--edit', '-e', self.cmd_edit, 'Edit the command databse in text editor')
        res['VERSION'] = ('--version', '-V', self.cmd_version, 'Prints out version information')
        res['HELP'] = ('--help', '-h', self.cmd_help, 'Request detailed information about flags or commands')
        res['COMPLETE'] = ('--complete', None, self.cmd_complete, 'Returns list of words which are supplied to the completion shell command')
        res['COMPLETION'] = ('--completion', None, self.cmd_completion, 'Return shell command to be added to the .rc file to allow completion')
        res['QUIET'] = ('--quiet', '-q', create_set_function('logging_level', self.config, self.config.QUIET_LEVEL), 'No output will be shown')
        res['VERBOSE'] = ('--verbose', '-v', create_set_function('logging_level', self.config, self.config.VERBOSE_LEVEL), 'More detailed output information')
        res['DEBUG'] = ('--debug', '-d', create_set_function('logging_level', self.config, self.config.DEBUG_LEVEL), 'Very detailed messages of script\'s inner workings')
        res['project_SCOPE'] = ('--project', '-p', lambda: set_scope('project'), 'Applies the command in the project command collection')
        res['GLOBAL_SCOPE'] = ('--global', '-g', lambda: set_scope('global'), 'Applies the command in the global command collection')
        return res

    def command_groups(self):
        res['PROJECT_COMMANDS'] = ArgumentGroup('project commands', None, self.load_project_aliases)
        res['CUSTOM_COMMANDS'] = ArgumentGroup('custom commands', None, self.load_aliases, 'You may add new custom commands via "cmd --save if the command is given alias, it will show up here')
        a = self.command_args()
        res['CMD_COMMANDS'] = ArgumentGroup('management commands', [a['SAVE'], a['FIND'], a['EDIT'], a['VERSION'], a['HELP'], a['COMPLETE'], a['COMPLETION']])
        res['CMD_SHOWN_COMMANDS'] = ArgumentGroup('management commands', [a['SAVE'], a['FIND'], a['EDIT'], a['VERSION'], a['HELP']])
        res['OUTPUT_ARGUMENTS'] = ArgumentGroup('', [a['QUIET'], a['VERBOSE'], a['DEBUG']])
        res['OPTIONAL_ARGUMENTS'] = ArgumentGroup('optional a', [a['QUIET'], a['VERBOSE'], a['DEBUG'], a['project_SCOPE'], a['GLOBAL_SCOPE']])
        return res

def set_function(what, property_name, value):
    what[property_name] = value

def create_set_function(what, property_name, value):
    return lambda: (set_function(what, property_name, value))

# == Main invocation =============================================================

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        form.print_str()
        logger.critical('Manually interrupted!')
