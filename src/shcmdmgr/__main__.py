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
import subprocess
import sys
import datetime
from os.path import join, exists
from string import Template

from shcmdmgr import config, filemanip, project, complete, cio, process
from shcmdmgr.complete import Complete
from shcmdmgr.command import Command, load_commands
from shcmdmgr.project import Project
from shcmdmgr.args import Argument, CommandArgument, ArgumentGroup
from shcmdmgr.parser import Parser

WORKING_DIRECTORY = os.getcwd()

# == Main Logic ==================================================================

def main():
    logger = None
    form = None
    try:
        logger = config.get_logger()
        form = cio.Formatter(logger)
        helpme = config.Help()
        pars = Parser(sys.argv, helpme)
        conf = config.get_conf()
        proj = Project.retrieve_project_if_present(WORKING_DIRECTORY, form)
        app = App(conf, logger, form, pars, proj, helpme)
        pars.shift() # skip the program invocation
        pars.load_all([app.argument_groups['OUTPUT_ARGUMENTS']])
        logger.setLevel(conf['logging_level'])
        logger.debug('Configuration: %s', str(conf))
        logger.debug('Script folder: %s', cio.quote(config.SCRIPT_PATH))
        logger.debug('Working directory: %s', cio.quote(WORKING_DIRECTORY))
        logger.debug('Arguments: %s', str(sys.argv))
        if proj: os.environ[config.PROJECT_ROOT_VAR] = proj.directory # expose variable to subprocesses
        pars.load_all([app.argument_groups['OPTIONAL_ARGUMENTS']])
        if conf['scope'] == config.AUTOMATIC_SCOPE:
            if proj: conf['scope'] = config.PROJECT_SCOPE
            else: conf['scope'] = config.GLOBAL_SCOPE
        if conf['scope'] == config.PROJECT_SCOPE and not proj:
            logger.critical('Scope is set to "project", however no project is present. To create project in the current folder run the "--init" command.')
            return config.USER_ERROR
        return app.main_command()
    except KeyboardInterrupt:
        if form: form.print_str()
        if logger: logger.critical('Manually interrupted!')

class App:
    def __init__(self, conf, logger, form, pars, proj, helpme):
        self.conf = conf
        self.logger = logger
        self.form = form
        self.parser = pars
        self.complete = None
        self.default_command_load_deja_vu = False
        self.project = proj
        self.help = helpme

    def main_command(self):
        current_command = self.parser.peek()
        if not current_command:
            if self.complete: return self.complete.complete_commands(self.load_aliases_raw(), self.load_project_aliases_raw())
            if self.help.print: return self.print_general_help()
            if self.conf['default_command']:
                new_args = self.conf['default_command'].split(' ')
                if len(new_args) != 0: # prevent doing nothing due to empty default command
                    if self.default_command_load_deja_vu: # prevent adding default command multiple times
                        self.logger.warning('The default command is invalid, it must include a command argument')
                        return config.USER_ERROR
                    self.default_command_load_deja_vu = True
                    sys.argv += new_args
                    return main()
            self.logger.warning('No command given')
            return config.USER_ERROR
        if not self.parser.may_have([self.argument_groups['PROJECT_COMMANDS'], self.argument_groups['CUSTOM_COMMANDS'], self.argument_groups['CMD_COMMANDS']]):
            self.logger.warning('The argument/command %s was not found', cio.quote(current_command))
            self.logger.info('run "cmd --help" if you are having trouble')
            return config.USER_ERROR
        return config.SUCCESSFULL_EXECUTION

    # == Formatting ==================================================================
    def print_general_help(self):
        help_str = ''
        help_str += 'usage: cmd [-q|-v|-d] [-g|-p] <command> [<args>]\n'
        help_str += '\n'
        help_str += 'Manage custom commands from a central location\n'
        self.form.print_str(help_str)
        main_groups = [
            self.argument_groups['PROJECT_COMMANDS'],
            self.argument_groups['CUSTOM_COMMANDS'],
            self.argument_groups['CMD_SHOWN_COMMANDS'],
            self.argument_groups['OPTIONAL_ARGUMENTS'],
        ]
        self.form.print_str(ArgumentGroup.to_str(main_groups), end='')
        # additional_str = ''
        # form.print_str(additional_str) #todo print info including special options (such as --complete)
        return config.SUCCESSFULL_EXECUTION

    # == Commands ====================================================================

    def cmd_help(self):
        if self.complete: return self.main_command()
        self.help.print = True
        remove_first_argument()
        return self.main_command()

    def cmd_version(self):
        if self.complete: return self.complete.nothing()
        self.parser.expect_nothing()
        self.form.print_str('cmd version ' + config.VERSION)
        return config.SUCCESSFULL_EXECUTION

    def cmd_initialize(self):
        if self.complete: return self.complete.nothing()
        self.parser.expect_nothing()
        new_file = config.PROJECT_COMMANDS_FILE_LOCATION
        if not exists(new_file):
            os.mkdir(os.path.dirname(new_file))
            filemanip.save_json_file([], new_file)
        return config.SUCCESSFULL_EXECUTION

    def cmd_save(self):
        alias = ''
        description = ''
        other_args = [
            Argument('--alias', '-a', lambda: print('TODO'), 'one word shortcut used to invoke the command'),
            Argument('--descr', '-d', lambda: print('TODO'), 'few words about the command\'s functionality'),
            Argument('--', None, lambda: print('TODO'), 'command to be saved follows'),
        ]
        self.parser.load_all([ArgumentGroup('save arguments (missing will be queried)', other_args)], self.help.print)
        arguments = self.parser.get_rest()
        if self.complete: return self.complete.nothing()
        show_edit = False
        if len(arguments) == 0: # supply the last command from history
            history_file_location = join(os.environ['HOME'], self.conf['history_home'])
            history_command_in_binary = subprocess.check_output(['tail', '-1', history_file_location])
            history_command = history_command_in_binary[:-1].decode("utf-8")
            arguments = history_command.split(' ')
            show_edit = True
        if len(arguments) > 0 and exists(arguments[0]): # substitute relative file path for absolute
            if self.conf['scope'] == config.PROJECT_SCOPE:
                path_from_project_root = os.path.relpath(join(WORKING_DIRECTORY, arguments[0]), self.project.directory)
                arguments[0] = '${}/{}'.format(config.PROJECT_ROOT_VAR, path_from_project_root)
            if self.conf['scope'] == config.GLOBAL_SCOPE:
                arguments[0] = os.path.realpath(join(WORKING_DIRECTORY, arguments[0]))
            show_edit = True
        command_to_save = ' '.join(arguments)
        if show_edit:
            command_to_save = self.form.input_str('The command to be saved: ', prefill=command_to_save)
        else:
            self.form.print_str('Saving command: ' + command_to_save)
        commands_file_location = self.get_context_command_file_location()
        if not exists(commands_file_location):
            filemanip.save_json_file([], commands_file_location)
        if alias == '': alias = self.form.input_str('Alias: ')
        if description == '': description = self.form.input_str('Short description: ')
        commands_db = load_commands(commands_file_location)
        creation_time = str(datetime.datetime.now().strftime(self.conf['time_format']))
        commands_db.append(Command(command_to_save, description, alias, creation_time))
        filemanip.save_json_file(commands_db, commands_file_location)
        return config.SUCCESSFULL_EXECUTION

    def get_context_command_file_location(self) -> str:
        if self.conf['scope'] == config.PROJECT_SCOPE and project: return self.project.commands_file
        if self.conf['scope'] == config.GLOBAL_SCOPE: return config.GLOBAL_COMMANDS_FILE_LOCATION
        return None

    def cmd_find(self):
        if self.complete: return self.complete.nothing()
        max_cmd_count = 4
        max_cmd_count_slack = 2
        commands_db = load_commands(config.GLOBAL_COMMANDS_FILE_LOCATION)
        if self.project: commands_db += self.project.commands
        selected_commands = []
        try:
            while True:
                self.form.print_str(40 * '=')
                arguments = self.parser.get_rest()
                if len(arguments) != 0:
                    query = ' '.join(arguments)
                    arguments = []
                else:
                    query = self.form.input_str('query $ ')
                try:
                    idx = int(query)
                    if idx not in range(1, len(selected_commands)+1):
                        self.form.print_str('invalid index')
                        continue
                    process.execute(selected_commands[idx-1], self.parser.get_rest())
                    break
                except ValueError as _:
                    pass
                index = 1
                results = []
                for cmd in commands_db:
                    result = cmd.find(query)
                    if result is not None:
                        (priority, formatted_text) = result
                        results.append((priority, formatted_text, cmd))
                total_results_count = len(results)
                if total_results_count == 0:
                    self.form.print_str('No results found')
                results = sorted(results, reverse=True) # by priority
                selected_commands = []
                cmd_showing_count = max_cmd_count
                if total_results_count <= cmd_showing_count + max_cmd_count_slack:
                    cmd_showing_count += max_cmd_count_slack
                for result in results[:cmd_showing_count]:
                    (_, text, cmd) = result
                    selected_commands.append(cmd)
                    self.form.print_str('--- ' + str(index) + ' ' + (30 * '-'))
                    self.form.print_str(text, end='')
                    index = index+1
                if total_results_count > cmd_showing_count:
                    self.form.print_str('\nand ' + str(total_results_count-cmd_showing_count) + ' other commands')
        except EOFError as _:
            self.form.print_str()
        return config.SUCCESSFULL_EXECUTION

    def cmd_edit(self):
        if self.complete: return self.complete.nothing()
        editor = 'vim'
        try:
            editor = Template('$EDITOR').substitute(os.environ)
        except KeyError:
            pass
        subprocess.run([editor, self.get_context_command_file_location()], check=True)
        return config.SUCCESSFULL_EXECUTION

    def cmd_complete(self):
        last_arg = sys.argv[-1]
        sys.argv = sys.argv[:-1]
        remove_first_argument()
        if self.complete: return main()
        self.complete = Complete(last_arg)
        self.logger.setLevel(config.QUIET_LEVEL) # fix when set after main() call
        main_res = main()
        for word in self.complete.words:
            print(word, end=' ')
        print()
        return main_res

    def cmd_completion(self):
        shell = self.parser.shift()
        self.parser.expect_nothing()
        completion_init_script_path = complete.completion_setup_script_path(shell)
        if exists(completion_init_script_path):
            self.form.print_str('source {} cmd'.format(completion_init_script_path))
        else:
            raise Exception('unsuported shell {}, choose bash or zsh'.format(cio.quote(shell)))
        return config.SUCCESSFULL_EXECUTION

    def load_aliases_raw(self):
        commands_db = load_commands(config.GLOBAL_COMMANDS_FILE_LOCATION)
        return [cmd.alias for cmd in commands_db if cmd.alias]

    def load_aliases(self):
        commands_db = load_commands(config.GLOBAL_COMMANDS_FILE_LOCATION)
        return [CommandArgument(cmd, self.logger, self.parser) for cmd in commands_db if cmd.alias]

    def load_project_aliases_raw(self):
        if self.project:
            return [cmd.alias for cmd in self.project.commands if cmd.alias]
        return None

    def load_project_aliases(self):
        if self.project:
            return [CommandArgument(cmd, self.logger, self.parser) for cmd in self.project.commands if cmd.alias]
        return None

    # == Arguments ===================================================================

    @property
    def argument_args(self):
        res = {}
        res['SAVE'] = Argument('--save', '-s', self.cmd_save, 'Saves command which is passed as further arguments')
        res['FIND'] = Argument('--find', '-f', self.cmd_find, 'Opens an interactive search for saved commands')
        res['EDIT'] = Argument('--edit', '-e', self.cmd_edit, 'Edit the command database in text editor')
        res['INIT'] = Argument('--init', '-i', self.cmd_initialize, 'Initialize a project')
        res['VERSION'] = Argument('--version', '-V', self.cmd_version, 'Prints out version information')
        res['HELP'] = Argument('--help', '-h', self.cmd_help, 'Request detailed information about flags or commands')
        res['COMPLETE'] = Argument('--complete', None, self.cmd_complete, 'Returns list of words which are supplied to the completion shell command')
        res['COMPLETION'] = Argument('--completion', None, self.cmd_completion, 'Return shell command to be added to the .rc file to allow completion')
        res['QUIET'] = Argument('--quiet', '-q', lambda: set_function(self.conf, 'logging_level', config.QUIET_LEVEL), 'No output will be shown')
        res['VERBOSE'] = Argument('--verbose', '-v', lambda: set_function(self.conf, 'logging_level', config.VERBOSE_LEVEL), 'More detailed output information')
        res['DEBUG'] = Argument('--debug', '-d', lambda: set_function(self.conf, 'logging_level', config.DEBUG_LEVEL), 'Very detailed messages of script\'s inner workings')
        res['project_SCOPE'] = Argument('--project', '-p', lambda: set_function(self.conf, 'scope', 'project'), 'Applies the command in the project command collection')
        res['GLOBAL_SCOPE'] = Argument('--global', '-g', lambda: set_function(self.conf, 'scope', 'global'), 'Applies the command in the global command collection')
        return res

    @property
    def argument_groups(self):
        res = {}
        res['PROJECT_COMMANDS'] = ArgumentGroup('project commands', None, self.load_project_aliases)
        res['CUSTOM_COMMANDS'] = ArgumentGroup('custom commands', None, self.load_aliases, 'You may add new custom commands via "cmd --save if the command is given alias, it will show up here')
        args = self.argument_args
        res['CMD_COMMANDS'] = ArgumentGroup('management commands', [args['SAVE'], args['FIND'], args['EDIT'], args['VERSION'], args['HELP'], args['INIT'], args['COMPLETE'], args['COMPLETION']])
        res['CMD_SHOWN_COMMANDS'] = ArgumentGroup('management commands', [args['SAVE'], args['FIND'], args['EDIT'], args['VERSION'], args['HELP']])
        res['OUTPUT_ARGUMENTS'] = ArgumentGroup('', [args['QUIET'], args['VERBOSE'], args['DEBUG']])
        res['OPTIONAL_ARGUMENTS'] = ArgumentGroup('optional arguments', [args['QUIET'], args['VERBOSE'], args['DEBUG'], args['project_SCOPE'], args['GLOBAL_SCOPE']])
        return res

def remove_first_argument():
    sys.argv = [sys.argv[0]] + sys.argv[2:]

def set_function(what, property_name, value):
    what[property_name] = value

# == Main invocation =============================================================

if __name__ == '__main__':
    sys.exit(main())
