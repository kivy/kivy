'''
Logger object
=============

Differents level are available : trace, debug, info, warning, error, critical.

Examples of usage::

    from kivy.logger import Logger

    Logger.info('title: This is a info')
    Logger.debug('title: This is a debug')

    try:
        raise Exception('bleh')
    except Exception:
        Logger.exception('Something happen!')

The message passed to the logger is splited to the first :. The left part is
used as a title, and the right part is used as a message. This way, you can
"categorize" your message easily::

    Logger.info('Application: This is a test')

    # will appear as

    [INFO   ] [Application ] This is a test

Logger configuration
--------------------

Logger can be controled in the Kivy configuration file::

    [kivy]
    log_level = info
    log_enable = 1
    log_dir = logs
    log_name = kivy_%y-%m-%d_%_.txt

More information about the allowed values is described in :mod:`kivy.config`
module.

Logger history
--------------

Even if the logger is not enabled, you can still have the history of latest 100
messages::

    from kivy.logger import LoggerHistory

    print(LoggerHistory.history)

'''

import logging
import os
import sys
import kivy
from kivy.compat import PY2
from random import randint
from functools import partial

__all__ = ('Logger', 'LOG_LEVELS', 'COLORS', 'LoggerHistory')

Logger = None

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = list(range(8))

#These are the sequences need to get colored ouput
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"

previous_stderr = sys.stderr


def formatter_message(message, use_color=True):
    if use_color:
        message = message.replace("$RESET", RESET_SEQ)
        message = message.replace("$BOLD", BOLD_SEQ)
    else:
        message = message.replace("$RESET", "").replace("$BOLD", "")
    return message

COLORS = {
    'TRACE': MAGENTA,
    'WARNING': YELLOW,
    'INFO': GREEN,
    'DEBUG': CYAN,
    'CRITICAL': RED,
    'ERROR': RED}

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

    def purge_logs(self, directory):
        '''Purge log is called randomly, to prevent log directory to be filled
        by lot and lot of log files.
        You've a chance of 1 on 20 to fire a purge log.
        '''
        if randint(0, 20) != 0:
            return

        # Use config ?
        maxfiles = 100

        print('Purge log fired. Analysing...')
        join = os.path.join
        unlink = os.unlink

        # search all log files
        l = [join(directory, x) for x in os.listdir(directory)]
        if len(l) > maxfiles:
            # get creation time on every files
            l = [{'fn': x, 'ctime': os.path.getctime(x)} for x in l]

            # sort by date
            l = sorted(l, key=lambda x: x['ctime'])

            # get the oldest (keep last maxfiles)
            l = l[:-maxfiles]
            print('Purge %d log files' % len(l))

            # now, unlink every files in the list
            for filename in l:
                unlink(filename['fn'])

        print('Purge finished !')

    def _configure(self):
        from time import strftime
        from kivy.config import Config
        log_dir = Config.get('kivy', 'log_dir')
        log_name = Config.get('kivy', 'log_name')

        _dir = kivy.kivy_home_dir
        if len(log_dir) and log_dir[0] == '/':
            _dir = log_dir
        else:
            _dir = os.path.join(_dir, log_dir)
            if not os.path.exists(_dir):
                os.mkdir(_dir)

        self.purge_logs(_dir)

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

        FileHandler.filename = filename
        FileHandler.fd = open(filename, 'w')

        Logger.info('Logger: Record log in %s' % filename)

    def _write_message(self, record):
        if FileHandler.fd in (None, False):
            return

        FileHandler.fd.write('[%-18s] ' % record.levelname)
        try:
            FileHandler.fd.write(record.msg)
        except UnicodeEncodeError:
            if PY2:
                FileHandler.fd.write(record.msg.encode('utf8'))
        FileHandler.fd.write('\n')
        FileHandler.fd.flush()

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
            except Exception:
                # deactivate filehandler...
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


class ColoredFormatter(logging.Formatter):

    def __init__(self, msg, use_color=True):
        logging.Formatter.__init__(self, msg)
        self.use_color = use_color

    def format(self, record):
        # XXX Hack to not show the fucking traceback for Numeric handler
        # Lot of people are complaining with that. Now we did.
        if 'Unable to load registered array format handler' in record.msg:
            if record.args and record.args[0] == 'numeric':
                return
        try:
            msg = record.msg.split(':', 1)
            if len(msg) == 2:
                record.msg = '[%-12s]%s' % (msg[0], msg[1])
        except:
            pass
        levelname = record.levelname
        if record.levelno == logging.TRACE:
            levelname = 'TRACE'
            record.levelname = levelname
        if self.use_color and levelname in COLORS:
            levelname_color = (
                COLOR_SEQ % (30 + COLORS[levelname]) + levelname + RESET_SEQ)
            record.levelname = levelname_color
        return logging.Formatter.format(self, record)


class ConsoleHandler(logging.StreamHandler):

    def filter(self, record):
        try:
            msg = record.msg
            k = msg.split(':', 1)
            if k[0] == 'stderr' and len(k) == 2:
                previous_stderr.write(k[1] + '\n')
                return False
        except:
            pass
        return True


class LogFile(object):

    def __init__(self, channel, func):
        self.buffer = ''
        self.func = func
        self.channel = channel

    def write(self, s):
        s = self.buffer + s
        self.flush()
        f = self.func
        channel = self.channel
        lines = s.split('\n')
        for l in lines[:-1]:
            f('%s: %s' % (channel, l))
        self.buffer = lines[-1]

    def flush(self):
        return


def logger_config_update(section, key, value):
    if LOG_LEVELS.get(value) is None:
        raise AttributeError('Loglevel {0!r} doesn\'t exists'.format(value))
    Logger.setLevel(level=LOG_LEVELS.get(value))

#: Kivy default logger instance
Logger = logging.getLogger('kivy')
Logger.logfile_activated = None
Logger.trace = partial(Logger.log, logging.TRACE)

# set the Kivy logger as the default
logging.root = Logger

# add default kivy logger
Logger.addHandler(LoggerHistory())
if 'KIVY_NO_FILELOG' not in os.environ:
    Logger.addHandler(FileHandler())

# Use the custom handler instead of streaming one.
if 'KIVY_NO_CONSOLELOG' not in os.environ:
    if hasattr(sys, '_kivy_logging_handler'):
        Logger.addHandler(getattr(sys, '_kivy_logging_handler'))
    else:
        use_color = os.name != 'nt'
        if os.environ.get('KIVY_BUILD') in ('android', 'ios'):
            use_color = False
        color_fmt = formatter_message(
            '[%(levelname)-18s] %(message)s', use_color)
        formatter = ColoredFormatter(color_fmt, use_color=use_color)
        console = ConsoleHandler()
        console.setFormatter(formatter)
        Logger.addHandler(console)

# install stderr handlers
sys.stderr = LogFile('stderr', Logger.warning)

#: Kivy history handler
LoggerHistory = LoggerHistory
