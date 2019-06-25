import configparser
from os.path import join, dirname
import textwrap

__all__ = ('get_cython_versions', 'get_cython_msg')


def get_cython_versions(setup_cfg=''):
    _cython_config = configparser.ConfigParser()
    if setup_cfg:
        _cython_config.read(setup_cfg)
    else:
        _cython_config.read(
            join(dirname(__file__), '..', '..', '..', 'setup.cfg'))

    cython_min = _cython_config['kivy']['cython_min']
    cython_max = _cython_config['kivy']['cython_max']
    cython_unsupported = _cython_config['kivy']['cython_exclude'].split(',')
    # ref https://github.com/cython/cython/issues/1968

    cython_requires = (
        'cython>={min_version},<={max_version},{exclusion}'.format(
            min_version=cython_min,
            max_version=cython_max,
            exclusion=','.join('!=%s' % excl for excl in cython_unsupported),
        )
    )

    return cython_requires, cython_min, cython_max, cython_unsupported


def get_cython_msg():
    cython_requires, cython_min, cython_max, cython_unsupported = \
        get_cython_versions()
    cython_unsupported_append = '''

    Please note that the following versions of Cython are not supported
    at all: {}'''.format(', '.join(map(str, cython_unsupported)))

    cython_min_msg = textwrap.dedent('''
    This version of Cython is not compatible with Kivy. Please upgrade to
    at least version {0}, preferably the newest supported version {1}.

    If your platform provides a Cython package, make sure you have upgraded
    to the newest version. If the newest version available is still too low,
    please remove it and install the newest supported Cython via pip:

        pip install -I "{3}"{2}
    '''.format(cython_min, cython_max,
               cython_unsupported_append if cython_unsupported else '',
               cython_requires))

    cython_max_msg = textwrap.dedent('''
    This version of Cython is untested with Kivy. While this version may
    work perfectly fine, it is possible that you may experience issues.
    Please downgrade to a supported version, or update cython_max in
    setup.cfg to your version of Cython. It is best to use the newest
    supported version, {1}, but the minimum supported version is {0}.

    If your platform provides a Cython package, check if you can downgrade
    to a supported version. Otherwise, uninstall the platform package and
    install Cython via pip:

        pip install -I "{3}"{2}
    '''.format(cython_min, cython_max,
               cython_unsupported_append if cython_unsupported else '',
               cython_requires))

    cython_unsupported_msg = textwrap.dedent('''
    This version of Cython suffers from known bugs and is unsupported.
    Please install the newest supported version, {1}, if possible, but
    the minimum supported version is {0}.

    If your platform provides a Cython package, check if you can install
    a supported version. Otherwise, uninstall the platform package and
    install Cython via pip:

        pip install -I "{3}"{2}
    '''.format(cython_min, cython_max, cython_unsupported_append,
               cython_requires))

    return cython_min_msg, cython_max_msg, cython_unsupported_msg
