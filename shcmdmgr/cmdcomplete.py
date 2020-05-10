'''
Completion utility class 
'''

COMPLETE = None

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

def get_complete(last_arg: str) -> Complete:
    global COMPLETE
    if not COMPLETE:
        COMPLETE = Complete(last_arg)
    return COMPLETE
