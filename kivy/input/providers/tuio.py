'''
TUIO Input Provider
===================

TUIO is the de facto standard network protocol for the transmission of
touch and fiducial information between a server and a client. To learn
more about TUIO (which is itself based on the OSC protocol), please
refer to http://tuio.org -- The specification should be of special
interest.

Configure a TUIO provider in the config.ini
-------------------------------------------

The TUIO provider can be configured in the configuration file in the
``[input]`` section::

    [input]
    # name = tuio,<ip>:<port>
    multitouchtable = tuio,192.168.0.1:3333

Configure a TUIO provider in the App
------------------------------------

You must add the provider before your application is run, like this::

    from kivy.app import App
    from kivy.config import Config

    class TestApp(App):
        def build(self):
            Config.set('input', 'multitouchscreen1', 'tuio,0.0.0.0:3333')
            # You can also add a second TUIO listener
            # Config.set('input', 'source2', 'tuio,0.0.0.0:3334')
            # Then do the usual things
            # ...
            return
'''

__all__ = ('TuioMotionEventProvider', 'Tuio2dCurMotionEvent',
           'Tuio2dObjMotionEvent')

from kivy.lib import osc
from collections import deque
from kivy.input.provider import MotionEventProvider
from kivy.input.factory import MotionEventFactory
from kivy.input.motionevent import MotionEvent
from kivy.input.shape import ShapeRect
from kivy.logger import Logger


class TuioMotionEventProvider(MotionEventProvider):
    '''The TUIO provider listens to a socket and handles some of the incoming
    OSC messages:

        * /tuio/2Dcur
        * /tuio/2Dobj

    You can easily extend the provider to handle new TUIO paths like so::

        # Create a class to handle the new TUIO type/path
        # Replace NEWPATH with the pathname you want to handle
        class TuioNEWPATHMotionEvent(MotionEvent):
            def __init__(self, id, args):
                super(TuioNEWPATHMotionEvent, self).__init__(id, args)

            def depack(self, args):
                # In this method, implement 'unpacking' for the received
                # arguments. you basically translate from TUIO args to Kivy
                # MotionEvent variables. If all you receive are x and y
                # values, you can do it like this:
                if len(args) == 2:
                    self.sx, self.sy = args
                    self.profile = ('pos', )
                self.sy = 1 - self.sy
                super(TuioNEWPATHMotionEvent, self).depack(args)

        # Register it with the TUIO MotionEvent provider.
        # You obviously need to replace the PATH placeholders appropriately.
        TuioMotionEventProvider.register('/tuio/PATH', TuioNEWPATHMotionEvent)

    .. note::

        The class name is of no technical importance. Your class will be
        associated with the path that you pass to the ``register()``
        function. To keep things simple, you should name your class after the
        path that it handles, though.
    '''

    __handlers__ = {}

    def __init__(self, device, args):
        super(TuioMotionEventProvider, self).__init__(device, args)
        args = args.split(',')
        if len(args) <= 0:
            Logger.error('Tuio: Invalid configuration for TUIO provider')
            Logger.error('Tuio: Format must be ip:port (eg. 127.0.0.1:3333)')
            err = 'Tuio: Current configuration is <%s>' % (str(','.join(args)))
            Logger.error(err)
            return None
        ipport = args[0].split(':')
        if len(ipport) != 2:
            Logger.error('Tuio: Invalid configuration for TUIO provider')
            Logger.error('Tuio: Format must be ip:port (eg. 127.0.0.1:3333)')
            err = 'Tuio: Current configuration is <%s>' % (str(','.join(args)))
            Logger.error(err)
            return None
        self.ip, self.port = args[0].split(':')
        self.port = int(self.port)
        self.handlers = {}
        self.oscid = None
        self.tuio_event_q = deque()
        self.touches = {}

    @staticmethod
    def register(oscpath, classname):
        '''Register a new path to handle in TUIO provider'''
        TuioMotionEventProvider.__handlers__[oscpath] = classname

    @staticmethod
    def unregister(oscpath, classname):
        '''Unregister a path to stop handling it in the TUIO provider'''
        if oscpath in TuioMotionEventProvider.__handlers__:
            del TuioMotionEventProvider.__handlers__[oscpath]

    @staticmethod
    def create(oscpath, **kwargs):
        '''Create a touch event from a TUIO path'''
        if oscpath not in TuioMotionEventProvider.__handlers__:
            raise Exception('Unknown %s touch path' % oscpath)
        return TuioMotionEventProvider.__handlers__[oscpath](**kwargs)

    def start(self):
        '''Start the TUIO provider'''
        self.oscid = osc.listen(self.ip, self.port)
        for oscpath in TuioMotionEventProvider.__handlers__:
            self.touches[oscpath] = {}
            osc.bind(self.oscid, self._osc_tuio_cb, oscpath)

    def stop(self):
        '''Stop the TUIO provider'''
        osc.dontListen(self.oscid)

    def update(self, dispatch_fn):
        '''Update the TUIO provider (pop events from the queue)'''

        # deque osc queue
        osc.readQueue(self.oscid)

        # read the Queue with event
        while True:
            try:
                value = self.tuio_event_q.pop()
            except IndexError:
                # queue is empty, we're done for now
                return
            self._update(dispatch_fn, value)

    def _osc_tuio_cb(self, *incoming):
        message = incoming[0]
        oscpath, types, args = message[0], message[1], message[2:]
        self.tuio_event_q.appendleft([oscpath, args, types])

    def _update(self, dispatch_fn, value):
        oscpath, args, types = value
        command = args[0]

        # verify commands
        if command not in ['alive', 'set']:
            return

        # move or create a new touch
        if command == 'set':
            id = args[1]
            if id not in self.touches[oscpath]:
                # new touch
                touch = TuioMotionEventProvider.__handlers__[oscpath](
                    self.device, id, args[2:])
                self.touches[oscpath][id] = touch
                dispatch_fn('begin', touch)
            else:
                # update a current touch
                touch = self.touches[oscpath][id]
                touch.move(args[2:])
                dispatch_fn('update', touch)

        # alive event, check for deleted touch
        if command == 'alive':
            alives = args[1:]
            to_delete = []
            for id in self.touches[oscpath]:
                if id not in alives:
                    # touch up
                    touch = self.touches[oscpath][id]
                    if touch not in to_delete:
                        to_delete.append(touch)

            for touch in to_delete:
                dispatch_fn('end', touch)
                del self.touches[oscpath][touch.id]


class TuioMotionEvent(MotionEvent):
    '''Abstraction for TUIO touches/fiducials.

    Depending on the tracking software you use (e.g. Movid, CCV, etc.) and its
    TUIO implementation, the TuioMotionEvent object can support multiple
    profiles such as:

        * Fiducial ID: profile name 'markerid', attribute ``.fid``
        * Position: profile name 'pos', attributes ``.x``, ``.y``
        * Angle: profile name 'angle', attribute ``.a``
        * Velocity vector: profile name 'mov', attributes ``.X``, ``.Y``
        * Rotation velocity: profile name 'rot', attribute ``.A``
        * Motion acceleration: profile name 'motacc', attribute ``.m``
        * Rotation acceleration: profile name 'rotacc', attribute ``.r``
    '''
    __attrs__ = ('a', 'b', 'c', 'X', 'Y', 'Z', 'A', 'B', 'C', 'm', 'r')

    def __init__(self, device, id, args):
        super(TuioMotionEvent, self).__init__(device, id, args)
        # Default argument for TUIO touches
        self.a = 0.0
        self.b = 0.0
        self.c = 0.0
        self.X = 0.0
        self.Y = 0.0
        self.Z = 0.0
        self.A = 0.0
        self.B = 0.0
        self.C = 0.0
        self.m = 0.0
        self.r = 0.0

    angle = property(lambda self: self.a)
    mot_accel = property(lambda self: self.m)
    rot_accel = property(lambda self: self.r)
    xmot = property(lambda self: self.X)
    ymot = property(lambda self: self.Y)
    zmot = property(lambda self: self.Z)


class Tuio2dCurMotionEvent(TuioMotionEvent):
    '''A 2dCur TUIO touch.'''

    def __init__(self, device, id, args):
        super(Tuio2dCurMotionEvent, self).__init__(device, id, args)

    def depack(self, args):
        self.is_touch = True
        if len(args) < 5:
            self.sx, self.sy = list(map(float, args[0:2]))
            self.profile = ('pos', )
        elif len(args) == 5:
            self.sx, self.sy, self.X, self.Y, self.m = list(map(float,
                                                                args[0:5]))
            self.Y = -self.Y
            self.profile = ('pos', 'mov', 'motacc')
        else:
            self.sx, self.sy, self.X, self.Y = list(map(float, args[0:4]))
            self.m, width, height = list(map(float, args[4:7]))
            self.Y = -self.Y
            self.profile = ('pos', 'mov', 'motacc', 'shape')
            if self.shape is None:
                self.shape = ShapeRect()
            self.shape.width = width
            self.shape.height = height
        self.sy = 1 - self.sy
        super(Tuio2dCurMotionEvent, self).depack(args)


class Tuio2dObjMotionEvent(TuioMotionEvent):
    '''A 2dObj TUIO object.
    '''

    def __init__(self, device, id, args):
        super(Tuio2dObjMotionEvent, self).__init__(device, id, args)

    def depack(self, args):
        self.is_touch = True
        if len(args) < 5:
            self.sx, self.sy = args[0:2]
            self.profile = ('pos', )
        elif len(args) == 9:
            self.fid, self.sx, self.sy, self.a, self.X, self.Y = args[:6]
            self.A, self.m, self.r = args[6:9]
            self.Y = -self.Y
            self.profile = ('markerid', 'pos', 'angle', 'mov', 'rot',
                            'motacc', 'rotacc')
        else:
            self.fid, self.sx, self.sy, self.a, self.X, self.Y = args[:6]
            self.A, self.m, self.r, width, height = args[6:11]
            self.Y = -self.Y
            self.profile = ('markerid', 'pos', 'angle', 'mov', 'rot', 'rotacc',
                            'acc', 'shape')
            if self.shape is None:
                self.shape = ShapeRect()
                self.shape.width = width
                self.shape.height = height
        self.sy = 1 - self.sy
        super(Tuio2dObjMotionEvent, self).depack(args)


class Tuio2dBlbMotionEvent(TuioMotionEvent):
    '''A 2dBlb TUIO object.
    # FIXME 3d shape are not supported
    /tuio/2Dobj set s i x y a       X Y A m r
    /tuio/2Dblb set s   x y a w h f X Y A m r
    '''

    def __init__(self, device, id, args):
        super(Tuio2dBlbMotionEvent, self).__init__(device, id, args)

    def depack(self, args):
        self.is_touch = True
        self.sx, self.sy, self.a, self.X, self.Y, sw, sh, sd, \
            self.A, self.m, self.r = args
        self.Y = -self.Y
        self.profile = ('pos', 'angle', 'mov', 'rot', 'rotacc',
                        'acc', 'shape')
        if self.shape is None:
            self.shape = ShapeRect()
            self.shape.width = sw
            self.shape.height = sh
        self.sy = 1 - self.sy
        super(Tuio2dBlbMotionEvent, self).depack(args)


# registers
TuioMotionEventProvider.register('/tuio/2Dcur', Tuio2dCurMotionEvent)
TuioMotionEventProvider.register('/tuio/2Dobj', Tuio2dObjMotionEvent)
TuioMotionEventProvider.register('/tuio/2Dblb', Tuio2dBlbMotionEvent)
MotionEventFactory.register('tuio', TuioMotionEventProvider)
