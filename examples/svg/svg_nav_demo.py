"""
SVG Navigation Demo
===================

Demonstrates practical SVG usage in a simple app:

* Three SVG icons in a bottom navigation bar switch between screens.
* Each screen contains a button rendered
  with a ``Rectangle`` canvas instruction fed by an SVG-rasterized texture.
  Pressing the button shows a pressed state by swapping to a second
  SVG texture.

The SVGs in the Image widget (in NavIcon), and the Rectangle (in SvgButton),
are rasterized once. Using mipmap they can be scaled down to any size without
loss of quality.

Navigation icons from the Lucide icon set (https://lucide.dev)
ISC License Copyright (c) Lucide Contributors
https://github.com/lucide-icons/lucide/blob/main/LICENSE

Requirements
------------
  pip install kivy[base] thorvg-python

Run from the project root::

    python examples/svg/svg_nav_demo.py
"""

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty

Window.clearcolor = (0.97, 0.97, 0.97, 1)

KV = """
<SvgButton>:
    size_hint: None, None
    size: '200dp', '48dp'
    font_size: '20sp'
    bold: True
    color: 'black'
    on_press: root.current_source = root.pressed_source
    on_release: root.current_source = root.normal_source
    canvas.before:
        Rectangle:
            source: root.current_source
            pos: self.pos
            size: self.size

# ── Tappable nav icon ─────────────────────────────────────────────────────────
<NavIcon>:
    # use an Image widget to display the SVG icon
    fit_mode: 'contain'
    mipmap: True

# ── Screens ───────────────────────────────────────────────────────────────────
<NavScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: '32dp'
        spacing: '24dp'
        Label:
            text: root.title
            font_size: '32sp'
            bold: True
            color: 0.1, 0.1, 0.1, 1
            size_hint_y: None
            height: '48dp'
            halign: 'left'
            text_size: self.width, None
        AnchorLayout:
            SvgButton:
                text: root.button_text

# ── Bottom navigation bar ─────────────────────────────────────────────────────
<NavBar@BoxLayout>:
    orientation: 'horizontal'
    size_hint_y: None
    height: '64dp'
    padding: ['16dp', '8dp']
    spacing: '8dp'
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: 0.82, 0.82, 0.82, 1
        Rectangle:
            pos: self.x, self.top - 1
            size: self.width, 1

    NavIcon:
        source: app.icon_mail
        on_release: app.root.ids.sm.current = 'mail'

    NavIcon:
        source: app.icon_house
        on_release: app.root.ids.sm.current = 'home'

    NavIcon:
        source: app.icon_settings
        on_release: app.root.ids.sm.current = 'settings'

# ── Root ──────────────────────────────────────────────────────────────────────
BoxLayout:
    orientation: 'vertical'
    ScreenManager:
        id: sm
        NavScreen:
            name: 'mail'
            title: 'Mail'
            button_text: 'Compose'
        NavScreen:
            name: 'home'
            title: 'Home'
            button_text: 'Go Home'
        NavScreen:
            name: 'settings'
            title: 'Settings'
            button_text: 'Save Settings'
    NavBar:
"""


class NavScreen(Screen):
    """A screen with a title label and a centred SvgButton."""
    title = StringProperty('')
    button_text = StringProperty('')


class SvgButton(ButtonBehavior, Label):
    """A button whose face is a BorderImage drawn from an SVG source file.

    """
    normal_source = StringProperty('button_glossy_normal.svg')
    pressed_source = StringProperty('button_glossy_pressed.svg')
    current_source = StringProperty('button_glossy_normal.svg')


class NavIcon(ButtonBehavior, Image):
    """A tappable SVG icon in the navigation bar."""
    pass


class SvgNavApp(App):
    icon_mail = StringProperty('mail.svg')
    icon_house = StringProperty('house.svg')
    icon_settings = StringProperty('settings.svg')

    def build(self):
        return Builder.load_string(KV)


if __name__ == '__main__':
    SvgNavApp().run()
