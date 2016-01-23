'''
OSC
===

This is an heavy modified version of PyOSC used to access the
`Open Sound Control <https://en.wikipedia.org/wiki/Open_Sound_Control>`_
protocol. It is used by Kivy internally for TUIO providers, but can also be
used by applications to interect with devices or processes using the OSC API.

.. warning::

    This is an external library and Kivy does not provide any support for it.
    It might change in the future and we advise you don't rely on it in your
    code.

'''

__version__ = "0"
__author__ = "www.ixi-software.net"
__license__ = "GNU General Public License"
__all__ = ("oscAPI", "OSC")

from .OSC import *
from .oscAPI import *


