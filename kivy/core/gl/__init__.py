'''
OpenGL
======

Select and use the best OpenGL library available. Depending on your system, the
core provider can select an OpenGL ES or a 'classic' desktop OpenGL library.
'''

from os import environ


MIN_REQUIRED_GL_VERSION = (2, 0)


if 'KIVY_DOC' not in environ:

    from kivy.logger import Logger
    from kivy.graphics import gl_init_resources
    from kivy.graphics.opengl_utils import gl_get_version
    from kivy.graphics.opengl import *

    def init_gl():
        gl_init_symbols()
        gl_init_resources()
        print_gl_version()

    def print_gl_version():
        version = str(glGetString(GL_VERSION))
        Logger.info('GL: OpenGL version <%s>' % version)
        Logger.info('GL: OpenGL vendor <%s>' % str(
            glGetString(GL_VENDOR)))
        Logger.info('GL: OpenGL renderer <%s>' % str(
            glGetString(GL_RENDERER)))
        Logger.info('GL: Shading version <%s>' % str(
            glGetString(GL_SHADING_LANGUAGE_VERSION)))
        Logger.info('GL: Texture max size <%s>' % str(
            glGetIntegerv(GL_MAX_TEXTURE_SIZE)[0]))
        Logger.info('GL: Texture max units <%s>' % str(
            glGetIntegerv(GL_MAX_TEXTURE_IMAGE_UNITS)[0]))

        # Let the user know if his graphics hardware/drivers are too old
        major, minor = gl_get_version()
        Logger.info('GL: OpenGL parsed version: %d, %d' % (major, minor))
        if (major, minor) < MIN_REQUIRED_GL_VERSION:
            msg = 'GL: Minimum required OpenGL version (2.0) NOT found! ' \
                    'Try upgrading your graphics drivers and/or your ' \
                    'graphics hardware in case of problems.'
            Logger.critical(msg)

    # To be able to use our GL provider, we must have a window
    # Automaticly import window auto to ensure the default window creation
    __import__('kivy.core.window')
