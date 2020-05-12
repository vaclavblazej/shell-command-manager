import os
import datetime
import shlex
import subprocess
from os.path import join, exists, dirname, basename
from string import Template

from shcmdmgr import config, filemanip, process
from shcmdmgr.cio import quote, print_str, search_and_format

PROJECT_SPECIFIC_SUBFOLDER = ".cmd"

LOGGER = config.get_logger()
CONF = config.get_conf()

def load_commands(commands_file_location):
    commands_db = filemanip.load_json_file(commands_file_location)
    return list(map(Command.from_json, commands_db))

# == Structure ===================================================================

class Command:
    # command can be either str, or a function (str[]) -> None
    def __init__(self, command: any, description: str = None, alias: str = None, creation_time: str = None):
        self.command = command
        if description == '':
            description = None
        self.description = description
        if alias == '':
            alias = None
        self.alias = alias
        if creation_time is None:
            creation_time = str(datetime.datetime.now().strftime(CONF['time_format']))
        self.creation_time = creation_time

    @classmethod
    def from_json(cls, data):
        return cls(**data)

    def find(self, query):
        to_check = [
            # {'name':'ali', 'field':self.alias},
            {'name':'cmd', 'field':self.command},
            {'name':'des', 'field':self.description},
            # {'name':'ctm', 'field':self.creation_time},
        ]
        total_priority = 0
        total_formatted_output = ""
        for check in to_check:
            (priority, formatted_output) = search_and_format(query, check['field'])
            total_priority += priority
            total_formatted_output += check['name'] + ': ' + formatted_output + '\n'
        if total_priority != 0:
            return (total_priority, total_formatted_output)
        return None

    def execute(self, args=None):
        if not args:
            args = []
        if isinstance(self.command, str):
            LOGGER.verbose('running command: ' + self.command)
            cmd_subs = Template(self.command).substitute(os.environ)
            LOGGER.debug('command with substituted variables: %s', str(cmd_subs))
            cmd_split = shlex.split(cmd_subs)
            LOGGER.debug('command splitted into arguments: %s', str(cmd_split))
            subprocess.run(cmd_split + args, check=False)
        else:
            self.command(args)

class Project:
    def __init__(self, directory):
        if not directory:
            raise Exception('The project directory {} is invalid'.format(quote(directory)))
        self.directory = directory
        self.conf = {
            'name': basename(self.directory),
            'completion': None
        }
        self.cmd_script_directory = join(self.directory, PROJECT_SPECIFIC_SUBFOLDER)
        self.config_file = join(self.cmd_script_directory, 'config.json')
        # conf.update(filemanip.load_json_file(self.config_file))
        self.commands_file = join(self.cmd_script_directory, 'commands.json')
        self.completion_script = join(self.cmd_script_directory, 'completion.py')
        self.help_script = join(self.cmd_script_directory, 'help.py')
        if not exists(self.commands_file):
            filemanip.save_json_file([], self.commands_file)
        self.commands = load_commands(self.commands_file)

    def print_help(self):
        if exists(self.help_script):
            process.run_script([self.help_script])
        else:
            print_str('You are in project: ' + self.directory)
            print_str('This project has no explicit help')
            print_str('Add it by creating a script in \'{project dir}/.cmd/help.py\' which will be executed (to pring help) instead of this message')

    @staticmethod
    def find_location(search_directory):
        currently_checked_folder = search_directory
        while True:
            possible_project_command_folder = join(currently_checked_folder, PROJECT_SPECIFIC_SUBFOLDER)
            if exists(possible_project_command_folder):
                return currently_checked_folder
            if currently_checked_folder == dirname(currently_checked_folder):
                return None # we are in the root directory
            currently_checked_folder = dirname(currently_checked_folder)

    @staticmethod
    def retrieve_project_if_present(search_directory):
        project_directory = Project.find_location(search_directory)
        if project_directory:
            return Project(project_directory)
        return None
