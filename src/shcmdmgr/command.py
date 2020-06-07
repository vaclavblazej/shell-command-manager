
from shcmdmgr import filemanip, cio

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
            (priority, formatted_output) = cio.search_and_format(query, check['field'])
            total_priority += priority
            total_formatted_output += check['name'] + ': ' + formatted_output + '\n'
        if total_priority != 0:
            return (total_priority, total_formatted_output)
        return None

def load_commands(commands_file_location) -> [Command]:
    commands_db = filemanip.load_json_file(commands_file_location)
    return [Command.from_json(j) for j in commands_db]
