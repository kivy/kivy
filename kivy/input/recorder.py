'''
Input recorder
==============

.. versionadded:: 1.1.0

.. warning::

    This part of Kivy is still experimental, and his API is subject to change in
    a future version.

This is a class that can record and replay some part of input events. This can
be used for test case, screen saver etc.

Once activated, the recorder will listen to any input event, and save some
properties in a file + the delta time. Later, you can play the input file: it
will generate fake touch with saved properties, and dispatch it to the event
loop.

By default, only the position are saved ('pos' profile and 'sx', 'sy',
attributes). Changes it only if you understand how input is working.

Recording events
----------------

The best way is to use the "recorder" module. Check the :doc:`api-kivy.modules`
documentation for learning about how to activate a module.

When activated, you can press F8 to start the recording. By default, events will
be written at `<currentpath>/recorder.kvi`. When you want to stop recording,
press F8 again.

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

You can extend the attributes to save, at one condition: attributes values must
be simple value, not instance of complex class. Aka, saving shape will not work.

Let's say you want to save angle and pressure of the touch, if available::

    from kivy.input.recorder import Recorder

    rec = Recorder(filename='myrecorder.kvi',
        record_attrs=['is_touch', 'sx', 'sy', 'angle', 'pressure'],
        record_profile_mask=['pos', 'angle', 'pressure'])
    rec.record = True

Or with modules variables::

    $ python main.py -m recorder,attrs=is_touch:sx:sy:angle:pressure,profile_mask=pos:angle:pressure

Known limitations
-----------------

  - Unable to save attributes with instance of complex class
  - Values that represent time will be not adjusted
  - Can replay only complete record, if a begin/update/end event is missing,
    this could lead to ghost touch.
  - Stopping the replay before the end can lead to ghost touch.

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


class RecorderMotionEvent(MotionEvent):

    def depack(self, args):
        for key, value in args.iteritems():
            setattr(self, key, value)
        super(RecorderMotionEvent, self).depack(args)


class Recorder(EventDispatcher):
    '''Recorder class, check module documentation for more information.
    '''

    window = ObjectProperty(None)
    '''Window instance to attach the recorder. If None set, it will use the
    default one.

    :data:`window` is a :class:`~kivy.properties.ObjectProperty`, default to
    None.
    '''

    counter = NumericProperty(0)
    '''Number of events recorded in the last session.

    :data:`counter` is a :class:`~kivy.properties.NumericProperty`, default to
    0, read-only.
    '''

    play = BooleanProperty(False)
    '''Boolean to start/stop the replay of the current file (if exist.)

    :data:`play` is a :class:`~kivy.properties.BooleanProperty`, default to
    False.
    '''

    record = BooleanProperty(False)
    '''Boolean to start/stop the recording of input events.

    :data:`record` is a :class:`~kivy.properties.BooleanProperty`, default to
    False.
    '''

    filename = StringProperty('recorder.kvi')
    '''Filename to save the output of recorder.

    :data:`filename` is a :class:`~kivy.properties.StringProperty`, default to
    'recorder.kvi'.
    '''

    record_attrs = ListProperty(['is_touch', 'sx', 'sy'])
    '''Attributes to record from the motion event.

    :data:`record_attrs` is a :class:`~kivy.properties.ListProperty`, default to
    ['is_touch', 'sx', 'sy'].
    '''

    record_profile_mask = ListProperty(['pos'])
    '''Profile to save in the fake motion event when replayed.

    :data:`record_profile_mask` is a :class:`~kivy.properties.ListProperty`,
    default to ['pos'].
    '''

    # internals
    record_fd = ObjectProperty(None)
    record_time = NumericProperty(0.)

    def __init__(self, **kwargs):
        super(Recorder, self).__init__(**kwargs)
        if self.window is None:
            # manually set the current window
            from kivy.core.window import Window
            self.window = Window
        self.window.bind(on_motion=self.on_motion)

    def on_motion(self, window, etype, motionevent):
        if not self.record:
            return
        args = {}
        for arg in self.record_attrs:
            if hasattr(motionevent, arg):
                args[arg] = getattr(motionevent, arg)
        args['profile'] = [x for x in motionevent.profile if x in
                self.record_profile_mask]
        self.record_fd.write('%r\n' % (
            (time() - self.record_time, etype, motionevent.uid, args), ))
        self.counter += 1

    def release(self):
        self.window.unbind(on_motion=self.on_motion)

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
            Logger.error('Recorder: Unable to found %r file, play aborted.' % (
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

    def update(self, dispatch_fn):
        if len(self.play_data) == 0:
            Logger.info('Recorder: Playing finished.')
            self.play = False

        dt = time() - self.play_time
        while len(self.play_data):
            event = self.play_data[0]
            assert(len(event) == 4)
            if event[0] > dt:
                return

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

            dispatch_fn(etype, me)

            self.play_data.pop(0)


def start(win, ctx):
    ctx.recorder = Recorder(window=win)


def stop(win, ctx):
    if hasattr(ctx, 'recorder'):
        ctx.recorder.release()
