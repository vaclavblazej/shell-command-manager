import unittest
import os.path
import sys

from shcmdmgr import complete, filemanip, config, cio, util, parser, __main__
from shcmdmgr.complete import Complete

class TestCompletion(unittest.TestCase):
    def test_complete_initialization(self):
        com = Complete('last-arg')
        self.assertTrue(com)
        com.commands(['last-arg-test', 'arg'])

    def test_complete(self):
        com = Complete('last-arg')
        self.assertTrue(com)
        com.nothing()

    def test_completion_location(self):
        complete.completion_setup_script_path('bash')

class TestFilemanip(unittest.TestCase):
    def test_load(self):
        filemanip.load_json_file(os.path.join('test', 'cmds.json'))
        filemanip.load_json_file(os.path.join('test', 'nonexistant.json'))

    def test_save(self):
        res = filemanip.load_json_file(os.path.join('test', 'cmds.json'))
        filemanip.save_json_file(res, os.path.join('test', 'tmp.json'))

class TestConfig(unittest.TestCase):
    def test_configuration(self):
        config.get_conf()

    def test_logger(self):
        config.get_logger()

    def test_logger_levels(self):
        log = config.get_logger()
        log.setLevel(config.DEBUG_LEVEL)
        log.debug('test')
        log.verbose('test')
        log.info('test')
        log.critical('test')
        log.error('test')

class TestUtil(unittest.TestCase):
    def test_terminal(self):
        util.get_terminal_dimensions()

def make_app(arguments):
    sys.argv = ['program'] + arguments
    conf = config.get_conf()
    logger = config.get_logger()
    form = cio.Formatter(logger)
    helpme = config.Help()
    pars = parser.Parser(arguments, helpme, form)
    return __main__.App(conf, logger, form, pars, None, helpme)

class TestMainGeneral(unittest.TestCase):
    def test_main_no_param(self):
        make_app([]).main_command()

    def test_main_version(self):
        make_app(['--version']).main_command()

    def test_main_completion(self):
        make_app(['--complete', '']).main_command()
        make_app(['--complete', '--version', '']).main_command()

    def test_main_help(self):
        make_app(['--help']).main_command()
        make_app(['--h']).main_command()

    def test_main_output_settings(self):
        make_app(['--quiet']).main_command()
        make_app(['--verbose']).main_command()
        make_app(['--debug']).main_command()

if __name__ == '__main__':
    unittest.main()
