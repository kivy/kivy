import os
from kivy.utils import platform


class SystemEmojiFontsFinder:
    """
    Class for detecting emoji fonts on the current operating system.

    Supported platforms: Windows, macOS, Linux, Android, and iOS.
    Features:
    - List available emoji fonts on the current system.
    - Automatically select the best available font.
    - Retrieve all potential emoji fonts per platform (for debugging).
    """

    # Known fonts on Windows
    WINDOWS_FONTS = [
        "C:/Windows/Fonts/seguiemj.ttf",  # Segoe UI Emoji
        "C:/Windows/Fonts/seguisym.ttf",  # Segoe UI Symbol
        "C:/Windows/Fonts/NotoColorEmoji.ttf",  # If installed
        "C:/Windows/Fonts/TwitterColorEmoji-SVGinOT.ttf",  # If installed
    ]

    # Known fonts on macOS
    MACOS_FONTS = [
        "/System/Library/Fonts/Apple Color Emoji.ttc",
        "/Library/Fonts/Apple Color Emoji.ttc",
        "/System/Library/Fonts/Helvetica.ttc",  # Has some symbols
        "/System/Library/Fonts/LastResort.otf",  # Fallback for missing chars
    ]

    # Known fonts on Linux
    LINUX_FONTS = [
        "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
        "/usr/share/fonts/TTF/NotoColorEmoji.ttf",
        "/usr/share/fonts/noto-cjk/NotoColorEmoji.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Has some symbols
        "/usr/share/fonts/TTF/TwitterColorEmoji-SVGinOT.ttf",
        "/usr/local/share/fonts/NotoColorEmoji.ttf",  # User-installed
        "~/.local/share/fonts/NotoColorEmoji.ttf",  # User local
        "/opt/google/chrome/fonts/NotoColorEmoji.ttf",  # Chrome
    ]

    # Known fonts on Android
    ANDROID_FONTS = [
        "/system/fonts/NotoColorEmoji.ttf",
        "/system/fonts/AndroidEmoji.ttf",  # Older versions
        "/system/fonts/DroidSansFallback.ttf",  # Has some symbols
        "/system/fonts/NotoSansCJK-Regular.ttc",  # Partial emoji support
    ]

    # Known fonts on iOS
    IOS_FONTS = [
        "/System/Library/Fonts/Core/Apple Color Emoji.ttc",
        "/System/Library/Fonts/Apple Color Emoji.ttc",
        "/var/mobile/Library/Fonts/Apple Color Emoji.ttc",
    ]

    @staticmethod
    def get_available_fonts():
        """
        Get a list of available emoji fonts for the current platform.

        The method:
        - Detects the platform using `kivy.utils.platform`.
        - Expands user paths with `~`.
        - Checks if the file exists on disk.

        :return: List of available font file paths.
        """
        font_map = {
            "win": SystemEmojiFontsFinder.WINDOWS_FONTS,
            "macosx": SystemEmojiFontsFinder.MACOS_FONTS,
            "linux": SystemEmojiFontsFinder.LINUX_FONTS,
            "android": SystemEmojiFontsFinder.ANDROID_FONTS,
            "ios": SystemEmojiFontsFinder.IOS_FONTS,
        }

        fonts = font_map.get(platform, [])
        available = []

        for font_path in fonts:
            expanded_path = os.path.expanduser(font_path)
            if os.path.exists(expanded_path):
                available.append(expanded_path)

        return available

    @staticmethod
    def get_best_emoji_font():
        """
        Get the best available emoji font for the current platform.

        The method returns the first valid font found in `get_available_fonts`.
        If none are available, it returns None.

        :return: Font file path (string) or None.
        """
        fonts = SystemEmojiFontsFinder.get_available_fonts()
        return fonts[0] if fonts else None

    @staticmethod
    def get_all_fonts():
        """
        Get all potential emoji fonts across supported platforms.

        Useful for development and debugging. This does not check
        if the files actually exist on disk.

        :return: Dictionary mapping platform names to font lists.
        """
        return {
            "windows": SystemEmojiFontsFinder.WINDOWS_FONTS,
            "macos": SystemEmojiFontsFinder.MACOS_FONTS,
            "linux": SystemEmojiFontsFinder.LINUX_FONTS,
            "android": SystemEmojiFontsFinder.ANDROID_FONTS,
            "ios": SystemEmojiFontsFinder.IOS_FONTS,
        }
