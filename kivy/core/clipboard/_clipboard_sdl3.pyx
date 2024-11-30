#cython: c_string_type=unicode, c_string_encoding=utf8
'''
TODO:
    - everything
'''

include '../../lib/sdl3.pxi'


def _has_text():
    return SDL_HasClipboardText()


def _get_text():
    return SDL_GetClipboardText()


def _set_text(text):
    SDL_SetClipboardText(text)
