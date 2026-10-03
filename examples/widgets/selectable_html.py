"""
Selectable HTML widget demo.

Run with:

    python selectable_html.py
"""

from kivy.app import App
from kivy.core.clipboard import Clipboard
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

from kivy.uix.selectable_html import SelectableHtmlLabel, open_external_link

SAMPLE_HTML = """
<div dir="auto">
  <h3>Selectable HTML</h3>
  <p>
    This widget renders HTML and keeps <b>text selection</b> in a readonly body.
    Visit <a href="https://kivy.org/doc/stable/">Kivy documentation</a>.
  </p>
  <p>
    Relative links are resolved with a base url:
    <a href="/guide">open relative guide</a>.
  </p>
</div>
"""


class SelectableHtmlDemo(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=dp(8), padding=dp(10), **kwargs)

        toolbar = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        copy_btn = Button(text='Copy selection')
        clear_btn = Button(text='Clear selection')
        copy_btn.bind(on_release=lambda *_: self.copy_selection())
        clear_btn.bind(on_release=lambda *_: self.clear_selection())
        toolbar.add_widget(copy_btn)
        toolbar.add_widget(clear_btn)
        self.add_widget(toolbar)

        self.html_widget = SelectableHtmlLabel(
            raw_html=SAMPLE_HTML,
            base_url='https://kivy.org',
            auto_open_links=False,
            size_hint_y=None,
            padding=[dp(4), dp(8), dp(4), dp(8)],
        )
        self.html_widget.bind(on_link_press=self.on_link_press)
        self.html_widget.bind(content_height=lambda *_: self.sync_height())

        content = BoxLayout(orientation='vertical', size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        content.add_widget(self.html_widget)

        scroller = ScrollView(do_scroll_x=False, bar_width=dp(4))
        scroller.add_widget(content)
        self.add_widget(scroller)

        self.status = Label(size_hint_y=None, height=dp(28), halign='left', valign='middle')
        self.status.bind(size=lambda *_: setattr(self.status, 'text_size', self.status.size))
        self.add_widget(self.status)

        self.sync_height()
        self.set_status('Long-press text to select. Click links to open.')

    def sync_height(self):
        self.html_widget.height = max(dp(320), float(self.html_widget.content_height) + dp(16))

    def set_status(self, value):
        self.status.text = str(value or '')

    def on_link_press(self, _instance, raw_url):
        opened, copied, resolved = open_external_link(
            raw_url,
            base_url=str(self.html_widget.base_url or ''),
            copy_on_failure=True,
        )
        self.html_widget.last_link_url = str(resolved or '')
        if opened:
            self.set_status('Opened link: {}'.format(resolved))
        elif copied:
            self.set_status('Copied link: {}'.format(resolved))
        else:
            self.set_status('Could not open link.')

    def copy_selection(self):
        selected = str(getattr(self.html_widget, 'selection_text', '') or '').strip()
        if selected:
            self.html_widget.copy(selected)
            self.set_status('Copied selected text.')
            return

        link_value = str(getattr(self.html_widget, 'last_link_url', '') or '').strip()
        if link_value:
            Clipboard.copy(link_value)
            self.set_status('Copied last clicked link.')
            return

        self.set_status('Nothing selected.')

    def clear_selection(self):
        clear_fn = getattr(self.html_widget, 'clear_selection_handles', None)
        if callable(clear_fn):
            clear_fn()
        self.set_status('Selection cleared.')


class SelectableHtmlApp(App):
    def build(self):
        return SelectableHtmlDemo()


if __name__ == '__main__':
    SelectableHtmlApp().run()
