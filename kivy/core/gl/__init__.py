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
    from kivy.graphics.opengl import *

    def init_gl():
        gl_init_symbols()
        gl_init_resources()
        print_gl_version()

    def print_gl_version():
        # As per http://www.opengl.org/resources/faq/technical/extensions.htm
        # the format for the string is:
        # """The first part of the return string must be of the form
        # [major-number].[minor-number], optionally followed by a release
        # number or other vendor-specific information.
        version = str(glGetString(GL_VERSION))
        try:
            majorminor = version.split()[0]
            major, minor = majorminor.split('.')
        except:
            # We don't want to bail out here if there is an error while parsing
            # Just raise a warning (God knows what vendors return here...)
            Logger.warning('GL: Error parsing OpenGL version: %s' % version)
        else:
            # If parsing went without problems, let the user know if his
            # graphics hardware/drivers are too old
            if (major, minor) < MIN_REQUIRED_GL_VERSION:
                msg = 'GL: Minimum required OpenGL version (2.0) NOT found! ' \
                      'Try upgrading your graphics drivers and/or your ' \
                      'graphics hardware in case of problems.'
                Logger.critical(msg)

        Logger.info('GL: OpenGL version <%s>' % version)
        Logger.info('GL: OpenGL vendor <%s>' % str(glGetString(GL_VENDOR)))
        Logger.info('GL: OpenGL renderer <%s>' % str(glGetString(GL_RENDERER)))

    # To be able to use our GL provider, we must have a window
    # Automaticly import window auto to ensure the default window creation
    import kivy.core.window
