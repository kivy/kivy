'''
Graphics: all low level function to draw object in OpenGL.

Previous version of graphx was rely on Immediate mode of Open Immediate mode
is not anymore allowed in OpenGL 3.0, and OpenGL ES.
This graphics module is the new and stable way to draw every elements inside
Kivy. We hardly ask you to use theses class !
'''

from kivy.graphics.instructions import *
from kivy.graphics.context_instructions import *
from kivy.graphics.vertex_instructions import *
