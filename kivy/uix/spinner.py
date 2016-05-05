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
from kivy.properties import ListProperty, ObjectProperty, BooleanProperty, \
    ReferenceListProperty, NumericProperty, DictProperty
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown


class SpinnerOption(Button):
    '''Special button used in the :class:`Spinner` dropdown list. By default,
    this is just a :class:`~kivy.uix.button.Button` with a size_hint_y of None
    and a height of :meth:`48dp <kivy.metrics.dp>`.
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

    text_autoupdate = BooleanProperty(False)
    '''Indicates if the spinner's :attr:`text` should be automatically
    updated with the first value of the :attr:`values` property.
    Setting it to True will cause the spinner to update its :attr:`text`
    property every time attr:`values` are changed.

    .. versionadded:: 1.9.2

    :attr:`text_autoupdate` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    option_cls = ObjectProperty(SpinnerOption)
    '''Class used to display the options within the dropdown list displayed
    under the Spinner. The `text` property of the class will be used to
    represent the value.

    The option class requires:

    - a `text` property, used to display the value.
    - an `on_release` event, used to trigger the option when pressed/touched.
    - a :attr:`~kivy.uix.widget.Widget.size_hint_y` of None.
    - the :attr:`~kivy.uix.widget.Widget.height` to be set.

    :attr:`option_cls` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to :class:`SpinnerOption`.

    .. versionchanged:: 1.8.0
        If you set a string, the :class:`~kivy.factory.Factory` will be used to
        resolve the class.

    '''

    option_defaults = DictProperty({})
    '''A dictionary of attribute/values that will be passed to each
    :attr:`option_cls` as it's created.

    :attr:`dropdown_cls` is an :class:`~kivy.properties.DictProperty` and
    defaults to the empty dictionary.

    .. versionadded:: 1.9.2
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

    sync_height = BooleanProperty(False)
    '''Each element in a dropdown list uses a default/user-supplied height.
    Set to True to propagate the Spinner's height value to each dropdown
    list element.

    .. versionadded:: 1.9.2

    :attr:`sync_height` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    maximum_option_width = NumericProperty(0)
    '''Automatically computed maximum width of all of the option items.

    .. versionadded:: 1.9.2

    :attr:`maximum_option_width` is a :class:`~kivy.properties.NumericProperty`
    and defaults to 0. It is read only.
    '''

    maximum_option_height = NumericProperty(0)
    '''Automatically computed maximum height of all of the option items.

    .. versionadded:: 1.9.2

    :attr:`maximum_option_height` is a
    :class:`~kivy.properties.NumericProperty` and defaults to 0. It is read
    only.
    '''

    maximum_option_size = ReferenceListProperty(
        maximum_option_width, maximum_option_height)
    '''Automatically computed maximum size of all of the option items.

    .. versionadded:: 1.9.2

    :attr:`maximum_option_size` is a
    :class:`~kivy.properties.ReferenceListProperty` of
    (:attr:`maximum_option_width`, :attr:`maximum_option_height`) properties.
    It is read only.
    '''

    def __init__(self, **kwargs):
        self._dropdown = None
        super(Spinner, self).__init__(**kwargs)
        fbind = self.fbind
        build_dropdown = self._build_dropdown
        fbind('on_release', self._toggle_dropdown)
        fbind('dropdown_cls', build_dropdown)
        fbind('option_cls', build_dropdown)
        fbind('values', self._update_dropdown)
        fbind('size', self._update_dropdown)
        fbind('text_autoupdate', self._update_dropdown)
        build_dropdown()

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
        values = self.values
        option_defaults = self.option_defaults
        text_autoupdate = self.text_autoupdate

        if isinstance(cls, string_types):
            cls = Factory.get(cls)

        dp.clear_widgets()

        for value in values:
            item = cls(text=value, **option_defaults)
            item.height = self.height if self.sync_height else item.height
            item.bind(on_release=lambda option: dp.select(option.text),
                      size=self._update_max_size)
            dp.add_widget(item)
        self._update_max_size()

        if text_autoupdate:
            if values:
                if not self.text or self.text not in values:
                    self.text = values[0]
            else:
                self.text = ''

    def _update_max_size(self, *largs):
        dp = self._dropdown
        if dp is None:
            return
        dp = getattr(dp, 'container', dp)  # so that it works with dropdown

        children = dp.children
        w = h = 0
        for c in children:
            w = max(w, c.width)
            h = max(h, c.height)
        self.maximum_option_size = w, h

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
