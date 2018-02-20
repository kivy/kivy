'''
ModalView
=========

.. versionadded:: 1.4.0

The :class:`ModalView` widget is used to create modal views. By default, the
view will cover the whole "parent" window.

Remember that the default size of a Widget is size_hint=(1, 1). If you don't
want your view to be fullscreen, either use size hints with values lower than
1 (for instance size_hint=(.8, .8)) or deactivate the size_hint and use fixed
size attributes.

Examples
--------

Example of a simple 400x400 Hello world view::

    view = ModalView(size_hint=(None, None), size=(400, 400))
    view.add_widget(Label(text='Hello world'))

By default, any click outside the view will dismiss it. If you don't
want that, you can set :attr:`ModalView.auto_dismiss` to False::

    view = ModalView(auto_dismiss=False)
    view.add_widget(Label(text='Hello world'))
    view.open()

To manually dismiss/close the view, use the :meth:`ModalView.dismiss` method of
the ModalView instance::

    view.dismiss()

Both :meth:`ModalView.open` and :meth:`ModalView.dismiss` are bindable. That
means you can directly bind the function to an action, e.g. to a button's
on_press ::

    # create content and add it to the view
    content = Button(text='Close me!')
    view = ModalView(auto_dismiss=False)
    view.add_widget(content)

    # bind the on_press event of the button to the dismiss function
    content.bind(on_press=view.dismiss)

    # open the view
    view.open()


ModalView Events
----------------

There are two events available: `on_open` which is raised when the view is
opening, and `on_dismiss` which is raised when the view is closed.
For `on_dismiss`, you can prevent the view from closing by explictly returning
True from your callback. ::

    def my_callback(instance):
        print('ModalView', instance, 'is being dismissed, but is prevented!')
        return True
    view = ModalView()
    view.add_widget(Label(text='Hello world'))
    view.bind(on_dismiss=my_callback)
    view.open()


.. versionchanged:: 1.5.0
    The ModalView can be closed by hitting the escape key on the
    keyboard if the :attr:`ModalView.auto_dismiss` property is True (the
    default).

'''

__all__ = ('ModalView', )

from kivy.logger import Logger
from kivy.animation import Animation
from kivy.uix.anchorlayout import AnchorLayout
from kivy.properties import StringProperty, BooleanProperty, ObjectProperty, \
    NumericProperty, ListProperty


class ModalView(AnchorLayout):
    '''ModalView class. See module documentation for more information.

    :Events:
        `on_open`:
            Fired when the ModalView is opened.
        `on_dismiss`:
            Fired when the ModalView is closed. If the callback returns True,
            the dismiss will be canceled.
    '''

    auto_dismiss = BooleanProperty(True)
    '''This property determines if the view is automatically
    dismissed when the user clicks outside it.

    :attr:`auto_dismiss` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to True.
    '''

    attach_to = ObjectProperty(None)
    '''If a widget is set on attach_to, the view will attach to the nearest
    parent window of the widget. If none is found, it will attach to the
    main/global Window.

    :attr:`attach_to` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    '''

    background_color = ListProperty([0, 0, 0, .7])
    '''Background color in the format (r, g, b, a).

    :attr:`background_color` is a :class:`~kivy.properties.ListProperty` and
    defaults to [0, 0, 0, .7].
    '''

    background = StringProperty(
        'atlas://data/images/defaulttheme/modalview-background')
    '''Background image of the view used for the view background.

    :attr:`background` is a :class:`~kivy.properties.StringProperty` and
    defaults to 'atlas://data/images/defaulttheme/modalview-background'.
    '''

    border = ListProperty([16, 16, 16, 16])
    '''Border used for :class:`~kivy.graphics.vertex_instructions.BorderImage`
    graphics instruction. Used for the :attr:`background_normal` and the
    :attr:`background_down` properties. Can be used when using custom
    backgrounds.

    It must be a list of four values: (bottom, right, top, left). Read the
    BorderImage instructions for more information about how to use it.

    :attr:`border` is a :class:`~kivy.properties.ListProperty` and defaults to
    (16, 16, 16, 16).
    '''

    # Internals properties used for graphical representation.

    _anim_alpha = NumericProperty(0)

    _anim_duration = NumericProperty(.1)

    _window = ObjectProperty(None, allownone=True, rebind=True)

    __events__ = ('on_open', 'on_dismiss')

    def __init__(self, **kwargs):
        self._parent = None
        super(ModalView, self).__init__(**kwargs)

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

    def open(self, *largs, **kwargs):
        '''Show the view window from the :attr:`attach_to` widget. If set, it
        will attach to the nearest window. If the widget is not attached to any
        window, the view will attach to the global
        :class:`~kivy.core.window.Window`.

        When the view is opened, it will be faded in with an animation. If you
        don't want the animation, use::

            view.open(animation=False)

        '''
        if self._window is not None:
            Logger.warning('ModalView: you can only open once.')
            return
        # search window
        self._window = self._search_window()
        if not self._window:
            Logger.warning('ModalView: cannot open view, no window found.')
            return
        self._window.add_widget(self)
        self._window.bind(
            on_resize=self._align_center,
            on_keyboard=self._handle_keyboard)
        self.center = self._window.center
        self.fbind('center', self._align_center)
        self.fbind('size', self._align_center)
        if kwargs.get('animation', True):
            a = Animation(_anim_alpha=1., d=self._anim_duration)
            a.bind(on_complete=lambda *x: self.dispatch('on_open'))
            a.start(self)
        else:
            self._anim_alpha = 1.
            self.dispatch('on_open')

    def dismiss(self, *largs, **kwargs):
        '''Close the view if it is open. If you really want to close the
        view, whatever the on_dismiss event returns, you can use the *force*
        argument:
        ::

            view = ModalView()
            view.dismiss(force=True)

        When the view is dismissed, it will be faded out before being
        removed from the parent. If you don't want animation, use::

            view.dismiss(animation=False)

        '''
        if self._window is None:
            return
        if self.dispatch('on_dismiss') is True:
            if kwargs.get('force', False) is not True:
                return
        if kwargs.get('animation', True):
            Animation(_anim_alpha=0., d=self._anim_duration).start(self)
        else:
            self._anim_alpha = 0
            self._real_remove_widget()

    def _align_center(self, *l):
        if self._window:
            self.center = self._window.center

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            if self.auto_dismiss:
                self.dismiss()
                return True
        super(ModalView, self).on_touch_down(touch)
        return True

    def on_touch_move(self, touch):
        super(ModalView, self).on_touch_move(touch)
        return True

    def on_touch_up(self, touch):
        super(ModalView, self).on_touch_up(touch)
        return True

    def on__anim_alpha(self, instance, value):
        if value == 0 and self._window is not None:
            self._real_remove_widget()

    def _real_remove_widget(self):
        if self._window is None:
            return
        self._window.remove_widget(self)
        self._window.unbind(
            on_resize=self._align_center,
            on_keyboard=self._handle_keyboard)
        self._window = None

    def on_open(self):
        pass

    def on_dismiss(self):
        pass

    def _handle_keyboard(self, window, key, *largs):
        if key == 27 and self.auto_dismiss:
            self.dismiss()
            return True


if __name__ == '__main__':
    from kivy.base import runTouchApp
    from kivy.uix.button import Button
    from kivy.uix.label import Label
    from kivy.uix.gridlayout import GridLayout
    from kivy.core.window import Window

    # add view
    content = GridLayout(cols=1)
    content.add_widget(Label(text='This is a hello world'))
    view = ModalView(size_hint=(None, None), size=(256, 256),
                     auto_dismiss=True)
    view.add_widget(content)

    def open_view(btn):
        view.open()

    layout = GridLayout(cols=3)
    for x in range(9):
        btn = Button(text='click me %s' % x)
        btn.bind(on_release=view.open)
        layout.add_widget(btn)
    Window.add_widget(layout)

    view.open()

    runTouchApp()
