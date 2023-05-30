'''
Recorder module
===============

.. versionadded:: 1.1.0

Create an instance of :class:`~kivy.input.recorder.Recorder`, attach to the
class, and bind some keys to record / play sequences:

    - F6: play the last record in a loop
    - F7: read the latest recording
    - F8: record input events

Configuration
-------------

.. |attrs| replace:: :attr:`~kivy.input.recorder.Recorder.record_attrs`
.. |profile_mask| replace::
    :attr:`~kivy.input.recorder.Recorder.record_profile_mask`

:Parameters:
    `attrs`: str, defaults to |attrs| value.
        Attributes to record from the motion event
    `profile_mask`: str, defaults to |profile_mask| value.
        Mask for motion event profile. Used to filter which profile will appear
        in the fake motion event when replayed.
    `filename`: str, defaults to 'recorder.kvi'
        Name of the file to record / play with

Usage
-----

For normal module usage, please see the :mod:`~kivy.modules` documentation.

'''

__all__ = ('start', 'stop')

from kivy.logger import Logger
from functools import partial


def replay(recorder, *args):
    if recorder.play:
        return
    else:
        recorder.play = True


def on_recorder_key(recorder, window, key, *largs):
    if key == 289:  # F8
        if recorder.play:
            Logger.error('Recorder: Cannot start recording while playing.')
            return
        recorder.record = not recorder.record
    elif key == 288:  # F7
        if recorder.record:
            Logger.error('Recorder: Cannot start playing while recording.')
            return
        recorder.play = not recorder.play
    elif key == 287:  # F6
        if recorder.play:
            recorder.unbind(play=replay)
        else:
            recorder.bind(play=replay)
            recorder.play = True


def start(win, ctx):
    keys = {}

    # attributes
    value = ctx.config.get('attrs', None)
    if value is not None:
        keys['record_attrs'] = value.split(':')

    # profile mask
    value = ctx.config.get('profile_mask', None)
    if value is not None:
        keys['record_profile_mask'] = value.split(':')

    # filename
    value = ctx.config.get('filename', None)
    if value is not None:
        keys['filename'] = value

    from kivy.input.recorder import Recorder
    ctx.recorder = Recorder(window=win, **keys)
    win.bind(on_key_down=partial(on_recorder_key, ctx.recorder))


def stop(win, ctx):
    if hasattr(ctx, 'recorder'):
        ctx.recorder.release()
