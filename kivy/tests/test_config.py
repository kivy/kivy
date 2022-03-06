"""This module houses test for the kivy config module."""
from kivy.config import ConfigParser
from os.path import join, dirname

SAMPLE_CONFIG = join(dirname(__file__), 'data', 'test.ini')


def test_configparser_callbacks():
    """Test that the ConfigParser handles callbacks."""
    def callback():
        pass

    config = ConfigParser()
    assert len(config._callbacks) == 0

    config.add_callback(callback, 'section', 'key')
    assert len(config._callbacks) == 1

    config.remove_callback(callback, 'section', 'key')
    assert len(config._callbacks) == 0


def test_configparser_read():
    """Test that the ConfigParser can read a config file."""
    config = ConfigParser()
    config.read(SAMPLE_CONFIG)
    assert config.get('section', 'key') == 'value'


def test_configparser_setdefaults():
    """Test the setdefaults method works as expected."""
    config = ConfigParser()
    config.setdefaults('section', {'test': '1'})

    assert config.get('section', 'test') == '1'
