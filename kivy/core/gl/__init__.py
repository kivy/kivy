'''
GL: Select which library will be used for providing OpenGL support
'''

# Right now, only PyOpenGL
from kivy.config import Config
from kivy.logger import Logger
import OpenGL
from OpenGL.GL import *
from OpenGL.GLU import *

# Disable pyOpenGL auto GL Error Check?
gl_check = Config.get('kivy', 'gl_error_check')
if gl_check.lower() in ['0', 'false', 'no']:
    import OpenGL
    OpenGL.ERROR_CHECKING = False

# To be able to use our GL provider, we must have a window
# Automaticly import window auto to ensure the default window creation
import kivy.core.window.default

# Display the current OpenGL version
version = glGetString(GL_VERSION)
Logger.info('GL: OpenGL version <%s>' % str(version))

