'''
Settings
========

.. versionadded:: 1.0.7

This module is a complete and extensible set for building Settings interface.
The interface is divided in 2: a sidebar containing a list of panels on the
left, and the selected panel on the right.

.. image:: images/settings_kivy.jpg
    :align: center

A :class:`SettingsPanel` is designed to control a
:class:`~kivy.config.ConfigParser` instance. The panel can be automatically
contructed from a JSON definitions files: you put the settings you want with a
title, description, type, section/key in the config parser... and that's done !

The settings are also integrated with the :class:`~kivy.app.App` class, if a key
is pressed, it will show your app settings on the screen, including the Kivy
settings.


.. _settings_json:

Create panel from JSON
----------------------

To create a panel, you need 2 things:

    * a :class:`~kivy.config.ConfigParser` instance with default values
    * a JSON file

.. warning::

    The ConfigParser required came from the :class:`kivy.config.ConfigParser`,
    not the default ConfigParser from Python libraries.

This is your duty to create and handle the :class:`~kivy.config.ConfigParser`
yourself. The panel will read the values from the ConfigParser instance, ensure
you have default values for every section / key in your JSON file !

The JSON settings file is a list containing dictionnaries with informations in
it. It can look like this::

    [
        {
            "type": "title",
            "title": "Windows"
        },
        {
            "type": "bool",
            "title": "Fullscreen",
            "desc": "Set the window in windowed or fullscreen",
            "section": "graphics",
            "key": "fullscreen",
            "true": "auto"
        }
    ]

Each element in the root list represent a line on the Panel. Only the "type" is
mandatory: this will create a custom instance of a settings "type" class,
previously registered, and all the others keys are the properties of that "type"
class:

    ============== =================================================
     Type           Associated class
    -------------- -------------------------------------------------
    title          :class:`SettingTitle`
    bool           :class:`SettingBoolean`
    numeric        :class:`SettingNumeric`
    options        :class:`SettingOptions`
    string         :class:`SettingString`
    ============== =================================================

That's mean, the first element is a type "title": it will create an instance of
:class:`SettingTitle`, then all the others key/value are used to set properties
inside that instance. The "title": "Windows" will set :data:`SettingTitle.title`
to "Windows".

Here is an example about how to use the previous JSON::

    from kivy.config import ConfigParser

    config = ConfigParser()
    config.read('myconfig.ini')

    s = Settings()
    s.add_json_panel('My custom panel', config, 'settings_custom.json')
    s.add_json_panel('Another panel', config, 'settings_test2.json')

    # then use the s as a widget...



'''

__all__ = ('Settings', 'SettingsPanel',
           'SettingItem', 'SettingBoolean', 'SettingNumeric',
           'SettingOptions')

import json
from kivy.config import ConfigParser
from kivy.animation import Animation
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, StringProperty, ListProperty, \
        BooleanProperty, NumericProperty


class SettingSpacer(Widget):
    # Internal class, not documented.
    pass


class SettingSidebarLabel(Label):
    # Internal class, not documented.

    panel = ObjectProperty(None)

    selected = BooleanProperty(False)

    panel_uid = NumericProperty(-1)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return
        panel = self.panel
        if not self.panel:
            return
        panel = panel.get_panel_by_uid(self.panel_uid)
        if not panel:
            return
        self.panel.select(panel)


class SettingItem(FloatLayout):
    '''Represent the most common item in the setting panel. It cannot be used
    directly, but you can implement a new type using it. This will build a line
    with a title and description on the left, and the setting on the right.

    Take a look at :class:`SettingBoolean`, :class:`SettingNumeric` and
    :class:`SettingOptions` as an example.

    :Events:
        `on_release`
            Fired when the item is touched then released
    '''

    title = StringProperty('<No title set>')
    '''Title of the item, default to '<No title set>'.

    :data:`title` is a :class:`~kivy.properties.StringProperty`, default to
    '<No title set>'.
    '''

    desc = StringProperty(None, allownone=True)
    '''Description of the item, that will be showed on the second line.

    :data:`desc` is a :class:`~kivy.properties.StringProperty`, default to None.
    '''

    disabled = BooleanProperty(False)
    '''Indicate if the setting is disabled or not. If it's disabled, any touch
    on the item will be discarded.

    :data:`disabled` is a :class:`~kivy.properties.BooleanProperty`, default to
    False.
    '''

    section = StringProperty(None)
    '''Section of the token inside the :class:`~kivy.config.ConfigParser`
    instance.

    :data:`section` is a :class:`~kivy.properties.StringProperty`, default to
    None.
    '''

    key = StringProperty(None)
    '''Key of the token inside the :data:`section` in the
    :class:`~kivy.config.ConfigParser` instance.

    :data:`key` is a :class:`~kivy.properties.StringProperty`, default to None.
    '''

    value = ObjectProperty(None)
    '''Value of the token, according to the :class:`~kivy.config.ConfigParser`
    instance. Any change to the value will trigger a
    :meth:`Settings.on_config_change` event.

    :data:`value` is a :class:`~kivy.properties.ObjectProperty`, default to
    None.
    '''

    panel = ObjectProperty(None)
    '''(internal) Reference to the panel that include the setting. You don't
    need to use it.

    :data:`panel` is a :class:`~kivy.properties.ObjectProperty`, default to None
    '''

    content = ObjectProperty(None)
    '''(internal) Reference to the widget that will contain the real setting.
    As soon as the content object is set, any further call to add_widget will
    call the content.add_widget. This is automatically set.

    :data:`content` is a :class:`~kivy.properties.ObjectProperty`, default to
    None.
    '''

    selected_alpha = NumericProperty(0)
    '''(internal) Numeric value from 0 to 1 used to animate the background when
    the user will touch the item.

    :data:`selected_alpha` is a :class:`~kivy.properties.NumericProperty`,
    default to 0.
    '''

    def __init__(self, **kwargs):
        self.register_event_type('on_release')
        super(SettingItem, self).__init__(**kwargs)
        self.value = self.panel.get_value(self.section, self.key)

    def add_widget(self, *largs):
        if self.content is None:
            return super(SettingItem, self).add_widget(*largs)
        return self.content.add_widget(*largs)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return
        if self.disabled:
            return
        touch.grab(self)
        self.selected_alpha = 1
        return super(SettingItem, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self.dispatch('on_release')
            Animation(selected_alpha=0, d=.25, t='out_quad').start(self)
            return True
        return super(SettingItem, self).on_touch_up(touch)

    def on_release(self):
        pass

    def on_value(self, instance, value):
        if not self.section or not self.key:
            return
        # get current value in config
        panel = self.panel
        panel.set_value(self.section, self.key, str(value))


class SettingBoolean(SettingItem):
    '''Implementation of a boolean setting in top of :class:`SettingItem`. It's
    represented with a :class:`~kivy.uix.switch.Switch`. You have the
    possibility to change the boolean value to another with the :data:`values`.
    '''

    values = ListProperty(['0', '1'])
    '''Values used when the setting is activated or not. If you prefer a setting
    that write "yes" and "no" on in the ConfigParser instance, you can do::

        SettingBoolean(..., values=['no', 'yes'])

    .. warning::

        You need a minimum of 2 values, the index 0 will be used as False, and
        index 1 as True

    :data:`values` is a :class:`~kivy.properties.ListProperty`, default to ['0',
    '1']
    '''


class SettingString(SettingItem):
    '''Implementation of a string setting in top of :class:`SettingItem`.
    The string setting is showed in a Label, but when you click on it, a Popup
    window will open with a textinput, available to set a custom value.
    '''

    popup = ObjectProperty(None, allownone=True)
    '''(internal) Used to store the current popup when it's showed

    :data:`popup` is a :class:`~kivy.properties.ObjectProperty`, default to
    None.
    '''

    textinput = ObjectProperty(None)
    '''(internal) Used to store the current textinput from the popup, and listen
    for any changes.

    :data:`popup` is a :class:`~kivy.properties.ObjectProperty`, default to
    None.
    '''

    def on_panel(self, instance, value):
        if value is None:
            return
        self.bind(on_release=self._create_popup)

    def _validate(self, instance):
        self.popup.dismiss()
        self.popup = None
        value = self.textinput.text.strip()
        if value == '':
            return
        self.value = value

    def _create_popup(self, instance):
        # create popup layout
        content = BoxLayout(orientation='vertical', spacing=5)
        self.popup = popup = Popup(title=self.title,
            content=content, size_hint=(None, None), size=(400, 250))

        # create the textinput used for numeric input
        self.textinput = textinput = TextInput(text=str(self.value),
            font_size=24, multiline=False, size_hint_y=None, height=50)
        textinput.bind(on_text_validate=self._validate)
        self.textinput = textinput

        # construct the content, widget are used as a spacer
        content.add_widget(Widget())
        content.add_widget(textinput)
        content.add_widget(Widget())
        content.add_widget(SettingSpacer())

        # 2 buttons are created for accept or cancel the current value
        btnlayout = BoxLayout(size_hint_y=None, height=50, spacing=5)
        btn = Button(text='Ok')
        btn.bind(on_release=self._validate)
        btnlayout.add_widget(btn)
        btn = Button(text='Cancel')
        btn.bind(on_release=popup.dismiss)
        btnlayout.add_widget(btn)
        content.add_widget(btnlayout)

        # all done, open the popup !
        popup.open()


class SettingNumeric(SettingString):
    '''Implementation of a numeric setting in top of :class:`SettingString`.
    The numeric setting is showed in a Label, but when you click on it, a Popup
    window will open with a textinput, available to set a custom value.
    '''

    def _validate(self, instance):
        self.popup.dismiss()
        self.popup = None
        try:
            value = int(self.textinput.text)
        except ValueError:
            return
        self.value = value


class SettingOptions(SettingItem):
    '''Implementation of an option list in top of :class:`SettingItem`.
    A label is used on the setting to show the current choice, and when you
    touch on it, a Popup will open with all the options displayed in list.
    '''

    options = ListProperty([])
    '''List of all availables options. This must be a list of "string",
    otherwise, it will crash :)

    :data:`options` is a :class:`~kivy.properties.ListProperty`, default to []
    '''

    popup = ObjectProperty(None, allownone=True)
    '''(internal) Used to store the current popup when it's showed

    :data:`popup` is a :class:`~kivy.properties.ObjectProperty`, default to
    None.
    '''

    def on_panel(self, instance, value):
        if value is None:
            return
        self.bind(on_release=self._create_popup)

    def _set_option(self, instance):
        self.value = instance.text
        self.popup.dismiss()

    def _create_popup(self, instance):
        # create the popup
        content = BoxLayout(orientation='vertical', spacing=5)
        self.popup = popup = Popup(content=content,
            title=self.title, size_hint=(None, None), size=(400, 400))
        popup.height = len(self.options) * 55 + 150

        # add all the options
        content.add_widget(Widget(size_hint_y=None, height=1))
        uid = str(self.uid)
        for option in self.options:
            state = 'down' if option == self.value else 'normal'
            btn = ToggleButton(text=option, state=state, group=uid)
            btn.bind(on_release=self._set_option)
            content.add_widget(btn)

        # finally, add a cancel button to return on the previous panel
        content.add_widget(SettingSpacer())
        btn = Button(text='Cancel', size_hint_y=None, height=50)
        btn.bind(on_release=popup.dismiss)
        content.add_widget(btn)

        # and open the popup !
        popup.open()


class SettingTitle(Label):
    '''A simple title label, used to seperate the panels line into sections.
    '''

    title = Label.text


class SettingsPanel(GridLayout):
    '''This class is used to contruct panel settings, and it's intended to be
    used inside a :class:`Settings` class.
    '''

    title = StringProperty('Default title')
    '''Title of the panel. The title will be reused by the :class:`Settings` in
    the sidebar.
    '''

    config = ObjectProperty(None, allownone=True)
    '''Instance to a :class:`kivy.config.ConfigParser` object.
    '''

    settings = ObjectProperty(None)
    '''Instance to a :class:`Settings` object, that will be used to fire the
    `on_config_change` event.
    '''

    def __init__(self, **kwargs):
        kwargs.setdefault('cols', 1)
        super(SettingsPanel, self).__init__(**kwargs)

    def on_config(self, instance, value):
        if value is None:
            return
        if not isinstance(value, ConfigParser):
            raise Exception('Invalid config object, you must use a'
                            'kivy.config.ConfigParser, not another one !')

    def get_value(self, section, key):
        '''Return the value of the section/key from the :data:`config`
        ConfigParser instance. This function is used by :class:`SettingItem` to
        get their value from their section/key.

        If you don't want to use a ConfigParser instance, you might want to
        derivate this function.
        '''
        config = self.config
        if not config:
            return
        return config.get(section, key)

    def set_value(self, section, key, value):
        current = self.get_value(section, key)
        if current == value:
            return
        config = self.config
        if config:
            config.set(section, key, value)
            config.write()
        settings = self.settings
        if settings:
            settings.dispatch('on_config_change',
                              config, section, key, value)


class Settings(BoxLayout):
    '''Settings UI. Check documentation for more information about the usage of
    this class.

    :Events:
        `on_config_change`: ConfigParser instance, section, key, value
            Fired when a section/key/value of a ConfigParser have changed
        `on_close`
            Fired when the button Close have been hit.
    '''

    selection = ObjectProperty(None, allownone=True)
    '''(internal) Reference the current selected label in the sidebar.

    :data:`selection` is a :class:`~kivy.properties.ObjectProperty`, default to
    None.
    '''

    content = ObjectProperty(None)
    '''(internal) Reference to the widget that will contain the panel widget.

    :data:`content` is a :class:`~kivy.properties.ObjectProperty`, default to
    None.
    '''

    menu = ObjectProperty(None)
    '''(internal) Reference to the widget that will contain the sidebar menu.

    :data:`menu` is a :class:`~kivy.properties.ObjectProperty`, default to
    None.
    '''

    def __init__(self, **kwargs):
        self._types = {}
        self._panels = {}
        self._initialized = False
        self.register_event_type('on_close')
        self.register_event_type('on_config_change')
        super(Settings, self).__init__(**kwargs)
        self.register_type('string', SettingString)
        self.register_type('bool', SettingBoolean)
        self.register_type('numeric', SettingNumeric)
        self.register_type('options', SettingOptions)
        self.register_type('title', SettingTitle)

    def on_menu(self, instance, value):
        if value and self.content:
            self._initialized = True

    def on_content(self, instance, value):
        if value and self.menu:
            self._initialized = True

    def on_close(self):
        pass

    def on_config_change(self, config, section, key, value):
        pass

    def register_type(self, tp, cls):
        '''Register a new type that can be used in the json definition.
        '''
        self._types[tp] = cls

    def add_json_panel(self, title, config, filename=None, data=None):
        '''Create and add a new :class:`SettingsPanel` using the configuration
        `config`, with the JSON definition `filename`.

        Check the :ref:`settings_json` section in the documentation for more
        information about JSON format, and the usage of this function.
        '''
        if filename is None and data is None:
            raise Exception('You must specify at least on of filename or data')
        if filename is not None:
            with open(filename, 'r') as fd:
                data = json.loads(fd.read())
        else:
            data = json.loads(data)
        if type(data) != list:
            raise ValueError('The first element must be a list')
        panel = SettingsPanel(title=title, settings=self, config=config)
        self.add_widget(panel)

        for setting in data:
            # determine the type and the class to use
            if not 'type' in setting:
                raise ValueError('One setting are missing the "type" element')
            ttype = setting['type']
            cls = self._types.get(ttype)
            if cls is None:
                raise ValueError('No class registered to handle the <%s> type' %
                                 setting['type'])

            # create a instance of the class, without the type attribute
            del setting['type']
            instance = cls(panel=panel, **setting)

            # instance created, add to the panel
            panel.add_widget(instance)

        return panel

    def add_kivy_panel(self):
        '''Add a panel for configuring Kivy. This panel act directly on the kivy
        configuration. Feel free to include or exclude it in your configuration.
        '''
        from kivy import kivy_data_dir
        from kivy.config import Config
        from os.path import join
        panel = self.add_json_panel('Kivy', Config,
            join(kivy_data_dir, 'settings_kivy.json'))

    def add_widget(self, widget, index=0):
        if self._initialized:
            assert(isinstance(widget, SettingsPanel))
            uid = widget.uid
            label = SettingSidebarLabel(text=widget.title, panel=self,
                                     panel_uid=uid)
            self.menu.add_widget(label)
            self._panels[uid] = (widget, label)
            # select the first panel
            if not self.selection:
                self.select(widget)
        else:
            return super(Settings, self).add_widget(widget, index)

    def get_panel_by_uid(self, uid):
        '''Return the panel previously added from his UID. If it's not exist,
        return None.
        '''
        if uid not in self._panels:
            return
        return self._panels[uid][0]

    def unselect(self):
        '''Unselect the current selection if exist.
        '''
        if not self.selection:
            return
        self.content.clear_widgets()
        self.selection.selected = False
        self.selection = None

    def select(self, panel):
        '''Select a panel previously added on the widget.
        '''
        # search the panel on the list
        found = False
        for idx, (wid, label) in self._panels.iteritems():
            if panel is wid:
                found = True
                break
        if not found:
            return
        # found a panel, use it.
        if self.selection:
            self.unselect()
        self.selection = label
        self.selection.selected = True
        self.content.add_widget(panel)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            super(Settings, self).on_touch_down(touch)
            return True

if __name__ == '__main__':
    from kivy.app import App

    class SettingsApp(App):

        def build(self):
            s = Settings()
            s.add_kivy_panel()
            s.bind(on_close=self.stop)
            return s

    SettingsApp().run()


