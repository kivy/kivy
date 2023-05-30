# -*- coding: utf-8 -*-
'''
Web Debugger
============

.. versionadded:: 1.2.0

.. warning::

    This module is highly experimental, use it with care.

This module will start a webserver and run in the background. You can
see how your application evolves during runtime, examine the internal
cache etc.

Run with::

    python main.py -m webdebugger

Then open your webbrowser on http://localhost:5000/

'''

__all__ = ('start', 'stop')

import os
if 'KIVY_DOC' not in os.environ:
    from kivy.modules._webdebugger import start, stop
else:
    start = stop = lambda *x: True
