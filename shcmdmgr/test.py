import unittest

from shcmdmgr import cmdcomplete

class TestMainInvocation(unittest.TestCase):
    def test_shell_invocation(self):
        com = cmdcomplete.get_complete('last-arg')
        self.assertTrue(com)

class TestMainInvocation(unittest.TestCase):
    def test_shell_invocation(self):
        com = cmdcomplete.get_complete('last-arg')
        self.assertTrue(com)

if __name__ == '__main__':
    unittest.main()

# Example:
# class TestStringMethods(unittest.TestCase):
    # # def setUp(self):
        # # self.widget = Widget('The widget')

    # # def tearDown(self):
        # # self.widget.dispose()

    # # @unittest.skipIf(mylib.__version__ < (1, 3), "not supported in this library version")
    # # @unittest.skipUnless(sys.platform.startswith("win"), "requires Windows")
    # def test_upper(self):
        # self.assertEqual('foo'.upper(), 'FOO')
