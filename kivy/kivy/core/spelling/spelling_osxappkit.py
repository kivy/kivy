'''
AppKit Spelling: Implements spelling backend based on OSX's spellchecking
                 features provided by the ApplicationKit.

                 NOTE:
                    Requires pyobjc and setuptools to be installed!
                    `sudo easy_install pyobjc setuptools`

                 Developers should read:
                    http://developer.apple.com/mac/library/documentation/
                        Cocoa/Conceptual/SpellCheck/SpellCheck.html
                    http://developer.apple.com/cocoa/pyobjc.html
'''


from AppKit import NSSpellChecker, NSMakeRange

from kivy.core.spelling import SpellingBase, NoSuchLangError


class SpellingOSXAppKit(SpellingBase):
    '''
    Spelling backend based on OSX's spelling features provided by AppKit.
    '''

    def __init__(self, language=None):
        self._language = NSSpellChecker.alloc().init()
        super(SpellingOSXAppKit, self).__init__(language)

    def select_language(self, language):
        success = self._language.setLanguage_(language)
        if not success:
            err = 'AppKit Backend: No language "%s" ' % (language, )
            raise NoSuchLangError(err)

    def list_languages(self):
        return list(self._language.availableLanguages())

    def check(self, word):
        # TODO Implement this!
        #      NSSpellChecker provides several functions that look like what we
        #      need, but they're a) slooow and b) return a strange result.
        #      Might be a snow leopard bug. Have to test further.
        #      See: http://paste.pocoo.org/show/217968/
        if not word:
            return None
        err = 'check() not currently supported by the OSX AppKit backend'
        raise NotImplementedError(err)

    def suggest(self, fragment):
        l = self._language
        # XXX Both ways below work on OSX 10.6. It has not been tested on any
        #     other version, but it should work.
        try:
            # This is deprecated as of OSX 10.6, hence the try-except
            return list(l.guessesForWord_(fragment))
        except AttributeError:
            # From 10.6 onwards you're supposed to do it like this:
            checkrange = NSMakeRange(0, len(fragment))
            g = l.\
                guessesForWordRange_inString_language_inSpellDocumentWithTag_(
                    checkrange, fragment, l.language(), 0)
            # Right, this was much easier, Apple! :-)
            return list(g)
