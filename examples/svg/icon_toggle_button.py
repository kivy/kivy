"""
icon_toggle_button.py
-----------------------
Demonstrates mixing ToggleButtonBehavior with SvgWidget to create a tappable
icon that changes colour on toggle - the classic "favourite star" pattern.

Three independent star buttons are shown.  Each is grey when untoggled and
gold when toggled on.

Run from the repo root::

    python icon_toggle_button.py
"""


from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.behaviors import ToggleButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.svg import SvgWidget


KV = '''
<StarIconToggleButton>:
    source: 'star.svg'
    size_hint: None, None
    size: '64dp', '64dp'
    fit_mode: 'contain'
    current_color: 'gold' if self.activated else 'grey'
    mipmap: False

<StarColumn>:
    orientation: 'vertical'
    size_hint: None, None
    size: '96dp', '120dp'
    spacing: '8dp'
    StarIconToggleButton:
        pos_hint: {'center_x': 0.5}
        group: 'star_group'
    Label:
        text: root.label_text
        color: 'lightgrey'
        font_size: '13sp'
        size_hint_y: None
        height: '24dp'

BoxLayout:
    padding: '32dp', '32dp'
    spacing: '32dp'
    StarColumn:
        label_text: 'Favorite'
    StarColumn:
        label_text: 'Bookmark'
    StarColumn:
        label_text: 'Highlight'
'''


class StarIconToggleButton(ToggleButtonBehavior, SvgWidget):
    pass


class StarColumn(BoxLayout):
    label_text = StringProperty()


class IconButtonApp(App):

    def build(self):
        Window.size = (420, 200)
        Window.clearcolor = (0.12, 0.12, 0.12, 1)
        self.title = 'Icon Toggle Button Demonstration'
        return Builder.load_string(KV)


if __name__ == '__main__':
    IconButtonApp().run()
