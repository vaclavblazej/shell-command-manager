
import logging
import filemanip
from os.path import join, dirname, realpath

script_path = dirname(dirname(realpath(__file__))) #todo
global_config_folder = join(script_path, '_config.json')
local_config_folder = join(script_path, 'config_local.json')

VERBOSE_LEVEL = 15
TEXT_LEVEL = 30
QUIET_LEVEL = 60
INFO_LEVEL = logging.INFO
DEBUG_LEVEL = logging.DEBUG
conf = None

def setup_logging():
    logging.addLevelName(VERBOSE_LEVEL, 'VERBOSE')
    def verbose(self, message, *args, **kws):
        if self.isEnabledFor(VERBOSE_LEVEL):
            self._log(VERBOSE_LEVEL, message, args, **kws)
    logging.Logger.verbose = verbose

def get_logger():
    logger = logging.getLogger()
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger

def get_conf():
    global conf
    if conf: return conf
    conf = { 'logging_level': INFO_LEVEL, }  # logging basic set up before config loads
    conf.update(filemanip.load_json_file(global_config_folder))
    conf.update(filemanip.load_json_file(local_config_folder))

