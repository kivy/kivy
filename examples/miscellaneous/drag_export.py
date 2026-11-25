'''
Drag-export demo — drag files out of a Kivy window onto the OS.

Run from the kivy source tree::

    python examples/miscellaneous/drag_export.py

Hold a button, drag out of the window, drop on the desktop or another app.
'''

import base64
from io import BytesIO

from kivy.app import App
from kivy.core.window import Window
from kivy.core.window.drag_export import DragFileItem, available
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.button import Button

_PNG_B64 = (
    'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAQAAAC1+jfqAAAAJUlEQVR42mP8z8BQ'
    'w0AEYBxVSFkoYGBg+A8ABdgBSe7rJAAAAABJRU5ErkJggg=='
)


class DragButton(Button):
    '''Fire ``on_drag`` once the button's grab moves (Button already grabs).'''

    __events__ = ('on_drag',)

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return

        self.dispatch('on_drag')

    def on_drag(self):
        pass


class DragExportApp(App):

    drag_available = available()

    _png = BytesIO(base64.b64decode(_PNG_B64))

    _readme = BytesIO(b'Kivy drag-export demo.\nDrop me anywhere.\n')

    def build(self):
        return Builder.load_string('''
#:import DragButton __main__.DragButton

BoxLayout:
    orientation: 'vertical'
    padding: dp(20)
    spacing: dp(12)

    Label:
        text: 'Hold a button and drag out of the window. Backend available: ' + str(app.drag_available)
        size_hint_y: None
        text_size: self.width, None
        height: self.texture_size[1]

    DragButton:
        text: 'Text file (snippet.txt)'
        size_hint_y: None
        height: dp(48)
        on_drag: app.export_text()

    DragButton:
        text: 'Image (icon.png)'
        size_hint_y: None
        height: dp(48)
        on_drag: app.export_image()

    DragButton:
        text: 'Readme (readme.txt)'
        size_hint_y: None
        height: dp(48)
        on_drag: app.export_readme()
''')

    def export_text(self):
        text = 'Hello from Kivy drag-out!\nUnicode: café ☕\n'

        def callback(path):
            with open(path, 'w', encoding='utf-8') as fh:
                fh.write(text)

        Window.begin_drag_files([DragFileItem('snippet.txt', False, callback)])

    def export_image(self):
        data = self._png.getvalue()

        def callback(path):
            with open(path, 'wb') as fh:
                fh.write(data)

        Window.begin_drag_files([DragFileItem('icon.png', False, callback)])

    def export_readme(self):
        data = self._readme.getvalue()

        def callback(path):
            with open(path, 'wb') as fh:
                fh.write(data)

        Window.begin_drag_files([DragFileItem('readme.txt', False, callback)])


if __name__ == '__main__':
    DragExportApp().run()
