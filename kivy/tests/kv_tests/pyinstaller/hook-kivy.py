from kivy.tools.packaging.pyinstaller_hooks import (
    add_dep_paths, excludedimports, datas, get_deps_all,
    get_factory_modules, kivy_modules, get_datas)

add_dep_paths()

hiddenimports = []  # get_deps_all()['hiddenimports']
hiddenimports = list(set(
    get_factory_modules() + kivy_modules + hiddenimports))
datas = datas + get_datas()


hiddenimports += [
    'kivy.core',

    'kivy.core.gl',
    'kivy.core.image',

    'kivy.core.image._img_sdl2',
    'kivy.core.image.img_dds',
    'kivy.core.image.img_gif',
    'kivy.core.image.img_pil',
    'kivy.core.image.img_sdl2',
    'kivy.core.image.img_tex',


    'kivy.core.text',

    'kivy.core.text._text_sdl2',
    'kivy.core.text.markup',
    'kivy.core.text.text_layout',
    'kivy.core.text.text_sdl2',

    'kivy.core.video',
    'kivy.core.video.video_null',

    'kivy.core.window',

    'kivy.core.window._window_sdl2',
    'kivy.core.window.window_sdl2',

    'kivy.graphics',

    'kivy.graphics.buffer',
    'kivy.graphics.c_opengl_debug',
    'kivy.graphics.c_opengl_mock',
    'kivy.graphics.cgl',
    'kivy.graphics.cgl_backend',

    'kivy.graphics.cgl_backend.cgl_debug',
    'kivy.graphics.cgl_backend.cgl_gl',
    'kivy.graphics.cgl_backend.cgl_glew',
    'kivy.graphics.cgl_backend.cgl_mock',
    'kivy.graphics.cgl_backend.cgl_sdl2',

    'kivy.graphics.cgl_debug',
    'kivy.graphics.cgl_gl',
    'kivy.graphics.cgl_glew',
    'kivy.graphics.cgl_mock',
    'kivy.graphics.cgl_sdl2',
    'kivy.graphics.compiler',
    'kivy.graphics.context',
    'kivy.graphics.context_instructions',
    'kivy.graphics.fbo',
    'kivy.graphics.gl_instructions',
    'kivy.graphics.instructions',
    'kivy.graphics.opengl',
    'kivy.graphics.opengl_utils',
    'kivy.graphics.scissor_instructions',
    'kivy.graphics.shader',
    'kivy.graphics.stencil_instructions',
    'kivy.graphics.svg',
    'kivy.graphics.tesselator',
    'kivy.graphics.texture',
    'kivy.graphics.transformation',
    'kivy.graphics.vbo',
    'kivy.graphics.vertex',
    'kivy.graphics.vertex_instructions',

]
