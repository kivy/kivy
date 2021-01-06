"""
Logger tests
============
"""

import pytest
import pathlib
import time

@pytest.mark.parametrize('n', [0, 1, 5])
def test_purge_logs(tmp_path, n):
    from kivy.config import Config
    from kivy.logger import FileHandler

    Config.set("kivy", "log_dir", str(tmp_path))
    Config.set("kivy", "log_maxfiles", n)

    # create the default file first so it gets deleted so names match
    handler = FileHandler()
    handler._configure()
    # must close file so it can be deleted
    handler.fd.close()
    # wait a little so the timestamps are different for different files
    time.sleep(.001)

    names = [f'log_{i}.txt' for i in range(n + 2)]
    for name in names:
        p = tmp_path / name
        p.write_text('some data')
        time.sleep(.001)

    handler.purge_logs()

    # files that should have remained after purge
    expected_names = list(reversed(names))[:n]
    files = {f.name for f in tmp_path.iterdir()}
    assert expected_names == files
