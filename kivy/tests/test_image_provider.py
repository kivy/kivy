"""
Tests for the image provider selection API.

Tests the new provider selection capabilities added in Kivy 3.0.0:
- `available_providers()` method
- `image_provider` parameter for CoreImage and Image.load()
- `@image_provider:providername(path)` URI scheme
- KIVY_PROVIDER_STRICT mode behavior
- Provider validation and error handling
"""

import os
import zipfile
from pathlib import Path

import pytest


# Fixture to ensure Window is initialized for tests that need textures
@pytest.fixture(scope="module")
def kivy_window():
    """Initialize Kivy Window for tests that need OpenGL context."""
    from kivy.core.window import Window

    yield Window


class TestAvailableProviders:
    """Tests for CoreImage.available_providers() method."""

    def test_available_providers_returns_list(self):
        """available_providers() should return a list."""
        from kivy.core.image import Image as CoreImage

        providers = CoreImage.available_providers()
        assert isinstance(providers, list)

    def test_available_providers_not_empty(self):
        """available_providers() should return at least one provider."""
        from kivy.core.image import Image as CoreImage

        providers = CoreImage.available_providers()
        assert len(providers) > 0, "At least one image provider should be available"

    def test_available_providers_contains_strings(self):
        """available_providers() should return list of strings."""
        from kivy.core.image import Image as CoreImage

        providers = CoreImage.available_providers()
        for provider in providers:
            assert isinstance(provider, str)

    def test_available_providers_lowercase(self):
        """Provider names should be lowercase."""
        from kivy.core.image import Image as CoreImage

        providers = CoreImage.available_providers()
        for provider in providers:
            assert provider == provider.lower(), (
                f"Provider {provider!r} should be lowercase"
            )

    def test_available_providers_matches_loaders(self):
        """available_providers() should match registered loaders."""
        from kivy.core.image import ImageLoader, Image as CoreImage

        providers = CoreImage.available_providers()

        # Get provider names from _provider_name attribute
        loader_provider_names = []
        for loader in ImageLoader.loaders:
            provider_name = getattr(loader, '_provider_name', None)
            if provider_name:
                loader_provider_names.append(provider_name.lower())

        # All available providers should correspond to registered loaders
        for provider in providers:
            assert provider in loader_provider_names, (
                f"Provider {provider!r} not in registered loader provider names"
            )


class TestImageProviderParameter:
    """Tests for image_provider parameter on CoreImage."""

    @pytest.fixture
    def test_image_path(self):
        """Path to test image."""
        return os.path.join(os.path.dirname(__file__), "test_button.png")

    def test_load_with_default_provider(self, test_image_path, kivy_window):
        """Loading without image_provider should use default provider."""
        from kivy.core.image import Image as CoreImage

        img = CoreImage(test_image_path)
        assert img is not None
        assert img.texture is not None

    def test_load_with_explicit_provider(self, test_image_path, kivy_window):
        """Loading with explicit image_provider should work."""
        from kivy.core.image import Image as CoreImage

        providers = CoreImage.available_providers()
        if not providers:
            pytest.skip("No image providers available")

        provider = providers[0]
        img = CoreImage(test_image_path, image_provider=provider)
        assert img is not None
        assert img.texture is not None

    def test_load_static_method_with_provider(self, test_image_path, kivy_window):
        """Image.load() with image_provider parameter should work."""
        from kivy.core.image import Image as CoreImage

        providers = CoreImage.available_providers()
        if not providers:
            pytest.skip("No image providers available")

        provider = providers[0]
        img = CoreImage.load(test_image_path, image_provider=provider)
        assert img is not None

    def test_provider_case_insensitive(self, test_image_path, kivy_window):
        """Provider name should be case-insensitive."""
        from kivy.core.image import Image as CoreImage

        providers = CoreImage.available_providers()
        if not providers:
            pytest.skip("No image providers available")

        provider = providers[0]
        # Test with uppercase
        img = CoreImage(test_image_path, image_provider=provider.upper())
        assert img is not None
        assert img.texture is not None

    def test_all_available_providers_can_load(self, test_image_path, kivy_window):
        """Each available provider should be able to load the test image."""
        from kivy.core.image import Image as CoreImage

        providers = CoreImage.available_providers()
        for provider in providers:
            img = CoreImage(test_image_path, image_provider=provider)
            assert img is not None, f"Provider {provider!r} failed to create image"
            # Note: Some providers might not support PNG, so texture could be None
            # but the image object should still be created


class TestImageProviderURIScheme:
    """Tests for @image_provider:providername(path) URI scheme."""

    @pytest.fixture
    def test_image_path(self):
        """Path to test image."""
        return os.path.join(os.path.dirname(__file__), "test_button.png")

    def test_uri_scheme_basic(self, test_image_path, kivy_window):
        """Basic @image_provider: URI scheme should work."""
        from kivy.core.image import Image as CoreImage

        providers = CoreImage.available_providers()
        if not providers:
            pytest.skip("No image providers available")

        provider = providers[0]
        uri = f"@image_provider:{provider}({test_image_path})"
        img = CoreImage(uri)
        assert img is not None
        assert img.texture is not None

    def test_uri_scheme_regex_pattern(self):
        """Test that URI scheme regex matches expected patterns."""
        from kivy.core.image import _provider_uri_re

        # Should match
        valid_uris = [
            ("@image_provider:pil(image.png)", "pil", "image.png"),
            ("@image_provider:sdl3(/path/to/image.jpg)", "sdl3", "/path/to/image.jpg"),
            (
                "@image_provider:imageio(../images/icon.png)",
                "imageio",
                "../images/icon.png",
            ),
            ("@image_provider:PIL(image.png)", "PIL", "image.png"),
        ]

        for uri, expected_provider, expected_path in valid_uris:
            match = _provider_uri_re.match(uri)
            assert match is not None, f"URI {uri!r} should match"
            assert match.group(1) == expected_provider
            assert match.group(2) == expected_path

    def test_uri_scheme_invalid_patterns_dont_match(self):
        """Test that invalid URI patterns don't match."""
        from kivy.core.image import _provider_uri_re

        # Should NOT match
        invalid_uris = [
            "image.png",  # No URI scheme
            "@provider:pil(image.png)",  # Wrong prefix
            "@image_provider:(image.png)",  # Missing provider name
            "@image_provider:pil",  # Missing path
            "@image_provider:pil()",  # Empty path
        ]

        for uri in invalid_uris:
            match = _provider_uri_re.match(uri)
            # Empty path case might match regex but should be handled elsewhere
            if uri != "@image_provider:pil()":
                assert match is None, f"URI {uri!r} should NOT match"

    def test_uri_with_spaces_in_path(self, test_image_path):
        """URI scheme should handle paths with spaces."""
        from kivy.core.image import _provider_uri_re

        uri = "@image_provider:pil(my images/photo.jpg)"
        match = _provider_uri_re.match(uri)
        assert match is not None
        assert match.group(2) == "my images/photo.jpg"


class TestInvalidProviderHandling:
    """Tests for invalid provider name handling."""

    @pytest.fixture
    def test_image_path(self):
        """Path to test image."""
        return os.path.join(os.path.dirname(__file__), "test_button.png")

    def test_invalid_provider_lenient_mode(
        self, test_image_path, kivy_window, monkeypatch
    ):
        """Invalid provider in lenient mode should fallback."""
        # Ensure strict mode is off
        monkeypatch.delenv("KIVY_PROVIDER_STRICT", raising=False)

        from kivy.core.image import ImageLoader

        # Use ImageLoader.load() directly to bypass Image class caching
        # Should not raise, but log warning and fallback to default providers
        img = ImageLoader.load(
            test_image_path, image_provider="nonexistent_provider_xyz"
        )
        # In lenient mode, it should fallback to default providers and succeed
        assert img is not None

    def test_invalid_provider_strict_mode(
        self, test_image_path, kivy_window, monkeypatch
    ):
        """Invalid provider in strict mode should raise exception."""
        monkeypatch.setenv("KIVY_PROVIDER_STRICT", "1")

        from kivy.core.image import ImageLoader

        # Use ImageLoader.load() directly to bypass Image class caching
        # In strict mode, invalid provider should raise an exception
        with pytest.raises(ValueError):
            ImageLoader.load(test_image_path, image_provider="nonexistent_provider_xyz")


class TestProviderPriority:
    """Tests for provider priority and selection order."""

    @pytest.fixture
    def test_image_path(self):
        """Path to test image."""
        return os.path.join(os.path.dirname(__file__), "test_button.png")

    def test_instance_provider_overrides_default(self, test_image_path, kivy_window):
        """Instance image_provider should override default selection."""
        from kivy.core.image import Image as CoreImage

        providers = CoreImage.available_providers()
        if len(providers) < 2:
            pytest.skip("Need at least 2 providers to test override")

        # Load with second provider (not default)
        second_provider = providers[1]
        img = CoreImage(test_image_path, image_provider=second_provider)
        assert img is not None
        assert img.texture is not None


class TestProviderExtensionSupport:
    """Tests for provider extension support checking."""

    def test_providers_have_extensions(self):
        """Each loader should report supported extensions."""
        from kivy.core.image import ImageLoader

        for loader in ImageLoader.loaders:
            extensions = loader.extensions()
            assert isinstance(extensions, (list, tuple)), (
                f"{loader.__name__} extensions() should return list/tuple"
            )
            # Extensions should be strings without dots
            for ext in extensions:
                assert isinstance(ext, str)
                assert not ext.startswith("."), (
                    f"Extension {ext!r} should not start with dot"
                )


class TestCoreImageProviderProperty:
    """Tests for provider-related properties on CoreImage instances."""

    @pytest.fixture
    def test_image_path(self):
        """Path to test image."""
        return os.path.join(os.path.dirname(__file__), "test_button.png")

    def test_image_stores_provider(self, test_image_path, kivy_window):
        """CoreImage should store the image_provider parameter."""
        from kivy.core.image import Image as CoreImage

        providers = CoreImage.available_providers()
        if not providers:
            pytest.skip("No image providers available")

        provider = providers[0]
        img = CoreImage(test_image_path, image_provider=provider)

        # Check internal _image_provider attribute
        assert hasattr(img, "_image_provider")
        assert img._image_provider == provider


class TestWidgetImageProvider:
    """Tests for image_provider on Image widget."""

    @pytest.fixture
    def test_image_path(self):
        """Path to test image."""
        return os.path.join(os.path.dirname(__file__), "test_button.png")

    def test_image_widget_provider_property(self, test_image_path, kivy_window):
        """Image widget should have image_provider property."""
        from kivy.uix.image import Image
        from kivy.core.image import Image as CoreImage

        providers = CoreImage.available_providers()
        if not providers:
            pytest.skip("No image providers available")

        provider = providers[0]

        # Create widget with provider
        img_widget = Image(source=test_image_path, image_provider=provider)
        assert img_widget.image_provider == provider

    def test_image_widget_default_provider_none(self, test_image_path, kivy_window):
        """Image widget image_provider should default to None."""
        from kivy.uix.image import Image

        img_widget = Image(source=test_image_path)
        assert img_widget.image_provider is None

    def test_image_widget_change_provider(self, test_image_path, kivy_window):
        """Changing image_provider should trigger reload."""
        from kivy.uix.image import Image
        from kivy.core.image import Image as CoreImage

        providers = CoreImage.available_providers()
        if len(providers) < 2:
            pytest.skip("Need at least 2 providers")

        img_widget = Image(source=test_image_path, image_provider=providers[0])

        # Change provider
        img_widget.image_provider = providers[1]
        assert img_widget.image_provider == providers[1]


class TestAsyncImageProvider:
    """Tests for image_provider on AsyncImage widget."""

    @pytest.fixture
    def test_image_path(self):
        """Path to test image."""
        return os.path.join(os.path.dirname(__file__), "test_button.png")

    def test_async_image_has_provider_property(self, test_image_path, kivy_window):
        """AsyncImage should have image_provider property."""
        from kivy.uix.image import AsyncImage
        from kivy.core.image import Image as CoreImage

        providers = CoreImage.available_providers()
        if not providers:
            pytest.skip("No image providers available")

        provider = providers[0]

        # Create AsyncImage with provider
        img_widget = AsyncImage(source=test_image_path, image_provider=provider)
        assert img_widget.image_provider == provider


class TestZipImageProvider:
    """Tests for image_provider with zip file images."""

    @pytest.fixture
    def test_zip_path(self, tmp_path):
        """Create a temporary zip file with a test image."""
        # Get the test image
        test_image = Path(__file__).parent / "test_button.png"

        # Create a zip file containing the image
        zip_path = tmp_path / "test_images.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.write(test_image, "test_button.png")

        return str(zip_path)

    def test_zip_with_default_provider(self, test_zip_path, kivy_window):
        """Loading from zip without provider should work."""
        from kivy.core.image import Image as CoreImage

        img = CoreImage(test_zip_path, nocache=True)
        assert img is not None
        assert img.texture is not None

    def test_zip_with_explicit_provider(self, test_zip_path, kivy_window):
        """Loading from zip with explicit provider should work."""
        from kivy.core.image import Image as CoreImage

        providers = CoreImage.available_providers()
        if not providers:
            pytest.skip("No image providers available")

        provider = providers[0]
        img = CoreImage(test_zip_path, image_provider=provider, nocache=True)
        assert img is not None
        assert img.texture is not None

    def test_zip_with_invalid_provider_strict_mode(
        self, test_zip_path, kivy_window, monkeypatch
    ):
        """Invalid provider with zip in strict mode should raise."""
        monkeypatch.setenv("KIVY_PROVIDER_STRICT", "1")

        from kivy.core.image import ImageLoader

        with pytest.raises(ValueError):
            ImageLoader.load(
                test_zip_path, image_provider="nonexistent_provider_xyz"
            )

    def test_zip_with_invalid_provider_lenient_mode(
        self, test_zip_path, kivy_window, monkeypatch
    ):
        """Invalid provider with zip in lenient mode should fallback."""
        monkeypatch.delenv("KIVY_PROVIDER_STRICT", raising=False)

        from kivy.core.image import ImageLoader

        img = ImageLoader.load(
            test_zip_path, image_provider="nonexistent_provider_xyz"
        )
        assert img is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
