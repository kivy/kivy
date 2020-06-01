import locale
import unittest
from unittest import mock


class CodecLoggingTestCase(unittest.TestCase):
    def test_log(self):
        with mock.patch("locale.getpreferredencoding", return_value="cp949"):
            from kivy import Config
            from kivy.logger import Logger

            Config.set("kivy", "log_enable", 1)
            Config.set("kivy", "log_level", "trace")
            for string in ["한국어", "Niñas and niños"]:
                Logger.trace("Lang: call_fn => value=%r" % (string,))
