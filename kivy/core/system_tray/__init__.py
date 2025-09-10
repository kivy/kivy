from kivy.core.system_tray._system_tray_sdl3 import (
    TrayIcon as _CoreTrayIcon,
    TrayMenu as _CoreTrayMenu,
    TrayMenuItem as _CoreTrayMenuItem,
)
"""
System tray icon with context menu functionality.

Provides integration with the OS notification area, allowing apps to display
an interactive icon with tooltip and customizable menu.
"""

class TrayIcon(_CoreTrayIcon):
    ...

class TrayMenu(_CoreTrayMenu):
    ...

class TrayMenuItem(_CoreTrayMenuItem):
    ...
