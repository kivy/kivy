"""
CGL: standard C interface for OpenGL
====================================

Kivy uses OpenGL and therefore requires a backend that provides it.
The backend used is controlled through the ``USE_OPENGL_MOCK`` and ``USE_SDL2``
compile-time variables and through the ``KIVY_GL_BACKEND`` runtime
environmental variable.

Currently, OpenGL is used through direct linking (gl/glew), sdl2,
or by mocking it. Setting ``USE_OPENGL_MOCK`` disables gl/glew.
Similarly, setting ``USE_SDL2`` to ``0`` will disable sdl2. Mocking
is always available.

At runtime the following backends are available and can be set using
``KIVY_GL_BACKEND``:

* ``gl`` -- Available on unix (the default backend). Unavailable when
  ``USE_OPENGL_MOCK=0``. Requires gl be installed.
* ``glew`` -- Available on Windows (the default backend). Unavailable when
  ``USE_OPENGL_MOCK=0``. Requires glew be installed.
* ``sdl2`` -- Available on Windows/unix (the default when gl/glew is disabled).
  Unavailable when ``USE_SDL2=0``. Requires ``kivy_deps.sdl2`` be installed.
* ``angle_sdl2`` -- Available on Windows with Python 3.5+.
  Unavailable when ``USE_SDL2=0``. Requires ``kivy_deps.sdl2`` and
  ``kivy_deps.angle`` be installed.
* ``mock`` -- Always available. Doesn't actually do anything.


Additionally, the following environmental runtime variables control the graphics
system:

* ``KIVY_GL_DEBUG`` -- Logs al gl calls when ``1``.
* ``KIVY_GRAPHICS`` -- Forces OpenGL ES2 when it is ``gles``. OpenGL ES2 is always
  used on the android, ios, rpi, and mali OSs.
"""

include "../include/config.pxi"

from sys import platform
from os import environ
from cgl cimport GLES2_Context
import importlib
from kivy.logger import Logger

cdef GLES2_Context g_cgl
cdef GLES2_Context *cgl = &g_cgl
cdef object cgl_name = None
cdef int kivy_opengl_es2 = USE_OPENGL_ES2 or environ.get('KIVY_GRAPHICS', '').lower() == 'gles'


cpdef cgl_get_initialized_backend_name():
    return cgl_name


cpdef cgl_get_backend_name(allowed=[], ignored=[]):
    if cgl_name:
        return cgl_name
    name = environ.get("KIVY_GL_BACKEND")
    if name:
        return name.lower()

    for name in ('glew', 'sdl2', 'gl', 'mock'):
        if allowed and name not in allowed:
            continue
        if name in ignored:
            continue

        mod = importlib.import_module("kivy.graphics.cgl_backend.cgl_{}".format(name))
        if mod.is_backend_supported():
            return name
    assert False


cdef GLES2_Context *cgl_get_context():
    return cgl


cdef void cgl_set_context(GLES2_Context* ctx):
    global cgl
    cgl = ctx


cpdef cgl_init(allowed=[], ignored=[]):
    Logger.info('GL: Using the "{}" graphics system'.format(
        'OpenGL ES 2' if kivy_opengl_es2 else 'OpenGL'))
    global cgl_name
    cgl_name = backend = cgl_get_backend_name(allowed, ignored)

    # for ANGLE, currently we use sdl2, and only on windows.
    if backend == "angle_sdl2":
        if platform != "win32":
            raise Exception("CGL: ANGLE backend can be used only on Windows")
        backend = "sdl2"

    if cgl_name not in {'glew', 'sdl2', 'angle_sdl2', 'mock', 'gl'}:
        raise ValueError('{} is not a recognized GL backend'.format(backend))

    mod = importlib.import_module("kivy.graphics.cgl_backend.cgl_{}".format(backend))
    mod.init_backend()
    log_cgl_funcs()

    use_debug = environ.get("KIVY_GL_DEBUG") == "1"
    if use_debug:
        mod = importlib.import_module("kivy.graphics.cgl_backend.cgl_debug")
        mod.init_backend_debug()


cdef void log_cgl_funcs() except *:
    if cgl.glActiveTexture == NULL:
        Logger.debug('GL: glActiveTexture is not available')
    if cgl.glAttachShader == NULL:
        Logger.debug('GL: glAttachShader is not available')
    if cgl.glBindAttribLocation == NULL:
        Logger.debug('GL: glBindAttribLocation is not available')
    if cgl.glBindBuffer == NULL:
        Logger.debug('GL: glBindBuffer is not available')
    if cgl.glBindFramebuffer == NULL:
        Logger.debug('GL: glBindFramebuffer is not available')
    if cgl.glBindRenderbuffer == NULL:
        Logger.debug('GL: glBindRenderbuffer is not available')
    if cgl.glBindTexture == NULL:
        Logger.debug('GL: glBindTexture is not available')
    if cgl.glBlendColor == NULL:
        Logger.debug('GL: glBlendColor is not available')
    if cgl.glBlendEquation == NULL:
        Logger.debug('GL: glBlendEquation is not available')
    if cgl.glBlendEquationSeparate == NULL:
        Logger.debug('GL: glBlendEquationSeparate is not available')
    if cgl.glBlendFunc == NULL:
        Logger.debug('GL: glBlendFunc is not available')
    if cgl.glBlendFuncSeparate == NULL:
        Logger.debug('GL: glBlendFuncSeparate is not available')
    if cgl.glBufferData == NULL:
        Logger.debug('GL: glBufferData is not available')
    if cgl.glBufferSubData == NULL:
        Logger.debug('GL: glBufferSubData is not available')
    if cgl.glCheckFramebufferStatus == NULL:
        Logger.debug('GL: glCheckFramebufferStatus is not available')
    if cgl.glClear == NULL:
        Logger.debug('GL: glClear is not available')
    if cgl.glClearColor == NULL:
        Logger.debug('GL: glClearColor is not available')
    if cgl.glClearStencil == NULL:
        Logger.debug('GL: glClearStencil is not available')
    if cgl.glColorMask == NULL:
        Logger.debug('GL: glColorMask is not available')
    if cgl.glCompileShader == NULL:
        Logger.debug('GL: glCompileShader is not available')
    if cgl.glCompressedTexImage2D == NULL:
        Logger.debug('GL: glCompressedTexImage2D is not available')
    if cgl.glCompressedTexSubImage2D == NULL:
        Logger.debug('GL: glCompressedTexSubImage2D is not available')
    if cgl.glCopyTexImage2D == NULL:
        Logger.debug('GL: glCopyTexImage2D is not available')
    if cgl.glCopyTexSubImage2D == NULL:
        Logger.debug('GL: glCopyTexSubImage2D is not available')
    if cgl.glCreateProgram == NULL:
        Logger.debug('GL: glCreateProgram is not available')
    if cgl.glCreateShader == NULL:
        Logger.debug('GL: glCreateShader is not available')
    if cgl.glCullFace == NULL:
        Logger.debug('GL: glCullFace is not available')
    if cgl.glDeleteBuffers == NULL:
        Logger.debug('GL: glDeleteBuffers is not available')
    if cgl.glDeleteFramebuffers == NULL:
        Logger.debug('GL: glDeleteFramebuffers is not available')
    if cgl.glDeleteProgram == NULL:
        Logger.debug('GL: glDeleteProgram is not available')
    if cgl.glDeleteRenderbuffers == NULL:
        Logger.debug('GL: glDeleteRenderbuffers is not available')
    if cgl.glDeleteShader == NULL:
        Logger.debug('GL: glDeleteShader is not available')
    if cgl.glDeleteTextures == NULL:
        Logger.debug('GL: glDeleteTextures is not available')
    if cgl.glDepthFunc == NULL:
        Logger.debug('GL: glDepthFunc is not available')
    if cgl.glDepthMask == NULL:
        Logger.debug('GL: glDepthMask is not available')
    if cgl.glDetachShader == NULL:
        Logger.debug('GL: glDetachShader is not available')
    if cgl.glDisable == NULL:
        Logger.debug('GL: glDisable is not available')
    if cgl.glDisableVertexAttribArray == NULL:
        Logger.debug('GL: glDisableVertexAttribArray is not available')
    if cgl.glDrawArrays == NULL:
        Logger.debug('GL: glDrawArrays is not available')
    if cgl.glDrawElements == NULL:
        Logger.debug('GL: glDrawElements is not available')
    if cgl.glEnable == NULL:
        Logger.debug('GL: glEnable is not available')
    if cgl.glEnableVertexAttribArray == NULL:
        Logger.debug('GL: glEnableVertexAttribArray is not available')
    if cgl.glFinish == NULL:
        Logger.debug('GL: glFinish is not available')
    if cgl.glFlush == NULL:
        Logger.debug('GL: glFlush is not available')
    if cgl.glFramebufferRenderbuffer == NULL:
        Logger.debug('GL: glFramebufferRenderbuffer is not available')
    if cgl.glFramebufferTexture2D == NULL:
        Logger.debug('GL: glFramebufferTexture2D is not available')
    if cgl.glFrontFace == NULL:
        Logger.debug('GL: glFrontFace is not available')
    if cgl.glGenBuffers == NULL:
        Logger.debug('GL: glGenBuffers is not available')
    if cgl.glGenerateMipmap == NULL:
        Logger.debug('GL: glGenerateMipmap is not available')
    if cgl.glGenFramebuffers == NULL:
        Logger.debug('GL: glGenFramebuffers is not available')
    if cgl.glGenRenderbuffers == NULL:
        Logger.debug('GL: glGenRenderbuffers is not available')
    if cgl.glGenTextures == NULL:
        Logger.debug('GL: glGenTextures is not available')
    if cgl.glGetActiveAttrib == NULL:
        Logger.debug('GL: glGetActiveAttrib is not available')
    if cgl.glGetActiveUniform == NULL:
        Logger.debug('GL: glGetActiveUniform is not available')
    if cgl.glGetAttachedShaders == NULL:
        Logger.debug('GL: glGetAttachedShaders is not available')
    if cgl.glGetAttribLocation == NULL:
        Logger.debug('GL: glGetAttribLocation is not available')
    if cgl.glGetBooleanv == NULL:
        Logger.debug('GL: glGetBooleanv is not available')
    if cgl.glGetBufferParameteriv == NULL:
        Logger.debug('GL: glGetBufferParameteriv is not available')
    if cgl.glGetError == NULL:
        Logger.debug('GL: glGetError is not available')
    if cgl.glGetFloatv == NULL:
        Logger.debug('GL: glGetFloatv is not available')
    if cgl.glGetFramebufferAttachmentParameteriv == NULL:
        Logger.debug('GL: glGetFramebufferAttachmentParameteriv is not available')
    if cgl.glGetIntegerv == NULL:
        Logger.debug('GL: glGetIntegerv is not available')
    if cgl.glGetProgramInfoLog == NULL:
        Logger.debug('GL: glGetProgramInfoLog is not available')
    if cgl.glGetProgramiv == NULL:
        Logger.debug('GL: glGetProgramiv is not available')
    if cgl.glGetRenderbufferParameteriv == NULL:
        Logger.debug('GL: glGetRenderbufferParameteriv is not available')
    if cgl.glGetShaderInfoLog == NULL:
        Logger.debug('GL: glGetShaderInfoLog is not available')
    if cgl.glGetShaderiv == NULL:
        Logger.debug('GL: glGetShaderiv is not available')
    if cgl.glGetShaderSource == NULL:
        Logger.debug('GL: glGetShaderSource is not available')
    if cgl.glGetString == NULL:
        Logger.debug('GL: glGetString is not available')
    if cgl.glGetTexParameterfv == NULL:
        Logger.debug('GL: glGetTexParameterfv is not available')
    if cgl.glGetTexParameteriv == NULL:
        Logger.debug('GL: glGetTexParameteriv is not available')
    if cgl.glGetUniformfv == NULL:
        Logger.debug('GL: glGetUniformfv is not available')
    if cgl.glGetUniformiv == NULL:
        Logger.debug('GL: glGetUniformiv is not available')
    if cgl.glGetUniformLocation == NULL:
        Logger.debug('GL: glGetUniformLocation is not available')
    if cgl.glGetVertexAttribfv == NULL:
        Logger.debug('GL: glGetVertexAttribfv is not available')
    if cgl.glGetVertexAttribiv == NULL:
        Logger.debug('GL: glGetVertexAttribiv is not available')
    if cgl.glHint == NULL:
        Logger.debug('GL: glHint is not available')
    if cgl.glIsBuffer == NULL:
        Logger.debug('GL: glIsBuffer is not available')
    if cgl.glIsEnabled == NULL:
        Logger.debug('GL: glIsEnabled is not available')
    if cgl.glIsFramebuffer == NULL:
        Logger.debug('GL: glIsFramebuffer is not available')
    if cgl.glIsProgram == NULL:
        Logger.debug('GL: glIsProgram is not available')
    if cgl.glIsRenderbuffer == NULL:
        Logger.debug('GL: glIsRenderbuffer is not available')
    if cgl.glIsShader == NULL:
        Logger.debug('GL: glIsShader is not available')
    if cgl.glIsTexture == NULL:
        Logger.debug('GL: glIsTexture is not available')
    if cgl.glLineWidth == NULL:
        Logger.debug('GL: glLineWidth is not available')
    if cgl.glLinkProgram == NULL:
        Logger.debug('GL: glLinkProgram is not available')
    if cgl.glPixelStorei == NULL:
        Logger.debug('GL: glPixelStorei is not available')
    if cgl.glPolygonOffset == NULL:
        Logger.debug('GL: glPolygonOffset is not available')
    if cgl.glReadPixels == NULL:
        Logger.debug('GL: glReadPixels is not available')
    if cgl.glRenderbufferStorage == NULL:
        Logger.debug('GL: glRenderbufferStorage is not available')
    if cgl.glSampleCoverage == NULL:
        Logger.debug('GL: glSampleCoverage is not available')
    if cgl.glScissor == NULL:
        Logger.debug('GL: glScissor is not available')
    if cgl.glShaderBinary == NULL:
        Logger.debug('GL: glShaderBinary is not available')
    if cgl.glShaderSource == NULL:
        Logger.debug('GL: glShaderSource is not available')
    if cgl.glStencilFunc == NULL:
        Logger.debug('GL: glStencilFunc is not available')
    if cgl.glStencilFuncSeparate == NULL:
        Logger.debug('GL: glStencilFuncSeparate is not available')
    if cgl.glStencilMask == NULL:
        Logger.debug('GL: glStencilMask is not available')
    if cgl.glStencilMaskSeparate == NULL:
        Logger.debug('GL: glStencilMaskSeparate is not available')
    if cgl.glStencilOp == NULL:
        Logger.debug('GL: glStencilOp is not available')
    if cgl.glStencilOpSeparate == NULL:
        Logger.debug('GL: glStencilOpSeparate is not available')
    if cgl.glTexImage2D == NULL:
        Logger.debug('GL: glTexImage2D is not available')
    if cgl.glTexParameterf == NULL:
        Logger.debug('GL: glTexParameterf is not available')
    if cgl.glTexParameteri == NULL:
        Logger.debug('GL: glTexParameteri is not available')
    if cgl.glTexSubImage2D == NULL:
        Logger.debug('GL: glTexSubImage2D is not available')
    if cgl.glUniform1f == NULL:
        Logger.debug('GL: glUniform1f is not available')
    if cgl.glUniform1fv == NULL:
        Logger.debug('GL: glUniform1fv is not available')
    if cgl.glUniform1i == NULL:
        Logger.debug('GL: glUniform1i is not available')
    if cgl.glUniform1iv == NULL:
        Logger.debug('GL: glUniform1iv is not available')
    if cgl.glUniform2f == NULL:
        Logger.debug('GL: glUniform2f is not available')
    if cgl.glUniform2fv == NULL:
        Logger.debug('GL: glUniform2fv is not available')
    if cgl.glUniform2i == NULL:
        Logger.debug('GL: glUniform2i is not available')
    if cgl.glUniform2iv == NULL:
        Logger.debug('GL: glUniform2iv is not available')
    if cgl.glUniform3f == NULL:
        Logger.debug('GL: glUniform3f is not available')
    if cgl.glUniform3fv == NULL:
        Logger.debug('GL: glUniform3fv is not available')
    if cgl.glUniform3i == NULL:
        Logger.debug('GL: glUniform3i is not available')
    if cgl.glUniform3iv == NULL:
        Logger.debug('GL: glUniform3iv is not available')
    if cgl.glUniform4f == NULL:
        Logger.debug('GL: glUniform4f is not available')
    if cgl.glUniform4fv == NULL:
        Logger.debug('GL: glUniform4fv is not available')
    if cgl.glUniform4i == NULL:
        Logger.debug('GL: glUniform4i is not available')
    if cgl.glUniform4iv == NULL:
        Logger.debug('GL: glUniform4iv is not available')
    if cgl.glUniformMatrix4fv == NULL:
        Logger.debug('GL: glUniformMatrix4fv is not available')
    if cgl.glUseProgram == NULL:
        Logger.debug('GL: glUseProgram is not available')
    if cgl.glValidateProgram == NULL:
        Logger.debug('GL: glValidateProgram is not available')
    if cgl.glVertexAttrib1f == NULL:
        Logger.debug('GL: glVertexAttrib1f is not available')
    if cgl.glVertexAttrib2f == NULL:
        Logger.debug('GL: glVertexAttrib2f is not available')
    if cgl.glVertexAttrib3f == NULL:
        Logger.debug('GL: glVertexAttrib3f is not available')
    if cgl.glVertexAttrib4f == NULL:
        Logger.debug('GL: glVertexAttrib4f is not available')
    if cgl.glVertexAttribPointer == NULL:
        Logger.debug('GL: glVertexAttribPointer is not available')
    if cgl.glViewport == NULL:
        Logger.debug('GL: glViewport is not available')
