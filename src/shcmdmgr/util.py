
from shcmdmgr import process

def get_terminal_dimensions():
    (height, width) = (process.run_command('stty size').split())
    return (int(width), int(height))
