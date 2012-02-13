from os.path import dirname, join
from functools import partial

curdir = dirname(__file__)


def install_hooks(sym, hookspath=None):

    _hookspath = [curdir]
    if hookspath is not None:
        _hookspath += hookspath

    sym['rthooks']['kivy'] = [join(curdir, 'rt-hook-kivy.py')]
    sym['Analysis'] = partial(sym['Analysis'], hookspath=_hookspath)
