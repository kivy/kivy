import os

os.environ["KIVY_TEXT"] = "sdl3"

from kivy.app import App
from kivy.core.text import LabelBase
from kivy.core.text.system_emoji_fonts import SystemEmojiFontsFinder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

fallback_options = [
    r"C:\Windows\Fonts\seguiemj.ttf",
    r"NotoColorEmoji.ttf",
]
LabelBase.register(
    name="MyFont1",
    fn_regular=r"C:\WINDOWS\FONTS\MTCORSVA.ttf",
    fallback_fonts=fallback_options,
)

available_emoji_fonts = SystemEmojiFontsFinder.get_available_fonts()
LabelBase.register(
    name="MyFont2",
    fn_regular=r"C:\WINDOWS\FONTS\ROCK.ttf",
    fallback_fonts=available_emoji_fonts,
)


class TestApp(App):
    def build(self):
        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)

        # using custom font
        label1 = Label(
            text="Code with ❤️ Build with 🔥 Ship with 🚀\nDreams → Reality 💫",
            font_name="MyFont1",
            bold=True,
            font_size="24sp",
            markup=True,
        )
        label2 = Label(
            text="Code with ❤️ Build with 🔥 Ship with 🚀\nDreams → Reality 💫",
            font_name="MyFont2",
            bold=True,
            font_size="24sp",
        )

        # native emoji support
        label3 = Label(
            text="Code with ❤️ Build with 🔥 Ship with 🚀\nDreams → Reality 💫",
            font_size="24sp",
        )

        layout.add_widget(label1)
        layout.add_widget(label2)
        layout.add_widget(label3)
        return layout


TestApp().run()
