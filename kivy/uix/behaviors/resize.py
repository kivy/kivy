'''
Resizable Behavior
===============

The :class:`~kivy.uix.behaviors.resize.ResizableBehavior`
`mixin <https://en.wikipedia.org/wiki/Mixin>`_ class provides Resize behavior.
When combined with a widget, dragging at the resize enabled widget edge
defined by the
:attr:`~kivy.uix.behaviors.resize.ResizableBehavior.resizable_border`
will resize the widget.

For an overview of behaviors, please refer to the :mod:`~kivy.uix.behaviors`
documentation.

Example
-------

The following example adds resize behavior to a sidebar to make it resizable

    from kivy.app import App
    from kivy.uix.floatlayout import FloatLayout
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.behaviors import ResizableBehavior
    from kivy.uix.label import Label
    from kivy.metrics import cm
    from kivy.uix.button import Button
    from kivy.graphics import *


    class ResizableSideBar(ResizableBehavior, BoxLayout):
        def __init__(self, **kwargs):
            super(ResizableSideBar, self).__init__(**kwargs)
            self.bg = Rectangle(pos=self.pos, size=self.size)
            self.resizable_right = True
            for x in range(1, 10):
                lbl = Label(size_hint=(1, None), height=(cm(1)))
                lbl.text = 'Text '+str(x)
                self.add_widget(lbl)
            self.bind(size=lambda obj, val: setattr(self.bg, 'size', val))

            instr = InstructionGroup()
            instr.add(Color(0.6, 0.6, 0.7, 1))
            instr.add(self.bg)
            self.canvas.before.add(instr)

    class Sample(FloatLayout):
        def __init__(self, **kwargs):
            super(Sample, self).__init__(**kwargs)
            sb = ResizableSideBar(orientation='vertical', size_hint=(None, 1))
            sb.width = cm(4)
            self.add_widget(sb)


    class SampleApp(App):
        def build(self):
            return Sample()


    SampleApp().run()

See :class:`~kivy.uix.behaviors.ResizableBehavior` for details.
'''

from __future__ import print_function
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.properties import BooleanProperty, NumericProperty, \
    StringProperty
from kivy.metrics import dp, cm
from kivy.graphics import Rectangle
from kivy.graphics import InstructionGroup

__all__ = ('ResizableBehavior', )


class ResizableCursor(Widget):
    '''
    The ResizableCursor is the mouse cursor

    .. versionadded:: 1.9.2
    '''

    hidden = BooleanProperty(False)
    '''State of cursors visibility
    It is switched to True when mouse is inside the widgets resize border
    and False when it isn't.

    :attr:`hidden` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    sides = ()
    source = StringProperty('')

    def __init__(self, parent, **kwargs):
        super(ResizableCursor, self).__init__(**kwargs)
        self.size_hint = (None, None)
        self.pos_hint = (None, None)
        self.source = 'data/images/resizable/transparent.png'
        self.parent = parent
        self.size = (dp(22), dp(22))
        self.pos = [-9999, -9999]

        # Makes an instruction group with a rectangle and
        # loads an image inside it
        # Binds its properties to mouse positional changes and events triggered
        instr = InstructionGroup()
        self.rect = Rectangle(pos=self.pos, size=self.size, source=self.source)
        instr.add(self.rect)
        self.parent.canvas.after.add(instr)
        self.bind(pos=lambda obj, val: setattr(self.rect, 'pos', val))
        self.bind(source=lambda obj, val: setattr(self.rect, 'source', val))
        self.bind(hidden=lambda obj, val: self.on_mouse_move(Window.mouse_pos))

    def on_mouse_move(self, val):
        if self.hidden:
            if self.pos[0] != -9999:
                self.pos[0] = -9999
        else:
            self.pos[0] = val[0] - self.width / 2.0
            self.pos[1] = val[1] - self.height / 2.0

    def change_side(self, left, right, up, down):
        # Changes images when ResizableBehavior.hovering_resizable
        # state changes
        if not self.hidden and self.sides != (left, right, up, down):
            if left and up or right and down:
                self.source = 'data/images/resizable/resize2.png'
            elif left and down or right and up:
                self.source = 'data/images/resizable/resize1.png'
            elif left or right:
                self.source = 'data/images/resizable/resize_horizontal.png'
            elif up or down:
                self.source = 'data/images/resizable/resize_vertical.png'
            else:
                if not any((left, right, up, down)):
                    self.source = 'data/images/resizable/transparent.png'
            self.sides = (left, right, up, down)


class ResizableBehavior(object):
    '''
    The ResizableBehavior `mixin <https://en.wikipedia.org/wiki/Mixin>`_
    class provides Resize behavior.
    When combined with a widget, dragging at the resize enabled widget edge
    defined by the
    :attr:`~kivy.uix.behaviors.resize.ResizableBehavior.resizable_border`
    will resize the widget. Please see the :mod:`drag behaviors module
    <kivy.uix.behaviors.resize>` documentation for more information.

    .. versionadded:: 1.9.2
    '''

    hovering = BooleanProperty(False)
    '''State of mouse hover.
    It is switched to True when mouse is on the widget and False when it isn't

    :attr:`hovering` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    hovering_resizable = BooleanProperty(False)
    '''State of mouse hover.
    It is switched to True when mouse is inside the widgets resize border
    and False when it isn't.

    :attr:`hovering_resizable` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to False.
    '''

    resizable_border = NumericProperty(dp(20))
    '''Widgets resizable border size on each side.
    Minimum resizing size is limited to resizable_border * 3 on all sides

    :attr:`resizable_border` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.5 centimeters.
    '''

    resizable_left = BooleanProperty(False)
    '''Enable / disable resizing on left side

    :attr:`resizable_left` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    resizable_right = BooleanProperty(False)
    '''Enable / disable resizing on right side

    :attr:`resizable_right` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    resizable_up = BooleanProperty(False)
    '''Enable / disable resizing on upper side

    :attr:`resizable_up` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    resizable_down = BooleanProperty(False)
    '''Enable / disable resizing on lower side

    :attr:`resizable_down` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    resizing_left = BooleanProperty(False)
    '''A State which is enabled/disabled depending on the position relative to
    the left resize border
    It is switched to True when mouse is inside the left resize border and
    False when it isn't.
    It adjusts the mouse cursor and manages resizing when touch is moved.

    :attr:`resizing_left` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    resizing_right = BooleanProperty(False)
    '''A State which is enabled/disabled depending on the position relative to
    the right resize border
    It is switched to True when mouse is inside the right resize border and
    False when it isn't.
    It adjusts the mouse cursor and manages resizing when touch is moved.

    :attr:`resizing_right` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    resizing_up = BooleanProperty(False)
    '''A State which is enabled/disabled depending on the position relative
    to the upper resize border
    It is switched to True when mouse is inside the upper resize border and
    False when it isn't.
    It adjusts the mouse cursor and manages resizing when touch is moved.

    :attr:`resizing_up` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    resizing_down = BooleanProperty(False)
    '''A State which is enabled/disabled depending on the position relative
    to the lower resize border
    It is switched to True when mouse is inside the lower resize border and
    False when it isn't.
    It adjusts the mouse cursor and manages resizing when touch is moved.

    :attr:`resizing_down` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    resizing = BooleanProperty(False)
    '''State of widget resizing.
    It is switched to True when a resize border is touched and back to
    False when it is released.
    It manages resizing when touch is moved.

    :attr:`resizing` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    can_move_resize = BooleanProperty(True)
    '''Move widget when resizing down or left.
    To keep position on screen in a floatlayout,
    actual postition has to be adjusted.
    Resizing and changing position variables is problematic
    inside movement restricting widgets,
    (StackLayout, BoxLayout, others) this property manages that.

    :attr:`can_move_resize` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to True.
    '''

    def __init__(self, **kwargs):
        super(ResizableBehavior, self).__init__(**kwargs)
        Window.bind(mouse_pos=lambda obj, val: self.on_mouse_move(val))
        self.cursor = None
        self.oldpos = []
        self.oldsize = []
        self.cursor = ResizableCursor(parent=self)

    def on_enter(self):
        self.on_enter_resizable()

    def on_leave(self):
        self.cursor.hidden = True

    def on_enter_resizable(self):
        Window.show_cursor = False
        self.cursor.hidden = False

    def on_leave_resizable(self):
        Window.show_cursor = True
        self.cursor.hidden = True

    def on_mouse_move(self, pos):
        if self.hovering and self.cursor:
            self.cursor.on_mouse_move(pos)
            if not self.resizing:
                if not self.collide_point(pos[0], pos[1]):
                    self.hovering = False
                    self.on_leave()
                    self.on_leave_resizable()
                else:
                    chkr = self.check_resizable_side(pos)
                    if chkr != self.hovering_resizable:
                        self.hovering_resizable = chkr
                        if chkr:
                            self.on_enter_resizable()
                        else:
                            self.on_leave_resizable()
        else:
            if self.collide_point(pos[0], pos[1]):
                self.hovering = True
                if not self.resizing:
                    self.check_resizable_side(pos)
                self.on_enter()

    def check_resizable_side(self, mpos):
        if self.resizable_left:
            self.resizing_left = False
            if mpos[0] > self.pos[0]:
                if mpos[0] < self.pos[0] + self.resizable_border:
                    self.resizing_left = True
        if self.resizable_right and not self.resizing_left:
            self.resizing_right = False
            if mpos[0] < self.pos[0] + self.width:
                if mpos[0] > self.pos[0] + self.width - self.resizable_border:
                    self.resizing_right = True
        if self.resizable_down:
            self.resizing_down = False
            if mpos[1] > self.pos[1]:
                if mpos[1] < self.pos[1] + self.resizable_border:
                    self.resizing_down = True
        if self.resizable_up and not self.resizing_down:
            self.resizing_up = False
            if mpos[1] < self.pos[1] + self.height:
                if mpos[1] > self.pos[1] + self.height - self.resizable_border:
                    self.resizing_up = True
        if self.cursor:
            self.cursor.change_side(
                self.resizing_left, self.resizing_right,
                self.resizing_up, self.resizing_down)
        if any((self.resizing_left, self.resizing_right,
               self.resizing_up, self.resizing_down)):
            return True
        else:
            return False

    def on_touch_down(self, touch):
        if not self.hovering:
            return super(ResizableBehavior, self).on_touch_down(touch)
        if not any([
            self.resizing_right, self.resizing_left,
            self.resizing_down, self.resizing_up
        ]):
            return super(ResizableBehavior, self).on_touch_down(touch)
        self.oldpos = list(self.pos)
        self.oldsize = list(self.size)
        self.resizing = True
        Window.show_cursor = False
        return True

    def on_touch_move(self, touch):
        if not self.resizing:
            return super(ResizableBehavior, self).on_touch_move(touch)
        rb3 = self.resizable_border * 3
        if self.resizing_right:
            if touch.pos[0] > self.pos[0] + rb3:
                self.width = touch.pos[0] - self.pos[0]
        elif self.resizing_left:
            if touch.pos[0] < self.oldpos[0] + self.oldsize[0] - rb3:
                if self.can_move_resize:
                    self.pos[0] = touch.pos[0]
                    self.width = self.oldpos[0] - touch.pos[0] + \
                        self.oldsize[0]
                else:
                    self.width = abs(touch.pos[0] - self.pos[0])
                    if self.width < rb3:
                        self.width = rb3
        if self.resizing_down:
            if touch.pos[1] < self.oldpos[1] + self.oldsize[1] - rb3:
                if self.can_move_resize:
                    self.pos[1] = touch.pos[1]
                    self.height = self.oldpos[1] - touch.pos[1] + \
                        self.oldsize[1]
                else:
                    self.height = abs(touch.pos[1] - self.pos[1])
                    if self.height < rb3:
                        self.height = rb3
        elif self.resizing_up:
            if touch.pos[1] > self.pos[1] + rb3:
                self.height = touch.pos[1] - self.pos[1]
        return True

    def on_touch_up(self, touch):
        if not self.resizing:
            return super(ResizableBehavior, self).on_touch_up(touch)
        self.resizing = False
        self.resizing_right = False
        self.resizing_left = False
        self.resizing_down = False
        self.resizing_up = False
        Window.show_cursor = True
        return True
