'''
Splitter
======

.. versionadded:: 1.5.0

.. image:: images/splitter.jpg
    :align: right

.. warning::

    This widget is still experimental, and its API is subject to change in
    a future version.

The :class:`Splitter` is a widget that helps you re-size it's child \
widget/layout by letting the user control the size of it's child  by \
dragging the boundary. This widget like :class:`~kivy.uix.scrollview.Scrollview`
allows only one child widget.

Usage::

    splitter = Splitter(sizable_from = 'right')
    splitter.add_widget(layout_or_widget_instance)
    splitter.min_size = 100
    splitter.max_size = 250

Change size of the strip/border used to resize::

    splitter.strip_size = '10pt'

Change appearance::

    splitter.strip_cls = your_custom_class

You could also change the appearance of the `strip_cls` which defaults to
:class:`SplitterStrip` by overriding the `kv` rule for like so in your app::

    <SplitterStrip>:
        horizontal: True if self.parent and self.parent.sizable_from[0] \
in ('t', 'b') else False
        background_normal: 'path to normal horizontal image' \
if self.horizontal else 'path to vertical normal image'
        background_down: 'path to pressed horizontal image' \
if self.horizontal else 'path to vertical pressed image'

'''


__all__ = ('Splitter', )

from kivy.uix.button import Button
from kivy.properties import (OptionProperty, NumericProperty, ObjectProperty,
                            ListProperty, BooleanProperty)
from kivy.uix.boxlayout import BoxLayout


class SplitterStrip(Button):
    '''Class used for graphical representation of \
    :class:`kivy.uix.splitter.SplitterStripe`
    '''
    pass


class Splitter(BoxLayout):
    '''See module documentation.

    :Events:
        `on_press`:
            Fired when the splitter is pressed
        `on_release`:
            Fired when the splitter is released

    .. versionchanged:: 1.6.0
        Added `on_press` and `on_release` events

    '''

    border = ListProperty([4, 4, 4, 4])
    '''Border used for :class:`~kivy.graphics.vertex_instructions.BorderImage`
    graphics instruction.

    It must be a list of four values: (top, right, bottom, left). Read the
    BorderImage instruction for more information about how to use it.

    :data:`border` is a :class:`~kivy.properties.ListProperty`, \
    default to (4, 4, 4, 4)
    '''

    strip_cls = ObjectProperty(SplitterStrip)
    '''Specifies the class of the resize Strip

    :data:`strip_cls` is a :class:`kivy.properties.ObjectProperty`
    defaults to :class:`~kivy.uix.splitter.SplitterStrip` which is of type\
    :class:`~kivy.uix.button.Button`
    '''

    sizable_from = OptionProperty('left',
        options=('left', 'right', 'top', 'bottom'))
    '''Specifies wether the widget is resizable from ::
        `left`, `right`, `top` or `bottom`

    :data:`sizable_from` is a :class:`~kivy.properties.OptionProperty`
    defaults to `left`
    '''

    strip_size = NumericProperty('10pt')
    '''Specifies the size of resize strip

    :data:`strp_size` is a :class:`~kivy.properties.NumericProperty`
    defaults to `10pt`
    '''

    min_size = NumericProperty('100pt')
    '''Specifies the minimum size beyond which the widget is not resizable

    :data:`min_size` is a :class:`~kivy.properties.NumericProperty`
    defaults to `100pt`
    '''

    max_size = NumericProperty('500pt')
    '''Specifies the maximum size beyond which the widget is not resizable

    :data:`max_size` is a :class:`~kivy.properties.NumericProperty`
    defaults to `500pt`
    '''

    __events__ = ('on_press', 'on_release')

    def __init__(self, **kwargs):
        self._container = None
        self._strip = None
        super(Splitter, self).__init__(**kwargs)

    def on_sizable_from(self, instance, sizable_from):
        if not instance._container:
            return

        sup = super(Splitter, instance)
        _strp = instance._strip
        if _strp:
            # remove any previous binds
            _strp.unbind(on_touch_down=instance.strip_down)
            _strp.unbind(on_touch_move=instance.strip_move)
            _strp.unbind(on_touch_up=instance.strip_up)
            self.unbind(disabled=_strp.setter('disabled'))

            sup.remove_widget(instance._strip)
        else:
            instance._strip = _strp = instance.strip_cls()

        sz_frm = instance.sizable_from[0]
        if sz_frm in ('l', 'r'):
            _strp.size_hint = None, 1
            _strp.width = instance.strip_size
            instance.orientation = 'horizontal'
            instance.unbind(strip_size=_strp.setter('width'))
            instance.bind(strip_size=_strp.setter('width'))
        else:
            _strp.size_hint = 1, None
            _strp.height = instance.strip_size
            instance.orientation = 'vertical'
            instance.unbind(strip_size=_strp.setter('height'))
            instance.bind(strip_size=_strp.setter('height'))

        index = 1
        if sz_frm in ('r', 'b'):
            index = 0
        sup.add_widget(_strp, index)

        _strp.bind(on_touch_down=instance.strip_down)
        _strp.bind(on_touch_move=instance.strip_move)
        _strp.bind(on_touch_up=instance.strip_up)
        _strp.disabled = self.disabled
        self.bind(disabled=_strp.setter('disabled'))

    def add_widget(self, widget, index=0):
        if self._container or not widget:
            return Exception('Splitter accepts only one Child')
        self._container = widget
        sz_frm = self.sizable_from[0]
        if sz_frm in ('l', 'r'):
            widget.size_hint_x = 1
        else:
            widget.size_hint_y = 1

        index = 0
        if sz_frm in ('r', 'b'):
            index = 1
        super(Splitter, self).add_widget(widget, index)
        self.on_sizable_from(self, self.sizable_from)

    def remove_widget(self, widget, *largs):
        super(Splitter, self).remove_widget(widget)
        if widget == self._container:
            self._container = None

    def clear_widgets(self):
        self.remove_widget(self._container)

    def strip_down(self, instance, touch):
        if not instance.collide_point(*touch.pos):
            return False
        touch.grab(self)
        self.dispatch('on_press')

    def on_press(self):
        pass

    def strip_move(self, instance, touch):
        if touch.grab_current is not instance:
            return False
        sign = 1
        max_size = self.max_size
        min_size = self.min_size
        sz_frm = self.sizable_from[0]

        if sz_frm in ('t', 'b'):
            diff_y = (touch.dy)
            if sz_frm == 'b':
                sign = -1
            if self.size_hint_y:
                self.size_hint_y = None
            if self.height > 0:
                self.height += sign * diff_y
            else:
                self.height = 1

            height = self.height
            self.height = max(min_size, min(height, max_size))
        else:
            diff_x = (touch.dx)
            if sz_frm == 'l':
                sign = -1
            if self.size_hint_x:
                self.size_hint_x = None
            if self.width > 0:
                self.width += sign * (diff_x)
            else:
                self.width = 1

            width = self.width
            self.width = max(min_size, min(width, max_size))

    def strip_up(self, instance, touch):
        if touch.grab_current is not instance:
            return
        touch.ungrab(instance)
        self.dispatch('on_release')

    def on_release(self):
        pass


if __name__ == '__main__':
    from kivy.app import App
    from kivy.uix.button import Button
    from kivy.uix.floatlayout import FloatLayout

    class SplitterApp(App):

        def build(self):
            root = FloatLayout()
            bx = BoxLayout()
            bx.add_widget(Button())
            bx.add_widget(Button())
            bx2 = BoxLayout()
            bx2.add_widget(Button())
            bx2.add_widget(Button())
            bx2.add_widget(Button())
            spl = Splitter(
                size_hint=(1, .25),
                pos_hint = {'top': 1},
                sizable_from = 'bottom')
            spl1 = Splitter(
                sizable_from='left',
                size_hint=(None, 1), width=90)
            spl1.add_widget(Button())
            bx.add_widget(spl1)
            spl.add_widget(bx)

            spl2 = Splitter(size_hint=(.25, 1))
            spl2.add_widget(bx2)
            spl2.sizable_from = 'right'
            root.add_widget(spl)
            root.add_widget(spl2)
            return root

    SplitterApp().run()
