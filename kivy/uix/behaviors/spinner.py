'''
Spinner Behavior
===============

.. versionadded:: 2.2.0

The :class:`~kivy.uix.behaviors.spinner.SpinnerBehavior`
`mixin <https://en.wikipedia.org/wiki/Mixin>`_ class provides
:class:`~kivy.uix.spinner.Spinner` behavior. You can combine this class with
other widgets, such as an :class:`~kivy.uix.button.Button`, to provide
custom spinners that preserve Kivy spinner behavior.

For an overview of behaviors, please refer to the :mod:`~kivy.uix.behaviors`
documentation.

Example
-------

The following example shows how a spinner behavior is mixed with a
:class:`~kivy.uix.button.Button` to create the well known spinner which opens
the dropdown options on button click.
Notice how option_cls of the :class:`~kivy.uix.behavior.SpinnerBehavior` is
overwritten to define the appearance of the dropdown elements::

    from kivy.app import App
    from kivy.uix.button import Button
    from kivy.uix.behaviors import SpinnerBehavior
    from kivy.uix.spinner import SpinnerButton


    class Spinner(SpinnerBehavior, Button):
        option_cls = ObjectProperty(SpinnerOption)
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

        def on_release(self):
            self.toggle_dropdown()


    class SampleApp(App):
        def build(self):
            return MySpinner()


    SampleApp().run()

See :class:`~kivy.uix.behaviors.SpinnerBehavior` for details.
'''

__all__ = ('SpinnerBehavior', )

from kivy.compat import string_types
from kivy.factory import Factory
from kivy.properties import ListProperty
from kivy.properties import ObjectProperty
from kivy.properties import BooleanProperty


class SpinnerBehavior(object):
    '''Spinner class, see module documentation for more information.

    .. versionadded:: 2.2.0
    '''

    values = ListProperty([])
    '''Values that can be selected by the user. It must be a list of strings.

    .. versionadded:: 2.2.0

    :attr:`~kivy.uix.behavior.SpinnerBehavior.values` is a
    :class:`~kivy.properties.ListProperty` and defaults to [].
    '''

    text_autoupdate = BooleanProperty(False)
    '''Indicates if the spinner's
    :attr:`~kivy.uix.behavior.SpinnerBehavior.text` should be automatically
    updated with the first value of the
    :attr:`~kivy.uix.behavior.SpinnerBehavior.values` property.
    Setting it to True will cause the spinner to update its
    :attr:`~kivy.uix.behavior.SpinnerBehavior.text` property every time
    :attr:`values` are changed.

    .. versionadded:: 2.2.0

    :attr:`~kivy.uix.behavior.SpinnerBehavior.text_autoupdate` is a
    :class:`~kivy.properties.BooleanProperty` and defaults to False.
    '''

    option_cls = ObjectProperty('SpinnerOption')
    '''Class used to display the options within the dropdown list displayed
    under the Spinner. The `text` property of the class will be used to
    represent the value.

    The option class requires:

    - a `text` property, used to display the value.
    - an `on_release` event, used to trigger the option when pressed/touched.
    - a :attr:`~kivy.uix.widget.Widget.size_hint_y` of None.
    - the :attr:`~kivy.uix.widget.Widget.height` to be set.

    If you set a string, the :class:`~kivy.factory.Factory` will be used to
    resolve the class.

    .. versionadded:: 2.2.0

    :attr:`~kivy.uix.behavior.SpinnerBehavior.option_cls` is an
    :class:`~kivy.properties.ObjectProperty` and defaults to 'SpinnerOption'.
    '''

    dropdown_cls = ObjectProperty("DropDown")
    '''Class used to display the dropdown list when the Spinner is pressed.

    If set to a string, the :class:`~kivy.factory.Factory` will be used to
    resolve the class name.

    .. versionadded:: 2.2.0

    :attr:`~kivy.uix.behavior.SpinnerBehavior.dropdown_cls` is an
    :class:`~kivy.properties.ObjectProperty` and defaults to 'DropDown'.
    '''

    is_open = BooleanProperty(False)
    '''By default, the spinner is not open. Set to True to open it.

    .. versionadded:: 2.2.0

    :attr:`~kivy.uix.behavior.SpinnerBehavior.is_open` is a
    :class:`~kivy.properties.BooleanProperty` and defaults to False.
    '''

    sync_height = BooleanProperty(False)
    '''Each element in a dropdown list uses a default/user-supplied height.
    Set to True to propagate the Spinner's height value to each dropdown
    list element.

    .. versionadded:: 2.2.0

    :attr:`~kivy.uix.behavior.SpinnerBehavior.sync_height` is a
    :class:`~kivy.properties.BooleanProperty` and defaults to False.
    '''

    def __init__(self, **kwargs):
        self._dropdown = None
        super().__init__(**kwargs)

        if not hasattr(self, 'text'):
            self.text = ''

        fbind = self.fbind
        build_dropdown = self._build_dropdown
        update_dropdown = self._update_dropdown
        fbind('dropdown_cls', build_dropdown)
        fbind('option_cls', build_dropdown)
        fbind('values', update_dropdown)
        fbind('size', self._update_dropdown_size)
        fbind('text_autoupdate', update_dropdown)
        fbind('is_open', self._on_is_open)
        build_dropdown()

    def _build_dropdown(self, *largs):
        if self._dropdown:
            self._dropdown.unbind(on_select=self._on_dropdown_select)
            self._dropdown.unbind(on_dismiss=self.close_dropdown)
            self._dropdown.dismiss()
            self._dropdown = None
        cls = self.dropdown_cls
        if isinstance(cls, string_types):
            cls = Factory.get(cls)
        self._dropdown = cls()
        self._dropdown.bind(on_select=self._on_dropdown_select)
        self._dropdown.bind(on_dismiss=self.close_dropdown)
        self._update_dropdown()

    def _update_dropdown_size(self, *largs):
        if not self.sync_height:
            return
        dp = self._dropdown
        if not dp:
            return

        container = dp.container
        if not container:
            return
        h = self.height
        for item in container.children[:]:
            item.height = h

    def _update_dropdown(self, *largs):
        dp = self._dropdown
        cls = self.option_cls
        values = self.values
        text_autoupdate = self.text_autoupdate
        if isinstance(cls, string_types):
            cls = Factory.get(cls)
        dp.clear_widgets()
        for value in values:
            item = cls(text=value)
            item.height = self.height if self.sync_height else item.height
            item.bind(on_release=lambda option: dp.select(option.text))
            dp.add_widget(item)
        if text_autoupdate:
            if values:
                if not self.text or self.text not in values:
                    self.text = values[0]
            else:
                self.text = ''

    def toggle_dropdown(self, *largs):
        '''Toggle the dropdown state of the spinner.

        Shows the dropdown if it is hidden and hides it otherwise.
        If there are no values set as dropdown options, this function does
        not have any effect.

        .. versionadded:: 2.2.0
        '''
        if self.values:
            self.is_open = not self.is_open

    def open_dropdown(self, *largs):
        '''Open the dropdown of the spinner.

        Shows the dropdown if it is hidden.
        If there are no values set as dropdown options, this function does
        not have any effect.

        .. versionadded:: 2.2.0
        '''
        if self.values:
            self.is_open = True

    def close_dropdown(self, *largs):
        '''Close the dropdown of the spinner.

        Hides the dropdown if it is visual.

        .. versionadded:: 2.2.0
        '''
        self.is_open = False

    def _on_dropdown_select(self, instance, data, *largs):
        self.text = data
        self.is_open = False

    def _on_is_open(self, instance, value):
        if value:
            self._dropdown.open(self)
        else:
            if self._dropdown.attach_to:
                self._dropdown.dismiss()
