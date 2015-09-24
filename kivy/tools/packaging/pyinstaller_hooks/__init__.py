from os.path import dirname, join

curdir = dirname(__file__)


def runtime_hooks():
    return [join(curdir, 'rt-hook-kivy.py')]


def hookspath():
    return [curdir]


def get_hooks():
    return {'hookspath': hookspath(), 'runtime_hooks': runtime_hooks()}
