'''
Input recorder
==============

.. versionadded:: 1.1.0

.. warning::

    This part of Kivy is still experimental and this API is subject to
    change in a future version.

This is a class that can record and replay some input events. This can
be used for test cases, screen savers etc.

Once activated, the recorder will listen for any input event and save its
properties in a file with the delta time. Later, you can play the input
file: it will generate fake touch events with the saved properties and
dispatch it to the event loop.

By default, only the position is saved ('pos' profile and 'sx', 'sy',
attributes). Change it only if you understand how input handling works.

Recording events
----------------

The best way is to use the "recorder" module. Check the :doc:`api-kivy.modules`
documentation to see how to activate a module.

Once activated, you can press F8 to start the recording. By default,
events will be written to `<currentpath>/recorder.kvi`. When you want to
stop recording, press F8 again.

You can replay the file by pressing F7.

Check the :doc:`api-kivy.modules.recorder` module for more information.

Manual play
-----------

You can manually open a recorder file, and play it by doing::

    from kivy.input.recorder import Recorder

    rec = Recorder(filename='myrecorder.kvi')
    rec.play = True

If you want to loop over that file, you can do::


    from kivy.input.recorder import Recorder

    def recorder_loop(instance, value):
        if value is False:
            instance.play = True

    rec = Recorder(filename='myrecorder.kvi')
    rec.bind(play=recorder_loop)
    rec.play = True

Recording more attributes
-------------------------

You can extend the attributes to save on one condition: attributes values must
be simple values, not instances of complex classes.

Let's say you want to save the angle and pressure of the touch, if available::

    from kivy.input.recorder import Recorder

    rec = Recorder(filename='myrecorder.kvi',
        record_attrs=['is_touch', 'sx', 'sy', 'angle', 'pressure'],
        record_profile_mask=['pos', 'angle', 'pressure'])
    rec.record = True

Or with modules variables::

    $ python main.py -m recorder,attrs=is_touch:sx:sy:angle:pressure, \
            profile_mask=pos:angle:pressure

Known limitations
-----------------

  - Unable to save attributes with instances of complex classes.
  - Values that represent time will not be adjusted.
  - Can replay only complete records. If a begin/update/end event is missing,
    this could lead to ghost touches.
  - Stopping the replay before the end can lead to ghost touches.

'''

__all__ = ('Recorder', )

from os.path import exists
from time import time
from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty, \
    NumericProperty, ListProperty
from kivy.input.motionevent import MotionEvent
from kivy.base import EventLoop
from kivy.logger import Logger
from ast import literal_eval
from functools import partial


class RecorderMotionEvent(MotionEvent):

    def depack(self, args):
        for key, value in list(args.items()):
            setattr(self, key, value)
        super(RecorderMotionEvent, self).depack(args)


class Recorder(EventDispatcher):
    '''Recorder class. Please check module documentation for more information.

    :Events:
        `on_stop`:
            Fired when the playing stops.

    .. versionchanged:: 1.10.0
        Event `on_stop` added.
    '''

    window = ObjectProperty(None)
    '''Window instance to attach the recorder. If None, it will use the
    default instance.

    :attr:`window` is a :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    '''

    counter = NumericProperty(0)
    '''Number of events recorded in the last session.

    :attr:`counter` is a :class:`~kivy.properties.NumericProperty` and defaults
    to 0, read-only.
    '''

    play = BooleanProperty(False)
    '''Boolean to start/stop the replay of the current file (if it exists).

    :attr:`play` is a :class:`~kivy.properties.BooleanProperty` and defaults to
    False.
    '''

    record = BooleanProperty(False)
    '''Boolean to start/stop the recording of input events.

    :attr:`record` is a :class:`~kivy.properties.BooleanProperty` and defaults
    to False.
    '''

    filename = StringProperty('recorder.kvi')
    '''Filename to save the output of the recorder.

    :attr:`filename` is a :class:`~kivy.properties.StringProperty` and defaults
    to 'recorder.kvi'.
    '''

    record_attrs = ListProperty(['is_touch', 'sx', 'sy'])
    '''Attributes to record from the motion event.

    :attr:`record_attrs` is a :class:`~kivy.properties.ListProperty` and
    defaults to ['is_touch', 'sx', 'sy'].
    '''

    record_profile_mask = ListProperty(['pos'])
    '''Profile to save in the fake motion event when replayed.

    :attr:`record_profile_mask` is a :class:`~kivy.properties.ListProperty` and
    defaults to ['pos'].
    '''

    # internals
    record_fd = ObjectProperty(None)
    record_time = NumericProperty(0.)

    __events__ = ('on_stop',)

    def __init__(self, **kwargs):
        super(Recorder, self).__init__(**kwargs)
        if self.window is None:
            # manually set the current window
            from kivy.core.window import Window
            self.window = Window
        self.window.bind(
            on_motion=self.on_motion,
            on_key_up=partial(self.on_keyboard, 'keyup'),
            on_key_down=partial(self.on_keyboard, 'keydown'),
            on_keyboard=partial(self.on_keyboard, 'keyboard'))

    def on_motion(self, window, etype, motionevent):
        if not self.record:
            return

        args = dict((arg, getattr(motionevent, arg))
                    for arg in self.record_attrs if hasattr(motionevent, arg))

        args['profile'] = [x for x in motionevent.profile if x in
                           self.record_profile_mask]
        self.record_fd.write('%r\n' % (
            (time() - self.record_time, etype, motionevent.uid, args), ))
        self.counter += 1

    def on_keyboard(self, etype, window, key, *args, **kwargs):
        if not self.record:
            return
        self.record_fd.write('%r\n' % (
            (time() - self.record_time, etype, 0, {
                'key': key,
                'scancode': kwargs.get('scancode'),
                'codepoint': kwargs.get('codepoint', kwargs.get('unicode')),
                'modifier': kwargs.get('modifier'),
                'is_touch': False}), ))
        self.counter += 1

    def release(self):
        self.window.unbind(
            on_motion=self.on_motion,
            on_key_up=self.on_keyboard,
            on_key_down=self.on_keyboard)

    def on_record(self, instance, value):
        if value:
            # generate a record filename
            self.counter = 0
            self.record_time = time()
            self.record_fd = open(self.filename, 'w')
            self.record_fd.write('#RECORDER1.0\n')
            Logger.info('Recorder: Recording inputs to %r' % self.filename)
        else:
            self.record_fd.close()
            Logger.info('Recorder: Recorded %d events in %r' % (self.counter,
                                                                self.filename))

    # needed for acting as an input provider
    def stop(self):
        pass

    def start(self):
        pass

    def on_play(self, instance, value):
        if not value:
            Logger.info('Recorder: Stop playing %r' % self.filename)
            EventLoop.remove_input_provider(self)
            return
        if not exists(self.filename):
            Logger.error('Recorder: Unable to find %r file, play aborted.' % (
                self.filename))
            return

        with open(self.filename, 'r') as fd:
            data = fd.read().splitlines()

        if len(data) < 2:
            Logger.error('Recorder: Unable to play %r, file truncated.' % (
                self.filename))
            return

        if data[0] != '#RECORDER1.0':
            Logger.error('Recorder: Unable to play %r, invalid header.' % (
                self.filename))
            return

        # decompile data
        self.play_data = [literal_eval(x) for x in data[1:]]
        self.play_time = time()
        self.play_me = {}
        Logger.info('Recorder: Start playing %d events from %r' %
                    (len(self.play_data), self.filename))
        EventLoop.add_input_provider(self)

    def on_stop(self):
        pass

    def update(self, dispatch_fn):
        if not self.play_data:
            Logger.info('Recorder: Playing finished.')
            self.play = False
            self.dispatch('on_stop')

        dt = time() - self.play_time
        while self.play_data:
            event = self.play_data[0]
            assert(len(event) == 4)
            if event[0] > dt:
                return

            me = None
            etype, uid, args = event[1:]
            if etype == 'begin':
                me = RecorderMotionEvent('recorder', uid, args)
                self.play_me[uid] = me
            elif etype == 'update':
                me = self.play_me[uid]
                me.depack(args)
            elif etype == 'end':
                me = self.play_me.pop(uid)
                me.depack(args)
            elif etype == 'keydown':
                self.window.dispatch(
                    'on_key_down',
                    args['key'],
                    args['scancode'],
                    args['codepoint'],
                    args['modifier'])
            elif etype == 'keyup':
                self.window.dispatch(
                    'on_key_up',
                    args['key'],
                    args['scancode'],
                    args['codepoint'],
                    args['modifier'])
            elif etype == 'keyboard':
                self.window.dispatch(
                    'on_keyboard',
                    args['key'],
                    args['scancode'],
                    args['codepoint'],
                    args['modifier'])

            if me:
                dispatch_fn(etype, me)

            self.play_data.pop(0)


def start(win, ctx):
    ctx.recorder = Recorder(window=win)


def stop(win, ctx):
    if hasattr(ctx, 'recorder'):
        ctx.recorder.release()
