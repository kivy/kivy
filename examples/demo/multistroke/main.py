#!/usr/bin/env python
# First Kivy app; second python app.. it's a mess.
from kivy.app import App
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.lang import Builder

# Local libraries
import touchanalyzer as TA
from touchanalyzer import TouchAnalyzer
from samplehistory import HistoryBrowser
from gesturebrowser import GestureBrowser
from appoptions import AppOptions

# Size hint for the MainMenu widget (others are scaled accordingly)
MENU_SIZE_HINT = .07

Builder.load_string('''
#:set menu_size_hint %f

<MainMenu>:
    rows: 1
    size_hint: (1, menu_size_hint)
    spacing: 5
    padding: 5
''' % (MENU_SIZE_HINT))


# Main menu - positioned at bottom of screen
# This entire app is an experiment, I'm sure there are better ways ^^

class MainMenu(GridLayout):
    '''MainMenu provides a simple horizontal list of buttons and emit an event
    when a new one is selected.'''
    def __init__(self, **kwargs):
        super(MainMenu, self).__init__(**kwargs)

        self.active = None
        self.add_widget(self._button(text='Sample', default=True))
        self.add_widget(self._button(text='Review'))
        self.add_widget(self._button(text='Gestures'))
        self.add_widget(self._button(text='Options'))
        self.register_event_type('on_mode_change')

    def menu_press(self, btn):
        if btn != self.active:
            self.active = btn
            self.dispatch('on_mode_change', btn.text)

    def on_mode_change(*l):
        pass

    def _button(self, **kwargs):
        kwargs.setdefault('group', 'mainmenu')
        kwargs.setdefault('size_hint', (.25, 1))
        r = ToggleButton(**kwargs)
        r.bind(on_press=self.menu_press)
        if kwargs.get('default', False):
            r.state = 'down'
            self.active = r
        return r


class MultistrokeApp(App):
    def build(self):

        # Analyzer is the drawing surface in 'Sample' mode
        self.analyzer = TouchAnalyzer(size_hint=(1, 1 - MENU_SIZE_HINT))

        # Hbrowser is the list of samples
        self.hbrowser = HistoryBrowser(self.analyzer,
            size_hint=(1, 1 - MENU_SIZE_HINT))

        # Make sure we add gestures to history as they are purged
        self.analyzer.bind(on_gesture_purge=self.hbrowser._load_history)

        # Gbrowser is the list of gesture templates
        self.gbrowser = GestureBrowser(self.analyzer.gdb,
            size_hint=(1, 1 - MENU_SIZE_HINT))

        self.options = AppOptions(size_hint=(None, 1 - MENU_SIZE_HINT))

        # Set up the main menu
        self.menu = MainMenu()
        self.menu.bind(on_mode_change=self.set_app_mode)

        # Now set up a gridlayout and return it
        self.app = GridLayout(cols=1)
        self.set_app_mode(None, 'Sample')
        return self.app

    def set_app_mode(self, menu, mode):
        self.app.clear_widgets()
        if mode == 'Sample':
            self.app.add_widget(self.analyzer)
        elif mode == 'Review':
            self.app.add_widget(self.hbrowser)
        elif mode == 'Gestures':
            self.gbrowser.import_gdb()
            self.app.add_widget(self.gbrowser)
        elif mode == 'Options':
            self.app.add_widget(self.options)
        self.app.add_widget(self.menu)

if __name__ in ('__main__', '__android__'):
    MultistrokeApp().run()
