from kivy.compat import PY2

from rtl.arabic_reshaper import reshape
from rtl.bidi.algorithm import get_display


def rtl_reshape(text):
    '''
    Chane the direction of text and do reshape for persian, arabic,... languages
    '''
    if PY2:
        if type(text) is unicode:
            reshape_text = reshape(text)
        else:
            unicode_text = text.decode('utf8')
            reshape_text = reshape(unicode_text)
    else:
        reshape_text = reshape(text)
    return get_display(reshape_text)
