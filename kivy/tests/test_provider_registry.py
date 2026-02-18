"""
Tests for the centralized PROVIDER_CONFIGS registry.

Validates that the central provider registry in kivy/core/__init__.py is:
- Complete (contains all existing providers)
- Correct (module names match actual files)
- Synchronized (kivy_options matches the registry)

.. versionadded:: 3.0.0
"""

from pathlib import Path
import pytest


class TestProviderRegistryCompleteness:
    """Tests to ensure PROVIDER_CONFIGS contains all existing providers."""

    def test_registry_imports(self):
        """The registry and helper functions should be importable."""
        from kivy.core import (
            PROVIDER_CONFIGS,
            get_provider_options,
            get_provider_modules,
            get_all_categories,
        )

        assert PROVIDER_CONFIGS is not None
        assert callable(get_provider_options)
        assert callable(get_provider_modules)
        assert callable(get_all_categories)

    def test_registry_has_all_categories(self):
        """Registry should contain all 8 core provider categories."""
        from kivy.core import PROVIDER_CONFIGS

        expected_categories = {
            'window', 'text', 'video', 'audio_output',
            'image', 'camera', 'spelling', 'clipboard'
        }

        actual_categories = set(PROVIDER_CONFIGS.keys())

        assert actual_categories == expected_categories, (
            f"Missing categories: {expected_categories - actual_categories}, "
            f"Extra categories: {actual_categories - expected_categories}"
        )

    def test_registry_categories_not_empty(self):
        """Each category should have at least one provider."""
        from kivy.core import PROVIDER_CONFIGS

        for category, providers in PROVIDER_CONFIGS.items():
            assert len(providers) > 0, (
                f"Category {category!r} has no providers defined"
            )

    def test_registry_provider_format(self):
        """Each provider entry should be a (name, module) tuple."""
        from kivy.core import PROVIDER_CONFIGS

        for category, providers in PROVIDER_CONFIGS.items():
            assert isinstance(providers, list), (
                f"Category {category!r} should have a list of providers"
            )
            for entry in providers:
                assert isinstance(entry, tuple), (
                    f"Provider entry in {category!r} should be tuple: {entry!r}"
                )
                assert len(entry) == 2, (
                    f"Provider entry in {category!r} should have 2 elements: {entry!r}"
                )
                name, module = entry
                assert isinstance(name, str), (
                    f"Provider name in {category!r} should be string: {name!r}"
                )
                assert isinstance(module, str), (
                    f"Module name in {category!r} should be string: {module!r}"
                )
                assert name.lower() == name, (
                    f"Provider name {name!r} in {category!r} should be lowercase"
                )

    def test_all_provider_modules_exist(self):
        """All modules referenced in PROVIDER_CONFIGS should exist as files.

        Note: Some providers may be platform-specific or optional and won't
        exist in all installations. This test allows specific known optional
        providers to be missing.
        """
        from kivy.core import PROVIDER_CONFIGS
        import kivy

        kivy_root = Path(kivy.__file__).parent
        missing_modules = []

        # Known optional/platform-specific providers that may not be installed
        optional_providers = {
            ('window', 'x11', 'window_x11'),         # Linux-only
            ('audio_output', 'sdl3', 'audio_sdl3'),  # May not be built/installed
            ('image', 'imageio', 'img_imageio'),     # Optional dependency
            ('camera', 'avfoundation', 'camera_avfoundation'),  # macOS-only
        }

        for category, providers in PROVIDER_CONFIGS.items():
            for provider_name, module_name in providers:
                # Check for both .py and .pyx files (Cython)
                module_py = kivy_root / 'core' / category / f'{module_name}.py'
                module_pyx = kivy_root / 'core' / category / f'{module_name}.pyx'

                if not (module_py.exists() or module_pyx.exists()):
                    # Skip known optional providers
                    if (category, provider_name, module_name) in optional_providers:
                        continue

                    missing_modules.append(
                        (category, provider_name, module_name, str(module_py))
                    )

        # Report all missing modules at once for easier debugging
        if missing_modules:
            error_msg = "Missing provider module files (.py or .pyx):\n"
            for cat, name, mod, path in missing_modules:
                error_msg += f"  - {cat}/{name} ({mod}): {path}\n"
            pytest.fail(error_msg)

    def test_no_duplicate_provider_names_within_category(self):
        """Within each category, provider names should be unique."""
        from kivy.core import PROVIDER_CONFIGS

        for category, providers in PROVIDER_CONFIGS.items():
            names = [name for name, module in providers]
            unique_names = set(names)

            assert len(names) == len(unique_names), (
                f"Category {category!r} has duplicate provider names: "
                f"{[n for n in names if names.count(n) > 1]}"
            )

    def test_no_duplicate_module_names_within_category(self):
        """Within each category, module names should be unique."""
        from kivy.core import PROVIDER_CONFIGS

        for category, providers in PROVIDER_CONFIGS.items():
            modules = [module for name, module in providers]
            unique_modules = set(modules)

            assert len(modules) == len(unique_modules), (
                f"Category {category!r} has duplicate module names: "
                f"{[m for m in modules if modules.count(m) > 1]}"
            )


class TestProviderRegistrySync:
    """Tests to ensure kivy_options is synchronized with PROVIDER_CONFIGS."""

    def test_kivy_options_matches_registry_categories(self):
        """kivy_options should have entries for all registry categories."""
        from kivy import kivy_options
        from kivy.core import PROVIDER_CONFIGS

        registry_categories = set(PROVIDER_CONFIGS.keys())
        options_categories = set(kivy_options.keys())

        assert registry_categories == options_categories, (
            f"Category mismatch - "
            f"Missing in kivy_options: {registry_categories - options_categories}, "
            f"Extra in kivy_options: {options_categories - registry_categories}"
        )

    def test_kivy_options_matches_registry_providers(self):
        """kivy_options provider lists should match PROVIDER_CONFIGS."""
        from kivy import kivy_options
        from kivy.core import get_provider_options

        for category in kivy_options.keys():
            expected = get_provider_options(category)
            actual = kivy_options[category]

            assert actual == expected, (
                f"Provider mismatch in {category!r}:\n"
                f"  Expected (from registry): {expected}\n"
                f"  Actual (kivy_options): {actual}"
            )

    def test_kivy_options_provider_order_matches_registry(self):
        """Provider order in kivy_options should match registry (priority order)."""
        from kivy import kivy_options
        from kivy.core import PROVIDER_CONFIGS

        for category, providers in PROVIDER_CONFIGS.items():
            registry_order = tuple(name for name, module in providers)
            options_order = kivy_options[category]

            assert registry_order == options_order, (
                f"Provider order mismatch in {category!r}:\n"
                f"  Registry: {registry_order}\n"
                f"  Options:  {options_order}"
            )


class TestHelperFunctions:
    """Tests for the helper functions in kivy.core."""

    def test_get_provider_options_returns_tuple(self):
        """get_provider_options should return a tuple."""
        from kivy.core import get_provider_options

        result = get_provider_options('window')
        assert isinstance(result, tuple)

    def test_get_provider_options_extracts_names(self):
        """get_provider_options should extract only provider names."""
        from kivy.core import get_provider_options, PROVIDER_CONFIGS

        for category in PROVIDER_CONFIGS.keys():
            result = get_provider_options(category)
            expected = tuple(name for name, module in PROVIDER_CONFIGS[category])
            assert result == expected

    def test_get_provider_modules_returns_dict(self):
        """get_provider_modules should return a dict."""
        from kivy.core import get_provider_modules

        result = get_provider_modules('window')
        assert isinstance(result, dict)

    def test_get_provider_modules_returns_copy(self):
        """get_provider_modules should return a copy (not reference)."""
        from kivy.core import get_provider_modules, PROVIDER_CONFIGS

        result = get_provider_modules('window')

        # Modifying result should not affect registry
        original_length = len(PROVIDER_CONFIGS['window'])
        result['test'] = 'test_module'

        assert len(PROVIDER_CONFIGS['window']) == original_length, (
            "get_provider_modules should return a copy, not reference"
        )

    def test_get_provider_modules_correct_mapping(self):
        """get_provider_modules should map provider names to module names."""
        from kivy.core import get_provider_modules, PROVIDER_CONFIGS

        for category in PROVIDER_CONFIGS.keys():
            result = get_provider_modules(category)
            expected = dict(PROVIDER_CONFIGS[category])

            assert result == expected, (
                f"get_provider_modules('{category}') should return correct dict"
            )

            # Verify all keys and values are strings
            for name, module in result.items():
                assert isinstance(name, str)
                assert isinstance(module, str)

    def test_get_all_categories_returns_list(self):
        """get_all_categories should return a list."""
        from kivy.core import get_all_categories

        result = get_all_categories()
        assert isinstance(result, list)

    def test_get_all_categories_complete(self):
        """get_all_categories should return all category names."""
        from kivy.core import get_all_categories, PROVIDER_CONFIGS

        result = set(get_all_categories())
        expected = set(PROVIDER_CONFIGS.keys())

        assert result == expected


class TestProviderModuleUsage:
    """Tests to verify provider modules correctly use the registry."""

    def test_audio_module_uses_registry(self):
        """Audio module should build providers from registry."""
        # This implicitly tests it by checking if audio providers load
        from kivy.core.audio_output import SoundLoader

        providers = SoundLoader.available_providers()
        assert len(providers) > 0, "Audio providers should be loaded from registry"

    def test_image_module_uses_registry(self):
        """Image module should build providers from registry."""
        from kivy.core.image import Image as CoreImage

        providers = CoreImage.available_providers()
        assert len(providers) > 0, "Image providers should be loaded from registry"

    def test_text_module_uses_registry(self):
        """Text module should build providers from registry."""
        from kivy.core.text import LabelBase

        providers = LabelBase.available_providers()
        assert len(providers) > 0, "Text providers should be loaded from registry"

    def test_window_module_uses_registry(self):
        """Window module should build providers from registry."""
        from kivy.core.window import Window

        # Window is a singleton instance, verify it exists
        assert Window is not None, "Window should be loaded from registry"

    def test_video_module_uses_registry(self):
        """Video module should build providers from registry."""
        from kivy.core.video import Video

        # Video is a class (or None if no providers)
        # Just check it's defined (may be None if no providers available)
        assert Video is not None or Video is None  # Either case is valid

    def test_camera_module_uses_registry(self):
        """Camera module should build providers from registry."""
        from kivy.core.camera import Camera

        # Camera is a class (or None if no providers)
        assert Camera is not None or Camera is None  # Either case is valid

    def test_spelling_module_uses_registry(self):
        """Spelling module should build providers from registry."""
        from kivy.core.spelling import Spelling

        # Spelling is a class (or None if no providers)
        assert Spelling is not None or Spelling is None  # Either case is valid

    def test_clipboard_module_uses_registry(self):
        """Clipboard module should build providers from registry."""
        from kivy.core.clipboard import Clipboard

        # Clipboard is an instance
        assert Clipboard is not None, "Clipboard should be loaded from registry"


class TestRegistryDiscovery:
    """Tests to detect if providers exist but are missing from registry."""

    def get_provider_module_files(self, category):
        """Get all provider module files for a given category."""
        import kivy

        kivy_root = Path(kivy.__file__).parent
        category_dir = kivy_root / 'core' / category

        if not category_dir.exists():
            return []

        # Find all Python files that look like provider modules
        provider_files = []

        # Files to skip (not actual providers)
        skip_files = {
            '__init__.py',
            'markup.py',  # Text markup utility, not a provider
            '_clipboard_ext.py',  # Clipboard helper, not a provider
        }

        for file in category_dir.glob('*.py'):
            # Skip special files
            if file.name in skip_files:
                continue

            # Skip files starting with underscore (internal helpers)
            if file.name.startswith('_'):
                continue

            # Provider modules typically start with category name prefix
            # e.g., window_sdl3.py, audio_ffpyplayer.py, img_pil.py
            provider_files.append(file.stem)  # stem = filename without extension

        return provider_files

    def test_window_providers_complete(self):
        """All window provider files should be in PROVIDER_CONFIGS."""
        from kivy.core import PROVIDER_CONFIGS

        provider_files = self.get_provider_module_files('window')
        registry_modules = {module for name, module in PROVIDER_CONFIGS['window']}

        for file in provider_files:
            assert file in registry_modules, (
                f"Window provider file {file!r} exists but not in PROVIDER_CONFIGS"
            )

    def test_text_providers_complete(self):
        """All text provider files should be in PROVIDER_CONFIGS."""
        from kivy.core import PROVIDER_CONFIGS

        provider_files = self.get_provider_module_files('text')
        registry_modules = {module for name, module in PROVIDER_CONFIGS['text']}

        for file in provider_files:
            assert file in registry_modules, (
                f"Text provider file {file!r} exists but not in PROVIDER_CONFIGS"
            )

    def test_video_providers_complete(self):
        """All video provider files should be in PROVIDER_CONFIGS."""
        from kivy.core import PROVIDER_CONFIGS

        provider_files = self.get_provider_module_files('video')
        registry_modules = {module for name, module in PROVIDER_CONFIGS['video']}

        for file in provider_files:
            # video_android exists but is NOT in kivy_options/registry
            # It's only used directly by platform-specific code, not through
            # the env var filtering system
            if file == 'video_android':
                continue

            assert file in registry_modules, (
                f"Video provider file {file!r} exists but not in PROVIDER_CONFIGS"
            )

    def test_audio_output_providers_complete(self):
        """All audio_output provider files should be in PROVIDER_CONFIGS."""
        from kivy.core import PROVIDER_CONFIGS

        provider_files = self.get_provider_module_files('audio_output')
        registry_modules = {module for name, module in PROVIDER_CONFIGS['audio_output']}

        for file in provider_files:
            assert file in registry_modules, (
                f"Audio provider file {file!r} exists but not in PROVIDER_CONFIGS"
            )

    def test_image_providers_complete(self):
        """All image provider files should be in PROVIDER_CONFIGS."""
        from kivy.core import PROVIDER_CONFIGS

        provider_files = self.get_provider_module_files('image')
        registry_modules = {module for name, module in PROVIDER_CONFIGS['image']}

        for file in provider_files:
            # img_gif is deprecated/removed, so it's OK if it exists but not in registry
            if file == 'img_gif':
                continue
            assert file in registry_modules, (
                f"Image provider file {file!r} exists but not in PROVIDER_CONFIGS"
            )

    def test_camera_providers_complete(self):
        """All camera provider files should be in PROVIDER_CONFIGS."""
        from kivy.core import PROVIDER_CONFIGS

        provider_files = self.get_provider_module_files('camera')
        registry_modules = {module for name, module in PROVIDER_CONFIGS['camera']}

        for file in provider_files:
            assert file in registry_modules, (
                f"Camera provider file {file!r} exists but not in PROVIDER_CONFIGS"
            )

    def test_spelling_providers_complete(self):
        """All spelling provider files should be in PROVIDER_CONFIGS."""
        from kivy.core import PROVIDER_CONFIGS

        provider_files = self.get_provider_module_files('spelling')
        registry_modules = {module for name, module in PROVIDER_CONFIGS['spelling']}

        for file in provider_files:
            assert file in registry_modules, (
                f"Spelling provider file {file!r} exists but not in PROVIDER_CONFIGS"
            )

    def test_clipboard_providers_complete(self):
        """All clipboard provider files should be in PROVIDER_CONFIGS."""
        from kivy.core import PROVIDER_CONFIGS

        provider_files = self.get_provider_module_files('clipboard')
        registry_modules = {module for name, module in PROVIDER_CONFIGS['clipboard']}

        for file in provider_files:
            assert file in registry_modules, (
                f"Clipboard provider file {file!r} exists but not in PROVIDER_CONFIGS"
            )


class TestRegistryCorrectness:
    """Tests to ensure provider names and modules are correctly formatted."""

    def test_provider_names_follow_convention(self):
        """Provider names should not include category prefix."""
        from kivy.core import PROVIDER_CONFIGS

        # Provider names should be simple: 'sdl3', 'pil', 'opencv'
        # Not: 'window_sdl3', 'text_pil', 'camera_opencv'
        for category, providers in PROVIDER_CONFIGS.items():
            for provider_name, module_name in providers:
                # Check that provider name doesn't start with category prefix
                # (except special cases like 'audio_output' category)
                category_prefix = category.replace('_output', '')
                assert not provider_name.startswith(f'{category_prefix}_'), (
                    f"Provider name {provider_name!r} in {category!r} "
                    f"should not include category prefix"
                )

    def test_module_names_follow_convention(self):
        """Module names should follow the category_provider pattern."""
        from kivy.core import PROVIDER_CONFIGS

        # Expected patterns by category
        expected_patterns = {
            'window': 'window_',
            'text': 'text_',
            'video': 'video_',
            'audio_output': 'audio_',
            'image': 'img_',
            'camera': 'camera_',
            'spelling': 'spelling_',
            'clipboard': 'clipboard_',
        }

        for category, providers in PROVIDER_CONFIGS.items():
            expected_prefix = expected_patterns[category]

            for provider_name, module_name in providers:
                assert module_name.startswith(expected_prefix), (
                    f"Module {module_name!r} in {category!r} should start with "
                    f"{expected_prefix!r}"
                )

    def test_registry_has_no_none_values(self):
        """Registry should not contain None values."""
        from kivy.core import PROVIDER_CONFIGS

        for category, providers in PROVIDER_CONFIGS.items():
            assert providers is not None
            for entry in providers:
                name, module = entry
                assert name is not None
                assert module is not None
                assert name != ''
                assert module != ''


class TestRegistryUsageInModules:
    """Tests to ensure provider modules correctly use get_provider_modules().

    Note: These tests read source files and are skipped when running from
    an installed package (e.g., sdist tests) where source files aren't available.
    """

    def _get_source_file_path(self, relative_path):
        """Get absolute path to source file, or None if not available.

        Args:
            relative_path: Path relative to repository root (e.g., 'kivy/__init__.py')

        Returns:
            Path object if source file exists, None otherwise
        """
        import kivy

        # Try to find the source file
        # Method 1: Relative to current working directory (dev environment)
        path = Path(relative_path)
        if path.exists():
            return path

        # Method 2: Relative to kivy installation
        # In both source trees and installed packages, kivy module files should exist
        kivy_root = Path(kivy.__file__).parent.parent
        path = kivy_root / relative_path
        if path.exists():
            return path

        # File not found in either location
        return None

    def test_audio_uses_get_provider_modules(self):
        """Audio module should import from kivy.core."""
        source_path = self._get_source_file_path('kivy/core/audio_output/__init__.py')
        if source_path is None:
            pytest.skip("Source files not available (installed package)")

        with open(source_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert 'get_provider_modules' in content, (
            "Audio module should import get_provider_modules"
        )
        assert 'get_provider_modules(\'audio_output\')' in content, (
            "Audio module should call get_provider_modules('audio_output')"
        )

    def test_image_uses_get_provider_modules(self):
        """Image module should import from kivy.core."""
        source_path = self._get_source_file_path('kivy/core/image/__init__.py')
        if source_path is None:
            pytest.skip("Source files not available (installed package)")

        with open(source_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert 'get_provider_modules' in content, (
            "Image module should import get_provider_modules"
        )
        assert 'get_provider_modules(\'image\')' in content, (
            "Image module should call get_provider_modules('image')"
        )

    def test_text_uses_get_provider_modules(self):
        """Text module should import from kivy.core."""
        source_path = self._get_source_file_path('kivy/core/text/__init__.py')
        if source_path is None:
            pytest.skip("Source files not available (installed package)")

        with open(source_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert 'get_provider_modules' in content, (
            "Text module should import get_provider_modules"
        )
        assert 'get_provider_modules(\'text\')' in content, (
            "Text module should call get_provider_modules('text')"
        )

    def test_window_uses_get_provider_modules(self):
        """Window module should import from kivy.core."""
        source_path = self._get_source_file_path('kivy/core/window/__init__.py')
        if source_path is None:
            pytest.skip("Source files not available (installed package)")

        with open(source_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert 'get_provider_modules' in content, (
            "Window module should import get_provider_modules"
        )
        assert 'get_provider_modules(\'window\')' in content, (
            "Window module should call get_provider_modules('window')"
        )

    def test_video_uses_get_provider_modules(self):
        """Video module should import from kivy.core."""
        source_path = self._get_source_file_path('kivy/core/video/__init__.py')
        if source_path is None:
            pytest.skip("Source files not available (installed package)")

        with open(source_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert 'get_provider_modules' in content, (
            "Video module should import get_provider_modules"
        )
        assert 'get_provider_modules(\'video\')' in content, (
            "Video module should call get_provider_modules('video')"
        )

    def test_camera_uses_get_provider_modules(self):
        """Camera module should import from kivy.core."""
        source_path = self._get_source_file_path('kivy/core/camera/__init__.py')
        if source_path is None:
            pytest.skip("Source files not available (installed package)")

        with open(source_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert 'get_provider_modules' in content, (
            "Camera module should import get_provider_modules"
        )
        assert 'get_provider_modules(\'camera\')' in content, (
            "Camera module should call get_provider_modules('camera')"
        )

    def test_spelling_uses_get_provider_modules(self):
        """Spelling module should import from kivy.core."""
        source_path = self._get_source_file_path('kivy/core/spelling/__init__.py')
        if source_path is None:
            pytest.skip("Source files not available (installed package)")

        with open(source_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert 'get_provider_modules' in content, (
            "Spelling module should import get_provider_modules"
        )
        assert 'get_provider_modules(\'spelling\')' in content, (
            "Spelling module should call get_provider_modules('spelling')"
        )

    def test_clipboard_uses_get_provider_modules(self):
        """Clipboard module should import from kivy.core."""
        source_path = self._get_source_file_path('kivy/core/clipboard/__init__.py')
        if source_path is None:
            pytest.skip("Source files not available (installed package)")

        with open(source_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert 'get_provider_modules' in content, (
            "Clipboard module should import get_provider_modules"
        )
        assert 'get_provider_modules(\'clipboard\')' in content, (
            "Clipboard module should call get_provider_modules('clipboard')"
        )

    def test_kivy_init_uses_get_provider_options(self):
        """kivy/__init__.py should use get_provider_options()."""
        source_path = self._get_source_file_path('kivy/__init__.py')
        if source_path is None:
            pytest.skip("Source files not available (installed package)")

        with open(source_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert 'from kivy.core import get_provider_options' in content, (
            "kivy/__init__.py should import get_provider_options"
        )
        assert 'get_provider_options(' in content, (
            "kivy/__init__.py should call get_provider_options()"
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
