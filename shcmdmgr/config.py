import logging
from os.path import join, dirname, realpath

from shcmdmgr import filemanip

SCRIPT_PATH = dirname(dirname(realpath(__file__)))
GLOBAL_CONFIG_FOLDER = join(SCRIPT_PATH, '_config.json')
LOCAL_CONFIG_FOLDER = join(SCRIPT_PATH, 'config_local.json')

VERBOSE_LEVEL = 15
TEXT_LEVEL = 30
QUIET_LEVEL = 60
INFO_LEVEL = logging.INFO
DEBUG_LEVEL = logging.DEBUG
CONF = None
VERSION = '0.0a1.dev1'

def setup_logging():
    logging.addLevelName(VERBOSE_LEVEL, 'VERBOSE')
    def verbose(self, message, *args, **kws):
        if self.isEnabledFor(VERBOSE_LEVEL):
            self._log(VERBOSE_LEVEL, message, args, **kws)
    logging.Logger.verbose = verbose

def get_logger():
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def get_conf():
    global CONF
    if CONF: return CONF
    CONF = {'logging_level': INFO_LEVEL,}  # logging basic set up before config loads
    CONF.update(filemanip.load_json_file(GLOBAL_CONFIG_FOLDER))
    CONF.update(filemanip.load_json_file(LOCAL_CONFIG_FOLDER))
    return CONF
