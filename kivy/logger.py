"""
Kivy Logging
============

By default, Kivy provides a logging system based on the standard Python
`logging <https://docs.python.org/3/library/logging.html>`_ module with
several additional features designed to be more convenient. These features
include:

 * simplied usage (single instance, simple configuration, works by default)
 * color-coded output on supported terminals
 * output to ``stderr`` by default
 * message categorization via colon separation
 * access to log history even if logging is disabled
 * built-in handling of various cross-platform considerations
 * any stray output written to ``sys.stderr`` is captured, and stored in the log
   file as a warning.

These features are configurable via the Config file or environment variables -
including falling back to only using the standard Python system.

Logger object
=============

The Kivy ``Logger`` class provides a singleton logging.logger instance.

As well as the standard logging levels (``debug``, ``info``,
``warning``, ``error`` and ``critical``), an additional ``trace`` level is
available.

Example Usage
-------------

Use the ``Logger`` as you would a standard Python logger. ::

    from kivy.logger import Logger

    Logger.info('title: This is a info message.')
    Logger.debug('title: This is a debug message.')

    try:
        raise Exception('bleh')
    except Exception:
        Logger.exception('Something happened!')

The message passed to the logger is split into two parts separated by a colon
(:). The first part is used as a title and the second part is used as the
message. This way, you can "categorize" your messages easily. ::

    Logger.info('Application: This is a test')

    # will appear as

    [INFO   ] [Application ] This is a test

You can change the logging level at any time using the ``setLevel`` method. ::

    from kivy.logger import Logger, LOG_LEVELS

    Logger.setLevel(LOG_LEVELS["debug"])

.. versionchanged:: 2.2.0

Interaction with other logging
------------------------------

The Kivy logging system will, by default, present all log messages sent from
any logger - e.g. from third-party libraries.

Additional handlers may be added.

.. warning:: Handlers that output to ``sys.stderr`` may cause loops, as stderr
   output is reported as a warning log message.

Logger Configuration
====================

Kivy Log Mode
-------------

At the highest level, Kivy's logging system is controlled by an environment
variable ``KIVY_LOG_MODE``. It may be given any of three values:
``KIVY``, ``PYTHON``, ``MIXED``

.. versionadded: 2.2.0

KIVY Mode (default)
^^^^^^^^^^^^^^^^^^^

In ``KIVY`` mode, all Kivy handlers are attached to the root logger, so all log
messages in the system are output to the Kivy log files and to the console. Any
stray output to ``sys.stderr`` is logged as a warning.

If you are writing an entire Kivy app from scratch, this is the most convenient
mode.

PYTHON Mode
^^^^^^^^^^^

In ``PYTHON`` mode, no handlers are added, and ``sys.stderr`` output is not
captured. It is left to the client to add appropriate handlers. (If none are
added, the ``logging`` module will output them to ``stderr``.)

Messages logged with ``Logger`` will be propagated to the root logger, from a
logger named ``kivy``.

If the Kivy app is part of a much larger project which has its own logging
regimen, this is the mode that gives most control.

The ``kivy.logger`` file contains a number of ``logging.handler``,
``logging.formatter``, and other helper classes to allow
users to adopt the features of Kivy logging that they like, including the
stderr redirection.

MIXED Mode
^^^^^^^^^^

In ``MIXED`` mode, handlers are added to the Kivy's ``Logger`` object directly,
and propagation is turned off. ``sys.stderr`` is not redirected.

Messages logged with Kivy's ``Logger`` will appear in the Kivy log file and
output to the Console.

However, messages logged with other Python loggers will not be handled by Kivy
handlers. The client will need to add their own.

If you like the features of Kivy ``Logger``, but are writing a Kivy app that
relies on third-party libraries that don't use colon-separation of categorise
or depend on the display of the logger name, this mode provides a compromise.

Again, the ``kivy.logger`` file contains re-usable logging features that can be
used to get the best of both systems.

Config Files
------------

In ``KIVY`` and ``MIXED`` modes, the logger handlers can be controlled via the
Kivy configuration file::

    [kivy]
    log_level = info
    log_enable = 1
    log_dir = logs
    log_name = kivy_%y-%m-%d_%_.txt
    log_maxfiles = 100

More information about the allowed values are described in the
:mod:`kivy.config` module.

In addition, the environment variables ``KIVY_NO_FILELOG`` and
``KIVY_NO_CONSOLELOG`` can be used to turn off the installation of the
corresponding handlers.


Logger History
--------------

Even if the logger is not enabled, you still have access to the last 100
LogRecords::

    from kivy.logger import LoggerHistory

    print(LoggerHistory.history)
"""

import logging
import os
import sys
from functools import partial
import pathlib

import kivy
from kivy.utils import platform


__all__ = (
    "add_kivy_handlers",
    "ColonSplittingLogRecord",
    "ColoredLogRecord",
    "COLORS",
    "ConsoleHandler",
    "file_log_handler",
    "FileHandler",
    "is_color_terminal",
    "KivyFormatter",
    "LOG_LEVELS",
    "Logger",
    "LoggerHistory",
    "ProcessingStream",
    "UncoloredLogRecord",
)


Logger = None


logging.addLevelName(9, 'TRACE')
logging.TRACE = 9
LOG_LEVELS = {
    'trace': logging.TRACE,
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL}


class FileHandler(logging.Handler):
    history = []
    filename = 'log.txt'
    fd = None
    log_dir = ''
    encoding = 'utf-8'

    def purge_logs(self):
        """Purge logs which exceed the maximum amount of log files,
        starting with the oldest creation timestamp (or edit-timestamp on Linux)
        """

        if not self.log_dir:
            return

        from kivy.config import Config
        maxfiles = Config.getint("kivy", "log_maxfiles")

        # Get path to log directory
        log_dir = pathlib.Path(self.log_dir)

        if maxfiles < 0:  # No log file limit set
            return

        Logger.info("Logger: Purge log fired. Processing...")

        # Get all files from log directory and corresponding creation timestamps
        files = [(item, item.stat().st_ctime)
                 for item in log_dir.iterdir() if item.is_file()]
        # Sort files by ascending timestamp
        files.sort(key=lambda x: x[1])

        for file, _ in files[:(-maxfiles or len(files))]:
            # More log files than allowed maximum,
            # delete files, starting with oldest creation timestamp
            # (or edit-timestamp on Linux)
            try:
                file.unlink()
            except (PermissionError, FileNotFoundError) as e:
                Logger.info(f"Logger: Skipped file {file}, {repr(e)}")

        Logger.info("Logger: Purge finished!")

    def _configure(self, *largs, **kwargs):
        from time import strftime
        from kivy.config import Config
        log_dir = Config.get('kivy', 'log_dir')
        log_name = Config.get('kivy', 'log_name')

        _dir = kivy.kivy_home_dir
        if log_dir and os.path.isabs(log_dir):
            _dir = log_dir
        else:
            _dir = os.path.join(_dir, log_dir)
        if not os.path.exists(_dir):
            os.makedirs(_dir)
        self.log_dir = _dir

        pattern = log_name.replace('%_', '@@NUMBER@@')
        pattern = os.path.join(_dir, strftime(pattern))
        n = 0
        while True:
            filename = pattern.replace('@@NUMBER@@', str(n))
            if not os.path.exists(filename):
                break
            n += 1
            if n > 10000:  # prevent maybe flooding ?
                raise Exception('Too many logfile, remove them')

        if FileHandler.filename == filename and FileHandler.fd is not None:
            return

        FileHandler.filename = filename
        if FileHandler.fd not in (None, False):
            FileHandler.fd.close()
        FileHandler.fd = open(filename, 'w', encoding=FileHandler.encoding)
        Logger.info('Logger: Record log in %s' % filename)

    def _write_message(self, record):
        if FileHandler.fd in (None, False):
            return

        msg = self.format(record)
        stream = FileHandler.fd
        fs = "%s\n"
        stream.write('[%-7s] ' % record.levelname)
        stream.write(fs % msg)
        stream.flush()

    def emit(self, message):
        # during the startup, store the message in the history
        if Logger.logfile_activated is None:
            FileHandler.history += [message]
            return

        # startup done, if the logfile is not activated, avoid history.
        if Logger.logfile_activated is False:
            FileHandler.history = []
            return

        if FileHandler.fd is None:
            try:
                self._configure()
                from kivy.config import Config
                Config.add_callback(self._configure, 'kivy', 'log_dir')
                Config.add_callback(self._configure, 'kivy', 'log_name')
            except Exception:
                # deactivate filehandler...
                if FileHandler.fd not in (None, False):
                    FileHandler.fd.close()
                FileHandler.fd = False
                Logger.exception('Error while activating FileHandler logger')
                return
            while FileHandler.history:
                _message = FileHandler.history.pop()
                self._write_message(_message)

        self._write_message(message)


class LoggerHistory(logging.Handler):

    history = []

    def emit(self, message):
        LoggerHistory.history = [message] + LoggerHistory.history[:100]

    @classmethod
    def clear_history(cls):
        del cls.history[:]

    def flush(self):
        super(LoggerHistory, self).flush()
        self.clear_history()


class ConsoleHandler(logging.StreamHandler):
    """
        Emits records to a stream (by default, stderr).

        However, if the msg starts with "stderr:" it is not formatted, but
        written straight to the stream.

        .. versionadded:: 2.2.0
    """

    def filter(self, record):
        try:
            msg = record.msg
            k = msg.split(':', 1)
            if k[0] == 'stderr' and len(k) == 2:
                # This message was scraped from stderr.
                # Emit it without formatting.
                self.stream.write(k[1] + '\n')
                # Don't pass it to the formatted emitter.
                return False
        except Exception:
            pass
        return True


class ProcessingStream(object):
    """
        Stream-like object that takes each completed line written to it,
        adds a given prefix, and applies the given function to it.

        .. versionadded:: 2.2.0
    """

    def __init__(self, channel, func):
        self.buffer = ""
        self.func = func
        self.channel = channel
        self.errors = ""

    def write(self, s):
        s = self.buffer + s
        self.flush()
        f = self.func
        channel = self.channel
        lines = s.split('\n')
        for line in lines[:-1]:
            f('%s: %s' % (channel, line))
        self.buffer = lines[-1]

    def flush(self):
        return

    def isatty(self):
        return False


def logger_config_update(section, key, value):
    if KIVY_LOG_MODE != "PYTHON":
        if LOG_LEVELS.get(value) is None:
            raise AttributeError('Loglevel {0!r} doesn\'t exists'.format(value))
        Logger.setLevel(level=LOG_LEVELS.get(value))


class ColonSplittingLogRecord(logging.LogRecord):
    """Clones an existing logRecord, but reformats the message field
    if it contains a colon.

    .. versionadded:: 2.2.0
    """

    def __init__(self, logrecord):
        try:
            parts = logrecord.msg.split(":", 1)
            if len(parts) == 2:
                new_msg = "[%-12s]%s" % (parts[0], parts[1])
            else:
                new_msg = parts[0]
        except Exception:
            new_msg = logrecord.msg

        super().__init__(
            name=logrecord.name,
            level=logrecord.levelno,
            pathname=logrecord.pathname,
            lineno=logrecord.lineno,
            msg=new_msg,
            args=logrecord.args,
            exc_info=logrecord.exc_info,
            func=logrecord.funcName,
            sinfo=logrecord.stack_info,
        )


class ColoredLogRecord(logging.LogRecord):
    """Clones an existing logRecord, but reformats the levelname to add
    color, and the message to add bolding (where indicated by $BOLD
    and $RESET in the message).

    .. versionadded:: 2.2.0"""

    BLACK = 0
    RED = 1
    GREEN = 2
    YELLOW = 3
    BLUE = 4
    MAGENTA = 5
    CYAN = 6
    WHITE = 7
    RESET_SEQ = "\033[0m"
    COLOR_SEQ = "\033[1;%dm"
    BOLD_SEQ = "\033[1m"

    LEVEL_COLORS = {
        "TRACE": MAGENTA,
        "WARNING": YELLOW,
        "INFO": GREEN,
        "DEBUG": CYAN,
        "CRITICAL": RED,
        "ERROR": RED,
    }

    @classmethod
    def _format_message(cls, message):
        return str(message).replace(
            "$RESET", cls.RESET_SEQ).replace("$BOLD", cls.BOLD_SEQ)

    @classmethod
    def _format_levelname(cls, levelname):
        if levelname in cls.LEVEL_COLORS:
            return (
                cls.COLOR_SEQ % (30 + cls.LEVEL_COLORS[levelname])
                + levelname
                + cls.RESET_SEQ
            )
        return levelname

    def __init__(self, logrecord):
        super().__init__(
            name=logrecord.name,
            level=logrecord.levelno,
            pathname=logrecord.pathname,
            lineno=logrecord.lineno,
            msg=logrecord.msg,
            args=logrecord.args,
            exc_info=logrecord.exc_info,
            func=logrecord.funcName,
            sinfo=logrecord.stack_info,
        )
        self.levelname = self._format_levelname(self.levelname)
        self.msg = self._format_message(self.msg)


# Included for backward compatibility only.
# Could be used to override colors.
COLORS = ColoredLogRecord.LEVEL_COLORS


class UncoloredLogRecord(logging.LogRecord):
    """Clones an existing logRecord, but reformats the message
    to remove $BOLD/$RESET markup.

    .. versionadded:: 2.2.0"""

    @classmethod
    def _format_message(cls, message):
        return str(message).replace("$RESET", "").replace("$BOLD", "")

    def __init__(self, logrecord):
        super().__init__(
            name=logrecord.name,
            level=logrecord.levelno,
            pathname=logrecord.pathname,
            lineno=logrecord.lineno,
            msg=logrecord.msg,
            args=logrecord.args,
            exc_info=logrecord.exc_info,
            func=logrecord.funcName,
            sinfo=logrecord.stack_info,
        )
        self.msg = self._format_message(self.msg)


class KivyFormatter(logging.Formatter):
    """Split out first field in message marked with a colon,
    and either apply terminal color codes to the record, or strip
    out color markup if colored logging is not available.

    .. versionadded:: 2.2.0"""

    def __init__(self, *args, use_color=True, **kwargs):
        super().__init__(*args, **kwargs)
        self._coloring_cls = (
            ColoredLogRecord if use_color else UncoloredLogRecord)

    def format(self, record):
        return super().format(
            self._coloring_cls(ColonSplittingLogRecord(record)))


def is_color_terminal():
    """ Detect whether the environment supports color codes in output.

    .. versionadded:: 2.2.0
    """

    return (
            (
                    os.environ.get("WT_SESSION") or
                    os.environ.get("COLORTERM") == 'truecolor' or
                    os.environ.get('PYCHARM_HOSTED') == '1' or
                    os.environ.get('TERM') in (
                        'rxvt',
                        'rxvt-256color',
                        'rxvt-unicode',
                        'rxvt-unicode-256color',
                        'xterm',
                        'xterm-256color',
                    )
            )
            and platform not in ('android', 'ios')
    )


#: Kivy default logger instance
# .. versionchanged:: 2.2.0
Logger = logging.getLogger('kivy')
Logger.logfile_activated = None
Logger.trace = partial(Logger.log, logging.TRACE)

file_log_handler = (
    FileHandler()
    if 'KIVY_NO_FILELOG' not in os.environ
    else None
)


# Issue #7891 describes an undocumented feature that was since removed
# Detect if a client was depending on it.
# .. versionchanged:: 2.2.0
assert not hasattr(sys, '_kivy_logging_handler'), \
    "Not supported. Try logging.root.addHandler()"


def add_kivy_handlers(logger):
    """ Add Kivy-specific handlers to a logger.

    .. versionadded:: 2.2.0
    """
    # add default kivy logger
    logger.addHandler(LoggerHistory())
    if file_log_handler:
        logger.addHandler(file_log_handler)

    # Use the custom handler instead of streaming one.
    # Don't output to stderr if it is set to None
    # stderr is set to None by pythonw and pyinstaller 5.7+
    if sys.stderr and 'KIVY_NO_CONSOLELOG' not in os.environ:
        use_color = is_color_terminal()
        if not use_color:
            # No additional control characters will be inserted inside the
            # levelname field, 7 chars will fit "WARNING"
            fmt = "[%(levelname)-7s] %(message)s"
        else:
            # levelname field width need to take into account the length of
            # the color control codes (7+4 chars for bold+color, and reset)
            fmt = "[%(levelname)-18s] %(message)s"
        formatter = KivyFormatter(fmt, use_color=use_color)
        console = ConsoleHandler()
        console.setFormatter(formatter)
        logger.addHandler(console)


KIVY_LOG_MODE = os.environ.get("KIVY_LOG_MODE", "KIVY")
assert KIVY_LOG_MODE in ("KIVY", "PYTHON", "MIXED"), "Unknown log mode"

if KIVY_LOG_MODE == "KIVY":
    # Add the Kivy handlers to the root logger, so they will be used
    # for all propagated log messages.
    add_kivy_handlers(logging.root)

    # Root logger defaults to warning. Let Logger be the limiting factor.
    logging.root.setLevel(logging.NOTSET)

    # install stderr handlers

    # Caution: If any logging handlers output to sys.stderr they should be
    # configured BEFORE this reconfiguration is done to avoid loops.
    sys.stderr = ProcessingStream("stderr", Logger.warning)
    # Sends all messages written to stderr to the Logger, after prefixing it
    # with "stderr:"
elif KIVY_LOG_MODE == "MIXED":
    # Add the Kivy handlers to the Kivy logger, so they will be used
    # for all messages sent through Logger, only.
    add_kivy_handlers(Logger)

    # Don't spread Kivy-related log messages to the root logger.
    Logger.propagate = False

    # Don't set stderr redirection: it is too likely to cause loops with other
    # handlers. Client can manually add it, if desired.
else:  # KIVY_LOG_MODE == "PYTHON"
    # Don't add handlers or redirect stderr. Client can manually add if desired.
    pass
