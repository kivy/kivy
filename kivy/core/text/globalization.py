
try:
    from rtl import rtl as _rtl
    from rtl.reshaper import has_arabic_letters
except ImportError:
    raise ImportError('The rtl package was not installed, You have to install it to use this feature.')


def arabic_reshape(text):
    return _rtl(text, bidi=False)


def arabic_bidi(data):
    return _rtl(data, reshape=False, digits=True)
