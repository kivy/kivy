"""Config file for coverage.py"""

import os
from coverage.backward import configparser          # pylint: disable-msg=W0622


class CoverageConfig(object):
    """Coverage.py configuration.

    The attributes of this class are the various settings that control the
    operation of coverage.py.

    """

    def __init__(self):
        """Initialize the configuration attributes to their defaults."""
        # Defaults for [run]
        self.branch = False
        self.cover_pylib = False
        self.data_file = ".coverage"
        self.parallel = False
        self.timid = False
        self.source = None

        # Defaults for [report]
        self.exclude_list = ['(?i)# *pragma[: ]*no *cover']
        self.ignore_errors = False
        self.omit = None
        self.include = None
        self.precision = 0

        # Defaults for [html]
        self.html_dir = "htmlcov"

        # Defaults for [xml]
        self.xml_output = "coverage.xml"

    def from_environment(self, env_var):
        """Read configuration from the `env_var` environment variable."""
        # Timidity: for nose users, read an environment variable.  This is a
        # cheap hack, since the rest of the command line arguments aren't
        # recognized, but it solves some users' problems.
        env = os.environ.get(env_var, '')
        if env:
            self.timid = ('--timid' in env)

    def from_args(self, **kwargs):
        """Read config values from `kwargs`."""
        for k, v in kwargs.items():
            if v is not None:
                setattr(self, k, v)

    def from_file(self, *files):
        """Read configuration from .rc files.

        Each argument in `files` is a file name to read.

        """
        cp = configparser.RawConfigParser()
        cp.read(files)

        # [run]
        if cp.has_option('run', 'branch'):
            self.branch = cp.getboolean('run', 'branch')
        if cp.has_option('run', 'cover_pylib'):
            self.cover_pylib = cp.getboolean('run', 'cover_pylib')
        if cp.has_option('run', 'data_file'):
            self.data_file = cp.get('run', 'data_file')
        if cp.has_option('run', 'parallel'):
            self.parallel = cp.getboolean('run', 'parallel')
        if cp.has_option('run', 'timid'):
            self.timid = cp.getboolean('run', 'timid')
        if cp.has_option('run', 'source'):
            self.source = self.get_list(cp, 'run', 'source')
        if cp.has_option('run', 'omit'):
            self.omit = self.get_list(cp, 'run', 'omit')
        if cp.has_option('run', 'include'):
            self.include = self.get_list(cp, 'run', 'include')

        # [report]
        if cp.has_option('report', 'exclude_lines'):
            # exclude_lines is a list of lines, leave out the blank ones.
            exclude_list = cp.get('report', 'exclude_lines')
            self.exclude_list = list(filter(None, exclude_list.split('\n')))
        if cp.has_option('report', 'ignore_errors'):
            self.ignore_errors = cp.getboolean('report', 'ignore_errors')
        if cp.has_option('report', 'omit'):
            self.omit = self.get_list(cp, 'report', 'omit')
        if cp.has_option('report', 'include'):
            self.include = self.get_list(cp, 'report', 'include')
        if cp.has_option('report', 'precision'):
            self.precision = cp.getint('report', 'precision')

        # [html]
        if cp.has_option('html', 'directory'):
            self.html_dir = cp.get('html', 'directory')

        # [xml]
        if cp.has_option('xml', 'output'):
            self.xml_output = cp.get('xml', 'output')

    def get_list(self, cp, section, option):
        """Read a list of strings from the ConfigParser `cp`.

        The value of `section` and `option` is treated as a comma- and newline-
        separated list of strings.  Each value is stripped of whitespace.

        Returns the list of strings.

        """
        value_list = cp.get(section, option)
        values = []
        for value_line in value_list.split('\n'):
            for value in value_line.split(','):
                value = value.strip()
                if value:
                    values.append(value)
        return values
