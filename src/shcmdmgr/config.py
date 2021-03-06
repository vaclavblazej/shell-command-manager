import logging
from os.path import join, dirname, realpath, exists

from shcmdmgr import filemanip

SCRIPT_PATH = dirname(realpath(__file__))
# SCRIPT_PATH = dirname(dirname(realpath(__file__)))
DATA_PATH = join(SCRIPT_PATH, 'data')
GLOBAL_CONFIG_FILE = join(DATA_PATH, '_config.json')
LOCAL_CONFIG_FILE = join(DATA_PATH, 'config_local.json')
GLOBAL_COMMANDS_FILE_LOCATION = join(DATA_PATH, 'commands.json')

VERBOSE_LEVEL = 15
TEXT_LEVEL = 30
QUIET_LEVEL = 60
INFO_LEVEL = logging.INFO
DEBUG_LEVEL = logging.DEBUG
VERSION = '0.1.2-dev0'

def get_logger():
    global LOGGER
    logging.addLevelName(VERBOSE_LEVEL, 'VERBOSE')
    def verbose(self, message, *args, **kws):
        if self.isEnabledFor(VERBOSE_LEVEL):
            self._log(VERBOSE_LEVEL, message, args, **kws)
    logging.Logger.verbose = verbose
    LOGGER = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    LOGGER.addHandler(handler)
    return LOGGER

def get_conf():
    conf = {'logging_level': INFO_LEVEL,}  # logging basic set up before config loads
    conf.update(filemanip.load_json_file(GLOBAL_CONFIG_FILE))
    conf.update(filemanip.load_json_file(LOCAL_CONFIG_FILE))
    return conf
