
import re, readline

import config
logger=config.get_logger()

def uv(to_print):
    return '"' + str(to_print) + '"'

def print_str(text="", level=config.TEXT_LEVEL, end='\n'):
    if level >= logger.level:
        print(text, end=end)

def input_str(text="", level=config.TEXT_LEVEL, end=''):
    prompt = ''
    if level >= logger.level: prompt = text
    return input(prompt)

def search_and_format(pattern:str, text:str) -> (int, str):
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
def input_with_prefill(prompt, text, level=config.TEXT_LEVEL):
    if not level >= logger.level: prompt = ''
    def hook():
        readline.insert_text(text)
        readline.redisplay()
    readline.set_pre_input_hook(hook)
    result = input(prompt)
    readline.set_pre_input_hook()
    return result

