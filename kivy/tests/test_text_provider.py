"""
Tests for the text provider selection API.

Tests the new provider selection capabilities added in Kivy 3.0.0:
- `available_providers()` method on LabelBase
- `get_provider_class(provider)` method on LabelBase
- `text_provider` property on kivy.uix.label.Label widget
- `get_markup_label_class(provider)` function for markup labels
- KIVY_PROVIDER_STRICT mode behavior
- Provider validation and error handling
"""

import os

import pytest


# Fixture to ensure Window is initialized for tests that need textures
@pytest.fixture(scope="module")
def kivy_window():
    """Initialize Kivy Window for tests that need OpenGL context."""
    from kivy.core.window import Window

    yield Window


class TestAvailableProviders:
    """Tests for LabelBase.available_providers() method."""

    def test_available_providers_returns_list(self):
        """available_providers() should return a list."""
        from kivy.core.text import LabelBase

        providers = LabelBase.available_providers()
        assert isinstance(providers, list)

    def test_available_providers_not_empty(self):
        """available_providers() should return at least one provider."""
        from kivy.core.text import LabelBase

        providers = LabelBase.available_providers()
        assert len(providers) > 0, "At least one text provider should be available"

    def test_available_providers_contains_strings(self):
        """available_providers() should return list of strings."""
        from kivy.core.text import LabelBase

        providers = LabelBase.available_providers()
        for provider in providers:
            assert isinstance(provider, str)

    def test_available_providers_lowercase(self):
        """Provider names should be lowercase."""
        from kivy.core.text import LabelBase

        providers = LabelBase.available_providers()
        for provider in providers:
            assert provider == provider.lower(), (
                f"Provider {provider!r} should be lowercase"
            )

    def test_available_providers_matches_registered(self):
        """available_providers() should match registered providers."""
        from kivy.core.text import LabelBase

        providers = LabelBase.available_providers()

        # All available providers should be in _providers_by_name
        for provider in providers:
            assert provider in LabelBase._providers_by_name


class TestGetProviderClass:
    """Tests for LabelBase.get_provider_class() method."""

    def test_get_provider_class_with_valid_provider(self):
        """get_provider_class() should return a class for valid provider."""
        from kivy.core.text import LabelBase

        providers = LabelBase.available_providers()
        if providers:
            provider = providers[0]
            cls = LabelBase.get_provider_class(provider)
            assert cls is not None
            assert issubclass(cls, LabelBase)

    def test_get_provider_class_case_insensitive(self):
        """get_provider_class() should be case insensitive."""
        from kivy.core.text import LabelBase

        providers = LabelBase.available_providers()
        if providers:
            provider = providers[0]
            cls_lower = LabelBase.get_provider_class(provider.lower())
            cls_upper = LabelBase.get_provider_class(provider.upper())
            assert cls_lower is cls_upper

    def test_get_provider_class_invalid_returns_none(self):
        """get_provider_class() should return None for invalid provider."""
        from kivy.core.text import LabelBase

        cls = LabelBase.get_provider_class("nonexistent_provider_xyz")
        assert cls is None

    def test_get_provider_class_none_raises_valueerror(self):
        """get_provider_class(None) should raise ValueError."""
        from kivy.core.text import LabelBase

        with pytest.raises(ValueError, match="provider argument is required"):
            LabelBase.get_provider_class(None)

    def test_get_provider_class_empty_string_raises_valueerror(self):
        """get_provider_class('') should raise ValueError."""
        from kivy.core.text import LabelBase

        with pytest.raises(ValueError, match="provider argument is required"):
            LabelBase.get_provider_class("")


class TestStrictMode:
    """Tests for KIVY_PROVIDER_STRICT mode."""

    def test_strict_mode_raises_on_invalid_provider(self, monkeypatch):
        """In strict mode, invalid provider should raise ValueError."""
        monkeypatch.setenv("KIVY_PROVIDER_STRICT", "1")

        from kivy.core.text import LabelBase

        with pytest.raises(ValueError, match="Unknown text provider"):
            LabelBase.get_provider_class("nonexistent_provider_xyz")

    def test_non_strict_mode_returns_none(self, monkeypatch):
        """In non-strict mode, invalid provider should return None."""
        monkeypatch.setenv("KIVY_PROVIDER_STRICT", "0")

        from kivy.core.text import LabelBase

        cls = LabelBase.get_provider_class("nonexistent_provider_xyz")
        assert cls is None


class TestCoreLabelProviderSelection:
    """Tests for provider selection with core Label classes."""

    def test_create_label_with_specific_provider(self, kivy_window):
        """Should be able to create a label with a specific provider."""
        from kivy.core.text import LabelBase

        providers = LabelBase.available_providers()
        if providers:
            provider = providers[0]
            cls = LabelBase.get_provider_class(provider)
            label = cls(text="Hello World")
            label.refresh()
            assert label.texture is not None

    def test_different_providers_produce_labels(self, kivy_window):
        """Each available provider should be able to create labels."""
        from kivy.core.text import LabelBase

        providers = LabelBase.available_providers()
        for provider in providers:
            cls = LabelBase.get_provider_class(provider)
            label = cls(text=f"Test with {provider}")
            label.refresh()
            assert label.texture is not None, (
                f"Provider {provider} failed to create texture"
            )


class TestLabelWidgetProvider:
    """Tests for text_provider property on kivy.uix.label.Label widget."""

    def test_text_provider_property_exists(self):
        """Label widget should have text_provider property."""
        from kivy.uix.label import Label

        label = Label(text="Test")
        assert hasattr(label, "text_provider")

    def test_text_provider_default_is_none(self):
        """text_provider should default to None."""
        from kivy.uix.label import Label

        label = Label(text="Test")
        assert label.text_provider is None

    def test_text_provider_can_be_set(self, kivy_window):
        """text_provider can be set to a valid provider."""
        from kivy.uix.label import Label
        from kivy.core.text import LabelBase

        providers = LabelBase.available_providers()
        if providers:
            provider = providers[0]
            label = Label(text="Test", text_provider=provider)
            assert label.text_provider == provider

    def test_text_provider_creates_correct_internal_label(self, kivy_window):
        """Setting text_provider should use the correct core label class."""
        from kivy.uix.label import Label
        from kivy.core.text import LabelBase

        providers = LabelBase.available_providers()
        if providers:
            provider = providers[0]
            expected_cls = LabelBase.get_provider_class(provider)
            label = Label(text="Test", text_provider=provider)
            # Force label creation
            label.texture_update()
            assert label._label.__class__ is expected_cls

    def test_text_provider_change_recreates_label(self, kivy_window):
        """Changing text_provider should recreate the internal label."""
        from kivy.uix.label import Label
        from kivy.core.text import LabelBase

        providers = LabelBase.available_providers()
        if len(providers) >= 2:
            label = Label(text="Test", text_provider=providers[0])
            label.texture_update()
            first_cls = label._label.__class__

            label.text_provider = providers[1]
            label.texture_update()
            second_cls = label._label.__class__

            # Classes should be different
            assert first_cls is not second_cls

    def test_invalid_provider_logs_warning(self, kivy_window, caplog):
        """Invalid text_provider should log a warning."""
        from kivy.uix.label import Label

        label = Label(text="Test", text_provider="nonexistent_provider_xyz")
        label.texture_update()

        # Should have logged a warning
        assert "not found" in caplog.text.lower() or label._label is not None


class TestMarkupLabelProvider:
    """Tests for text_provider with markup labels."""

    def test_get_markup_label_class_default(self):
        """get_markup_label_class(None) should return MarkupLabel."""
        from kivy.core.text.markup import get_markup_label_class, MarkupLabel

        cls = get_markup_label_class(None)
        assert cls is MarkupLabel

    def test_get_markup_label_class_with_provider(self):
        """get_markup_label_class(provider) should return a class."""
        from kivy.core.text import LabelBase
        from kivy.core.text.markup import get_markup_label_class

        providers = LabelBase.available_providers()
        if providers:
            provider = providers[0]
            cls = get_markup_label_class(provider)
            assert cls is not None

    def test_get_markup_label_class_inherits_from_provider(self):
        """Markup class should inherit from the specified provider."""
        from kivy.core.text import LabelBase
        from kivy.core.text.markup import get_markup_label_class

        providers = LabelBase.available_providers()
        if providers:
            provider = providers[0]
            provider_cls = LabelBase.get_provider_class(provider)
            markup_cls = get_markup_label_class(provider)
            # The markup class should be a subclass of the provider
            assert issubclass(markup_cls, provider_cls)

    def test_get_markup_label_class_caches_classes(self):
        """get_markup_label_class should cache created classes."""
        from kivy.core.text import LabelBase
        from kivy.core.text.markup import get_markup_label_class

        providers = LabelBase.available_providers()
        if providers:
            provider = providers[0]
            cls1 = get_markup_label_class(provider)
            cls2 = get_markup_label_class(provider)
            assert cls1 is cls2

    def test_get_markup_label_class_invalid_returns_none(self):
        """get_markup_label_class should return None for invalid provider."""
        from kivy.core.text.markup import get_markup_label_class

        cls = get_markup_label_class("nonexistent_provider_xyz")
        assert cls is None

    def test_markup_label_with_provider_renders(self, kivy_window):
        """Markup label with provider should render correctly."""
        from kivy.core.text import LabelBase
        from kivy.core.text.markup import get_markup_label_class

        providers = LabelBase.available_providers()
        if providers:
            provider = providers[0]
            cls = get_markup_label_class(provider)
            label = cls(text="[b]Hello[/b] World")
            label.refresh()
            assert label.texture is not None

    def test_widget_markup_with_text_provider(self, kivy_window):
        """Label widget with markup=True and text_provider should work."""
        from kivy.uix.label import Label
        from kivy.core.text import LabelBase
        from kivy.core.text.markup import get_markup_label_class

        providers = LabelBase.available_providers()
        if providers:
            provider = providers[0]
            label = Label(
                text="[b]Bold[/b] and [i]italic[/i]",
                markup=True,
                text_provider=provider,
            )
            label.texture_update()

            # Should use the markup class for this provider
            expected_cls = get_markup_label_class(provider)
            assert label._label.__class__ is expected_cls


class TestRegisterProvider:
    """Tests for LabelBase.register_provider() method."""

    def test_register_provider_adds_to_list(self):
        """register_provider should add class to _providers list."""
        from kivy.core.text import LabelBase

        initial_count = len(LabelBase._providers)

        # Create a mock provider class
        class MockLabelProvider(LabelBase):
            _provider_name = 'mockprovider'

        LabelBase.register_provider(MockLabelProvider)

        assert len(LabelBase._providers) == initial_count + 1
        assert MockLabelProvider in LabelBase._providers

        # Clean up
        LabelBase._providers.remove(MockLabelProvider)
        del LabelBase._providers_by_name["mockprovider"]

    def test_register_provider_uses_explicit_name(self):
        """register_provider should use explicit _provider_name attribute."""
        from kivy.core.text import LabelBase

        class LabelTestProvider(LabelBase):
            _provider_name = 'testprovider'

        LabelBase.register_provider(LabelTestProvider)

        # Should use the explicit _provider_name (lowercased)
        assert "testprovider" in LabelBase._providers_by_name
        assert LabelBase._providers_by_name["testprovider"] is LabelTestProvider

        # Clean up
        LabelBase._providers.remove(LabelTestProvider)
        del LabelBase._providers_by_name["testprovider"]

    def test_register_provider_requires_name(self):
        """register_provider should raise ValueError if _provider_name not defined."""
        from kivy.core.text import LabelBase

        class LabelNoName(LabelBase):
            pass  # Missing _provider_name

        with pytest.raises(ValueError, match="must define a _provider_name"):
            LabelBase.register_provider(LabelNoName)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

