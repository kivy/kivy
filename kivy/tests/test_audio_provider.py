"""
Tests for the audio provider selection API.

Tests the provider selection capabilities for audio:
- `available_providers()` method on SoundLoader
- `audio_output_provider` parameter for SoundLoader.load()
- KIVY_PROVIDER_STRICT mode behavior
"""

import os
import pytest


class TestAvailableProviders:
    """Tests for SoundLoader.available_providers() method."""

    def test_available_providers_returns_list(self):
        """available_providers() should return a list."""
        from kivy.core.audio_output import SoundLoader

        providers = SoundLoader.available_providers()
        assert isinstance(providers, list)

    def test_available_providers_not_empty(self):
        """available_providers() should return at least one provider."""
        from kivy.core.audio_output import SoundLoader

        providers = SoundLoader.available_providers()
        assert len(providers) > 0, "At least one audio provider should be available"

    def test_available_providers_contains_strings(self):
        """available_providers() should return list of strings."""
        from kivy.core.audio_output import SoundLoader

        providers = SoundLoader.available_providers()
        for provider in providers:
            assert isinstance(provider, str)

    def test_available_providers_lowercase(self):
        """Provider names should be lowercase."""
        from kivy.core.audio_output import SoundLoader

        providers = SoundLoader.available_providers()
        for provider in providers:
            assert provider == provider.lower(), (
                f"Provider {provider!r} should be lowercase"
            )

    def test_available_providers_matches_classes(self):
        """available_providers() should match registered classes."""
        from kivy.core.audio_output import SoundLoader

        providers = SoundLoader.available_providers()

        # Get class names (strip 'Sound' prefix and lowercase)
        class_names = []
        for classobj in SoundLoader._classes:
            name = classobj.__name__
            if name.startswith("Sound"):
                name = name[len("Sound"):]
            class_names.append(name.lower())

        # All available providers should correspond to registered classes
        for provider in providers:
            assert provider in class_names, (
                f"Provider {provider!r} not in registered classes"
            )

    def test_available_providers_no_sound_prefix(self):
        """Provider names should not have 'Sound' prefix."""
        from kivy.core.audio_output import SoundLoader

        providers = SoundLoader.available_providers()
        for provider in providers:
            assert not provider.startswith("sound"), (
                f"Provider {provider!r} should not start with 'sound'"
            )


class TestProviderExtensionSupport:
    """Tests for provider extension support checking."""

    def test_providers_have_extensions(self):
        """Each loader should report supported extensions."""
        from kivy.core.audio_output import SoundLoader

        for classobj in SoundLoader._classes:
            extensions = classobj.extensions()
            assert isinstance(extensions, (list, tuple)), (
                f"{classobj.__name__} extensions() should return list/tuple"
            )
            # Extensions should be strings without dots
            for ext in extensions:
                assert isinstance(ext, str)
                assert not ext.startswith("."), (
                    f"Extension {ext!r} should not start with dot"
                )


class TestAudioOutputProviderParameter:
    """Tests for audio_output_provider parameter on SoundLoader.load()."""

    @pytest.fixture
    def test_audio_path(self):
        """Path to test audio file."""
        # Use a path that exists for testing - the actual loading may fail
        # if the audio file doesn't exist, but we can test the provider logic
        return os.path.join(os.path.dirname(__file__), "sample1.ogg")

    def test_load_with_explicit_provider(self, test_audio_path):
        """Loading with explicit audio_output_provider should attempt that provider."""
        from kivy.core.audio_output import SoundLoader

        providers = SoundLoader.available_providers()
        if not providers:
            pytest.skip("No audio providers available")

        # This test just verifies the parameter is accepted
        # The actual load may fail if file doesn't exist
        provider = providers[0]
        # We can't guarantee the file exists, so we just test the API
        sound = SoundLoader.load(test_audio_path, audio_output_provider=provider)
        # Result may be None if file doesn't exist, but no exception should be raised

    def test_provider_case_insensitive(self, test_audio_path):
        """Provider name should be case-insensitive."""
        from kivy.core.audio_output import SoundLoader

        providers = SoundLoader.available_providers()
        if not providers:
            pytest.skip("No audio providers available")

        provider = providers[0]
        # Test with uppercase - should not raise
        sound = SoundLoader.load(test_audio_path,
                                 audio_output_provider=provider.upper())


class TestInvalidProviderHandling:
    """Tests for invalid provider name handling."""

    @pytest.fixture
    def test_audio_path(self):
        """Path to test audio file."""
        return os.path.join(os.path.dirname(__file__), "sample1.ogg")

    def test_invalid_provider_lenient_mode(self, test_audio_path, monkeypatch):
        """Invalid provider in lenient mode should fallback."""
        # Ensure strict mode is off
        monkeypatch.delenv("KIVY_PROVIDER_STRICT", raising=False)

        from kivy.core.audio_output import SoundLoader

        # Should not raise, but log warning and fallback to default providers
        sound = SoundLoader.load(
            test_audio_path, audio_output_provider="nonexistent_provider_xyz"
        )
        # Result may be None if no provider can handle it, but no exception

    def test_invalid_provider_strict_mode(self, test_audio_path, monkeypatch):
        """Invalid provider in strict mode should raise exception."""
        monkeypatch.setenv("KIVY_PROVIDER_STRICT", "1")

        from kivy.core.audio_output import SoundLoader

        # In strict mode, invalid provider should raise an exception
        with pytest.raises(ValueError):
            SoundLoader.load(
                test_audio_path, audio_output_provider="nonexistent_provider_xyz"
            )

    def test_unsupported_format_strict_mode(self, monkeypatch):
        """Provider that doesn't support format should raise in strict mode."""
        monkeypatch.setenv("KIVY_PROVIDER_STRICT", "1")

        from kivy.core.audio_output import SoundLoader

        providers = SoundLoader.available_providers()
        if not providers:
            pytest.skip("No audio providers available")

        # Try to load a file with an extension the provider likely doesn't support
        provider = providers[0]
        fake_file = "test.xyz_unsupported_format"

        with pytest.raises(ValueError):
            SoundLoader.load(fake_file, audio_output_provider=provider)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

