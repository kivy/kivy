'''Splitter
======

.. versionadded:: 1.5.0

.. image:: images/splitter.jpg
    :align: right

The :class:`Splitter` is a widget that helps you re-size it's child
widget/layout by letting you re-size it via dragging the boundary or
double tapping the boundary. This widget is similar to the
:class:`~kivy.uix.scrollview.ScrollView` in that it allows only one
child widget.

Usage::

    splitter = Splitter(sizable_from = 'right')
    splitter.add_widget(layout_or_widget_instance)
    splitter.min_size = 100
    splitter.max_size = 250

To change the size of the strip/border used for resizing::

    splitter.strip_size = '10pt'

To change its appearance::

    splitter.strip_cls = your_custom_class

You can also change the appearance of the `strip_cls`, which defaults to
:class:`SplitterStrip`, by overriding the `kv` rule in your app:

.. code-block:: kv

    <SplitterStrip>:
        horizontal: True if self.parent and self.parent.sizable_from[0] \
in ('t', 'b') else False
        background_normal: 'path to normal horizontal image' \
if self.horizontal else 'path to vertical normal image'
        background_down: 'path to pressed horizontal image' \
if self.horizontal else 'path to vertical pressed image'

'''


__all__ = ('Splitter', )

from kivy.compat import string_types
from kivy.factory import Factory
from kivy.uix.button import Button
from kivy.properties import (OptionProperty, NumericProperty, ObjectProperty,
                             ListProperty, BooleanProperty)
from kivy.uix.boxlayout import BoxLayout


class SplitterStrip(Button):
    '''Class used for tbe graphical representation of a
    :class:`kivy.uix.splitter.SplitterStripe`.
    '''
    pass


class Splitter(BoxLayout):
    '''See module documentation.

    :Events:
        `on_press`:
            Fired when the splitter is pressed.
        `on_release`:
            Fired when the splitter is released.

    .. versionchanged:: 1.6.0
        Added `on_press` and `on_release` events.

    '''

    border = ListProperty([4, 4, 4, 4])
    '''Border used for the
    :class:`~kivy.graphics.vertex_instructions.BorderImage`
    graphics instruction.

    This must be a list of four values: (bottom, right, top, left).
    Read the BorderImage instructions for more information about how
    to use it.

    :attr:`border` is a :class:`~kivy.properties.ListProperty` and
    defaults to (4, 4, 4, 4).
    '''

    strip_cls = ObjectProperty(SplitterStrip)
    '''Specifies the class of the resize Strip.

    :attr:`strip_cls` is an :class:`kivy.properties.ObjectProperty` and
    defaults to :class:`~kivy.uix.splitter.SplitterStrip`, which is of type
    :class:`~kivy.uix.button.Button`.

    .. versionchanged:: 1.8.0
        If you set a string, the :class:`~kivy.factory.Factory` will be used to
        resolve the class.

    '''

    sizable_from = OptionProperty('left', options=(
        'left', 'right', 'top', 'bottom'))
    '''Specifies whether the widget is resizable. Options are:
    `left`, `right`, `top` or `bottom`

    :attr:`sizable_from` is an :class:`~kivy.properties.OptionProperty`
    and defaults to `left`.
    '''

    strip_size = NumericProperty('10pt')
    '''Specifies the size of resize strip

    :attr:`strp_size` is a :class:`~kivy.properties.NumericProperty`
    defaults to `10pt`
    '''

    min_size = NumericProperty('100pt')
    '''Specifies the minimum size beyond which the widget is not resizable.

    :attr:`min_size` is a :class:`~kivy.properties.NumericProperty` and
    defaults to `100pt`.
    '''

    max_size = NumericProperty('500pt')
    '''Specifies the maximum size beyond which the widget is not resizable.

    :attr:`max_size` is a :class:`~kivy.properties.NumericProperty`
    and defaults to `500pt`.
    '''

    _parent_proportion = NumericProperty(0.)
    '''(internal) Specifies the distance that the slider has travelled
    across its parent, used to automatically maintain a sensible
    position if the parent is resized.

    :attr:`_parent_proportion` is a
    :class:`~kivy.properties.NumericProperty` and defaults to 0.

    .. versionadded:: 1.9.0
    '''

    _bound_parent = ObjectProperty(None, allownone=True)
    '''(internal) References the widget whose size is currently being
    tracked by :attr:`_parent_proportion`.

    :attr:`_bound_parent` is a
    :class:`~kivy.properties.ObjectProperty` and defaults to None.

    .. versionadded:: 1.9.0
    '''

    keep_within_parent = BooleanProperty(False)
    '''If True, will limit the splitter to stay within its parent widget.

    :attr:`keep_within_parent` is a
    :class:`~kivy.properties.BooleanProperty` and defaults to False.

    .. versionadded:: 1.9.0
    '''

    rescale_with_parent = BooleanProperty(False)
    '''If True, will automatically change size to take up the same
    proportion of the parent widget when it is resized, while
    staying within :attr:`min_size` and :attr:`max_size`. As long as
    these attributes can be satisfied, this stops the
    :class:`Splitter` from exceeding the parent size during rescaling.

    :attr:`rescale_with_parent` is a
    :class:`~kivy.properties.BooleanProperty` and defaults to False.

    .. versionadded:: 1.9.0
    '''

    __events__ = ('on_press', 'on_release')

    def __init__(self, **kwargs):
        self._container = None
        self._strip = None
        super(Splitter, self).__init__(**kwargs)

        do_size = self._do_size
        fbind = self.fbind
        fbind('max_size', do_size)
        fbind('min_size', do_size)
        fbind('parent', self._rebind_parent)

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
            cls = instance.strip_cls
            if isinstance(cls, string_types):
                cls = Factory.get(cls)
            instance._strip = _strp = cls()

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

    def _rebind_parent(self, instance, new_parent):
        if self._bound_parent is not None:
            self._bound_parent.unbind(size=self.rescale_parent_proportion)
        if self.parent is not None:
            new_parent.bind(size=self.rescale_parent_proportion)
        self._bound_parent = new_parent
        self.rescale_parent_proportion()

    def rescale_parent_proportion(self, *args):
        if not self.parent:
            return
        if self.rescale_with_parent:
            parent_proportion = self._parent_proportion
            if self.sizable_from in ('top', 'bottom'):
                new_height = parent_proportion * self.parent.height
                self.height = max(self.min_size,
                                 min(new_height, self.max_size))
            else:
                new_width = parent_proportion * self.parent.width
                self.width = max(self.min_size, min(new_width, self.max_size))

    def _do_size(self, instance, value):
        if self.sizable_from[0] in ('l', 'r'):
            self.width = max(self.min_size, min(self.width, self.max_size))
        else:
            self.height = max(self.min_size, min(self.height, self.max_size))

    def strip_move(self, instance, touch):
        if touch.grab_current is not instance:
            return False
        max_size = self.max_size
        min_size = self.min_size
        sz_frm = self.sizable_from[0]

        if sz_frm in ('t', 'b'):
            diff_y = (touch.dy)
            if self.keep_within_parent:
                if sz_frm == 't' and (self.top + diff_y) > self.parent.top:
                    diff_y = self.parent.top - self.top
                elif sz_frm == 'b' and (self.y + diff_y) < self.parent.y:
                    diff_y = self.parent.y - self.y
            if sz_frm == 'b':
                diff_y *= -1
            if self.size_hint_y:
                self.size_hint_y = None
            if self.height > 0:
                self.height += diff_y
            else:
                self.height = 1

            height = self.height
            self.height = max(min_size, min(height, max_size))

            self._parent_proportion = self.height / self.parent.height
        else:
            diff_x = (touch.dx)
            if self.keep_within_parent:
                if sz_frm == 'l' and (self.x + diff_x) < self.parent.x:
                    diff_x = self.parent.x - self.x
                elif (sz_frm == 'r' and
                      (self.right + diff_x) > self.parent.right):
                    diff_x = self.parent.right - self.right
            if sz_frm == 'l':
                diff_x *= -1
            if self.size_hint_x:
                self.size_hint_x = None
            if self.width > 0:
                self.width += diff_x
            else:
                self.width = 1

            width = self.width
            self.width = max(min_size, min(width, max_size))

            self._parent_proportion = self.width / self.parent.width

    def strip_up(self, instance, touch):
        if touch.grab_current is not instance:
            return

        if touch.is_double_tap:
            max_size = self.max_size
            min_size = self.min_size
            sz_frm = self.sizable_from[0]
            s = self.size

            if sz_frm in ('t', 'b'):
                if self.size_hint_y:
                    self.size_hint_y = None
                if s[1] - min_size <= max_size - s[1]:
                    self.height = max_size
                else:
                    self.height = min_size
            else:
                if self.size_hint_x:
                    self.size_hint_x = None
                if s[0] - min_size <= max_size - s[0]:
                    self.width = max_size
                else:
                    self.width = min_size
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
                pos_hint={'top': 1},
                sizable_from='bottom')
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
