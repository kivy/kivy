cdef extern from "text_skia_implem.cpp":
    cppclass SkiaOpenGLRenderer:
        SkiaOpenGLRenderer(unsigned int buffer_id, unsigned int tex_width, unsigned int tex_height)
        void render_text(const char* text)


cdef class TextSkia:
    cdef SkiaOpenGLRenderer* _renderer

    def __init__(self, buffer_id, tex_width, tex_height):
        print("Setup a new SkiaOpenGLRenderer with fbo buffer id: ", buffer_id)
        self._renderer = new SkiaOpenGLRenderer(buffer_id, tex_width, tex_height)

    def render(self, text, font_size, font_name, fg_color):
        self._renderer.render_text(text)



        