"""Demonstrate opt-in SDL3 fallback using available system emoji fonts."""
import os

os.environ["KIVY_TEXT"] = "sdl3"

from kivy import kivy_data_dir
from kivy.app import App
from kivy.core.text import LabelBase
from kivy.core.text.system_emoji_fonts import SystemEmojiFontsFinder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label


class FontFallbackApp(App):
    def build(self):
        fallbacks = SystemEmojiFontsFinder.get_available_fonts()
        LabelBase.register(
            name="EmojiFallback",
            fn_regular=os.path.join(kivy_data_dir, "fonts", "Roboto-Regular.ttf"),
            fallback_fonts=fallbacks,
        )
        layout = BoxLayout(orientation="vertical")
        layout.add_widget(Label(
            text="Code with ❤️ Build with 🔥 Ship with 🚀",
            font_name="EmojiFallback", font_size="24sp",
        ))
        layout.add_widget(Label(
            text="Fallback fonts: " + (", ".join(fallbacks) or
                                      "none found; bundle a font to try this"),
            font_size="14sp",
        ))
        return layout


if __name__ == "__main__":
    FontFallbackApp().run()
