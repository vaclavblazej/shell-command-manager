#!/usr/bin/env python3
# Keep the program in a single file with at most 1000 lines, if possible.

# This script provides management for custom scripts from a central location

# It IS designed to
# * make a clear overview of custom-made commands
# * provide a common interface fot the commands
# * todo ...

# It IS NOT designed to
# * provide standard functions or libraries to be used in the commands
# * check correctness or analyse the commands
# * todo ...

# === TODOS ===
# * todo ...

import os, sys, argparse, logging, subprocess, enum
from os.path import *

SUCCESSFULL_EXECUTION = 0
USER_ERROR = 1 # argument format is fine, but content is wrong
INVALID_ARGUMENT = 129 # argument format is wrong

VERBOSE_LEVEL = 15
QUIET_LEVEL = 60

class ArgumentParser(argparse.ArgumentParser):  # bad argument exit code override
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(INVALID_ARGUMENT, '%s: error: %s\n' % (self.prog, message))

parser = ArgumentParser(
        description='Manage custom scripts from a central location',
        # epilog='Confront documentation of this script for examples and usage of various concepts.'
        )
parser.add_argument('--version', dest='version', action='store_true', help='prints out version information')
parser.add_argument('-q', '--quiet', dest='logging_level', const=QUIET_LEVEL, action='store_const', help='no output will be shown')
parser.add_argument('-v', '--verbose', dest='logging_level', const=VERBOSE_LEVEL, action='store_const', help='more detailed info')
parser.add_argument('-d', '--debug', dest='logging_level', const=logging.DEBUG, action='store_const', help='very detailed messages of script\'s inner workings')

conf = { 'logging_level': logging.INFO, }  # logging is set up before config loads
script_path = dirname(realpath(__file__))
working_directory = os.getcwd()
global_config_folder = join(script_path, 'config.json')
local_config_folder = join(script_path, 'config_local.json')
problem_search_location = realpath(join(script_path, '..', 'acm-problems/problems'))
version = '0.0.1'

# == Main Logic ==================================================================

def main():
    configure()
    global args
    args = parser.parse_args()
    setup_logging()
    if args.logging_level: conf['logging_level'] = args.logging_level
    logger.setLevel(conf['logging_level'])
    logger.debug('Configuration: ' + str(conf))
    logger.debug('Script folder: ' + uv(script_path))
    logger.debug('Working directory: ' + uv(working_directory))
    logger.debug('Arguments: ' + str(sys.argv))

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        return SUCCESSFULL_EXECUTION

    if args.version:
        print('cmd version ' + version)
        return SUCCESSFULL_EXECUTION

    return SUCCESSFULL_EXECUTION

# == Formatting ==================================================================

def uv(to_print):
    return '"' + str(to_print) + '"'

# == Structure ===================================================================

class SomeClass:
    pass

# == Configuration ===============================================================

def setup_logging():
    logging.addLevelName(VERBOSE_LEVEL, 'VERBOSE')
    def verbose(self, message, *args, **kws):
        if self.isEnabledFor(VERBOSE_LEVEL):
            self._log(VERBOSE_LEVEL, message, args, **kws)
    logging.Logger.verbose = verbose
    global logger
    logger = logging.getLogger()
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

def configure():
    conf.update(load_configuration(global_config_folder))
    conf.update(load_configuration(local_config_folder))
    return

def load_configuration(config_file_location):
    try:
        with open(config_file_location) as config_file:
            data = json.load(config_file)
    except FileNotFoundError:
        return dict()
    return data

# == Core Script Logic Chunks ====================================================

def run_command(command_with_arguments):
    p = subprocess.Popen(command_with_arguments)
    try:
        p.wait(timeout)
    except subprocess.TimeoutExpired as ex:
        p.kill()
        raise ex

# == Main invocation =============================================================

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        logger.critical('Manually interrupted!')
