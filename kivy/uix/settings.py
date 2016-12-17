'''
Settings
========

.. versionadded:: 1.0.7

This module provides a complete and extensible framework for adding a
Settings interface to your application. By default, the interface uses
a :class:`SettingsWithSpinner`, which consists of a
:class:`~kivy.uix.spinner.Spinner` (top) to switch between individual
settings panels (bottom). See :ref:`differentlayouts` for some
alternatives.

.. image:: images/settingswithspinner_kivy.jpg
    :align: center

A :class:`SettingsPanel` represents a group of configurable options. The
:attr:`SettingsPanel.title` property is used by :class:`Settings` when a panel
is added: it determines the name of the sidebar button. SettingsPanel controls
a :class:`~kivy.config.ConfigParser` instance.

The panel can be automatically constructed from a JSON definition file: you
describe the settings you want and corresponding sections/keys in the
ConfigParser instance... and you're done!

Settings are also integrated into the :class:`~kivy.app.App` class. Use
:meth:`Settings.add_kivy_panel` to configure the Kivy core settings in a panel.


.. _settings_json:

Create a panel from JSON
------------------------

To create a panel from a JSON-file, you need two things:

    * a :class:`~kivy.config.ConfigParser` instance with default values
    * a JSON file

.. warning::

    The :class:`kivy.config.ConfigParser` is required. You cannot use the
    default ConfigParser from Python libraries.

You must create and handle the :class:`~kivy.config.ConfigParser`
object. SettingsPanel will read the values from the associated
ConfigParser instance. Make sure you have set default values (using
:attr:`~kivy.config.ConfigParser.setdefaults`) for all the sections/keys
in your JSON file!

The JSON file contains structured information to describe the available
settings. Here is an example::

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
    path           :class:`SettingPath`
    ============== =================================================

    .. versionadded:: 1.1.0
        Added :attr:`SettingPath` type

In the JSON example above, the first element is of type "title". It will create
a new instance of :class:`SettingTitle` and apply the rest of the key-value
pairs to the properties of that class, i.e. "title": "Windows" sets the
:attr:`~SettingsPanel.title` property of the panel to "Windows".

To load the JSON example to a :class:`Settings` instance, use the
:meth:`Settings.add_json_panel` method. It will automatically instantiate a
:class:`SettingsPanel` and add it to :class:`Settings`::

    from kivy.config import ConfigParser

    config = ConfigParser()
    config.read('myconfig.ini')

    s = Settings()
    s.add_json_panel('My custom panel', config, 'settings_custom.json')
    s.add_json_panel('Another panel', config, 'settings_test2.json')

    # then use the s as a widget...


.. _differentlayouts:

Different panel layouts
-----------------------

A kivy :class:`~kivy.app.App` can automatically create and display a
:class:`Settings` instance. See the :attr:`~kivy.app.App.settings_cls`
documentation for details on how to choose which settings class to
display.

Several pre-built settings widgets are available. All except
:class:`SettingsWithNoMenu` include close buttons triggering the
on_close event.

- :class:`Settings`: Displays settings with a sidebar at the left to
  switch between json panels.

- :class:`SettingsWithSidebar`: A trivial subclass of
  :class:`Settings`.

- :class:`SettingsWithSpinner`: Displays settings with a spinner at
  the top, which can be used to switch between json panels. Uses
  :class:`InterfaceWithSpinner` as the
  :attr:`~Settings.interface_cls`. This is the default behavior from
  Kivy 1.8.0.

- :class:`SettingsWithTabbedPanel`: Displays json panels as individual
  tabs in a :class:`~kivy.uix.tabbedpanel.TabbedPanel`. Uses
  :class:`InterfaceWithTabbedPanel` as the :attr:`~Settings.interface_cls`.

- :class:`SettingsWithNoMenu`: Displays a single json panel, with no
  way to switch to other panels and no close button. This makes it
  impossible for the user to exit unless
  :meth:`~kivy.app.App.close_settings` is overridden with a different
  close trigger! Uses :class:`InterfaceWithNoMenu` as the
  :attr:`~Settings.interface_cls`.

You can construct your own settings panels with any layout you choose
by setting :attr:`Settings.interface_cls`. This should be a widget
that displays a json settings panel with some way to switch between
panels. An instance will be automatically created by :class:`Settings`.

Interface widgets may be anything you like, but *must* have a method
add_panel that receives newly created json settings panels for the
interface to display. See the documentation for
:class:`InterfaceWithSidebar` for more information. They may
optionally dispatch an on_close event, for instance if a close button
is clicked. This event is used by :class:`Settings` to trigger its own
on_close event.

For a complete, working example, please see
:file:`kivy/examples/settings/main.py`.

'''

__all__ = ('Settings', 'SettingsPanel', 'SettingItem', 'SettingString',
           'SettingPath', 'SettingBoolean', 'SettingNumeric', 'SettingOptions',
           'SettingTitle', 'SettingsWithSidebar', 'SettingsWithSpinner',
           'SettingsWithTabbedPanel', 'SettingsWithNoMenu',
           'InterfaceWithSidebar', 'ContentPanel', 'MenuSidebar')

import json
import os
from kivy.factory import Factory
from kivy.metrics import dp
from kivy.config import ConfigParser
from kivy.animation import Animation
from kivy.compat import string_types, text_type
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.tabbedpanel import TabbedPanelHeader
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.scrollview import ScrollView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, StringProperty, ListProperty, \
    BooleanProperty, NumericProperty, DictProperty


class SettingSpacer(Widget):
    # Internal class, not documented.
    pass


class SettingItem(FloatLayout):
    '''Base class for individual settings (within a panel). This class cannot
    be used directly; it is used for implementing the other setting classes.
    It builds a row with a title/description (left) and a setting control
    (right).

    Look at :class:`SettingBoolean`, :class:`SettingNumeric` and
    :class:`SettingOptions` for usage examples.

    :Events:
        `on_release`
            Fired when the item is touched and then released.

    '''

    title = StringProperty('<No title set>')
    '''Title of the setting, defaults to '<No title set>'.

    :attr:`title` is a :class:`~kivy.properties.StringProperty` and defaults to
    '<No title set>'.
    '''

    desc = StringProperty(None, allownone=True)
    '''Description of the setting, rendered on the line below the title.

    :attr:`desc` is a :class:`~kivy.properties.StringProperty` and defaults to
    None.
    '''

    disabled = BooleanProperty(False)
    '''Indicate if this setting is disabled. If True, all touches on the
    setting item will be discarded.

    :attr:`disabled` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    section = StringProperty(None)
    '''Section of the token inside the :class:`~kivy.config.ConfigParser`
    instance.

    :attr:`section` is a :class:`~kivy.properties.StringProperty` and defaults
    to None.
    '''

    key = StringProperty(None)
    '''Key of the token inside the :attr:`section` in the
    :class:`~kivy.config.ConfigParser` instance.

    :attr:`key` is a :class:`~kivy.properties.StringProperty` and defaults to
    None.
    '''

    value = ObjectProperty(None)
    '''Value of the token according to the :class:`~kivy.config.ConfigParser`
    instance. Any change to this value will trigger a
    :meth:`Settings.on_config_change` event.

    :attr:`value` is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None.
    '''

    panel = ObjectProperty(None)
    '''(internal) Reference to the SettingsPanel for this setting. You don't
    need to use it.

    :attr:`panel` is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None.
    '''

    content = ObjectProperty(None)
    '''(internal) Reference to the widget that contains the real setting.
    As soon as the content object is set, any further call to add_widget will
    call the content.add_widget. This is automatically set.

    :attr:`content` is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None.
    '''

    selected_alpha = NumericProperty(0)
    '''(internal) Float value from 0 to 1, used to animate the background when
    the user touches the item.

    :attr:`selected_alpha` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.
    '''

    __events__ = ('on_release', )

    def __init__(self, **kwargs):
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
        if not isinstance(value, string_types):
            value = str(value)
        panel.set_value(self.section, self.key, value)


class SettingBoolean(SettingItem):
    '''Implementation of a boolean setting on top of a :class:`SettingItem`. It
    is visualized with a :class:`~kivy.uix.switch.Switch` widget. By default,
    0 and 1 are used for values: you can change them by setting :attr:`values`.
    '''

    values = ListProperty(['0', '1'])
    '''Values used to represent the state of the setting. If you want to use
    "yes" and "no" in your ConfigParser instance::

        SettingBoolean(..., values=['no', 'yes'])

    .. warning::

        You need a minimum of two values, the index 0 will be used as False,
        and index 1 as True

    :attr:`values` is a :class:`~kivy.properties.ListProperty` and defaults to
    ['0', '1']
    '''


class SettingString(SettingItem):
    '''Implementation of a string setting on top of a :class:`SettingItem`.
    It is visualized with a :class:`~kivy.uix.label.Label` widget that, when
    clicked, will open a :class:`~kivy.uix.popup.Popup` with a
    :class:`~kivy.uix.textinput.Textinput` so the user can enter a custom
    value.
    '''

    popup = ObjectProperty(None, allownone=True)
    '''(internal) Used to store the current popup when it's shown.

    :attr:`popup` is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None.
    '''

    textinput = ObjectProperty(None)
    '''(internal) Used to store the current textinput from the popup and
    to listen for changes.

    :attr:`textinput` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    '''

    def on_panel(self, instance, value):
        if value is None:
            return
        self.fbind('on_release', self._create_popup)

    def _dismiss(self, *largs):
        if self.textinput:
            self.textinput.focus = False
        if self.popup:
            self.popup.dismiss()
        self.popup = None

    def _validate(self, instance):
        self._dismiss()
        value = self.textinput.text.strip()
        self.value = value

    def _create_popup(self, instance):
        # create popup layout
        content = BoxLayout(orientation='vertical', spacing='5dp')
        popup_width = min(0.95 * Window.width, dp(500))
        self.popup = popup = Popup(
            title=self.title, content=content, size_hint=(None, None),
            size=(popup_width, '250dp'))

        # create the textinput used for numeric input
        self.textinput = textinput = TextInput(
            text=self.value, font_size='24sp', multiline=False,
            size_hint_y=None, height='42sp')
        textinput.bind(on_text_validate=self._validate)
        self.textinput = textinput

        # construct the content, widget are used as a spacer
        content.add_widget(Widget())
        content.add_widget(textinput)
        content.add_widget(Widget())
        content.add_widget(SettingSpacer())

        # 2 buttons are created for accept or cancel the current value
        btnlayout = BoxLayout(size_hint_y=None, height='50dp', spacing='5dp')
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
    '''Implementation of a Path setting on top of a :class:`SettingItem`.
    It is visualized with a :class:`~kivy.uix.label.Label` widget that, when
    clicked, will open a :class:`~kivy.uix.popup.Popup` with a
    :class:`~kivy.uix.filechooser.FileChooserListView` so the user can enter
    a custom value.

    .. versionadded:: 1.1.0
    '''

    popup = ObjectProperty(None, allownone=True)
    '''(internal) Used to store the current popup when it is shown.

    :attr:`popup` is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None.
    '''

    textinput = ObjectProperty(None)
    '''(internal) Used to store the current textinput from the popup and
    to listen for changes.

    :attr:`textinput` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    '''

    show_hidden = BooleanProperty(False)
    '''Whether to show 'hidden' filenames. What that means is
    operating-system-dependent.

    :attr:`show_hidden` is an :class:`~kivy.properties.BooleanProperty` and
    defaults to False.

    .. versionadded:: 1.9.2
    '''

    dirselect = BooleanProperty(True)
    '''Whether to allow selection of directories.

    :attr:`dirselect` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to True.

    .. versionadded:: 1.9.2
    '''

    def on_panel(self, instance, value):
        if value is None:
            return
        self.fbind('on_release', self._create_popup)

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
        popup_width = min(0.95 * Window.width, dp(500))
        self.popup = popup = Popup(
            title=self.title, content=content, size_hint=(None, 0.9),
            width=popup_width)

        # create the filechooser
        initial_path = self.value or os.getcwd()
        self.textinput = textinput = FileChooserListView(
            path=initial_path, size_hint=(1, 1),
            dirselect=self.dirselect, show_hidden=self.show_hidden)
        textinput.bind(on_path=self._validate)

        # construct the content
        content.add_widget(textinput)
        content.add_widget(SettingSpacer())

        # 2 buttons are created for accept or cancel the current value
        btnlayout = BoxLayout(size_hint_y=None, height='50dp', spacing='5dp')
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
    '''Implementation of a numeric setting on top of a :class:`SettingString`.
    It is visualized with a :class:`~kivy.uix.label.Label` widget that, when
    clicked, will open a :class:`~kivy.uix.popup.Popup` with a
    :class:`~kivy.uix.textinput.Textinput` so the user can enter a custom
    value.
    '''

    def _validate(self, instance):
        # we know the type just by checking if there is a '.' in the original
        # value
        is_float = '.' in str(self.value)
        self._dismiss()
        try:
            if is_float:
                self.value = text_type(float(self.textinput.text))
            else:
                self.value = text_type(int(self.textinput.text))
        except ValueError:
            return


class SettingOptions(SettingItem):
    '''Implementation of an option list on top of a :class:`SettingItem`.
    It is visualized with a :class:`~kivy.uix.label.Label` widget that, when
    clicked, will open a :class:`~kivy.uix.popup.Popup` with a
    list of options from which the user can select.
    '''

    options = ListProperty([])
    '''List of all availables options. This must be a list of "string" items.
    Otherwise, it will crash. :)

    :attr:`options` is a :class:`~kivy.properties.ListProperty` and defaults
    to [].
    '''

    popup = ObjectProperty(None, allownone=True)
    '''(internal) Used to store the current popup when it is shown.

    :attr:`popup` is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None.
    '''

    def on_panel(self, instance, value):
        if value is None:
            return
        self.fbind('on_release', self._create_popup)

    def _set_option(self, instance):
        self.value = instance.text
        self.popup.dismiss()

    def _create_popup(self, instance):
        # create the popup
        content = BoxLayout(orientation='vertical', spacing='5dp')
        popup_width = min(0.95 * Window.width, dp(500))
        self.popup = popup = Popup(
            content=content, title=self.title, size_hint=(None, None),
            size=(popup_width, '400dp'))
        popup.height = len(self.options) * dp(55) + dp(150)

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
        btn = Button(text='Cancel', size_hint_y=None, height=dp(50))
        btn.bind(on_release=popup.dismiss)
        content.add_widget(btn)

        # and open the popup !
        popup.open()


class SettingTitle(Label):
    '''A simple title label, used to organize the settings in sections.
    '''

    title = Label.text

    panel = ObjectProperty(None)


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
        if 'cols' not in kwargs:
            self.cols = 1
        super(SettingsPanel, self).__init__(**kwargs)

    def on_config(self, instance, value):
        if value is None:
            return
        if not isinstance(value, ConfigParser):
            raise Exception('Invalid config object, you must use a'
                            'kivy.config.ConfigParser, not another one !')

    def get_value(self, section, key):
        '''Return the value of the section/key from the :attr:`config`
        ConfigParser instance. This function is used by :class:`SettingItem` to
        get the value for a given section/key.

        If you don't want to use a ConfigParser instance, you might want to
        override this function.
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


class InterfaceWithSidebar(BoxLayout):
    '''The default Settings interface class. It displays a sidebar menu
    with names of available settings panels, which may be used to switch
    which one is currently displayed.

    See :meth:`~InterfaceWithSidebar.add_panel` for information on the
    method you must implement if creating your own interface.

    This class also dispatches an event 'on_close', which is triggered
    when the sidebar menu's close button is released. If creating your
    own interface widget, it should also dispatch such an event which
    will automatically be caught by :class:`Settings` and used to
    trigger its own 'on_close' event.

    '''

    menu = ObjectProperty()
    '''(internal) A reference to the sidebar menu widget.

    :attr:`menu` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    '''

    content = ObjectProperty()
    '''(internal) A reference to the panel display widget (a
    :class:`ContentPanel`).

    :attr:`content` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.

    '''

    __events__ = ('on_close', )

    def __init__(self, *args, **kwargs):
        super(InterfaceWithSidebar, self).__init__(*args, **kwargs)
        self.menu.close_button.bind(
            on_release=lambda j: self.dispatch('on_close'))

    def add_panel(self, panel, name, uid):
        '''This method is used by Settings to add new panels for possible
        display. Any replacement for ContentPanel *must* implement
        this method.

        :Parameters:
            `panel`: :class:`SettingsPanel`
                It should be stored and the interface should provide a way to
                switch between panels.
            `name`:
                The name of the panel as a string. It may be used to represent
                the panel but isn't necessarily unique.
            `uid`:
                A unique int identifying the panel. It should be used to
                identify and switch between panels.

        '''
        self.menu.add_item(name, uid)
        self.content.add_panel(panel, name, uid)

    def on_close(self, *args):
        pass


class InterfaceWithSpinner(BoxLayout):
    '''A settings interface that displays a spinner at the top for
    switching between panels.

    The workings of this class are considered internal and are not
    documented. See :meth:`InterfaceWithSidebar` for
    information on implementing your own interface class.

    '''

    __events__ = ('on_close', )

    menu = ObjectProperty()
    '''(internal) A reference to the sidebar menu widget.

    :attr:`menu` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    '''

    content = ObjectProperty()
    '''(internal) A reference to the panel display widget (a
    :class:`ContentPanel`).

    :attr:`menu` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.

    '''

    def __init__(self, *args, **kwargs):
        super(InterfaceWithSpinner, self).__init__(*args, **kwargs)
        self.menu.close_button.bind(
            on_release=lambda j: self.dispatch('on_close'))

    def add_panel(self, panel, name, uid):
        '''This method is used by Settings to add new panels for possible
        display. Any replacement for ContentPanel *must* implement
        this method.

        :Parameters:
            `panel`: :class:`SettingsPanel`
                It should be stored and the interface should provide a way to
                switch between panels.
            `name`:
                The name of the panel as a string. It may be used to represent
                the panel but may not be unique.
            `uid`:
                A unique int identifying the panel. It should be used to
                identify and switch between panels.

        '''
        self.content.add_panel(panel, name, uid)
        self.menu.add_item(name, uid)

    def on_close(self, *args):
        pass


class ContentPanel(ScrollView):
    '''A class for displaying settings panels. It displays a single
    settings panel at a time, taking up the full size and shape of the
    ContentPanel. It is used by :class:`InterfaceWithSidebar` and
    :class:`InterfaceWithSpinner` to display settings.

    '''

    panels = DictProperty({})
    '''(internal) Stores a dictionary mapping settings panels to their uids.

    :attr:`panels` is a :class:`~kivy.properties.DictProperty` and
    defaults to {}.

    '''

    container = ObjectProperty()
    '''(internal) A reference to the GridLayout that contains the
    settings panel.

    :attr:`container` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.

    '''

    current_panel = ObjectProperty(None)
    '''(internal) A reference to the current settings panel.

    :attr:`current_panel` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.

    '''

    current_uid = NumericProperty(0)
    '''(internal) A reference to the uid of the current settings panel.

    :attr:`current_uid` is a
    :class:`~kivy.properties.NumericProperty` and defaults to 0.

    '''

    def add_panel(self, panel, name, uid):
        '''This method is used by Settings to add new panels for possible
        display. Any replacement for ContentPanel *must* implement
        this method.

        :Parameters:
            `panel`: :class:`SettingsPanel`
                It should be stored and displayed when requested.
            `name`:
                The name of the panel as a string. It may be used to represent
                the panel.
            `uid`:
                A unique int identifying the panel. It should be stored and
                used to identify panels when switching.

        '''
        self.panels[uid] = panel
        if not self.current_uid:
            self.current_uid = uid

    def on_current_uid(self, *args):
        '''The uid of the currently displayed panel. Changing this will
        automatically change the displayed panel.

        :Parameters:
            `uid`:
                A panel uid. It should be used to retrieve and display
                a settings panel that has previously been added with
                :meth:`add_panel`.

        '''
        uid = self.current_uid
        if uid in self.panels:
            if self.current_panel is not None:
                self.remove_widget(self.current_panel)
            new_panel = self.panels[uid]
            self.add_widget(new_panel)
            self.current_panel = new_panel
            return True
        return False  # New uid doesn't exist

    def add_widget(self, widget):
        if self.container is None:
            super(ContentPanel, self).add_widget(widget)
        else:
            self.container.add_widget(widget)

    def remove_widget(self, widget):
        self.container.remove_widget(widget)


class Settings(BoxLayout):

    '''Settings UI. Check module documentation for more information on how
    to use this class.

    :Events:
        `on_config_change`: ConfigParser instance, section, key, value
            Fired when the section's key-value pair of a ConfigParser changes.

            .. warning:

                value will be str/unicode type, regardless of the setting
                type (numeric, boolean, etc)
        `on_close`
            Fired by the default panel when the Close button is pressed.

        '''

    interface = ObjectProperty(None)
    '''(internal) Reference to the widget that will contain, organise and
    display the panel configuration panel widgets.

    :attr:`interface` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.

    '''

    interface_cls = ObjectProperty(InterfaceWithSidebar)
    '''The widget class that will be used to display the graphical
    interface for the settings panel. By default, it displays one Settings
    panel at a time with a sidebar to switch between them.

    :attr:`interface_cls` is an
    :class:`~kivy.properties.ObjectProperty` and defaults to
    :class:`InterfaceWithSidebar`.

    .. versionchanged:: 1.8.0
        If you set a string, the :class:`~kivy.factory.Factory` will be used to
        resolve the class.

    '''

    __events__ = ('on_close', 'on_config_change')

    def __init__(self, *args, **kargs):
        self._types = {}
        super(Settings, self).__init__(*args, **kargs)
        self.add_interface()
        self.register_type('string', SettingString)
        self.register_type('bool', SettingBoolean)
        self.register_type('numeric', SettingNumeric)
        self.register_type('options', SettingOptions)
        self.register_type('title', SettingTitle)
        self.register_type('path', SettingPath)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            super(Settings, self).on_touch_down(touch)
            return True

    def register_type(self, tp, cls):
        '''Register a new type that can be used in the JSON definition.
        '''
        self._types[tp] = cls

    def on_close(self, *args):
        pass

    def add_interface(self):
        '''(Internal) creates an instance of :attr:`Settings.interface_cls`,
        and sets it to :attr:`~Settings.interface`. When json panels are
        created, they will be added to this interface which will display them
        to the user.
        '''
        cls = self.interface_cls
        if isinstance(cls, string_types):
            cls = Factory.get(cls)
        interface = cls()
        self.interface = interface
        self.add_widget(interface)
        self.interface.bind(on_close=lambda j: self.dispatch('on_close'))

    def on_config_change(self, config, section, key, value):
        pass

    def add_json_panel(self, title, config, filename=None, data=None):
        '''Create and add a new :class:`SettingsPanel` using the configuration
        `config` with the JSON definition `filename`.

        Check the :ref:`settings_json` section in the documentation for more
        information about JSON format and the usage of this function.
        '''
        panel = self.create_json_panel(title, config, filename, data)
        uid = panel.uid
        if self.interface is not None:
            self.interface.add_panel(panel, title, uid)

    def create_json_panel(self, title, config, filename=None, data=None):
        '''Create new :class:`SettingsPanel`.

        .. versionadded:: 1.5.0

        Check the documentation of :meth:`add_json_panel` for more information.
        '''
        if filename is None and data is None:
            raise Exception('You must specify either the filename or data')
        if filename is not None:
            with open(filename, 'r') as fd:
                data = json.loads(fd.read())
        else:
            data = json.loads(data)
        if type(data) != list:
            raise ValueError('The first element must be a list')
        panel = SettingsPanel(title=title, settings=self, config=config)

        for setting in data:
            # determine the type and the class to use
            if 'type' not in setting:
                raise ValueError('One setting are missing the "type" element')
            ttype = setting['type']
            cls = self._types.get(ttype)
            if cls is None:
                raise ValueError(
                    'No class registered to handle the <%s> type' %
                    setting['type'])

            # create a instance of the class, without the type attribute
            del setting['type']
            str_settings = {}
            for key, item in setting.items():
                str_settings[str(key)] = item

            instance = cls(panel=panel, **str_settings)

            # instance created, add to the panel
            panel.add_widget(instance)

        return panel

    def add_kivy_panel(self):
        '''Add a panel for configuring Kivy. This panel acts directly on the
        kivy configuration. Feel free to include or exclude it in your
        configuration.

        See :meth:`~kivy.app.App.use_kivy_settings` for information on
        enabling/disabling the automatic kivy panel.

        '''
        from kivy import kivy_data_dir
        from kivy.config import Config
        from os.path import join
        self.add_json_panel('Kivy', Config,
                            join(kivy_data_dir, 'settings_kivy.json'))


class SettingsWithSidebar(Settings):
    '''A settings widget that displays settings panels with a sidebar to
    switch between them. This is the default behaviour of
    :class:`Settings`, and this widget is a trivial wrapper subclass.

    '''


class SettingsWithSpinner(Settings):
    '''A settings widget that displays one settings panel at a time with a
    spinner at the top to switch between them.

    '''
    def __init__(self, *args, **kwargs):
        self.interface_cls = InterfaceWithSpinner
        super(SettingsWithSpinner, self).__init__(*args, **kwargs)


class SettingsWithTabbedPanel(Settings):
    '''A settings widget that displays settings panels as pages in a
    :class:`~kivy.uix.tabbedpanel.TabbedPanel`.
    '''

    __events__ = ('on_close', )

    def __init__(self, *args, **kwargs):
        self.interface_cls = InterfaceWithTabbedPanel
        super(SettingsWithTabbedPanel, self).__init__(*args, **kwargs)

    def on_close(self, *args):
        pass


class SettingsWithNoMenu(Settings):
    '''A settings widget that displays a single settings panel with *no*
    Close button. It will not accept more than one Settings panel. It
    is intended for use in programs with few enough settings that a
    full panel switcher is not useful.

    .. warning::

        This Settings panel does *not* provide a Close
        button, and so it is impossible to leave the settings screen
        unless you also add other behaviour or override
        :meth:`~kivy.app.App.display_settings` and
        :meth:`~kivy.app.App.close_settings`.

    '''
    def __init__(self, *args, **kwargs):
        self.interface_cls = InterfaceWithNoMenu
        super(SettingsWithNoMenu, self).__init__(*args, **kwargs)


class InterfaceWithNoMenu(ContentPanel):
    '''The interface widget used by :class:`SettingsWithNoMenu`. It
    stores and displays a single settings panel.

    This widget is considered internal and is not documented. See the
    :class:`ContentPanel` for information on defining your own content
    widget.

    '''
    def add_widget(self, widget):
        if self.container is not None and len(self.container.children) > 0:
            raise Exception(
                'ContentNoMenu cannot accept more than one settings panel')
        super(InterfaceWithNoMenu, self).add_widget(widget)


class InterfaceWithTabbedPanel(FloatLayout):
    '''The content widget used by :class:`SettingsWithTabbedPanel`. It
    stores and displays Settings panels in tabs of a TabbedPanel.

    This widget is considered internal and is not documented. See
    :class:`InterfaceWithSidebar` for information on defining your own
    interface widget.

    '''
    tabbedpanel = ObjectProperty()
    close_button = ObjectProperty()

    __events__ = ('on_close', )

    def __init__(self, *args, **kwargs):
        super(InterfaceWithTabbedPanel, self).__init__(*args, **kwargs)
        self.close_button.bind(on_release=lambda j: self.dispatch('on_close'))

    def add_panel(self, panel, name, uid):
        scrollview = ScrollView()
        scrollview.add_widget(panel)
        if not self.tabbedpanel.default_tab_content:
            self.tabbedpanel.default_tab_text = name
            self.tabbedpanel.default_tab_content = scrollview
        else:
            panelitem = TabbedPanelHeader(text=name, content=scrollview)
            self.tabbedpanel.add_widget(panelitem)

    def on_close(self, *args):
        pass


class MenuSpinner(BoxLayout):
    '''The menu class used by :class:`SettingsWithSpinner`. It provides a
    sidebar with an entry for each settings panel.

    This widget is considered internal and is not documented. See
    :class:`MenuSidebar` for information on menus and creating your own menu
    class.

    '''
    selected_uid = NumericProperty(0)
    close_button = ObjectProperty(0)
    spinner = ObjectProperty()
    panel_names = DictProperty({})
    spinner_text = StringProperty()
    close_button = ObjectProperty()

    def add_item(self, name, uid):
        values = self.spinner.values
        if name in values:
            i = 2
            while name + ' {}'.format(i) in values:
                i += 1
            name = name + ' {}'.format(i)
        self.panel_names[name] = uid
        self.spinner.values.append(name)
        if not self.spinner.text:
            self.spinner.text = name

    def on_spinner_text(self, *args):
        text = self.spinner_text
        self.selected_uid = self.panel_names[text]


class MenuSidebar(FloatLayout):
    '''The menu used by :class:`InterfaceWithSidebar`. It provides a
    sidebar with an entry for each settings panel, which the user may
    click to select.

    '''

    selected_uid = NumericProperty(0)
    '''The uid of the currently selected panel. This may be used to switch
    between displayed panels, e.g. by binding it to the
    :attr:`~ContentPanel.current_uid` of a :class:`ContentPanel`.

    :attr:`selected_uid` is a
    :class:`~kivy.properties.NumericProperty` and defaults to 0.

    '''

    buttons_layout = ObjectProperty(None)
    '''(internal) Reference to the GridLayout that contains individual
    settings panel menu buttons.

    :attr:`buttons_layout` is an
    :class:`~kivy.properties.ObjectProperty` and defaults to None.

    '''

    close_button = ObjectProperty(None)
    '''(internal) Reference to the widget's Close button.

    :attr:`buttons_layout` is an
    :class:`~kivy.properties.ObjectProperty` and defaults to None.

    '''

    def add_item(self, name, uid):
        '''This method is used to add new panels to the menu.

        :Parameters:
            `name`:
                The name (a string) of the panel. It should be used
                to represent the panel in the menu.
            `uid`:
                The name (an int) of the panel. It should be used internally
                to represent the panel and used to set self.selected_uid when
                the panel is changed.

        '''

        label = SettingSidebarLabel(text=name, uid=uid, menu=self)
        if len(self.buttons_layout.children) == 0:
            label.selected = True
        if self.buttons_layout is not None:
            self.buttons_layout.add_widget(label)

    def on_selected_uid(self, *args):
        '''(internal) unselects any currently selected menu buttons, unless
        they represent the current panel.

        '''
        for button in self.buttons_layout.children:
            if button.uid != self.selected_uid:
                button.selected = False


class SettingSidebarLabel(Label):
    # Internal class, not documented.
    selected = BooleanProperty(False)
    uid = NumericProperty(0)
    menu = ObjectProperty(None)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return
        self.selected = True
        self.menu.selected_uid = self.uid


if __name__ == '__main__':
    from kivy.app import App

    class SettingsApp(App):

        def build(self):
            s = Settings()
            s.add_kivy_panel()
            s.bind(on_close=self.stop)
            return s

    SettingsApp().run()
