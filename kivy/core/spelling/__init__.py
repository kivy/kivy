'''
Spelling
========

Provides abstracted access to a range of spellchecking backends as well as
word suggestions. The API is inspired by enchant but other backends can be
added that implement the same API.

Spelling currently requires `python-enchant` for all platforms except
OSX, where a native implementation exists.

::

    >>> from kivy.core.spelling import Spelling
    >>> s = Spelling()
    >>> s.list_languages()
    ['en', 'en_CA', 'en_GB', 'en_US']
    >>> s.select_language('en_US')
    >>> s.suggest('helo')
    [u'hole', u'help', u'helot', u'hello', u'halo', u'hero', u'hell', u'held',
     u'helm', u'he-lo']

'''

__all__ = ('Spelling', 'SpellingBase', 'NoSuchLangError',
           'NoLanguageSelectedError')

import sys
from kivy.core import core_select_lib


class NoSuchLangError(Exception):
    '''
    Exception to be raised when a specific language could not be found.
    '''
    pass


class NoLanguageSelectedError(Exception):
    '''
    Exception to be raised when a language-using method is called but no
    language was selected prior to the call.
    '''
    pass


class SpellingBase(object):
    '''
    Base class for all spelling providers.
    Supports some abstract methods for checking words and getting suggestions.
    '''

    def __init__(self, language=None):
        '''
        If a `language` identifier (such as 'en_US') is provided and a matching
        language exists, it is selected. If an identifier is provided and no
        matching language exists, a NoSuchLangError exception is raised by
        self.select_language().
        If no `language` identifier is provided, we just fall back to the first
        one that is available.

        :Parameters:
            `language`: str, defaults to None
                If provided, indicates the language to be used. This needs
                to be a language identifier understood by select_language(),
                i.e. one of the options returned by list_languages().
                If nothing is provided, the first available language is used.
                If no language is available, NoLanguageSelectedError is raised.
        '''
        langs = self.list_languages()
        try:
            # If no language was specified, we just use the first one
            # that is available.
            fallback_lang = langs[0]
        except IndexError:
            raise NoLanguageSelectedError("No languages available!")
        self.select_language(language or fallback_lang)

    def select_language(self, language):
        '''
        From the set of registered languages, select the first language
        for `language`.

        :Parameters:
            `language`: str
                Language identifier. Needs to be one of the options returned by
                list_languages(). Sets the language used for spell checking and
                word suggestions.
        '''
        raise NotImplementedError('select_language() method not implemented '
                                  'by abstract spelling base class!')

    def list_languages(self):
        '''
        Return a list of all supported languages.
        E.g. ['en', 'en_GB', 'en_US', 'de', ...]
        '''
        raise NotImplementedError('list_languages() is not implemented '
                                  'by abstract spelling base class!')

    def check(self, word):
        '''
        If `word` is a valid word in `self._language` (the currently active
        language), returns True. If the word shouldn't be checked, returns
        None (e.g. for ''). If it is not a valid word in `self._language`,
        return False.

        :Parameters:
            `word`: str
                The word to check.
        '''
        raise NotImplementedError('check() not implemented by abstract ' +
                                  'spelling base class!')

    def suggest(self, fragment):
        '''
        For a given `fragment` (i.e. part of a word or a word by itself),
        provide corrections (`fragment` may be misspelled) or completions
        as a list of strings.

        :Parameters:
            `fragment`: str
                The word fragment to get suggestions/corrections for.
                E.g. 'foo' might become 'of', 'food' or 'foot'.

        '''
        raise NotImplementedError('suggest() not implemented by abstract ' +
                                  'spelling base class!')


_libs = (('enchant', 'spelling_enchant', 'SpellingEnchant'), )
if sys.platform == 'darwin':
    _libs += (('osxappkit', 'spelling_osxappkit', 'SpellingOSXAppKit'), )

Spelling = core_select_lib('spelling', _libs)
