import unittest
from kivy import Config
from kivy.logger import Logger


class CodecLoggingTestCase(unittest.TestCase):
    def test_log(self):
        Config.set("kivy", "log_enable", 1)
        Config.set("kivy", "log_level", "trace")
        for string in ["한국어", "Niñas and niños"]:
            Logger.trace('Lang: call_fn => value=%r' % (string,))
