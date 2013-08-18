'''
Spinner
=======

.. versionadded:: 1.4.0

.. image:: images/spinner.jpg
    :align: right

Spinner is a widget that provide a quick way to select one value from a set. In
the default state, a spinner show its currently selected value. Touching the
spinner displays a dropdown menu with all other available values. from which the
user can select a new one.

Example::

    from kivy.base import runTouchApp
    from kivy.uix.spinner import Spinner

    spinner = Spinner(
        # default value showed
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

from kivy.properties import ListProperty, ObjectProperty, BooleanProperty
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown


class SpinnerOption(Button):
    '''Special button used in the dropdown list. We just set the default
    size_hint_y and height.
    '''
    pass


class Spinner(Button):
    '''Spinner class, see module documentation for more information
    '''

    values = ListProperty()
    '''Values that can be selected by the user. It must be a list of strings.

    :data:`values` is a :class:`~kivy.properties.ListProperty`, default to [].
    '''

    option_cls = ObjectProperty(SpinnerOption)
    '''Class used to display the options within the dropdown list displayed
    under the Spinner. The `text` property in the class will represent the
    value.

    The option class require at least:

    - one `text` property where the value will be put
    - one `on_release` event that you need to trigger when the option is
      touched.

    :data:`option_cls` is a :class:`~kivy.properties.ObjectProperty`, default
    to :class:`SpinnerOption`.
    '''

    dropdown_cls = ObjectProperty(DropDown)
    '''Class used to display the dropdown list when the Spinner is pressed.

    :data:`dropdown_cls` is a :class:`~kivy.properties.ObjectProperty`, default
    to :class:`~kivy.uix.dropdown.DropDown`.
    '''

    is_open = BooleanProperty(False)
    '''By default, the spinner is not open. Set to true to open it.

    :data:`is_open` is a :class:`~kivy.properties.BooleanProperty`, default to
    False.

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
            self._dropdown.unbind(on_dismiss=self._toggle_dropdown)
            self._dropdown.dismiss()
            self._dropdown = None
        self._dropdown = self.dropdown_cls()
        self._dropdown.bind(on_select=self._on_dropdown_select)
        self._dropdown.bind(on_dismiss=self._toggle_dropdown)
        self._update_dropdown()

    def _update_dropdown(self, *largs):
        dp = self._dropdown
        cls = self.option_cls
        dp.clear_widgets()
        for value in self.values:
            item = cls(text=value)
            item.bind(on_release=lambda option: dp.select(option.text))
            dp.add_widget(item)

    def _toggle_dropdown(self, *largs):
        self.is_open = not self.is_open

    def _on_dropdown_select(self, instance, data, *largs):
        self.text = data
        self.is_open = False

    def on_is_open(self, instance, value):
        if value:
            self._dropdown.open(self)
        else:
            if self._dropdown.attach_to:
                self._dropdown.dismiss()

