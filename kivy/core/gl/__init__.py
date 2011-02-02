'''
OpenGL
======

Select and use the best OpenGL library available. Depending on your system, the
core provider can select an OpenGL ES or a 'classic' desktop OpenGL library.
'''

# Right now, only PyOpenGL
from os import environ

if 'KIVY_DOC' not in environ:

    from kivy.logger import Logger
    from kivy.graphics import gl_init_resources
    from kivy.graphics.opengl import *

    def init_gl():
        gl_init_symbols()
        gl_init_resources()
        print_gl_version()

    def print_gl_version():
        version = glGetString(GL_VERSION)
        Logger.info('GL: OpenGL version <%s>' % str(version))

    # To be able to use our GL provider, we must have a window
    # Automaticly import window auto to ensure the default window creation
    import kivy.core.window
