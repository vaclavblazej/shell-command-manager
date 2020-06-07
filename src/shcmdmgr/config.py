import logging
from os.path import join, dirname, realpath

from shcmdmgr import filemanip

SUCCESSFULL_EXECUTION = 0
USER_ERROR = 1 # argument format is fine, but content is wrong
INVALID_ARGUMENT = 129 # argument format is wrong

SCRIPT_PATH = dirname(realpath(__file__))
# SCRIPT_PATH = dirname(dirname(realpath(__file__)))
DATA_PATH = join(SCRIPT_PATH, 'data')
GLOBAL_CONFIG_FILE = join(DATA_PATH, '_config.json')
LOCAL_CONFIG_FILE = join(DATA_PATH, 'config_local.json')
GLOBAL_COMMANDS_FILE_LOCATION = join(DATA_PATH, 'commands.json')
PROJECT_ROOT_VAR = 'project_root'

DEBUG_LEVEL = logging.DEBUG # 10
VERBOSE_LEVEL = 15
INFO_LEVEL = logging.INFO # 20
TEXT_LEVEL = 30
CRITICAL_LEVEL = logging.CRITICAL # 50
QUIET_LEVEL = 60

VERSION = '0.1.2-dev0'

def get_logger():
    logging.addLevelName(VERBOSE_LEVEL, 'VERBOSE')
    def verbose(self, message, *args, **kws):
        if self.isEnabledFor(VERBOSE_LEVEL):
            self._log(VERBOSE_LEVEL, message, args, **kws)
    logging.Logger.verbose = verbose
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def get_conf():
    conf = {'logging_level': INFO_LEVEL,}  # logging basic set up before config loads
    conf.update(filemanip.load_json_file(GLOBAL_CONFIG_FILE))
    conf.update(filemanip.load_json_file(LOCAL_CONFIG_FILE))
    return conf
