from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.settings import (SettingsWithSidebar,
                               SettingsWithSpinner,
                               SettingsWithTabbedPanel)
from kivy.properties import OptionProperty, ObjectProperty


class SettingsApp(App):

    display_type = OptionProperty('normal', options=['normal', 'popup'])

    settings_popup = ObjectProperty(None, allownone=True)

    def build(self):

        paneltype = Label(text='What kind of settings panel to use?')

        sidebar_button = Button(text='Sidebar')
        sidebar_button.bind(on_press=lambda j: self.set_settings_cls(
            SettingsWithSidebar))
        spinner_button = Button(text='Spinner')
        spinner_button.bind(on_press=lambda j: self.set_settings_cls(
            SettingsWithSpinner))
        tabbed_button = Button(text='TabbedPanel')
        tabbed_button.bind(on_press=lambda j: self.set_settings_cls(
            SettingsWithTabbedPanel))

        buttons = BoxLayout(orientation='horizontal')
        buttons.add_widget(sidebar_button)
        buttons.add_widget(spinner_button)
        buttons.add_widget(tabbed_button)

        displaytype = Label(text='How to display the settings?')
        display_buttons = BoxLayout(orientation='horizontal')
        onwin_button = Button(text='on window')
        onwin_button.bind(on_press=lambda j: self.set_display_type('normal'))
        popup_button = Button(text='in a popup')
        popup_button.bind(on_press=lambda j: self.set_display_type('popup'))
        display_buttons.add_widget(onwin_button)
        display_buttons.add_widget(popup_button)

        instruction = Label(text='Click to open the settings panel:')
        settings_button = Button(text='Open settings')
        settings_button.bind(on_press=self.open_settings)

        layout = BoxLayout(orientation='vertical')
        layout.add_widget(paneltype)
        layout.add_widget(buttons)
        layout.add_widget(displaytype)
        layout.add_widget(display_buttons)
        layout.add_widget(instruction)
        layout.add_widget(settings_button)

        return layout

    def on_settings_cls(self, *args):
        self.destroy_settings()

    def set_settings_cls(self, panel_type):
        self.settings_cls = panel_type

    def set_display_type(self, display_type):
        self.destroy_settings()
        self.display_type = display_type

    def display_settings(self, settings):
        if self.display_type == 'popup':
            p = self.settings_popup
            if p is None:
                self.settings_popup = p = Popup(content=settings,
                                                title='Settings',
                                                size_hint=(0.8, 0.8))
            if p.content is not settings:
                p.content = settings
            p.open()
        else:
            super(SettingsApp, self).display_settings(settings)

    def close_settings(self, *args):
        if self.display_type == 'popup':
            p = self.settings_popup
            if p is not None:
                p.dismiss()
        else:
            super(SettingsApp, self).close_settings()


if __name__ == '__main__':
    SettingsApp().run()
