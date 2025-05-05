import threading
import time

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.label import Label


class ThemedLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text = f"Current system theme is: {Window.get_system_theme()}"
        self.start_system_theme_monitor()

    def start_system_theme_monitor(self, interval=1.0):
        """
        Starts a background monitor that checks for system theme changes.

        Args:
            interval (float): Time interval in seconds between theme checks.
        """

        def monitor():
            last_theme = Window.get_system_theme()
            while True:
                time.sleep(interval)
                current_theme = Window.get_system_theme()
                if current_theme != last_theme:
                    last_theme = current_theme
                    Clock.schedule_once(
                        lambda dt: self.on_system_theme_change(current_theme)
                    )

        threading.Thread(target=monitor, daemon=True).start()

    def on_system_theme_change(self, new_theme):
        """
        Callback executed when the system theme changes.

        Args:
            new_theme (str): The new system theme.
        """
        self.text = f"Current system theme is: {new_theme}"


class ThemeMonitorApp(App):
    def build(self):
        label = ThemedLabel(font_size=20)
        return label


if __name__ == "__main__":
    ThemeMonitorApp().run()
