import locale
import unittest
from unittest import mock
from kivy import Config
from kivy.logger import Logger, FileHandler
import pytest


class CodecLoggingTestCase(unittest.TestCase):
    def test_log_handles_cp949(self):
        with mock.patch("locale.getpreferredencoding", return_value="cp949"):
            FileHandler.fd = None
            FileHandler.encoding = "utf-8"
            Config.set("kivy", "log_enable", 1)
            Config.set("kivy", "log_level", "trace")
            for string in ["한국어", "Niñas and niños"]:
                Logger.trace("Lang: call_fn => value=%r" % (string,))

    def test_non_utf8_encoding_raises_exception(
        self,
    ):  # the old error before utf-8 was standard
        FileHandler.fd = None
        FileHandler.encoding = "cp949"
        Config.set("kivy", "log_enable", 1)
        Config.set("kivy", "log_level", "trace")

        with pytest.raises(UnicodeError):
            Logger.trace("Lang: call_fn => value=%r" % ("Niñas and niños",))
