from kivy import (
    kivy_configure, kivy_register_post_configuration, get_includes,
    kivy_usage)
from unittest.mock import Mock, patch
from os.path import exists, isdir


def test_kivy_configure():
    """Test the kivy_configure calls the post_configuration callbacks."""
    mock_callback = Mock()
    kivy_register_post_configuration(mock_callback)
    kivy_configure()

    mock_callback.assert_called()


def test_kivy_get_includes():
    """Test that the `get_includes` function return a list of valid paths."""
    paths = get_includes()
    assert len(paths) > 2, "get_includes does not return a full path list."
    for path in paths:
        assert exists(path) and isdir(path), \
            "get_includes returns invalid paths."


def test_kivy_usage():
    """Test the kivy_usage command."""
    with patch('kivy.print') as mock_print:
        kivy_usage()
        mock_print.assert_called()
