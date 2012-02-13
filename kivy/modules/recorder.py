'''
Recorder module
===============

.. versionadded:: 1.1.0

Create an instance of :class:`~kivy.input.recorder.Recorder`, attach to the
class, and bind some keys to record / play sequences:

    - F7: read the latest recording
    - F8: record input events

Configuration
-------------

:Parameters:
    `attrs`: str, default to :data:`~kivy.input.recorder.Recorder.record_attrs`
    value.

        Attributes to record from the motion event

    `profile_mask`: str, default to
    :data:`~kivy.input.recorder.Recorder.record_profile_mask` value.

        Mask for motion event profile. Used to filter which profile will appear
        in the fake motion event when replayed.

    `filename`: str, default to 'recorder.kvi'

        Name of the file to record / play with

'''

from kivy.input.recorder import Recorder
from kivy.logger import Logger
from functools import partial


def on_recorder_key(recorder, window, key, *largs):
    if key == 289: # F8
        if recorder.play:
            Logger.error('Recorder: Cannot start recording while playing.')
            return
        recorder.record = not recorder.record
    elif key == 288: # F7
        if recorder.record:
            Logger.error('Recorder: Cannot start playing while recording.')
            return
        recorder.play = not recorder.play


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

    ctx.recorder = Recorder(window=win, **keys)
    win.bind(on_key_down=partial(on_recorder_key, ctx.recorder))


def stop(win, ctx):
    if hasattr(ctx, 'recorder'):
        ctx.recorder.release()

