'''
AppKit Spelling: Implements spelling backend based on macOS's spellchecking
                 features provided by AppKit's NSSpellChecker, through
                 rubicon-objc.

                 Developers should read:
                    https://developer.apple.com/documentation/appkit/nsspellchecker

.. versionchanged:: 3.0.0
    Uses rubicon-objc instead of PyObjC, and implements
    :meth:`~kivy.core.spelling.SpellingBase.check`.
'''

import sys

from rubicon.objc import ObjCClass
from rubicon.objc.runtime import load_library
from rubicon.objc.types import NSRange

from kivy.core.spelling import SpellingBase, NoSuchLangError

load_library('AppKit')
NSSpellChecker = ObjCClass('NSSpellChecker')

# NSNotFound is NSIntegerMax
NS_NOT_FOUND = sys.maxsize


class SpellingOSXAppKit(SpellingBase):
    '''
    Spelling backend based on macOS's spelling features provided by AppKit.
    '''

    def __init__(self, language=None):
        self._checker = NSSpellChecker.sharedSpellChecker
        super(SpellingOSXAppKit, self).__init__(language)

    def select_language(self, language):
        if not self._checker.setLanguage(language):
            err = 'AppKit Backend: No language "%s" ' % (language, )
            raise NoSuchLangError(err)

    def list_languages(self):
        return [str(lang) for lang in self._checker.availableLanguages]

    def check(self, word):
        if not word:
            return None
        misspelled = self._checker.checkSpellingOfString(
            word, startingAt=0, language=self._checker.language,
            wrap=False, inSpellDocumentWithTag=0, wordCount=None)
        return misspelled.location == NS_NOT_FOUND

    def suggest(self, fragment):
        checker = self._checker
        guesses = checker.guessesForWordRange(
            NSRange(0, len(fragment)), inString=fragment,
            language=checker.language, inSpellDocumentWithTag=0)
        if guesses is None:
            return []
        return [str(g) for g in guesses]
