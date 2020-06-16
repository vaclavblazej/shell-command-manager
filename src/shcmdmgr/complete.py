
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

    def add_words(self, new_words):
        if not self.__words:
            self.__words = []
        self.__words += new_words

    @staticmethod
    def nothing():
        return config.SUCCESSFULL_EXECUTION

    def commands(self, *words_list):
        cmd_commands = ['--save', '--find', '--version', '--help', '-s', '-f', '-h']
        flags = ['-q', '-v', '-d']
        for words in words_list:
            self.words += words
        self.words += cmd_commands
        self.words += flags
        return config.SUCCESSFULL_EXECUTION

def completion_setup_script_path(shell: str) -> str:
    return join(config.DATA_PATH, 'completion/setup.{}'.format(shell))
