'''
Spinner
=======

.. versionadded:: 1.4.0

.. image:: images/spinner.jpg
    :align: right

Spinner is a widget that provides a quick way to select one value from a set.
In the default state, a spinner shows its currently selected value.
Touching the spinner displays a dropdown menu with all the other available
values from which the user can select a new one.

Example::

    from kivy.base import runTouchApp
    from kivy.uix.spinner import Spinner

    spinner = Spinner(
        # default value shown
        text='Home',
        # available values
        values=('Home', 'Work', 'Other', 'Custom'),
        # just for positioning in our example
        size_hint=(None, None),
        size=(100, 44),
        pos_hint={'center_x': .5, 'center_y': .5})

    def show_selected_value(spinner, text):
        print('The spinner', spinner, 'have text', text)

    spinner.bind(text=show_selected_value)

    runTouchApp(spinner)

'''

__all__ = ('Spinner', 'SpinnerOption')

from kivy.compat import string_types
from kivy.factory import Factory
from kivy.properties import ListProperty, ObjectProperty, BooleanProperty
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown


class SpinnerOption(Button):
    '''Special button used in the dropdown list. We just set the default
    size_hint_y and height.
    '''
    pass


class Spinner(Button):
    '''Spinner class, see module documentation for more information.
    '''

    values = ListProperty()
    '''Values that can be selected by the user. It must be a list of strings.

    :attr:`values` is a :class:`~kivy.properties.ListProperty` and defaults to
    [].
    '''

    option_cls = ObjectProperty(SpinnerOption)
    '''Class used to display the options within the dropdown list displayed
    under the Spinner. The `text` property of the class will be used to
    represent the value.

    The option class requires at least:

    - a `text` property, used to display the value.
    - an `on_release` event, used to trigger the option when pressed/touched.

    :attr:`option_cls` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to :class:`SpinnerOption`.

    .. versionchanged:: 1.8.0
        If you set a string, the :class:`~kivy.factory.Factory` will be used to
        resolve the class.

    '''

    dropdown_cls = ObjectProperty(DropDown)
    '''Class used to display the dropdown list when the Spinner is pressed.

    :attr:`dropdown_cls` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to :class:`~kivy.uix.dropdown.DropDown`.

    .. versionchanged:: 1.8.0
        If you set a string, the :class:`~kivy.factory.Factory` will be used to
        resolve the class.

    '''

    is_open = BooleanProperty(False)
    '''By default, the spinner is not open. Set to True to open it.

    :attr:`is_open` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.

    .. versionadded:: 1.4.0
    '''

    def __init__(self, **kwargs):
        self._dropdown = None
        super(Spinner, self).__init__(**kwargs)
        self.bind(
            on_release=self._toggle_dropdown,
            dropdown_cls=self._build_dropdown,
            option_cls=self._build_dropdown,
            values=self._update_dropdown)
        self._build_dropdown()

    def _build_dropdown(self, *largs):
        if self._dropdown:
            self._dropdown.unbind(on_select=self._on_dropdown_select)
            self._dropdown.unbind(on_dismiss=self._close_dropdown)
            self._dropdown.dismiss()
            self._dropdown = None
        cls = self.dropdown_cls
        if isinstance(cls, string_types):
            cls = Factory.get(cls)
        self._dropdown = cls()
        self._dropdown.bind(on_select=self._on_dropdown_select)
        self._dropdown.bind(on_dismiss=self._close_dropdown)
        self._update_dropdown()

    def _update_dropdown(self, *largs):
        dp = self._dropdown
        cls = self.option_cls
        if isinstance(cls, string_types):
            cls = Factory.get(cls)
        dp.clear_widgets()
        for value in self.values:
            item = cls(text=value)
            item.bind(on_release=lambda option: dp.select(option.text))
            dp.add_widget(item)

    def _toggle_dropdown(self, *largs):
        self.is_open = not self.is_open

    def _close_dropdown(self, *largs):
        self.is_open = False

    def _on_dropdown_select(self, instance, data, *largs):
        self.text = data
        self.is_open = False

    def on_is_open(self, instance, value):
        if value:
            self._dropdown.open(self)
        else:
            if self._dropdown.attach_to:
                self._dropdown.dismiss()
