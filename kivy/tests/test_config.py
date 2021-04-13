"""This module houses test for the kivy config module."""
from kivy.config import ConfigParser


def test_configparser_callbacks():
    def callback():
        pass

    config = ConfigParser()
    assert len(config._callbacks) == 0

    config.add_callback(callback, 'section', 'key')
    assert len(config._callbacks) == 1

    config.remove_callback(callback, 'section', 'key')
    assert len(config._callbacks) == 0
