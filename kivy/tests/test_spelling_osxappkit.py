"""Tests for kivy.core.spelling.spelling_osxappkit.

The provider imports rubicon-objc at module level, so the first tests load it
by file path with a fake ``rubicon`` package in ``sys.modules`` and run on any
platform. The tests at the end use the real NSSpellChecker and only run on
macOS.
"""

import importlib.util
import sys
import types
from contextlib import contextmanager
from pathlib import Path

import pytest

_MODULE_PATH = (
    Path(__file__).parent.parent / "core" / "spelling" /
    "spelling_osxappkit.py"
)


class _FakeRange:
    def __init__(self, location, length):
        self.location = location
        self.length = length


class _FakeChecker:
    def __init__(self):
        self.availableLanguages = ["en", "fr"]
        self.language = None
        self.misspelled_at = sys.maxsize
        self.guesses = ["hello", "help"]
        self.guess_calls = []

    def setLanguage(self, language):
        if language not in self.availableLanguages:
            return False
        self.language = language
        return True

    def checkSpellingOfString(self, word, **kwargs):
        return _FakeRange(self.misspelled_at, 0)

    def guessesForWordRange(self, word_range, **kwargs):
        self.guess_calls.append((word_range.location, word_range.length,
                                 kwargs["inString"], kwargs["language"]))
        return self.guesses


class _FakeNSSpellChecker:
    sharedSpellChecker = None


@contextmanager
def _load_module():
    # Importing kivy.core.spelling selects and imports a provider, so it must
    # happen before the fakes are installed.
    import kivy.core.spelling  # noqa: F401

    objc = types.ModuleType("rubicon.objc")
    objc.ObjCClass = lambda name: _FakeNSSpellChecker
    runtime = types.ModuleType("rubicon.objc.runtime")
    runtime.load_library = lambda name: None
    objc_types = types.ModuleType("rubicon.objc.types")
    objc_types.NSRange = _FakeRange
    fakes = {
        "rubicon": types.ModuleType("rubicon"),
        "rubicon.objc": objc,
        "rubicon.objc.runtime": runtime,
        "rubicon.objc.types": objc_types,
    }
    saved = {name: sys.modules.get(name) for name in fakes}
    sys.modules.update(fakes)
    _FakeNSSpellChecker.sharedSpellChecker = _FakeChecker()
    try:
        spec = importlib.util.spec_from_file_location(
            "spelling_osxappkit", _MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        yield module
    finally:
        for name, mod in saved.items():
            if mod is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = mod


def test_selects_the_first_language_by_default():
    with _load_module() as module:
        speller = module.SpellingOSXAppKit()

    assert speller.list_languages() == ["en", "fr"]
    assert speller._checker.language == "en"


def test_unknown_language_raises():
    from kivy.core.spelling import NoSuchLangError

    with _load_module() as module:
        with pytest.raises(NoSuchLangError):
            module.SpellingOSXAppKit("xx")


def test_check():
    with _load_module() as module:
        speller = module.SpellingOSXAppKit("en")
        checker = speller._checker

        assert speller.check("") is None
        assert speller.check("hello") is True
        checker.misspelled_at = 0
        assert speller.check("helo") is False


def test_suggest():
    with _load_module() as module:
        speller = module.SpellingOSXAppKit("fr")
        checker = speller._checker

        assert speller.suggest("helo") == ["hello", "help"]
        assert checker.guess_calls == [(0, 4, "helo", "fr")]
        checker.guesses = None
        assert speller.suggest("zzzz") == []


# Real NSSpellChecker (macOS only)

_needs_appkit = pytest.mark.skipif(
    sys.platform != "darwin" or importlib.util.find_spec("rubicon") is None,
    reason="needs macOS and rubicon-objc")


@pytest.fixture
def english_speller():
    from kivy.core.spelling import spelling_osxappkit

    speller = spelling_osxappkit.SpellingOSXAppKit()
    english = [lang for lang in speller.list_languages()
               if lang.startswith("en")]
    if not english:
        pytest.skip("no English dictionary installed")
    speller.select_language(english[0])
    return speller


@_needs_appkit
def test_real_check(english_speller):
    assert english_speller.check("hello") is True
    assert english_speller.check("helo") is False


@_needs_appkit
def test_real_suggest(english_speller):
    assert "help" in english_speller.suggest("helo")
