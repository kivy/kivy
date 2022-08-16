"""
Logger tests
============
"""

import pytest
import pathlib
import time


@pytest.fixture
def file_handler():
    # restores handler to original state
    from kivy.config import Config

    log_dir = Config.get("kivy", "log_dir")
    log_maxfiles = Config.get("kivy", "log_maxfiles")

    try:
        yield None
    finally:
        Config.set("kivy", "log_dir", log_dir)
        Config.set("kivy", "log_maxfiles", log_maxfiles)


@pytest.mark.parametrize('n', [0, 1, 5])
def test_purge_logs(tmp_path, file_handler, n):
    from kivy.config import Config
    from kivy.logger import FileHandler

    Config.set("kivy", "log_dir", str(tmp_path))
    Config.set("kivy", "log_maxfiles", n)

    # create the default file first so it gets deleted so names match
    handler = FileHandler()
    handler._configure()
    open_file = pathlib.Path(handler.filename).name
    # wait a little so the timestamps are different for different files
    time.sleep(.05)

    names = [f'log_{i}.txt' for i in range(n + 2)]
    for name in names:
        p = tmp_path / name
        p.write_text('some data')
        time.sleep(.05)

    handler.purge_logs()

    # files that should have remained after purge
    expected_names = list(reversed(names))[:n]
    files = {f.name for f in tmp_path.iterdir()}
    if open_file in files:
        # one of the remaining files is the current open log, remove it
        files.remove(open_file)
        if len(expected_names) == len(files) + 1:
            # the open log may or may not have been counted in the remaining
            # files, remove one from expected to match removed open file
            expected_names = expected_names[:-1]

    assert set(expected_names) == files


def test_trace_level():
    """Kivy logger defines a custom level of Trace."""
    from kivy.logger import Logger, LOG_LEVELS, LoggerHistory
    import logging

    Logger.setLevel(9)
    # Try different ways to trigger a trace:
    Logger.trace("test: This is trace message 1")
    logging.log(logging.TRACE, "test: This is trace message 2")
    Logger.log(LOG_LEVELS["trace"], "test: This is trace message 3")
    # Not supported:
    # logging.trace('test: This is trace message 4')

    last_log_records = LoggerHistory.history[:3]
    assert all(log_record.levelno == 9 for log_record in last_log_records), [
        log_record.levelno for log_record in last_log_records
    ]


def test_trace_level_has_level_name():
    from kivy.logger import Logger, LoggerHistory

    Logger.setLevel(9)
    Logger.trace("test: This is trace message 1")
    assert LoggerHistory.history[0].levelname == "TRACE"
