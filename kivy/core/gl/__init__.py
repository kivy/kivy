# pylint: disable=W0611
'''
OpenGL
======

Select and use the best OpenGL library available. Depending on your system, the
core provider can select an OpenGL ES or a 'classic' desktop OpenGL library.
'''

from os import environ
from sys import platform, exit


MIN_REQUIRED_GL_VERSION = (2, 0)


def msgbox(message):
    if platform == 'win32':
        import win32ui
        win32ui.MessageBox(message, 'Kivy Fatal Error')
        exit(1)

if 'KIVY_DOC' not in environ:

    from kivy.logger import Logger
    from kivy.graphics import gl_init_resources
    from kivy.graphics.opengl_utils import gl_get_version
    from kivy.graphics.opengl import *
    from kivy.utils import platform

    def init_gl():
        gl_init_symbols()
        print_gl_version()
        gl_init_resources()

    def print_gl_version():
        version = glGetString(GL_VERSION)
        vendor = glGetString(GL_VENDOR)
        renderer = glGetString(GL_RENDERER)
        Logger.info('GL: OpenGL version <{0}>'.format(version))
        Logger.info('GL: OpenGL vendor <{0}>'.format(vendor))
        Logger.info('GL: OpenGL renderer <{0}>'.format(renderer))

        # Let the user know if his graphics hardware/drivers are too old
        major, minor = gl_get_version()
        Logger.info('GL: OpenGL parsed version: %d, %d' % (major, minor))
        if (major, minor) < MIN_REQUIRED_GL_VERSION:
            msg = (
                'GL: Minimum required OpenGL version (2.0) NOT found!\n\n'
                'OpenGL version detected: {0}.{1}\n\n'
                'Version: {2}\nVendor: {3}\nRenderer: {4}\n\n'
                'Try upgrading your graphics drivers and/or your '
                'graphics hardware in case of problems.\n\n'
                'The application will leave now.').format(
                        major, minor, version, vendor, renderer)
            Logger.critical(msg)
            msgbox(msg)

        if platform != 'android':
            # XXX in the android emulator (latest version at 22 march 2013),
            # this call was segfaulting the gl stack.
            Logger.info('GL: Shading version <{0}>'.format(
                glGetString(GL_SHADING_LANGUAGE_VERSION)))
        Logger.info('GL: Texture max size <{0}>'.format(
            glGetIntegerv(GL_MAX_TEXTURE_SIZE)[0]))
        Logger.info('GL: Texture max units <{0}>'.format(
            glGetIntegerv(GL_MAX_TEXTURE_IMAGE_UNITS)[0]))

    # To be able to use our GL provider, we must have a window
    # Automaticly import window auto to ensure the default window creation
    import kivy.core.window
