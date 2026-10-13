"""
Resource cache-key normalization tests
=======================================

Kivy keys its resource caches (``kv.resourcefind`` in
:mod:`kivy.resources` and ``kv.loader`` in :mod:`kivy.loader`) on a
*normalized* form of the requested filename. Different spellings of the same
local file -- separator variants (``'a/b.png'`` vs ``'a\\b.png'``), redundant
``.``/``..`` segments, case differences on case-insensitive platforms and
:class:`pathlib.Path` inputs -- therefore share a single cache entry instead of
resolving/fetching the same file more than once.

URIs (``atlas://``, ``data:``, ``http://`` and the ``@image_provider:...``
scheme) are keyed verbatim so their scheme separators are never mangled.
"""

import os
from pathlib import Path

import pytest

from kivy.cache import Cache
from kivy.utils import path_to_str


# ---------------------------------------------------------------------------
# kivy.resources._cache_key
# ---------------------------------------------------------------------------

def test_resources_cache_key_normalizes_paths():
    from kivy.resources import _cache_key

    forward = _cache_key('img/asset.png')
    native = _cache_key(os.path.join('img', 'asset.png'))
    from_path = _cache_key(path_to_str(Path('img/asset.png')))
    redundant = _cache_key('img/./asset.png')

    # every spelling of the same relative path collapses to one key
    assert forward == native == from_path == redundant


def test_resources_cache_key_is_case_insensitive_where_platform_is():
    from kivy.resources import _cache_key

    # only assert case folding on platforms where normcase folds case
    # (e.g. Windows); on POSIX normcase is the identity.
    if os.path.normcase('AbC') == 'abc':
        assert _cache_key('Img/Asset.PNG') == _cache_key('img/asset.png')
    else:
        assert _cache_key('Img/Asset.PNG') != _cache_key('img/asset.png')


@pytest.mark.parametrize('uri', [
    'atlas://data/images/defaulttheme/button',
    'data:image/png;base64,AAAA',
    '@image_provider:tex(some/inner/path.png)',
])
def test_resources_cache_key_leaves_uris_verbatim(uri):
    from kivy.resources import _cache_key

    assert _cache_key(uri) == uri


# ---------------------------------------------------------------------------
# resource_find: cross-spelling requests share one cache entry
# ---------------------------------------------------------------------------

def test_resource_find_dedups_across_spellings(tmp_path, monkeypatch):
    from kivy import resources

    base = tmp_path / 'res'
    (base / 'img').mkdir(parents=True)
    target = base / 'img' / 'asset.png'
    target.write_bytes(b'x')

    # count how often the (expensive) filesystem resolution actually runs
    calls = []
    real_resolve = resources._resolve_path

    def counting_resolve(filename):
        calls.append(filename)
        return real_resolve(filename)

    monkeypatch.setattr(resources, '_resolve_path', counting_resolve)

    resources.resource_add_path(str(base))
    try:
        Cache.remove('kv.resourcefind')
        spellings = [
            'img/asset.png',
            os.path.join('img', 'asset.png'),
            path_to_str(Path('img/asset.png')),
            'img/./asset.png',
        ]
        results = [
            resources.resource_find(s, use_cache=True) for s in spellings
        ]

        assert results[0] is not None
        # all spellings resolve to the same absolute file
        assert len(set(results)) == 1
        # ... and only the first spelling triggered a resolution; every other
        # spelling was served from the shared cache entry.
        assert len(calls) == 1
    finally:
        resources.resource_remove_path(str(base))
        Cache.remove('kv.resourcefind')


def test_resource_find_pathlib_hits_str_cache_entry(tmp_path, monkeypatch):
    from kivy import resources

    base = tmp_path / 'res2'
    (base / 'img').mkdir(parents=True)
    (base / 'img' / 'asset.png').write_bytes(b'x')

    calls = []
    real_resolve = resources._resolve_path

    def counting_resolve(filename):
        calls.append(filename)
        return real_resolve(filename)

    monkeypatch.setattr(resources, '_resolve_path', counting_resolve)

    resources.resource_add_path(str(base))
    try:
        Cache.remove('kv.resourcefind')
        str_result = resources.resource_find('img/asset.png', use_cache=True)
        path_result = resources.resource_find(
            Path('img/asset.png'), use_cache=True)

        assert str_result == path_result
        # the Path request reused the str request's cache entry
        assert len(calls) == 1
    finally:
        resources.resource_remove_path(str(base))
        Cache.remove('kv.resourcefind')


def test_resource_find_does_not_mangle_uri():
    from kivy import resources

    uri = 'atlas://data/images/defaulttheme/button'
    assert resources.resource_find(uri) == uri


# ---------------------------------------------------------------------------
# kivy.loader._loader_cache_key
# ---------------------------------------------------------------------------

def test_loader_cache_key_normalizes_paths():
    from kivy.loader import _loader_cache_key

    forward = _loader_cache_key('img/asset.png')
    native = _loader_cache_key(os.path.join('img', 'asset.png'))
    from_path = _loader_cache_key(path_to_str(Path('img/asset.png')))
    redundant = _loader_cache_key('img/./asset.png')

    assert forward == native == from_path == redundant


@pytest.mark.parametrize('uri', [
    'http://example.com/x.png',
    'https://example.com/x.png',
    'ftp://example.com/x.png',
    'smb://host/share/x.png',
    'atlas://data/images/defaulttheme/button',
    'data:image/png;base64,AAAA',
])
def test_loader_cache_key_leaves_urls_verbatim(uri):
    from kivy.loader import _loader_cache_key

    assert _loader_cache_key(uri) == uri


def test_loader_dedups_inflight_requests_across_spellings():
    """A second, differently-spelled request for an in-flight load reuses the
    same queue/cache entry (no duplicate fetch) and its client is tracked under
    the shared normalized key."""
    from kivy.core.image import ImageLoader
    from kivy.loader import LoaderBase, _loader_cache_key

    loader = LoaderBase()
    # constructing the returned ProxyImage needs a working image provider for
    # the loading image; skip locally when none is available (CI has providers).
    if not getattr(ImageLoader, 'loaders', None):
        pytest.skip('no image provider available')
    try:
        loader.loading_image
    except Exception:
        pytest.skip('no image provider available')

    Cache.remove('kv.loader')
    loader.image('img/asset.png')
    loader.image(os.path.join('img', 'asset.png'))

    try:
        # the second spelling did not enqueue a second load
        assert len(loader._q_load) == 1
        # both pending clients are tracked under the one normalized key
        keys = {key for (key, client) in loader._client}
        assert keys == {_loader_cache_key('img/asset.png')}
    finally:
        Cache.remove('kv.loader')
