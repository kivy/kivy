'''
Settings
========

.. versionadded:: 1.0.7

This module is a complete and extensible framework for building a Settings
interface in your application. The interface consists of a sidebar with a list
of panels (on the left) and the selected panel (right).

.. image:: images/settings_kivy.jpg
    :align: center

:class:`SettingsPanel` represents a group of configurable options. The
:data:`SettingsPanel.title` property is used by :class:`Settings` when a panel
is added - it determines the name of the sidebar button. SettingsPanel controls
a :class:`~kivy.config.ConfigParser` instance.

The panel can be automatically constructed from a JSON definition file: you
describe the settings you want and corresponding sections/keys in the
ConfigParser instance... and you're done!

Settings are also integrated with the :class:`~kivy.app.App` class. Use
:func:`Settings.add_kivy_panel` to configure the Kivy core settings in a panel.


.. _settings_json:

Create panel from JSON
----------------------

To create a panel from a JSON-file, you need 2 things:

    * a :class:`~kivy.config.ConfigParser` instance with default values
    * a JSON file

.. warning::

    The :class:`kivy.config.ConfigParser` is required, you cannot use the
    default ConfigParser from Python libraries.

It is your duty to create and handle the :class:`~kivy.config.ConfigParser`
object yourself. SettingsPanel will read the values from the associated
ConfigParser instance. Make sure you have default values for all sections/keys
in your JSON file!

The JSON file contains structured information to describe the available
settings. It can look like this::

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

Each element in the root list represents a setting that the user can configure.
Only the "type" key is mandatory: an instance of the associated class will be
created and used for the setting - other keys are assigned to corresponding
properties of that class.

    ============== =================================================
     Type           Associated class
    -------------- -------------------------------------------------
    title          :class:`SettingTitle`
    bool           :class:`SettingBoolean`
    numeric        :class:`SettingNumeric`
    options        :class:`SettingOptions`
    string         :class:`SettingString`
    path           :class:`SettingPath` (new from 1.1.0)
    ============== =================================================

In the JSON example above, the first element is of type "title". It will create
a new instance of :class:`SettingTitle` and apply the rest of the key/value
pairs to the properties of that class, ie "title": "Windows" sets the
:data:`SettingTitle.title` property to "Windows".

To load the JSON example to a :class:`Settings` instance, use the
:data:`Settings.add_json_panel` method. It will automatically instantiate
:class:`SettingsPanel` and add it to :class:`Settings`::

    from kivy.config import ConfigParser

    config = ConfigParser()
    config.read('myconfig.ini')

    s = Settings()
    s.add_json_panel('My custom panel', config, 'settings_custom.json')
    s.add_json_panel('Another panel', config, 'settings_test2.json')

    # then use the s as a widget...



'''

__all__ = ('Settings', 'SettingsPanel', 'SettingItem', 'SettingString',
           'SettingPath', 'SettingBoolean', 'SettingNumeric',
           'SettingOptions')

import json
import os
from kivy.config import ConfigParser
from kivy.animation import Animation
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
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
    '''Base class for individual settings (within a panel). This class cannot
    be used directly; it is used for implementing the other setting classes.
    It builds a row with title/description (left) and setting control (right).

    Look at :class:`SettingBoolean`, :class:`SettingNumeric` and
    :class:`SettingOptions` for usage example.

    :Events:
        `on_release`
            Fired when the item is touched then released

    '''

    title = StringProperty('<No title set>')
    '''Title of the setting, default to '<No title set>'.

    :data:`title` is a :class:`~kivy.properties.StringProperty`, default to
    '<No title set>'.
    '''

    desc = StringProperty(None, allownone=True)
    '''Description of the setting, rendered on the line below title.

    :data:`desc` is a :class:`~kivy.properties.StringProperty`, default to None.
    '''

    disabled = BooleanProperty(False)
    '''Indicate if this setting is disabled. If True, all touches on the setting
    item will be discarded.

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
    '''(internal) Reference to the SettingsPanel with this setting. You don't
    need to use it.

    :data:`panel` is a :class:`~kivy.properties.ObjectProperty`, default to None
    '''

    content = ObjectProperty(None)
    '''(internal) Reference to the widget that contains the real setting.
    As soon as the content object is set, any further call to add_widget will
    call the content.add_widget. This is automatically set.

    :data:`content` is a :class:`~kivy.properties.ObjectProperty`, default to
    None.
    '''

    selected_alpha = NumericProperty(0)
    '''(internal) Float value from 0 to 1, used to animate the background when
    the user touches the item.

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
    '''Implementation of a boolean setting on top of :class:`SettingItem`. It's
    visualized with a :class:`~kivy.uix.switch.Switch` widget. By default,
    0 and 1 are used for values, you can change them by setting :data:`values`.
    '''

    values = ListProperty(['0', '1'])
    '''Values used to represent the state of the setting. If you use "yes" and
    "no" in your ConfigParser instance::

        SettingBoolean(..., values=['no', 'yes'])

    .. warning::

        You need a minimum of 2 values, the index 0 will be used as False, and
        index 1 as True

    :data:`values` is a :class:`~kivy.properties.ListProperty`, default to ['0',
    '1']
    '''


class SettingString(SettingItem):
    '''Implementation of a string setting on top of :class:`SettingItem`.
    It's visualized with a :class:`~kivy.uix.label.Label` widget that, when
    clicked, will open a :class:`~kivy.uix.popup.Popup` with a
    :class:`~kivy.uix.textinput.Textinput` so the user can enter a custom value.
    '''

    popup = ObjectProperty(None, allownone=True)
    '''(internal) Used to store the current popup when it's shown

    :data:`popup` is a :class:`~kivy.properties.ObjectProperty`, default to
    None.
    '''

    textinput = ObjectProperty(None)
    '''(internal) Used to store the current textinput from the popup, and listen
    for changes.

    :data:`popup` is a :class:`~kivy.properties.ObjectProperty`, default to
    None.
    '''

    def on_panel(self, instance, value):
        if value is None:
            return
        self.bind(on_release=self._create_popup)

    def _dismiss(self, *largs):
        if self.textinput:
            self.textinput.focus = False
        if self.popup:
            self.popup.dismiss()
        self.popup = None

    def _validate(self, instance):
        self._dismiss()
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
        btn.bind(on_release=self._dismiss)
        btnlayout.add_widget(btn)
        content.add_widget(btnlayout)

        # all done, open the popup !
        popup.open()


class SettingPath(SettingItem):
    '''Implementation of a Path setting on top of :class:`SettingItem`.
    It's visualized with a :class:`~kivy.uix.label.Label` widget that, when
    clicked, will open a :class:`~kivy.uix.popup.Popup` with a
    :class:`~kivy.uix.filechooser.FileChooserListView` so the user can enter
    a custom value.

    .. versionadded:: 1.1.0
    '''

    popup = ObjectProperty(None, allownone=True)
    '''(internal) Used to store the current popup when it's shown

    :data:`popup` is a :class:`~kivy.properties.ObjectProperty`, default to
    None.
    '''

    textinput = ObjectProperty(None)
    '''(internal) Used to store the current textinput from the popup, and listen
    for changes.

    :data:`popup` is a :class:`~kivy.properties.ObjectProperty`, default to
    None.
    '''

    def on_panel(self, instance, value):
        if value is None:
            return
        self.bind(on_release=self._create_popup)

    def _dismiss(self, *largs):
        if self.textinput:
            self.textinput.focus = False
        if self.popup:
            self.popup.dismiss()
        self.popup = None

    def _validate(self, instance):
        self._dismiss()
        value = self.textinput.selection

        if not value:
            return

        self.value = os.path.realpath(value[0])

    def _create_popup(self, instance):
        # create popup layout
        content = BoxLayout(orientation='vertical', spacing=5)
        self.popup = popup = Popup(title=self.title,
            content=content, size_hint=(None, None), size=(400, 400))

        # create the filechooser
        self.textinput = textinput = FileChooserListView(path=str(self.value),
                                                         size_hint=(1, 1),
                                                         dirselect=True)
        textinput.bind(on_path=self._validate)
        self.textinput = textinput

        # construct the content
        content.add_widget(textinput)
        content.add_widget(SettingSpacer())

        # 2 buttons are created for accept or cancel the current value
        btnlayout = BoxLayout(size_hint_y=None, height=50, spacing=5)
        btn = Button(text='Ok')
        btn.bind(on_release=self._validate)
        btnlayout.add_widget(btn)
        btn = Button(text='Cancel')
        btn.bind(on_release=self._dismiss)
        btnlayout.add_widget(btn)
        content.add_widget(btnlayout)

        # all done, open the popup !
        popup.open()


class SettingNumeric(SettingString):
    '''Implementation of a numeric setting on top of :class:`SettingString`.
    It's visualized with a :class:`~kivy.uix.label.Label` widget that, when
    clicked, will open a :class:`~kivy.uix.popup.Popup` with a
    :class:`~kivy.uix.textinput.Textinput` so the user can enter a custom value.
    '''

    def _validate(self, instance):
        self._dismiss()
        try:
            self.value = int(self.textinput.text)
        except ValueError:
            return


class SettingOptions(SettingItem):
    '''Implementation of an option list on top of :class:`SettingItem`.
    It's visualized with a :class:`~kivy.uix.label.Label` widget that, when
    clicked, will open a :class:`~kivy.uix.popup.Popup` with a
    list of options that the user can select from.
    '''

    options = ListProperty([])
    '''List of all availables options. This must be a list of "string",
    otherwise, it will crash :)

    :data:`options` is a :class:`~kivy.properties.ListProperty`, default to []
    '''

    popup = ObjectProperty(None, allownone=True)
    '''(internal) Used to store the current popup when it's shown

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
    '''A simple title label, used to organize the settings in sections.
    '''

    title = Label.text


class SettingsPanel(GridLayout):
    '''This class is used to contruct panel settings, for use with a
    :class:`Settings` instance or subclass.
    '''

    title = StringProperty('Default title')
    '''Title of the panel. The title will be reused by the :class:`Settings` in
    the sidebar.
    '''

    config = ObjectProperty(None, allownone=True)
    '''A :class:`kivy.config.ConfigParser` instance. See module documentation
    for more information.
    '''

    settings = ObjectProperty(None)
    '''A :class:`Settings` instance that will be used to fire the
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
        get the value for a given section/key.

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
    '''Settings UI. Check module documentation for more information on how to
    use this class.

    :Events:
        `on_config_change`: ConfigParser instance, section, key, value
            Fired when section/key/value of a ConfigParser changes
        `on_close`
            Fired when the Close-button is pressed.
    '''

    selection = ObjectProperty(None, allownone=True)
    '''(internal) Reference to the selected label in the sidebar.

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
        self.register_type('path', SettingPath)

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
            str_settings = {}
            for key, item in setting.iteritems():
                str_settings[str(key)] = item

            instance = cls(panel=panel, **str_settings)

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
        self.add_json_panel('Kivy', Config,
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

