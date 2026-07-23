"""
pathlib.Path support tests
===========================

Verify that Kivy's path-accepting APIs accept :class:`pathlib.Path` (any
:class:`os.PathLike`) in addition to ``str``. Each relevant case is
parametrized over ``str`` and ``Path`` to prove equivalence and guard against
regressions.

The low-level string coercion is centralized in
:func:`kivy.utils.path_to_str` and, for widget properties, in
:class:`kivy.properties.StringProperty`.
"""

import os
from pathlib import Path

import pytest

from kivy.utils import path_to_str


# ---------------------------------------------------------------------------
# path_to_str helper
# ---------------------------------------------------------------------------

def test_path_to_str_coerces_pathlike():
    p = Path('a/b/c.png')
    result = path_to_str(p)
    assert isinstance(result, str)
    assert result == os.fspath(p)


@pytest.mark.parametrize('value', [
    'plain-string',
    'atlas://tex/id',
    'http://example.com/x.png',
    'data:image/png;base64,AAAA',
    b'raw-bytes',
    None,
    123,
])
def test_path_to_str_passthrough(value):
    # Non-PathLike values must be returned unchanged (identity).
    assert path_to_str(value) is value


def test_path_to_str_bytesio_passthrough():
    import io
    bio = io.BytesIO()
    assert path_to_str(bio) is bio


# ---------------------------------------------------------------------------
# StringProperty coercion (requires the compiled properties extension)
# ---------------------------------------------------------------------------

def test_stringproperty_accepts_path():
    from kivy.event import EventDispatcher
    from kivy.properties import StringProperty

    class Probe(EventDispatcher):
        src = StringProperty('')
        opt = StringProperty(None, allownone=True)

    p = Probe()
    fired = []
    p.bind(src=lambda *a: fired.append(a))

    p.src = Path('a/b/c.png')
    assert isinstance(p.src, str)
    assert p.src == os.fspath(Path('a/b/c.png'))
    assert len(fired) == 1

    # Assigning the equal string value must not re-dispatch.
    fired.clear()
    p.src = os.fspath(Path('a/b/c.png'))
    assert len(fired) == 0

    # Plain strings (including URIs) untouched.
    p.src = 'atlas://tex/id'
    assert p.src == 'atlas://tex/id'

    # allownone still works and coerces Path.
    p.opt = None
    assert p.opt is None
    p.opt = Path('x/y')
    assert p.opt == os.fspath(Path('x/y'))


def test_stringproperty_rejects_non_path_non_str():
    from kivy.event import EventDispatcher
    from kivy.properties import StringProperty

    class Probe(EventDispatcher):
        src = StringProperty('')

    p = Probe()
    with pytest.raises(ValueError):
        p.src = 12345


# ---------------------------------------------------------------------------
# resource_find
# ---------------------------------------------------------------------------

RESOURCE_CACHE = 'kv.resourcefind'
_RESOURCE = 'uix/textinput.py'


def test_resource_find_path_equals_str():
    from kivy.cache import Cache
    from kivy.resources import resource_find

    Cache.remove(RESOURCE_CACHE)
    from_str = resource_find(_RESOURCE)
    from_path = resource_find(Path(_RESOURCE))
    assert from_str is not None
    assert from_path is not None
    assert from_str == from_path


def test_resource_find_path_cache_consistency():
    from kivy.cache import Cache
    from kivy.resources import resource_find

    Cache.remove(RESOURCE_CACHE)
    p = Path(_RESOURCE)
    first = resource_find(p)
    assert first is not None
    # The cache key is the coerced (str) form, so a second call with the same
    # Path argument must hit the cache.
    cached = Cache.get(RESOURCE_CACHE, path_to_str(p))
    assert cached == first
    assert resource_find(p) == first


@pytest.mark.parametrize('uri', ['atlas://data/x/id', 'data:image/png;base64,AAAA'])
def test_resource_find_uri_str_untouched(uri):
    from kivy.resources import resource_find
    # URIs are plain str and must never be coerced/mangled.
    assert resource_find(uri) == uri


def test_resource_add_remove_path_accepts_path(tmp_path):
    from kivy.resources import (
        resource_add_path, resource_remove_path, resource_paths)

    resource_add_path(tmp_path)
    assert os.fspath(tmp_path) in resource_paths
    # Idempotent add with the same Path.
    resource_add_path(tmp_path)
    assert resource_paths.count(os.fspath(tmp_path)) == 1
    resource_remove_path(tmp_path)
    assert os.fspath(tmp_path) not in resource_paths


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def test_config_read_write_accepts_path(tmp_path):
    from kivy.config import ConfigParser

    cfg_file = tmp_path / 'my.ini'
    cfg_file.write_text('[section]\nkey = value\n', encoding='utf-8')

    cfg = ConfigParser()
    cfg.read(cfg_file)  # Path
    assert cfg.get('section', 'key') == 'value'
    assert cfg.filename == os.fspath(cfg_file)
    # write() round-trips to the same file.
    cfg.set('section', 'key', 'value2')
    cfg.write()
    assert 'value2' in cfg_file.read_text(encoding='utf-8')


def test_config_read_rejects_multiple_filenames():
    from kivy.config import ConfigParser
    cfg = ConfigParser()
    with pytest.raises(Exception):
        cfg.read(['a.ini', 'b.ini'])


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

def test_jsonstore_accepts_path(tmp_path):
    from kivy.storage.jsonstore import JsonStore

    store = JsonStore(tmp_path / 'store.json')
    store.put('tshirt', size='M', color='blue')
    assert store.exists('tshirt')
    assert store.get('tshirt')['size'] == 'M'
    # Reopen with a Path to confirm it persisted.
    store2 = JsonStore(tmp_path / 'store.json')
    assert store2.get('tshirt')['color'] == 'blue'


def test_dictstore_accepts_path(tmp_path):
    from kivy.storage.dictstore import DictStore

    store = DictStore(tmp_path / 'store.dict')
    store.put('k', v=1)
    assert store.get('k')['v'] == 1


# ---------------------------------------------------------------------------
# Builder (kv loading) -- no GL context required for rule registration
# ---------------------------------------------------------------------------

def test_builder_load_unload_file_accepts_path(tmp_path):
    from kivy.lang import Builder
    from kivy.factory import Factory

    kv = tmp_path / 'pathlib_rule.kv'
    kv.write_text(
        '<PathlibTestWidget@Widget>:\n'
        '    size_hint: 0.25, 0.25\n',
        encoding='utf-8',
    )

    Builder.load_file(kv)  # Path
    assert 'PathlibTestWidget' in Factory.classes

    # Unloading with a Path must match the entry registered via load_file.
    Builder.unload_file(kv)
    # Factory entry registered from a kv file is removed on unload.
    assert Factory.classes.get('PathlibTestWidget', {}).get('cls') is None


# ---------------------------------------------------------------------------
# Provider-dependent cases (skipped when the provider is unavailable, e.g.
# a headless checkout without SDL3 runtime libraries; validated in CI).
# ---------------------------------------------------------------------------

def _image_asset():
    from kivy.resources import resource_find
    return resource_find('data/logo/kivy-icon-64.png')


def test_coreimage_loads_from_path():
    from kivy.core.image import Image as CoreImage, ImageLoader
    if not ImageLoader.loaders:
        pytest.skip('no image provider available')
    asset = _image_asset()
    if not asset:
        pytest.skip('image asset not found')
    img = CoreImage(Path(asset))
    assert img.texture is not None
    assert img.filename == os.fspath(Path(asset))


def test_corelabel_font_name_accepts_path():
    try:
        from kivy.core.text import Label as CoreLabel
    except Exception:
        pytest.skip('no text provider available')
    from kivy.resources import resource_find
    font = resource_find('data/fonts/DejaVuSans.ttf')
    if not font:
        pytest.skip('font asset not found')
    lbl = CoreLabel(text='hi', font_name=Path(font))
    try:
        lbl.refresh()
    except Exception:
        pytest.skip('text provider cannot render in this environment')
    assert lbl.texture is not None


def test_soundloader_accepts_path():
    from kivy.core.audio_output import SoundLoader
    if not SoundLoader._classes:
        pytest.skip('no audio provider available')
    from kivy.resources import resource_find
    snd_file = resource_find('data/logo/kivy-icon-64.png')  # any bundled file
    # We only assert coercion/no-crash on the load path; a non-audio file may
    # legitimately return None.
    sound = SoundLoader.load(Path(snd_file) if snd_file else Path('missing.wav'))
    if sound is not None:
        assert isinstance(sound.source, str)
