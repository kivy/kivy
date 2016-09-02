'''
This is a extended unittest module for Kivy, to make unittest based on
graphics with OpenGL context.

The idea is to let user render a Widget tree, and after 1, 2 or x frame, a
screenshot will be done, and be compared to the original one.
If no screenshot exist for the current test, the very first one will be used.

The screenshots lives in kivy/tests/results, in PNG format, 320x240.
'''

__all__ = ('GraphicUnitTest', )

import unittest
import logging
import os
log = logging.getLogger('unittest')

_base = object
if not bool(int(os.environ.get('USE_OPENGL_MOCK', 0))):
    _base = unittest.TestCase


class GraphicUnitTest(_base):

    def render(self, root, framecount=1):
        '''Call rendering process using the `root` widget.
        The screenshot will be done in `framecount` frames.
        '''
        from kivy.base import runTouchApp
        self.framecount = framecount
        runTouchApp(root)

        # reset for the next test, but nobody will know if it will be used :/
        if self.test_counter != 0:
            self.tearDown(fake=True)
            self.setUp()

    def run(self, name):
        '''Extend the run of unittest, to check if results directory have been
        found. If no results directory exists, the test will be ignored.
        '''
        from os.path import join, dirname, exists
        results_dir = join(dirname(__file__), 'results')
        if not exists(results_dir):
            log.warning('No result directory found, cancel test.')
            return
        self.test_counter = 0
        self.results_dir = results_dir
        self.test_failed = False
        return super(GraphicUnitTest, self).run(name)

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
        Window.bind(on_flip=self.on_window_flip)

        # ensure our window is correctly created
        Window.create_window()
        Window.canvas.clear()

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
        #log.debug('framecount %d' % self.framecount)
        self.framecount -= 1
        if self.framecount > 0:
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
                import pygame
                s1 = pygame.image.load(tmpfn)
                s2 = pygame.image.load(reffn)
                sd1 = pygame.image.tostring(s1, 'RGB')
                sd2 = pygame.image.tostring(s2, 'RGB')
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
