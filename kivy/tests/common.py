'''
This is a extended unittest module for Kivy, to make unittests based on
graphics with an OpenGL context.

The idea is to render a Widget tree, and after 1, 2 or more frames, a
screenshot will be made and be compared to the original one.
If no screenshot exists for the current test, the very first one will be used.

The screenshots live in the 'kivy/tests/results' folder and are in PNG format,
320x240 pixels.
'''

__all__ = ('GraphicUnitTest', )

import unittest
import logging
import os
import threading
from kivy.graphics.cgl import cgl_get_backend_name
from kivy.input.motionevent import MotionEvent
log = logging.getLogger('unittest')


_base = object
if 'mock' != cgl_get_backend_name():
    _base = unittest.TestCase

make_screenshots = os.environ.get('KIVY_UNITTEST_SCREENSHOTS')
http_server = None
http_server_ready = threading.Event()


def ensure_web_server():
    if http_server is not None:
        return True

    def _start_web_server():
        global http_server
        try:
            from SimpleHTTPServer import SimpleHTTPRequestHandler
            from SocketServer import TCPServer
        except ImportError:
            from http.server import SimpleHTTPRequestHandler
            from socketserver import TCPServer

        try:
            handler = SimpleHTTPRequestHandler
            handler.directory = os.path.join(
                os.path.dirname(__file__), "..", "..")
            http_server = TCPServer(
                ("", 8000), handler, bind_and_activate=False)
            http_server.daemon_threads = True
            http_server.allow_reuse_address = True
            http_server.server_bind()
            http_server.server_activate()
            http_server_ready.set()
            http_server.serve_forever()
        except:
            import traceback
            traceback.print_exc()
        finally:
            http_server = None
            http_server_ready.set()

    th = threading.Thread(target=_start_web_server)
    th.daemon = True
    th.start()
    http_server_ready.wait()
    if http_server is None:
        raise Exception("Unable to start webserver")


class GraphicUnitTest(_base):
    framecount = 0

    def _force_refresh(self, *largs):
        # this prevent in some case to be stuck if the screen doesn't refresh
        # and we wait for a number of self.framecount that never goes down
        from kivy.base import EventLoop
        win = EventLoop.window
        if win and win.canvas:
            win.canvas.ask_update()

    def render(self, root, framecount=1):
        '''Call rendering process using the `root` widget.
        The screenshot will be done in `framecount` frames.
        '''
        from kivy.base import runTouchApp
        from kivy.clock import Clock
        self.framecount = framecount
        try:
            Clock.schedule_interval(self._force_refresh, 1)
            runTouchApp(root)
        finally:
            Clock.unschedule(self._force_refresh)

        # reset for the next test, but nobody will know if it will be used :/
        if self.test_counter != 0:
            self.tearDown(fake=True)
            self.setUp()

    def run(self, *args, **kwargs):
        '''Extend the run of unittest, to check if results directory have been
        found. If no results directory exists, the test will be ignored.
        '''
        from os.path import join, dirname, exists
        results_dir = join(dirname(__file__), 'results')
        if make_screenshots and not exists(results_dir):
            log.warning('No result directory found, cancel test.')
            os.mkdir(results_dir)
        self.test_counter = 0
        self.results_dir = results_dir
        self.test_failed = False
        return super(GraphicUnitTest, self).run(*args, **kwargs)

    def setUp(self):
        '''Prepare the graphic test, with:
            - Window size fixed to 320x240
            - Default kivy configuration
            - Without any kivy input
        '''

        # use default kivy configuration (don't load user file.)
        from os import environ
        environ['KIVY_USE_DEFAULTCONFIG'] = '1'

        # force window size + remove all inputs
        from kivy.config import Config
        Config.set('graphics', 'width', '320')
        Config.set('graphics', 'height', '240')
        for items in Config.items('input'):
            Config.remove_option('input', items[0])

        # bind ourself for the later screenshot
        from kivy.core.window import Window
        self.Window = Window
        Window.bind(on_flip=self.on_window_flip)

        # ensure our window is correctly created
        Window.create_window()
        Window.register()
        Window.initialized = True
        Window.canvas.clear()
        Window.close = lambda *s: True

    def on_window_flip(self, window):
        '''Internal method to be called when the window have just displayed an
        image.
        When an image is showed, we decrement our framecount. If framecount is
        come to 0, we are taking the screenshot.

        The screenshot is done in a temporary place, and is compared to the
        original one -> test ok/ko.
        If no screenshot is available in the results directory, a new one will
        be created.
        '''
        from kivy.base import EventLoop
        from tempfile import mkstemp
        from os.path import join, exists
        from os import unlink, close
        from shutil import move, copy

        # don't save screenshot until we have enough frames.
        # log.debug('framecount %d' % self.framecount)
        # ! check if there is 'framecount', otherwise just
        # ! assume zero e.g. if handling runTouchApp manually
        self.framecount = getattr(self, 'framecount', 0) - 1
        if self.framecount > 0:
            return

        # don't create screenshots if not requested manually
        if not make_screenshots:
            EventLoop.stop()
            return

        reffn = None
        match = False
        try:
            # just get a temporary name
            fd, tmpfn = mkstemp(suffix='.png', prefix='kivyunit-')
            close(fd)
            unlink(tmpfn)

            # get a filename for the current unit test
            self.test_counter += 1
            test_uid = '%s-%d.png' % (
                '_'.join(self.id().split('.')[-2:]),
                self.test_counter)

            # capture the screen
            log.info('Capturing screenshot for %s' % test_uid)
            tmpfn = window.screenshot(tmpfn)
            log.info('Capture saved at %s' % tmpfn)

            # search the file to compare to
            reffn = join(self.results_dir, test_uid)
            log.info('Compare with %s' % reffn)

            # get sourcecode
            import inspect
            frame = inspect.getouterframes(inspect.currentframe())[6]
            sourcecodetab, line = inspect.getsourcelines(frame[0])
            line = frame[2] - line
            currentline = sourcecodetab[line]
            sourcecodetab[line] = '<span style="color: red;">%s</span>' % (
                currentline)
            sourcecode = ''.join(sourcecodetab)
            sourcecodetab[line] = '>>>>>>>>\n%s<<<<<<<<\n' % currentline
            sourcecodeask = ''.join(sourcecodetab)

            if not exists(reffn):
                log.info('No image reference, move %s as ref ?' % test_uid)
                if self.interactive_ask_ref(sourcecodeask, tmpfn, self.id()):
                    move(tmpfn, reffn)
                    tmpfn = reffn
                    log.info('Image used as reference')
                    match = True
                else:
                    log.info('Image discarded')
            else:
                from kivy.core.image import Image as CoreImage
                s1 = CoreImage(tmpfn, keep_data=True)
                sd1 = s1.image._data[0].data
                s2 = CoreImage(reffn, keep_data=True)
                sd2 = s2.image._data[0].data
                if sd1 != sd2:
                    log.critical(
                        '%s at render() #%d, images are different.' % (
                            self.id(), self.test_counter))
                    if self.interactive_ask_diff(sourcecodeask,
                                                 tmpfn, reffn, self.id()):
                        log.critical('user ask to use it as ref.')
                        move(tmpfn, reffn)
                        tmpfn = reffn
                        match = True
                    else:
                        self.test_failed = True
                else:
                    match = True

            # generate html
            from os.path import join, dirname, exists, basename
            from os import mkdir
            build_dir = join(dirname(__file__), 'build')
            if not exists(build_dir):
                mkdir(build_dir)
            copy(reffn, join(build_dir, 'ref_%s' % basename(reffn)))
            if tmpfn != reffn:
                copy(tmpfn, join(build_dir, 'test_%s' % basename(reffn)))
            with open(join(build_dir, 'index.html'), 'at') as fd:
                color = '#ffdddd' if not match else '#ffffff'
                fd.write('<div style="background-color: %s">' % color)
                fd.write('<h2>%s #%d</h2>' % (self.id(), self.test_counter))
                fd.write('<table><tr><th>Reference</th>'
                         '<th>Test</th>'
                         '<th>Comment</th>')
                fd.write('<tr><td><img src="ref_%s"/></td>' %
                         basename(reffn))
                if tmpfn != reffn:
                    fd.write('<td><img src="test_%s"/></td>' %
                             basename(reffn))
                else:
                    fd.write('<td>First time, no comparison.</td>')
                fd.write('<td><pre>%s</pre></td>' % sourcecode)
                fd.write('</table></div>')
        finally:
            try:
                if reffn != tmpfn:
                    unlink(tmpfn)
            except:
                pass
            EventLoop.stop()

    def tearDown(self, fake=False):
        '''When the test is finished, stop the application, and unbind our
        current flip callback.
        '''
        from kivy.base import stopTouchApp
        from kivy.core.window import Window
        Window.unbind(on_flip=self.on_window_flip)
        stopTouchApp()

        if not fake and self.test_failed:
            self.assertTrue(False)
        super(GraphicUnitTest, self).tearDown()

    def interactive_ask_ref(self, code, imagefn, testid):
        from os import environ
        if 'UNITTEST_INTERACTIVE' not in environ:
            return True

        from tkinter import Tk, Label, LEFT, RIGHT, BOTTOM, Button
        from PIL import Image, ImageTk

        self.retval = False

        root = Tk()

        def do_close():
            root.destroy()

        def do_yes():
            self.retval = True
            do_close()

        image = Image.open(imagefn)
        photo = ImageTk.PhotoImage(image)
        Label(root, text='The test %s\nhave no reference.' % testid).pack()
        Label(root, text='Use this image as a reference ?').pack()
        Label(root, text=code, justify=LEFT).pack(side=RIGHT)
        Label(root, image=photo).pack(side=LEFT)
        Button(root, text='Use as reference', command=do_yes).pack(side=BOTTOM)
        Button(root, text='Discard', command=do_close).pack(side=BOTTOM)
        root.mainloop()

        return self.retval

    def interactive_ask_diff(self, code, tmpfn, reffn, testid):
        from os import environ
        if 'UNITTEST_INTERACTIVE' not in environ:
            return False

        from tkinter import Tk, Label, LEFT, RIGHT, BOTTOM, Button
        from PIL import Image, ImageTk

        self.retval = False

        root = Tk()

        def do_close():
            root.destroy()

        def do_yes():
            self.retval = True
            do_close()

        phototmp = ImageTk.PhotoImage(Image.open(tmpfn))
        photoref = ImageTk.PhotoImage(Image.open(reffn))
        Label(root, text='The test %s\nhave generated an different'
              'image as the reference one..' % testid).pack()
        Label(root, text='Which one is good ?').pack()
        Label(root, text=code, justify=LEFT).pack(side=RIGHT)
        Label(root, image=phototmp).pack(side=RIGHT)
        Label(root, image=photoref).pack(side=LEFT)
        Button(root, text='Use the new image -->',
               command=do_yes).pack(side=BOTTOM)
        Button(root, text='<-- Use the reference',
               command=do_close).pack(side=BOTTOM)
        root.mainloop()

        return self.retval

    def advance_frames(self, count):
        '''Render the new frames and:

        * tick the Clock
        * dispatch input from all registered providers
        * flush all the canvas operations
        * redraw Window canvas if necessary
        '''
        from kivy.base import EventLoop
        for i in range(count):
            EventLoop.idle()


class UnitTestTouch(MotionEvent):
    '''Custom MotionEvent representing a single touch. Similar to `on_touch_*`
    methods from the Widget class, this one introduces:

    * touch_down
    * touch_move
    * touch_up

    Create a new touch with::

        touch = UnitTestTouch(x, y)

    then you press it on the default position with::

        touch.touch_down()

    or move it or even release with these simple calls::

        touch.touch_move(new_x, new_y)
        touch.touch_up()
    '''

    def __init__(self, x, y):
        '''Create a MotionEvent instance with X and Y of the first
        position a touch is at.
        '''

        from kivy.base import EventLoop
        self.eventloop = EventLoop
        win = EventLoop.window

        super(UnitTestTouch, self).__init__(
            # device, (tuio) id, args
            "UnitTestTouch", 99, {
                "x": x / float(win.width),
                "y": y / float(win.height),
            }
        )

    def touch_down(self, *args):
        self.eventloop.post_dispatch_input("begin", self)

    def touch_move(self, x, y):
        win = self.eventloop.window
        self.move({
            "x": x / float(win.width),
            "y": y / float(win.height)
        })
        self.eventloop.post_dispatch_input("update", self)

    def touch_up(self, *args):
        self.eventloop.post_dispatch_input("end", self)

    def depack(self, args):
        # set MotionEvent to touch
        self.is_touch = True

        # set sx/sy properties to ratio (e.g. X / win.width)
        self.sx = args['x']
        self.sy = args['y']

        # set profile to accept x, y and pos properties
        self.profile = ['pos']

        # run depack after we set the values
        super(UnitTestTouch, self).depack(args)
