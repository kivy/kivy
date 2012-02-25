'''
Kivy hook for PyInstaller
=========================

Kivy load itself in a complete dynamic way. PyImported don't see most of the
import cause of the Factory and Core.
In addition, the data and missing module are not copied automatically.

With this hook, everything needed for running kivy is correctly copied.

Check kivy documentation about how to use theses hook for packaging application.
'''

import kivy
from kivy.factory import Factory


def get_modules():
    return [x.get('module', None) for x in Factory.classes.itervalues()]


datas = [
    (kivy.kivy_data_dir, 'kivy_install'),
    (kivy.kivy_modules_dir, 'kivy_install'),
    (kivy.kivy_exts_dir, 'kivy_install'),
]

# extensions
_kivy_modules = [
    # pygame
    'pygame.event',
    'pygame.video',
    'pygame.image',
    'pygame.display',
    'pygame',

    # external modules
    'kivy.lib.osc',
    'kivy.lib.osc.OSC',
    'kivy.lib.osc.oscAPI',
    'kivy.lib.mtdev',

    # compiled modules
    'kivy.event',
    'kivy.graphics.buffer',
    'kivy.graphics.c_opengl_debug',
    'kivy.graphics.compiler',
    'kivy.graphics.context_instructions',
    'kivy.graphics.fbo',
    'kivy.graphics.instructions',
    'kivy.graphics.opengl',
    'kivy.graphics.opengl_utils',
    'kivy.graphics.shader',
    'kivy.graphics.stenctil_instructions',
    'kivy.graphics.texture',
    'kivy.graphics.transformation',
    'kivy.graphics.vbo',
    'kivy.graphics.vertex',
    'kivy.graphics.vertex_instructions',
    'kivy.properties',

    # core
    'kivy.core.image.img_pygame',
    'kivy.core.audio.audio_gstreamer',
    'kivy.core.audio.audio_pygame',
    'kivy.core.camera.camera_gstreamer',
    'kivy.core.camera.camera_opencv',
    'kivy.core.video.video_pyglet',
    'kivy.core.video.video_gstreamer',
    'kivy.core.text.text_pygame',
    'kivy.core.text.markup',
    'kivy.core.clipboard.clipboard_pygame',
    'kivy.core.clipboard.clipboard_dummy',
    'kivy.core.window.window_pygame',
]

hiddenimports = _kivy_modules + get_modules()
hiddenimports = list(set(hiddenimports))

