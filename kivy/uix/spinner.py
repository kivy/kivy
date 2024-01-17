'''
Spinner
=======

.. versionadded:: 1.4.0

.. image:: images/spinner.jpg
    :align: right

:class:`~kivy.uix.spinner.Spinner` is a widget that provides a quick way to
select one value from a set.
In the default state, a spinner shows its currently selected value.
Touching the spinner displays a dropdown menu with all the other available
values from which the user can select a new one.

:class:`~kivy.uix.spinner.TextInputSpinner` is another variant of a spinner
which provides a :class:`~kivy.uix.textinput.TextInput` as main visual input
element. In the default state, the :class:`~kivy.uix.spinner.TextInputSpinner`
appears like a usual :class:`~kivy.uix.textinput.TextInput` input element.
Interacting with the spinner by touching or typing displays the dropdown menu
as for a :class:`~kivy.uix.spinner.Spinner`.

Example::

    from kivy.base import runTouchApp
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.spinner import Spinner
    from kivy.uix.spinner import TextInputSpinner

    spinner = Spinner(
        # default value shown
        text='Home',
        # available values
        values=('Home', 'Work', 'Other', 'Custom'),
    )

    textinput_spinner = TextInputSpinner(
        # default value shown
        text='',
        values=('One', 'Two', 'Three', '_THREE_'),
    )

    boxlayout = BoxLayout(
        # just for positioning of the example
        orientation='vertical',
        size_hint=(None, None),
        size=(100, 88),
        pos_hint={'center_x': .5, 'center_y': .5},
    )

    def show_selected_value(spinner, text):
        print('The spinner', spinner.__class__.__name__, 'has text', text)

    spinner.bind(text=show_selected_value)
    textinput_spinner.bind(text=show_selected_value)

    runTouchApp(boxlayout)


Kv Example::

    BoxLayout:
        orientation='vertical'
        size_hint: None, None
        size: 100, 88
        pos_hint: {'center': (.5, .5)}

        Spinner:
            text: 'Home'
            values: 'Home', 'Work', 'Other', 'Custom'
            on_text:
                print("The spinner {} has text {}".format(self, self.text))

        TextInputSpinner:
            text: 'Home'
            values: 'One', 'Two', 'Three', '_THREE_'
            on_text:
                print("The spinner {} has text {}".format(self, self.text))
'''

__all__ = ('Spinner', 'SpinnerOption', 'TextInputSpinner')

from kivy.properties import BooleanProperty
from kivy.uix.behaviors import SpinnerBehavior
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput


class SpinnerOption(Button):
    '''Special button used in the :class:`~kivy.uix.spinner.Spinner` dropdown
    list. By default, this is just a :class:`~kivy.uix.button.Button` with a
    size_hint_y of None and a height of :meth:`48dp <kivy.metrics.dp>`.
    '''
    pass


class Spinner(SpinnerBehavior, Button):
    '''Spinner class, see module documentation for more information.

    .. versionchanged:: 2.2.0
        The behavior / logic of the spinner has been moved to
        :class:`~kivy.uix.behaviors.SpinnerBehavior`.
    '''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fbind('on_release', self.toggle_dropdown)


class TextInputSpinner(SpinnerBehavior, TextInput):
    '''TextInputSpinner class, see module documentation for more information.

    .. versionadded:: 2.2.0
    '''

    live_filter = BooleanProperty(True)
    '''Indicates if the :class:`~kivy.uix.spinner.TextInputSpinner` should be
    live updated when the TextInput gets updated e.g., by typing.

    Setting this property to True will cause the
    :class:`~kivy.uix.spinner.TextInputSpinner` to update its visual options in
    the dropdown selection every time
    :attr:`~kivy.uix.spinner.TextInputSpinner.text` is changed. Filtering is
    based on :meth:`~kivy.uix.spinner.TextInputSpinner.filter_function`.

    This option will cause :attr:`~kivy.uix.spinner.TextInputSpinner.values`
    being overwritten with the currently visual options. To get an unfiltered
    list of all options, access the
    :attr:`~kivy.uix.spinner.TextInputSpinner.values_unfiltered`.

    .. versionadded:: 2.2.0

    :attr:`~kivy.uix.spinner.TextInputSpinner.live_filter` is a
    :class:`~kivy.properties.BooleanProperty` and defaults to True.
    '''

    filter_case_sensitive = BooleanProperty(False)
    '''Defines case sensitivity for live_filtering.

    Setting this property to False will make the
    :meth:`~kivy.uix.spinner.TextInputSpinner.filter_function` ignore the
    capitalization.

    .. versionadded:: 2.2.0

    :attr:`~kivy.uix.spinner.TextInputSpinner.live_filter` is a
    :class:`~kivy.properties.BooleanProperty` and defaults to False.
    '''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multiline = False

        self.values_unfiltered = self.values
        self._filter_values_recursion_depth = 0

        fbind = self.fbind
        fbind('values', self._filter_updated_values)
        fbind('live_filter', self._live_filter_values)
        fbind('text', self._on_text)
        fbind('on_touch_down', self._on_touch_down)

    def _filter_updated_values(self, *largs):
        self._filter_values(self.values)

    def _live_filter_values(self, *largs):
        self._filter_values(self.values_unfiltered)

    def filter_function(self, current_text, option):
        '''A function which is used when
        :attr:`~kivy.uix.spinner.TextInputSpinner.live_filter` is set to True.

        The :attr:`~kivy.uix.spinner.TextInputSpinner.filter_case_sensitive`
        defines wether this function ignores capitalization.

        This function could be overwritten to implement custom a custom filter
        behavior. To do so, the replacing function must accept two parameters
        of which the first parameter will provide the current value of
        :attr:`~kivy.uix.spinner.TextInputSpinner.text` and the second
        parameter will provide an option value. The function should return True
        if it should be listed in the dropdown list and False if the option
        should be hidden.

        .. versionadded:: 2.2.0
        '''
        if self.filter_case_sensitive:
            return current_text in option
        else:
            return current_text.lower() in option.lower()

    def _filter_values(self, values):
        self._filter_values_recursion_depth += 1
        if self._filter_values_recursion_depth > 1:
            self._filter_values_recursion_depth -= 1
            return

        self.values_unfiltered = list(values)
        current_text = self.text
        filter_function = self.filter_function
        if self.live_filter and len(self.text) > 0:
            self.values = [
                value
                for value in values
                if filter_function(current_text, value)
            ]
        else:
            self.values = self.values_unfiltered

        self._filter_values_recursion_depth -= 1

    def _on_text(self, instance, value):
        self._live_filter_values(self.values_unfiltered)
        if not self.is_open:
            self.open_dropdown()

    def _on_touch_down(self, instance, event):
        if self.collide_point(*event.pos):
            self.toggle_dropdown()
        return super().on_touch_down(event)

    def close_dropdown(self, *largs):
        super().close_dropdown(*largs)
        self.focus = False
