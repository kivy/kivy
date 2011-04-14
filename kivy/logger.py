'''
Logger object
=============

Differents level are available :
    - debug
    - info
    - warning
    - error
    - critical

Examples of usage::

    from kivy.logger import Logger
    Logger.notice('This is a notice')
    Logger.debug('This is a notice')

    try:
        raise Exception('bleh')
    except Exception, e:
        Logger.exception(e)

Logger can be controled in the Kivy configuration.
'''

import logging
import os
import sys
import kivy
from random import randint
from functools import partial

__all__ = ('Logger', 'LOG_LEVELS', 'COLORS', 'LoggerHistory')

Logger = None

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

#These are the sequences need to get colored ouput
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"


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

        print 'Purge log fired. Analysing...'
        join = os.path.join
        unlink = os.unlink

        # search all log files
        l = map(lambda x: join(directory, x), os.listdir(directory))
        if len(l) > maxfiles:
            # get creation time on every files
            l = zip(l, map(os.path.getctime, l))

            # sort by date
            l.sort(cmp=lambda x, y: cmp(x[1], y[1]))

            # get the oldest (keep last maxfiles)
            l = l[:-maxfiles]
            print 'Purge %d log files' % len(l)

            # now, unlink every files in the list
            for filename in l:
                unlink(filename[0])

        print 'Purge finished !'

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
            if n > 10000: # prevent maybe flooding ?
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
            FileHandler.fd.write(record.msg.encode('utf8'))
        FileHandler.fd.write('\n')
        FileHandler.fd.flush()

    def emit(self, message):
        if not Logger.logfile_activated:
            FileHandler.history += [message]
            return

        if FileHandler.fd is None:
            try:
                self._configure()
            except Exception:
                # deactivate filehandler...
                FileHandler.fd = False
                Logger.exception('Error while activating FileHandler logger')
                return
            for _message in FileHandler.history:
                self._write_message(_message)

        self._write_message(message)


class HistoryHandler(logging.Handler):

    history = []

    def emit(self, message):
        HistoryHandler.history = [message] + HistoryHandler.history[:100]


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
            levelname_color = COLOR_SEQ % (30 + COLORS[levelname]) \
                                + levelname + RESET_SEQ
            record.levelname = levelname_color
        return logging.Formatter.format(self, record)


class ColoredLogger(logging.Logger):
    use_color = True
    if os.name == 'nt':
        use_color = False

    FORMAT = '[%(levelname)-18s] %(message)s'
    COLOR_FORMAT = formatter_message(FORMAT, use_color)

    def __init__(self, name):
        logging.Logger.__init__(self, name, logging.DEBUG)
        color_formatter = ColoredFormatter(self.COLOR_FORMAT,
                                           use_color=self.use_color)
        console = logging.StreamHandler()
        console.setFormatter(color_formatter)

        # Use the custom handler instead of streaming one.
        if hasattr(sys, '_kivy_logging_handler'):
            self.addHandler(getattr(sys, '_kivy_logging_handler'))
        else:
            self.addHandler(console)
        self.addHandler(HistoryHandler())
        self.addHandler(FileHandler())
        return


if 'nosetests' not in sys.argv:
    logging.setLoggerClass(ColoredLogger)

#: Kivy default logger instance
Logger = logging.getLogger('Kivy')
Logger.logfile_activated = False

Logger.trace = partial(Logger.log, logging.TRACE)

#: Kivy history handler
LoggerHistory = HistoryHandler

