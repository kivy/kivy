'''
Popup
=====

.. versionadded:: 1.0.7

.. image:: images/popup.jpg
    :align: right

The :class:`Popup` widget is used to create modal popups. By default, the popup
will cover the whole "parent" window. When you are creating a Popup, you must at
minimum set a :data:`Popup.title` and a :data:`Popup.content` widget.

Remember that the default size of a Widget is size_hint=(1, 1). If you don't
want your popup to be fullscreen, deactivate the size_hint and use a specific
size attribute.

Examples
--------

Example of a simple 400x400 Hello world popup::

    popup = Popup(title='Test popup',
        content=Label(text='Hello world'),
        size_hint=(None, None), size=(400, 400))

By default, any click outside the popup will dismiss it. If you don't
want that, you can set :data:`Popup.auto_dismiss` to False::

    popup = Popup(title='Test popup', content=Label(text='Hello world'),
                  auto_dismiss=False)
    popup.open()

To manually dismiss/close the popup, use :meth:`Popup.dismiss`::

    popup.dismiss()

The :meth:`Popup.open` and :meth:`Popup.dismiss` are bindable. That means you
can directly bind the function to an action, like an a Button's on_press ::

    # create content and assign to the popup
    content = Button(text='Close me!')
    popup = Popup(content=content, auto_dismiss=False)

    # bind the on_press event of the button to the our dismiss function
    content.bind(on_press=popup.dismiss)

    # open the popup
    popup.open()


Popup events
------------

There are 2 events available: `on_open` when the popup is opening, and
`on_dismiss` when it is closed. For `on_dismiss`, you can prevent the
popup from closing by explictly returning True from your callback ::

    def my_callback(instance):
        print 'Popup', instance, 'is beeing dismiss, but i dont want!'
        return True
    popup = Popup(content=Label(text='Hello world'))
    popup.bind(on_dismiss=my_callback)
    popup.open()

'''


from kivy.logger import Logger
from kivy.animation import Animation
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import StringProperty, BooleanProperty, ObjectProperty, \
    NumericProperty, ListProperty


class Popup(FloatLayout):
    '''Popup class, see module documentation for more information.

    :Events:
        `on_open`:
            Fired when the Popup is opened
        `on_dismiss`:
            Fired when the Popup is closed. If the callback returns True, the
            dismiss will be canceled.
    '''

    title = StringProperty('No title')
    '''String that represent the title of the popup.

    :data:`title` is a :class:`~kivy.properties.StringProperty`, default to 'No
    title'.
    '''

    auto_dismiss = BooleanProperty(True)
    '''Default to True, this property determines if the popup is automatically
    dismissed when the user clicks outside it.

    :data:`auto_dismiss` is a :class:`~kivy.properties.BooleanProperty`, default
    to True.
    '''

    attach_to = ObjectProperty(None)
    '''If a widget is set on attach_to, the popup will attach to the nearest
    parent window of the Widget. If none is found, it will attach to the
    main/global Window.

    :data:`attach_to` is a :class:`~kivy.properties.ObjectProperty`, default to
    None.
    '''

    content = ObjectProperty(None)
    '''Content of the popup, that is displayed just under the title.

    :data:`content` is a :class:`~kivy.properties.ObjectProperty`, default to
    None.
    '''

    background_color = ListProperty([0, 0, 0, .7])
    '''Background color, in the format (r, g, b, a).

    .. versionadded:: 1.1.0

    :data:`background_color` is a :class:`~kivy.properties.ListProperty`,
    default to [0, 0, 0, .7].
    '''

    background = StringProperty(
        'atlas://data/images/defaulttheme/popup-background')
    '''Background image of the popup used for the popup background.

    .. versionadded:: 1.1.0

    :data:`background` is an :class:`~kivy.properties.StringProperty`,
    default to 'atlas://data/images/defaulttheme/popup-background'
    '''

    border = ListProperty([16, 16, 16, 16])
    '''Border used for :class:`~kivy.graphics.vertex_instructions.BorderImage`
    graphics instruction, used itself for :data:`background_normal` and
    :data:`background_down`. Can be used when using custom background.

    .. versionadded:: 1.1.0

    It must be a list of 4 value: (top, right, bottom, left). Read the
    BorderImage instruction for more information about how to play with it.

    :data:`border` is a :class:`~kivy.properties.ListProperty`, default to (16,
    16, 16, 16)
    '''

    separator_color = ListProperty([47 / 255., 167 / 255., 212 / 255., 1.])
    '''Color used by the separator between title and content.

    .. versionadded:: 1.1.0

    :data:`background_color` is a :class:`~kivy.properties.ListProperty`,
    default to [47 / 255., 167 / 255., 212 / 255., 1.]
    '''

    separator_height = NumericProperty(2)
    '''Height of the separator.

    .. versionadded:: 1.1.0

    :data:`separator_height` is a :class:`~kivy.properties.NumericProperty`,
    default to 2.
    '''

    # Internals properties used for graphical representation.

    _container = ObjectProperty(None)

    _anim_alpha = NumericProperty(0)

    _anim_duration = NumericProperty(.100)

    _window = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        self.register_event_type('on_open')
        self.register_event_type('on_dismiss')
        self._parent = None
        super(Popup, self).__init__(**kwargs)

    def _search_window(self):
        # get window to attach to
        window = None
        if self.attach_to is not None:
            window = self.attach_to.get_parent_window()
            if not window:
                window = self.attach_to.get_root_window()
        if not window:
            from kivy.core.window import Window
            window = Window
        return window

    def open(self, *largs):
        '''Show the popup window from the :data:`attach_to` widget. If set, it
        will attach to the nearest window. If the widget is not attached to any
        window, the popup will attach to the global
        :class:`~kivy.core.window.Window`.
        '''
        # search window
        self._window = self._search_window()
        if not self._window:
            Logger.warning('Popup: cannot open popup, no window found.')
            return self
        self._window.add_widget(self)
        self._window.bind(on_resize=self._align_center)
        self.center = self._window.center
        Animation(_anim_alpha=1., d=self._anim_duration).start(self)
        self.dispatch('on_open')
        return self

    def dismiss(self, *largs, **kwargs):
        '''Close the popup if it's opened. If you really want to close the
        popup, whatever the on_dismiss event return, you can do like this:
        ::

            popup = Popup(...)
            popup.dismiss(force=True)

        '''
        if self._window is None:
            return self
        if self.dispatch('on_dismiss') is True:
            if kwargs.get('force', False) is not True:
                return self
        Animation(_anim_alpha=0., d=self._anim_duration).start(self)
        return self

    def on_size(self, instance, value):
        self._align_center()

    def _align_center(self, *l):
        if self._window:
            self.center = self._window.center

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            if self.auto_dismiss:
                self.dismiss()
                return True
        super(Popup, self).on_touch_down(touch)
        return True

    def on_touch_move(self, touch):
        super(Popup, self).on_touch_move(touch)
        return True

    def on_touch_up(self, touch):
        super(Popup, self).on_touch_up(touch)
        return True

    def on__anim_alpha(self, instance, value):
        if value == 0 and self._window is not None:
            self._window.remove_widget(self)
            self._window.unbind(on_resize=self._align_center)
            self._window = None

    def on_content(self, instance, value):
        if not hasattr(value, 'popup'):
            value.create_property('popup')
        value.popup = self
        if self._container:
            self._container.clear_widgets()
            self._container.add_widget(value)

    def on__container(self, instance, value):
        if value is None or self.content is None:
            return
        self._container.clear_widgets()
        self._container.add_widget(self.content)

    def on_open(self):
        pass

    def on_dismiss(self):
        pass


if __name__ == '__main__':
    from kivy.base import runTouchApp
    from kivy.uix.button import Button
    from kivy.uix.label import Label
    from kivy.uix.gridlayout import GridLayout
    from kivy.core.window import Window

    layout = GridLayout(cols=3)
    for x in xrange(9):
        btn = Button(text=str(x))
        layout.add_widget(btn)
    Window.add_widget(layout)

    # add popup
    content = GridLayout(cols=1)
    content_cancel = Button(text='Cancel', size_hint_y=None, height=40)
    content.add_widget(Label(text='This is an hello world'))
    content.add_widget(content_cancel)
    popup = Popup(title='Test popup',
                  size_hint=(None, None), size=(256, 256),
                  content=content)
    content_cancel.bind(on_release=popup.dismiss)
    btn.bind(on_release=popup.open)

    popup.open()

    runTouchApp()
