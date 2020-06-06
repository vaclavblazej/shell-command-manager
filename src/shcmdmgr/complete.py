'''
Completion utility class 
'''

from os.path import join

from shcmdmgr import config

class Complete:
    def __init__(self, last_arg: str):
        self.last_arg = last_arg
        self.words = []

    @property
    def words(self):
        res_words = []
        for word in self.__words:
            if word.startswith(self.last_arg) and (len(self.last_arg) != 0 or word[0] != '-'):
                res_words.append(word)
        return res_words

    @words.setter
    def words(self, words):
        self.__words = words

def complete_nothing():
    return config.SUCCESSFULL_EXECUTION

def complete_commands(words):
    cmd_commands = ['--save', '--find', '--version', '--help', '-s', '-f', '-h']
    flags = ['-q', '-v', '-d']
    COMPLETE.words += words
    COMPLETE.words += cmd_commands
    COMPLETE.words += flags
    return config.SUCCESSFULL_EXECUTION

def completion_setup_script_path(shell: str, config) -> str:
    return join(config.DATA_PATH, 'completion/setup.{}'.format(shell))
