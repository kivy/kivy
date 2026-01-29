"""
Set KIVY_HOME for App-Specific Configuration
=============================================

This module provides a utility to set KIVY_HOME to an app-specific directory
before importing Kivy. This ensures each application has its own isolated
configuration, logs, and cache directories.

Usage:
    from set_kivy_home import set_app_name  # BEFORE importing kivy
    set_app_name('MyApp')

    from kivy.app import App  # Now safe to import

Platform Paths:
    Windows: %APPDATA%/<appname>/.kivy
    macOS: ~/Library/Application Support/<appname>/.kivy
    Linux: $XDG_DATA_HOME/<appname>/.kivy (typically ~/.local/share/<appname>/.kivy)

Note:
    This must be called BEFORE importing any kivy modules, otherwise
    RuntimeError will be raised.
"""

from os import environ
import sys
from sys import platform as _sys_platform
from pathlib import Path


def _get_platform():
    """Get the current platform (from kivy.utils)."""
    # On Android sys.platform returns 'linux2', so prefer to check the
    # existence of environ variables set during Python initialization
    kivy_build = environ.get('KIVY_BUILD', '')
    if kivy_build in {'android', 'ios'}:
        return kivy_build
    elif 'P4A_BOOTSTRAP' in environ:
        return 'android'
    elif 'ANDROID_ARGUMENT' in environ:
        # We used to use this method to detect android platform,
        # leaving it here to be backwards compatible with `pydroid3`
        # and similar tools outside kivy's ecosystem
        return 'android'
    elif _sys_platform in ('win32', 'cygwin'):
        return 'win'
    elif _sys_platform == 'darwin':
        return 'macosx'
    elif _sys_platform.startswith('linux'):
        return 'linux'
    elif _sys_platform.startswith('freebsd'):
        return 'linux'
    return 'unknown'


def set_app_name(app_name):
    """
    Set the app name for desktop platforms to configure KIVY_HOME.

    This function sets KIVY_HOME to an app-specific directory based on
    platform conventions. It must be called BEFORE importing any Kivy modules.

    Args:
        app_name (str): The name of your application. The name will be
            normalized (lowercased, 'app' suffix stripped) to match
            App.user_data_dir behavior.

    Raises:
        RuntimeError: If kivy.config has already been imported.
        ValueError: If the platform is unknown.

    Example:
        >>> from set_kivy_home import set_app_name
        >>> set_app_name('MyApp')
        >>> from kivy.app import App
        >>> # KIVY_HOME is now set to app-specific directory

    Note:
        - If KIVY_HOME is already set, this function does nothing
        - On mobile platforms (iOS, Android), this function does nothing
        - The .kivy directory will be created if it doesn't exist
    """
    platform = _get_platform()

    # Skip if KIVY_HOME already set or on mobile platforms
    if environ.get('KIVY_HOME', None) or platform in ('ios', 'android'):
        return

    # Check that Config hasn't been imported yet
    if 'kivy.config' in sys.modules:
        raise RuntimeError(
            "Config has already been imported. "
            "set_app_name must execute before kivy.config to ensure "
            "proper initialization order."
        )

    # Normalize app name (lowercase, strip 'app' suffix)
    # This matches the behavior of App.user_data_dir
    name = app_name.lower()
    name = name[:-3] if name.endswith('app') else name

    # Set platform-specific path
    if platform == 'win':
        kivy_home = Path(environ['APPDATA']) / f'{name}/.kivy'
    elif platform == 'macosx':
        kivy_home = Path(f'~/Library/Application Support/{name}/.kivy')
    elif platform == 'linux':
        p = Path(environ.get('XDG_DATA_HOME', '~/.local/share'))
        kivy_home = p / f'{name}/.kivy'
    else:
        raise ValueError(f'Unknown platform: {platform}')

    # Expand ~ and create directory
    kivy_home = kivy_home.expanduser()
    kivy_home.mkdir(parents=True, exist_ok=True)

    # Set environment variable
    environ['KIVY_HOME'] = str(kivy_home)
