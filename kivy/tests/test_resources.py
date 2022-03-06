"""
Resource loading tests
======================
"""
import pytest
import tempfile
import os
from unittest.mock import patch
from kivy.cache import Cache
from kivy.clock import Clock
from kivy.resources import resource_find, resource_add_path


@pytest.fixture
def test_file():
    return "uix/textinput.py"


RESOURCE_CACHE = "kv.resourcefind"


def test_load_resource_cached(test_file):
    Cache.remove(RESOURCE_CACHE)
    found_file = resource_find(test_file)
    assert found_file is not None
    cached_filename = Cache.get(RESOURCE_CACHE, test_file)
    assert found_file == cached_filename


def test_load_resource_not_cached(test_file):
    Cache.remove(RESOURCE_CACHE)
    found_file = resource_find(test_file, use_cache=False)
    assert found_file is not None
    cached_filename = Cache.get(RESOURCE_CACHE, test_file)
    assert cached_filename is None


def test_load_resource_not_found():
    Cache.remove(RESOURCE_CACHE)
    missing_file_name = "missing_test_file.foo"

    find_missing_file = resource_find(missing_file_name)
    assert find_missing_file is None

    with tempfile.TemporaryDirectory() as temp_dir:
        missing_file_path = os.path.join(temp_dir, missing_file_name)

        with open(missing_file_path, "w"):
            pass  # touch file

        find_missing_file_again = resource_find(missing_file_name)
        assert find_missing_file_again is None

        cached_filename = Cache.get(RESOURCE_CACHE, missing_file_name)
        assert cached_filename is None

        resource_add_path(temp_dir)

        found_file = resource_find(missing_file_name)
        assert missing_file_path == found_file
        assert missing_file_path == Cache.get(RESOURCE_CACHE, missing_file_name)


def test_timestamp_and_lastaccess(test_file):
    Cache.remove(RESOURCE_CACHE)
    start = Clock.get_time()

    resource_find(test_file)
    ts = Cache.get_timestamp(RESOURCE_CACHE, test_file)
    last_access = Cache.get_lastaccess(RESOURCE_CACHE, test_file)

    assert ts >= start, 'Last timestamp not accurate.'
    assert last_access >= start, 'Last access time is not accurate.'


def test_print_usage():
    with patch('kivy.cache.print') as mock_print:
        Cache.print_usage()
        mock_print.assert_called()
