# pylint: disable=W0611
'''
OpenGL
======

Select and use the best OpenGL library available. Depending on your system, the
core provider can select an OpenGL ES or a 'classic' desktop OpenGL library.
'''

import sys
from os import environ

MIN_REQUIRED_GL_VERSION = (2, 0)


def msgbox(message):
    if sys.platform == 'win32':
        import ctypes
        from ctypes.wintypes import LPCWSTR
        ctypes.windll.user32.MessageBoxW(None, LPCWSTR(message),
                                         u"Kivy Fatal Error", 0)
        sys.exit(1)


if 'KIVY_DOC' not in environ:

    from kivy.logger import Logger
    from kivy.graphics import gl_init_resources
    from kivy.graphics.opengl_utils import gl_get_version
    from kivy.graphics.opengl import (
        GL_VERSION,
        GL_VENDOR,
        GL_RENDERER,
        GL_MAX_TEXTURE_IMAGE_UNITS,
        GL_MAX_TEXTURE_SIZE,
        GL_SHADING_LANGUAGE_VERSION,
        glGetString,
        glGetIntegerv,
        gl_init_symbols,
    )
    from kivy.graphics.cgl import cgl_get_initialized_backend_name
    from kivy.utils import platform

    def init_gl(allowed=[], ignored=[]):
        gl_init_symbols(allowed, ignored)
        print_gl_version()
        gl_init_resources()

    def print_gl_version():
        backend = cgl_get_initialized_backend_name()
        Logger.info('GL: Backend used <{}>'.format(backend))
        version = glGetString(GL_VERSION)
        vendor = glGetString(GL_VENDOR)
        renderer = glGetString(GL_RENDERER)
        Logger.info('GL: OpenGL version <{0}>'.format(version))
        Logger.info('GL: OpenGL vendor <{0}>'.format(vendor))
        Logger.info('GL: OpenGL renderer <{0}>'.format(renderer))

        # Let the user know if his graphics hardware/drivers are too old
        major, minor = gl_get_version()
        Logger.info('GL: OpenGL parsed version: %d, %d' % (major, minor))
        if ((major, minor) < MIN_REQUIRED_GL_VERSION and backend != "mock"):
            if hasattr(sys, "_kivy_opengl_required_func"):
                sys._kivy_opengl_required_func(major, minor, version, vendor,
                                               renderer)
            else:
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
            Logger.info('GL: Shading version <{0}>'.format(glGetString(
                GL_SHADING_LANGUAGE_VERSION)))
        Logger.info('GL: Texture max size <{0}>'.format(glGetIntegerv(
            GL_MAX_TEXTURE_SIZE)[0]))
        Logger.info('GL: Texture max units <{0}>'.format(glGetIntegerv(
            GL_MAX_TEXTURE_IMAGE_UNITS)[0]))

    # To be able to use our GL provider, we must have a window
    # Automatically import window auto to ensure the default window creation
    import kivy.core.window  # NOQA
