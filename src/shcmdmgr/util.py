
import os

def get_terminal_dimensions():
    (height, width) = (os.popen('stty size', 'r').read().split())
    return (int(width), int(height))
