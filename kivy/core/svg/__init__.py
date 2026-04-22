'''
SVG
===

Core classes for loading and rendering SVG documents to rasterized textures.

The SVG provider system is **separate** from :mod:`kivy.core.image`. It uses a
stateful interface that separates document loading from rasterization, which
enables adaptive re-rasterization at different sizes without reloading the
document.

Providers register themselves at import time via :meth:`SvgLoader.register`.
The :class:`SvgLoader` registry tries each registered provider in priority
order when :meth:`SvgLoader.load` or :meth:`SvgLoader.load_data` is called.

This module is the backend used by :class:`~kivy.uix.svg.SvgWidget` and
:class:`~kivy.uix.svg.AsyncSvgWidget`.  Application code should use those
widgets rather than calling :class:`SvgLoader` directly.

.. versionadded:: 3.0.0
'''

from abc import ABC, abstractmethod

from kivy.logger import Logger
from kivy.core import core_register_libs, get_provider_modules, make_provider_tuple


class SvgProviderBase(ABC):
    '''Abstract base class for SVG providers.

    Subclasses must set :attr:`_provider_name` and implement all methods.
    The interface separates **loading** (parse the SVG document once) from
    **rendering** (rasterize to RGBA pixels at a requested size), so that a
    single loaded document can be re-rendered at different sizes or with
    different runtime overrides without re-parsing from disk.
    '''

    _provider_name = None
    '''Provider name used as a registry key.  Must be set by every subclass.'''

    @abstractmethod
    def load(self, source):
        '''Parse an SVG document from a file path.

        :param str source: Absolute path to the SVG file.
        :returns: ``True`` on success, ``False`` on failure.
        :rtype: bool
        '''

    @abstractmethod
    def load_data(self, data, mimetype='svg'):
        '''Parse an SVG document from raw bytes.

        :param bytes data: Raw SVG content.
        :param str mimetype: MIME type or extension hint (e.g. ``'svg'``).
        :returns: ``True`` on success, ``False`` on failure.
        :rtype: bool
        '''

    @abstractmethod
    def get_document_size(self):
        '''Return the intrinsic ``(width, height)`` of the SVG document.

        Derived from the SVG ``viewBox`` or ``width``/``height`` attributes.
        Returns ``(0.0, 0.0)`` if the document has not been loaded yet.

        :rtype: tuple[float, float]
        '''

    @abstractmethod
    def get_element_ids(self):
        '''Return all element ``id`` attribute values found in the document.

        The list is built once at load time by scanning the SVG XML.
        Returns an empty list if the document has not been loaded yet.

        :rtype: list[str]
        '''

    @abstractmethod
    def render(self, width, height, current_color=None, element_overrides=None):
        '''Rasterize the SVG to RGBA pixels at the given dimensions.

        :param int width: Render width in pixels.
        :param int height: Render height in pixels.
        :param current_color: Optional ``(r, g, b[, a])`` float tuple
            (values 0.0-1.0) providing the RGB colour for CSS
            ``currentColor``.  Per the SVG spec, ``currentColor`` is RGB
            only; the alpha component, if supplied, is ignored.
        :type current_color: tuple or None
        :param element_overrides: Optional ``dict`` mapping element ``id``
            strings to override dicts with optional keys:

            - ``'visible'`` (bool) - ``False`` forces opacity to 0.
            - ``'opacity'`` (float 0.0-1.0) - overrides SVG native opacity
              when the element is visible.

            Absent keys use SVG defaults.
        :type element_overrides: dict or None
        :returns: A buffer-protocol object exposing ``width * height * 4``
            bytes of raw RGBA pixels, or ``None`` on failure.

            Providers are allowed to return either a plain :class:`bytes`
            object or any other object that implements the Python buffer
            protocol (for example, a backend-native render target that
            avoids a pixel-buffer copy). Consumers that need an owned
            :class:`bytes` instance should wrap the return value in
            :func:`bytes` explicitly; consumers that call
            :meth:`kivy.graphics.texture.Texture.blit_buffer` can pass the
            return value through directly because ``blit_buffer`` accepts
            buffer-protocol objects and will not copy the pixels a second
            time.
        :rtype: buffer-protocol object (``bytes``, ``memoryview``,
            backend render target, ...) or ``None``
        '''


class SvgLoader:
    '''Registry and factory for SVG providers.

    Providers self-register at import time via :meth:`register`. Call
    :meth:`load` or :meth:`load_data` to obtain a loaded
    :class:`SvgProviderBase` instance.
    '''

    providers = []  # List of provider classes in priority order
    providers_by_name = {}  # O(1) lookup by lowercase name

    @staticmethod
    def register(provider_class):
        '''Register an SVG provider class.

        Called automatically at the bottom of each provider module.

        :param provider_class: A subclass of :class:`SvgProviderBase` with a
            non-``None`` ``_provider_name`` attribute.
        :raises ValueError: If ``_provider_name`` is not set.
        '''
        name = getattr(provider_class, '_provider_name', None)
        if name is None:
            raise ValueError(
                f'{provider_class.__name__} must define a _provider_name'
                ' class attribute'
            )
        SvgLoader.providers.append(provider_class)
        SvgLoader.providers_by_name[name.lower()] = provider_class
        Logger.debug(f'SvgLoader: registered provider {name!r}')

    @classmethod
    def load(cls, source):
        '''Try each registered provider in order and return the first that
        successfully loads *source*.

        :param str source: File path to the SVG document.
        :returns: A loaded :class:`SvgProviderBase` instance, or ``None`` if
            no provider could load the document.
        '''
        for provider_class in cls.providers:
            try:
                provider = provider_class()
                if provider.load(source):
                    return provider
            except Exception as exc:
                Logger.debug(
                    f'SvgLoader: provider {provider_class._provider_name!r}'
                    f' failed on {source!r}: {exc}'
                )
        Logger.error(f'SvgLoader: no provider could load {source!r}')
        return None

    @classmethod
    def load_data(cls, data, mimetype='svg'):
        '''Try each registered provider in order and return the first that
        successfully loads *data*.

        :param bytes data: Raw SVG content.
        :param str mimetype: MIME type or extension hint.
        :returns: A loaded :class:`SvgProviderBase` instance, or ``None``.
        '''
        for provider_class in cls.providers:
            try:
                provider = provider_class()
                if provider.load_data(data, mimetype):
                    return provider
            except Exception as exc:
                Logger.debug(
                    f'SvgLoader: provider {provider_class._provider_name!r}'
                    f' failed on in-memory data: {exc}'
                )
        Logger.error('SvgLoader: no provider could load in-memory SVG data')
        return None


_svg_providers = get_provider_modules('svg')
svg_libs = [make_provider_tuple('thorvg', _svg_providers)]
libs_loaded = core_register_libs('svg', svg_libs)
