"""
Logger tests
============
"""

import logging
import os
import pathlib
import sys
import time

import pytest

# Used to determine which tests must be skipped
LOG_MODE = os.environ.get("KIVY_LOG_MODE", "KIVY")


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


@pytest.mark.parametrize("n", [0, 1, 5])
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
    time.sleep(0.05)

    names = [f"log_{i}.txt" for i in range(n + 2)]
    for name in names:
        p = tmp_path / name
        p.write_text("some data")
        time.sleep(0.05)

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


@pytest.mark.xfail  # Issue #7986 not yet fixed.
def test_logger_history_size():
    from kivy.logger import Logger, LoggerHistory

    for x in range(200):
        Logger.info(x)
    assert len(LoggerHistory.history) == 100, "Wrong size: %s" % len(
        LoggerHistory.history
    )


@pytest.mark.skipif(
    LOG_MODE != "KIVY",
    reason="Requires KIVY_LOG_MODE==KIVY to run.",
)
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


@pytest.mark.skipif(
    LOG_MODE == "PYTHON",
    reason="Requires KIVY_LOG_MODE!=PYTHON to run.",
)
def test_trace_level_has_level_name():
    from kivy.logger import Logger, LoggerHistory

    Logger.setLevel(9)
    Logger.trace("test: This is trace message 1")
    assert LoggerHistory.history[0].levelname == "TRACE"


def test_logging_does_not_deep_copy():
    # If the Logger does a deep copy of an uncopyable
    # data structure, it will fail. See issues #7585 and #7528.

    import threading
    from kivy.logger import Logger

    class UncopyableDatastructure:
        def __init__(self, name):
            self._lock = threading.Lock()
            self._name = name

        def __str__(self):
            return "UncopyableDatastructure(name=%r)" % self._name

    s = UncopyableDatastructure("Uncopyable")
    Logger.error("The value of s is %s", s)


def configured_string_logging(unique_code, formatter=None):
    """
    Helper function provides logger configured to write to log_output.
    """
    from io import StringIO

    log_output = StringIO()

    handler = logging.StreamHandler(stream=log_output)
    if formatter:
        handler.setFormatter(formatter)

    logger = logging.getLogger("tests.%s" % unique_code)

    # Do not escalate to root/Kivy loggers.
    logger.setLevel(9)  # Catch everything
    logger.propagate = False
    assert not logger.hasHandlers(), "Must use unique code between tests."

    logger.addHandler(handler)

    return logger, log_output


def test_colonsplittinglogrecord_with_colon():
    from kivy.logger import ColonSplittingLogRecord

    originallogrecord = logging.LogRecord(
        name="kivy.test",
        level=logging.DEBUG,
        pathname="test.py",
        lineno=1,
        msg="Part1: Part2: Part 3",
        args=("args",),
        exc_info=None,
        func="test_colon_splitting",
        sinfo=None,
    )
    # Just making sure we know what it looks like before.
    assert (
        str(originallogrecord)
        == '<LogRecord: kivy.test, 10, test.py, 1, "Part1: Part2: Part 3">'
    )
    shimmedlogrecord = ColonSplittingLogRecord(originallogrecord)
    assert (
        str(shimmedlogrecord) == "<LogRecord: kivy.test, 10, test.py, 1, "
        '"[Part1       ] Part2: Part 3">'
    )


def test_colonsplittinglogrecord_without_colon():
    from kivy.logger import ColonSplittingLogRecord

    originallogrecord = logging.LogRecord(
        name="kivy.test",
        level=logging.DEBUG,
        pathname="test.py",
        lineno=1,
        msg="Part1 Part2 Part 3",
        args=("args",),
        exc_info=None,
        func="test_colon_splitting",
        sinfo=None,
    )
    shimmedlogrecord = ColonSplittingLogRecord(originallogrecord)
    # No colons means no change.
    assert str(originallogrecord) == str(shimmedlogrecord)

    # Try a non-string (Issue #7984)
    originallogrecord = logging.LogRecord(
        name="kivy.test",
        level=logging.DEBUG,
        pathname="test.py",
        lineno=1,
        msg=1,
        args=None,
        exc_info=None,
        func="test_colon_splitting",
        sinfo=None,
    )
    shimmedlogrecord = ColonSplittingLogRecord(originallogrecord)
    # No colons means no change.
    assert str(originallogrecord) == str(shimmedlogrecord)


def test_uncoloredlogrecord_without_markup():
    from kivy.logger import UncoloredLogRecord

    originallogrecord = logging.LogRecord(
        name="kivy.test",
        level=logging.DEBUG,
        pathname="test.py",
        lineno=1,
        msg="Part1: Part2 Part 3",
        args=("args",),
        exc_info=None,
        func="test_colon_splitting",
        sinfo=None,
    )
    shimmedlogrecord = UncoloredLogRecord(originallogrecord)
    # No markup means no change.
    assert str(originallogrecord) == str(shimmedlogrecord)

    # Try a non-string (Issue #7984)
    originallogrecord = logging.LogRecord(
        name="kivy.test",
        level=logging.DEBUG,
        pathname="test.py",
        lineno=1,
        msg=1,
        args=None,
        exc_info=None,
        func="test_colon_splitting",
        sinfo=None,
    )
    shimmedlogrecord = UncoloredLogRecord(originallogrecord)
    assert str(originallogrecord) == str(shimmedlogrecord)


def test_uncoloredlogrecord_with_markup():
    from kivy.logger import UncoloredLogRecord

    originallogrecord = logging.LogRecord(
        name="kivy.test",
        level=logging.DEBUG,
        pathname="test.py",
        lineno=1,
        msg="Part1: $BOLDPart2$RESET Part 3",
        args=("args",),
        exc_info=None,
        func="test_colon_splitting",
        sinfo=None,
    )
    shimmedlogrecord = UncoloredLogRecord(originallogrecord)
    # No markup means no change.
    assert (
        str(shimmedlogrecord)
        == '<LogRecord: kivy.test, 10, test.py, 1, "Part1: Part2 Part 3">'
    )


def test_coloredlogrecord_without_markup():
    from kivy.logger import ColoredLogRecord

    originallogrecord = logging.LogRecord(
        name="kivy.test",
        level=logging.DEBUG,
        pathname="test.py",
        lineno=1,
        msg="Part1: Part2 Part 3",
        args=("args",),
        exc_info=None,
        func="test_colon_splitting",
        sinfo=None,
    )
    shimmedlogrecord = ColoredLogRecord(originallogrecord)
    # The str() looks the same, because it doesn't include levelname.
    assert str(originallogrecord) == str(shimmedlogrecord)
    # But there is a change in the levelname
    assert originallogrecord.levelname != shimmedlogrecord.levelname
    assert shimmedlogrecord.levelname == "\x1b[1;36mDEBUG\x1b[0m"

    # Try a non-string (Issue #7984)
    originallogrecord = logging.LogRecord(
        name="kivy.test",
        level=logging.DEBUG,
        pathname="test.py",
        lineno=1,
        msg=1,
        args=None,
        exc_info=None,
        func="test_colon_splitting",
        sinfo=None,
    )
    shimmedlogrecord = ColoredLogRecord(originallogrecord)
    assert str(originallogrecord) == str(shimmedlogrecord)


def test_coloredlogrecord_with_markup():
    from kivy.logger import ColoredLogRecord

    originallogrecord = logging.LogRecord(
        name="kivy.test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Part1: $BOLDPart2$RESET Part 3",
        args=("args",),
        exc_info=None,
        func="test_colon_splitting",
        sinfo=None,
    )
    shimmedlogrecord = ColoredLogRecord(originallogrecord)
    # Bolding has been added to message.
    assert (
        str(shimmedlogrecord) == "<LogRecord: kivy.test, 20, test.py, 1, "
        '"Part1: \x1b[1mPart2\x1b[0m Part 3">'
    )
    # And there is a change in the levelname
    assert originallogrecord.levelname != shimmedlogrecord.levelname
    assert shimmedlogrecord.levelname == "\x1b[1;32mINFO\x1b[0m"


def test_kivyformatter_colon_no_color():
    from kivy.logger import KivyFormatter

    formatter = KivyFormatter("[%(levelname)-7s] %(message)s", use_color=False)
    logger, log_output = configured_string_logging("1", formatter)
    logger.info("Fancy: $BOLDmess$RESETage")
    assert log_output.getvalue() == "[INFO   ] [Fancy       ] message\n"


def test_kivyformatter_colon_color():
    from kivy.logger import KivyFormatter

    formatter = KivyFormatter("[%(levelname)-18s] %(message)s", use_color=True)

    logger, log_output = configured_string_logging("2", formatter)
    logger.info("Fancy: $BOLDmess$RESETage")
    assert (
        log_output.getvalue()
        == "[\x1b[1;32mINFO\x1b[0m   ] [Fancy       ] \x1b[1mmess\x1b[0mage\n"
    )


@pytest.mark.logmodepython
@pytest.mark.logmodemixed
@pytest.mark.skipif(
    LOG_MODE == "KIVY",
    reason="Requires KIVY_LOG_MODE!=KIVY to run.",
)
def test_kivy_log_mode_marker_on():
    """
    This is a test of the pytest markers.
    This should only be invoked if the environment variable is appropriately set
    (before pytest is run).

    Also, tests that kivy.logger paid attention to the environment variable
    """
    assert logging.root.level != 0, "Root logger was modified"


@pytest.mark.skipif(
    LOG_MODE != "KIVY",
    reason="Requires KIVY_LOG_MODE==KIVY to run.",
)
def test_kivy_log_mode_marker_off():
    """
    This is a test of the pytest markers.
    This should only be invoked if the environment variable is properly set
    (before pytest is run).

    Also, tests that kivy.logger paid attention to the environment variable
    """
    assert logging.root.level == 0, "Root logger was not modified"


# These tests are an overly-dramatic simulation of a third-party library's
# logging infrastructure.
#
# A handler is attached to the root-logger, which takes action when a
# critical message is logged.


class NuclearReactorMonitoringHandler(logging.Handler):
    NUCLEAR_REACTOR_STATUS = "Nominal"

    def __init__(self):
        super().__init__(level=logging.CRITICAL)

    def emit(self, log_record):
        # The fact that this was called means a critical log record
        # was created.
        sys.stderr.write("Please proceed immediately to the nearest exit.\n")
        sys.stderr.flush()
        self.NUCLEAR_REACTOR_STATUS = "Evacuated"


def simulate_evacuation():
    logging.getLogger().addHandler(logging.StreamHandler())

    handler = NuclearReactorMonitoringHandler()
    logging.getLogger().addHandler(handler)

    nuclear_core_logger = logging.getLogger("powerstation.core")
    nuclear_core_logger.info("Core temperature nominal")
    assert handler.NUCLEAR_REACTOR_STATUS == "Nominal"
    nuclear_core_logger.critical("Radioactive gas leak")
    assert handler.NUCLEAR_REACTOR_STATUS == "Evacuated"


@pytest.mark.logmodepython
@pytest.mark.logmodemixed
def test_third_party_handlers_work():
    # This should work under any mode.
    simulate_evacuation()


def are_regular_logs_handled():
    from kivy.logger import LoggerHistory

    LoggerHistory.clear_history()
    logging.getLogger("test").info(1)
    return bool(LoggerHistory.history)


def are_kivy_logger_logs_handled():
    from kivy.logger import LoggerHistory, Logger

    LoggerHistory.clear_history()
    Logger.info(1)
    return bool(LoggerHistory.history)


def is_stderr_output_handled():
    from kivy.logger import LoggerHistory

    LoggerHistory.clear_history()
    sys.stderr.write("Test output to stderr\n")
    sys.stderr.flush()
    return bool(LoggerHistory.history)


@pytest.mark.skipif(
    LOG_MODE != "KIVY",
    reason="Requires KIVY_LOG_MODE==KIVY to run.",
)
def test_kivy_mode_handlers():
    assert are_regular_logs_handled()
    assert are_kivy_logger_logs_handled()
    # This line doesn't work because of pytest's handling of stderr.
    # Runs fine as stand-alone code.
    # assert is_stderr_output_handled()


@pytest.mark.logmodepython
@pytest.mark.skipif(
    LOG_MODE != "PYTHON",
    reason="Requires KIVY_LOG_MODE==PYTHON to run.",
)
def test_python_mode_handlers():
    assert not are_regular_logs_handled()
    assert not are_kivy_logger_logs_handled()
    assert not is_stderr_output_handled()


@pytest.mark.logmodemixed
@pytest.mark.skipif(
    LOG_MODE != "MIXED",
    reason="Requires KIVY_LOG_MODE==MIXED to run.",
)
def test_mixed_mode_handlers():
    assert not are_regular_logs_handled()
    assert are_kivy_logger_logs_handled()
    assert not is_stderr_output_handled()


@pytest.mark.logmodepython
@pytest.mark.skipif(
    LOG_MODE != "PYTHON",
    reason="Requires KIVY_LOG_MODE==PYTHON to run.",
)
def test_logger_fix_8345():
    """
    The test checks that the ConsoleHandler is not in the Logger
    handlers list if stderr is None.  Test sets stderr to None,
    if the Console handler is found, the test fails.
    Pythonw and Pyinstaller 5.7+ (with console set to false) set stderr
    to None.
    """
    from kivy.logger import Logger, add_kivy_handlers, ConsoleHandler
    original_sys_stderr = sys.stderr
    sys.stderr = None
    add_kivy_handlers(Logger)
    sys.stderr = original_sys_stderr  # restore sys.stderr
    console_handler_found = any(
        isinstance(handler, ConsoleHandler) for handler in Logger.handlers
    )
    assert (
        not console_handler_found
    ), "Console handler added, despite sys.stderr being None"
