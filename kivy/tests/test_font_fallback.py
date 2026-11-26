"""Fallback registration and native SDL3 rendering regressions.

Uses bundled fonts and software surfaces; no system fonts or GL window needed.
"""
from pathlib import Path

import pytest


@pytest.fixture
def fonts(monkeypatch):
    from kivy import kivy_data_dir
    from kivy.core.text import Label, LabelBase

    monkeypatch.setattr(LabelBase, '_fonts', LabelBase._fonts.copy())
    monkeypatch.setattr(LabelBase, '_font_fallbacks',
                        LabelBase._font_fallbacks.copy())
    root = Path(kivy_data_dir) / 'fonts'
    return root / 'Roboto-Regular.ttf', root / 'DejaVuSans.ttf'


@pytest.fixture
def sdl_label():
    # Import directly so SDL3 can also be tested when PIL is the default.
    return pytest.importorskip('kivy.core.text.text_sdl3').LabelSDL3


def test_registration_preserves_faces_and_snapshots_fallbacks(fonts):
    from kivy.core.text import Label, LabelBase

    primary, fallback = fonts
    paths = [fallback, fallback, primary]
    LabelBase.register('test-fallback', primary, fallback_fonts=paths)
    paths.clear()
    assert LabelBase._fonts['test-fallback'] == (str(primary),) * 4
    assert LabelBase._font_fallbacks['test-fallback'] == (
        str(fallback), str(primary))


@pytest.mark.parametrize('target', ['alias', 'path', 'cached_path'])
def test_switching_font_clears_previous_fallbacks(fonts, target):
    from kivy.core.text import Label, LabelBase

    primary, fallback = fonts
    LabelBase.register('test-fallback', primary, fallback_fonts=[fallback])
    LabelBase.register('test-plain', primary)
    label = Label(font_name='test-fallback')
    assert label.options['fallback_fonts'] == (str(fallback),)
    if target == 'cached_path':
        Label(font_name=primary)
    label.options['font_name'] = 'test-plain' if target == 'alias' else primary
    label.resolve_font_name()
    assert label.options['fallback_fonts'] == ()


def test_invalid_registration_is_atomic(fonts, tmp_path):
    from kivy.core.text import Label, LabelBase

    primary, fallback = fonts
    LabelBase.register('test-fallback', primary, fallback_fonts=[fallback])
    for invalid in [tmp_path / 'missing.ttf', tmp_path, None]:
        with pytest.raises(IOError, match='Fallback font file'):
            LabelBase.register('test-fallback', fallback,
                               fallback_fonts=[invalid])
        assert LabelBase._fonts['test-fallback'][0] == str(primary)
        assert LabelBase._font_fallbacks['test-fallback'] == (str(fallback),)


def test_single_path_is_not_treated_as_sequence(fonts):
    from kivy.core.text import Label, LabelBase

    primary, fallback = fonts
    with pytest.raises(TypeError, match='sequence'):
        LabelBase.register('test-fallback', primary,
                           fallback_fonts=str(fallback))


def test_reregister_without_fallbacks_clears_chain(fonts):
    from kivy.core.text import Label, LabelBase

    primary, fallback = fonts
    LabelBase.register('test-fallback', primary, fallback_fonts=[fallback])
    LabelBase.register('test-fallback', primary)
    assert Label(font_name='test-fallback').options['fallback_fonts'] == ()


@pytest.mark.parametrize('fallback_first', [False, True])
def test_native_cache_does_not_mix_aliases(fonts, sdl_label, fallback_first):
    from kivy.core.text import Label, LabelBase

    primary, fallback = fonts
    LabelBase.register('test-fallback', primary, fallback_fonts=[fallback])
    LabelBase.register('test-plain', primary)
    labels = [sdl_label(font_name=name, font_size=31 + fallback_first)
              for name in ['test-plain', 'test-fallback']]
    for label in reversed(labels) if fallback_first else labels:
        label.get_extents('\u2603')  # snowman: absent in bundled Roboto
    plain, chain = labels
    donor = sdl_label(font_name=fallback, font_size=31 + fallback_first)
    assert chain.get_extents('\u2603')[0] == donor.get_extents('\u2603')[0]
    assert chain.get_extents('\u2603')[0] != plain.get_extents('\u2603')[0]
    assert chain.get_extents('A') == plain.get_extents('A')


def test_native_reregister_changes_rendering(fonts, sdl_label):
    from kivy.core.text import Label, LabelBase

    primary, fallback = fonts
    LabelBase.register('test-reregister', primary, fallback_fonts=[fallback])
    label = sdl_label(font_name='test-reregister', font_size=33)
    before = label.get_extents('\u2603')
    LabelBase.register('test-reregister', primary)
    label.resolve_font_name()
    assert label.get_extents('\u2603')[0] != before[0]


def _pixels(label, text):
    from kivy.core.text._text_sdl3 import _SurfaceContainer

    # Fixed canvas allows comparison independent of primary font line metrics.
    surface = _SurfaceContainer(160, 80)
    surface.render(label, text, 0, 0)
    return surface.get_data().data


def test_native_renders_fallback_and_survives_cache_eviction(fonts, sdl_label):
    from kivy.core.text import Label, LabelBase

    primary, fallback = fonts
    LabelBase.register('test-fallback', primary, fallback_fonts=[fallback])
    label = sdl_label(font_name='test-fallback', font_size=30)
    plain = sdl_label(font_name=primary, font_size=30)
    expected = _pixels(label, '\u2603')
    assert expected != _pixels(plain, '\u2603')
    for size in range(10, 80):
        sdl_label(font_name='test-fallback', font_size=size).get_extents('\u2603')
    assert _pixels(label, '\u2603') == expected


def test_bad_font_file_does_not_prevent_later_fallback(fonts, sdl_label, tmp_path):
    from kivy.core.text import Label, LabelBase

    primary, fallback = fonts
    invalid = tmp_path / 'invalid.ttf'
    invalid.write_text('Not a font')
    LabelBase.register('test-fallback', primary,
                       fallback_fonts=[invalid, fallback])
    label = sdl_label(font_name='test-fallback', font_size=30)
    donor = sdl_label(font_name=fallback, font_size=30)
    assert label.get_extents('\u2603')[0] == donor.get_extents('\u2603')[0]


def test_discovery_ignores_directories_and_duplicate_paths(monkeypatch, tmp_path):
    from kivy.core.text import system_emoji_fonts as module

    font = tmp_path / 'emoji.ttf'
    font.touch()
    finder = module.SystemEmojiFontsFinder
    monkeypatch.setattr(module, 'platform', 'linux')
    monkeypatch.setattr(finder, 'LINUX_FONTS',
                        [str(tmp_path), str(font), str(font)])
    assert finder.get_available_fonts() == [str(font)]


def test_windows_discovery_uses_windows_directory(monkeypatch, tmp_path):
    from kivy.core.text import system_emoji_fonts as module

    font = tmp_path / 'Fonts' / 'seguiemj.ttf'
    font.parent.mkdir()
    font.touch()
    monkeypatch.setenv('WINDIR', str(tmp_path))
    monkeypatch.setattr(module, 'platform', 'win')
    assert module.SystemEmojiFontsFinder.get_available_fonts() == [str(font)]
