from os.path import join, exists, dirname, basename

from shcmdmgr import filemanip, process, cio
from shcmdmgr.command import load_commands

PROJECT_SPECIFIC_SUBFOLDER = ".cmd"

class Project:
    def __init__(self, directory, form):
        if not directory:
            raise Exception('The project directory {} is invalid'.format(cio.quote(directory)))
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
        self.form = form

    def print_help(self):
        if exists(self.help_script):
            process.run_script([self.help_script])
        else:
            self.form.print_str('You are in project: ' + self.directory)
            self.form.print_str('This project has no explicit help')
            self.form.print_str('Add it by creating a script in \'{project dir}/.cmd/help.py\' which will be executed (to pring help) instead of this message')

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
    def retrieve_project_if_present(search_directory, formatter):
        project_directory = Project.find_location(search_directory)
        if project_directory:
            return Project(project_directory, formatter)
        return None
