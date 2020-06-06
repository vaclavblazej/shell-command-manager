import re
import readline

from shcmdmgr import config

def quote(to_print):
    return '"' + str(to_print) + '"'

class Formatter:
    def __init__(self, logger):
        self.logger = logger

    def print_str(self, text="", level=None, end='\n'):
        if not level: level = config.TEXT_LEVEL
        if level >= self.logger.level:
            print(text, end=end)

    def search_and_format(self, pattern: str, text: str) -> (int, str):
        if text is None:
            return (0, "")
        priority = 0
        occurences = list(re.finditer(pattern, text, re.I))
        color_format = '\033[{0}m'
        color_str = color_format.format(31) # red color
        reset_str = color_format.format(0) # default color
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
    def input_str(self, prompt, prefill='', level=None):
        if not level: level = config.TEXT_LEVEL
        if level < self.logger.level: prompt = ''
        def hook():
            readline.insert_text(prefill)
            readline.redisplay()
        readline.set_pre_input_hook(hook)
        result = input(prompt)
        readline.set_pre_input_hook()
        return result
