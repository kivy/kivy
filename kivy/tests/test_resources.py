"""
Resource loading tests
======================
"""
import pytest
import tempfile
import os
from kivy.cache import Cache

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
