"""
Logger tests
============
"""

import unittest
import pathlib

from kivy.config import Config
from kivy.logger import FileHandler


class LoggerTest(unittest.TestCase):
    def test_purge_logs(self):
        maxfiles = 1
        log_path = pathlib.Path("test_logs")

        Config.set("kivy", "log_dir", log_path)
        Config.set("kivy", "log_maxfiles", maxfiles)

        FileHandler().purge_logs()

        current_files = [f for f in log_path.iterdir() if f.is_file()]

        self.assertEqual(maxfiles, len(current_files))
