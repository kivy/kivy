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

from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.properties import BooleanProperty, NumericProperty, \
    StringProperty, ListProperty
from kivy.metrics import dp, cm
from kivy.graphics import Rectangle
from kivy.graphics import InstructionGroup
from kivy.uix.modalview import ModalView
from kivy.logger import Logger
from kivy.app import App
from time import time

__all__ = ('ResizableBehavior', )


class ModalViewModified(ModalView):
    '''
    The ModalViewModified is the parent of ResizableCursor

    .. versionadded:: 1.9.2
    '''

    last_opened = 0.0

    def __init__(self, **kwargs):
        super(ModalViewModified, self).__init__(**kwargs)
        self.auto_dismiss = False
        self.size_hint = (None, None)
        self.background_color = (0, 0, 0, 0)
        self.pos = (-9999, -9999)
        self.cursor = ResizableCursor()
        self.add_widget(self.cursor)
        self.open()

    def open(self, *largs):
        self._window = self._search_window()
        if not self._window:
            Logger.warning('ModalView: cannot open view, no window found.')
            return
        self._window.add_widget(self)

    def put_on_top(self, *args):
        self.dismiss()
        self.open()

    def on_hidden(self, val):
        # View has to be reopened to get it on top of other widgets
        timenow = time()
        if not val and timenow > self.last_opened + 1:
            self.dismiss()
            self.open()
            self.last_opened = timenow

    def on_touch_down(self, *args):
        pass

    def on_touch_up(self, *args):
        pass

    def on_touch_move(self, *args):
        pass


class ResizableCursor(Widget):
    '''
    The ResizableCursor is the mouse cursor

    .. versionadded:: 1.9.2
    '''

    hidden = BooleanProperty(True)
    '''State of cursors visibility
    It is switched to True when mouse is inside the widgets resize border
    and False when it isn't.

    :attr:`hidden` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to True.
    '''

    resize_icon_paths = ListProperty([
    'data/images/resizable/resize_horizontal.png',
    'data/images/resizable/resize2.png',
    'data/images/resizable/resize_vertical.png',
    'data/images/resizable/resize1.png',
    'data/images/resizable/transparent.png'
    ])
    '''Cursor icon paths,

    :attr:`resize_icon_paths` is a :class:`~kivy.properties.ListProperty` and
    defaults to [
    'data/images/resizable/resize_horizontal.png',
    'data/images/resizable/resize2.png',
    'data/images/resizable/resize_vertical.png',
    'data/images/resizable/resize1.png',
    'data/images/resizable/transparent.png'
    ]
    '''

    grabbed_by = None
    '''Object reference.
    Is used to prevent attribute changes from multiple widgets at same time.

    :attr:`grabbed_by` defaults to None.
    '''

    sides = ()
    source = StringProperty('')

    def __init__(self, **kwargs):
        super(ResizableCursor, self).__init__(**kwargs)
        self.size_hint = (None, None)
        self.pos_hint = (None, None)
        self.source = ''
        self.rect = Rectangle(pos=(-9998,-9998), size=(1, 1))
        self.size = (dp(22), dp(22))
        self.pos = [-9998, -9998]

        # Makes an instruction group with a rectangle and
        # loads an image inside it
        # Binds its properties to mouse positional changes and events triggered
        instr = InstructionGroup()
        instr.add(self.rect)
        self.canvas.after.add(instr)
        self.bind(pos=lambda obj, val: setattr(self.rect, 'pos', val))
        self.bind(source=lambda obj, val: setattr(self.rect, 'source', val))
        self.bind(hidden=lambda obj, val: self.on_mouse_move(Window.mouse_pos))
        Window.bind(mouse_pos=lambda obj, val: self.on_mouse_move(val))

    def on_size(self, obj, val):
        self.rect.size = val

    def on_hidden(self, obj, val):
        if not self.disabled:
            self.parent.on_hidden(val)
            if val:
                Window.show_cursor = True
            else:
                Window.show_cursor = False

    def on_mouse_move(self, val):
        if self.hidden or self.disabled or not self.source:
            if self.pos[0] != -9999:
                self.pos[0] = -9999
        else:
            self.pos[0] = val[0] - self.width / 2.0
            self.pos[1] = val[1] - self.height / 2.0

    def change_side(self, left, right, up, down):
        # Changes images when ResizableBehavior.hovering_resizable
        # state changes
        if self.disabled:
            return
        if not self.hidden and self.sides != (left, right, up, down):
            if left and up or right and down:
                self.source = self.resize_icon_paths[1]
            elif left and down or right and up:
                self.source = self.resize_icon_paths[3]
            elif left or right:
                self.source = self.resize_icon_paths[0]
            elif up or down:
                self.source = self.resize_icon_paths[2]
            else:
                if not any((left, right, up, down)):
                    self.pos[0] = -9999
            self.sides = (left, right, up, down)

    def grab(self, wid):
        self.grabbed_by = wid

    def ungrab(self, wid):
        if self.grabbed_by == wid:
            self.grabbed_by = None

    def on_disabled(self, obj, val):
        if not val:
            Window.show_cursor = True


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
    defaults to 20 dp.
    '''

    resizable_border_offset = NumericProperty(0)
    '''Positive values move the resizable_border outside of the widget
    and negative values put it closer to the center of the widget.
    A value of resizable_border * 0.5 will center it on the widgets border,
    which is the most expected behavior, but can sometimes interfere with
    nearby widgets.

    :attr:`resizable_border_offset` is a
    :class:`~kivy.properties.NumericProperty` and defaults to 0.
    '''

    min_resizable_width = NumericProperty(0)
    '''Minimum width

    :attr:`min_resizable_width` is a :class:`~kivy.properties.NumericProperty`
    and defaults to 0 (disabled).
    '''

    min_resizable_height = NumericProperty(0)
    '''Minimum height

    :attr:`min_resizable_height` is a :class:`~kivy.properties.NumericProperty`
    and defaults to 0 (disabled).
    '''

    max_resizable_width = NumericProperty(0)
    '''Maximum width

    :attr:`max_resizable_width` is a :class:`~kivy.properties.NumericProperty`
    and defaults to 0 (disabled).
    '''

    max_resizable_height = NumericProperty(0)
    '''Maximum height

    :attr:`max_resizable_height` is a :class:`~kivy.properties.NumericProperty`
    and defaults to 0 (disabled).
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

    resize_lock = BooleanProperty(False)
    '''Enable / disable resizing

    :attr:`resize_lock` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    def __init__(self, **kwargs):
        super(ResizableBehavior, self).__init__(**kwargs)
        Window.bind(mouse_pos=lambda obj, val: self.on_mouse_move(val))
        self.cursor = None
        app = App.get_running_app()
        try:
            app.resizable_cursor
        except AttributeError:
            app.resizable_cursor = ModalViewModified()
            Clock.schedule_once(app.resizable_cursor.put_on_top, 0)
        self.modalview = app.resizable_cursor
        self.cursor = self.modalview.cursor
        self.oldpos, self.oldsize = [], []

    def on_enter_resizable(self):
        self.cursor.hidden = False

    def on_leave_resizable(self):
        self.cursor.hidden = True

    def on_mouse_move(self, pos):
        if self.resize_lock:
            return

        if self.cursor and self.cursor.grabbed_by is None:
            oldhover = self.hovering_resizable
            self.hovering_resizable = self.check_resizable_side(pos[0], pos[1])
            if oldhover != self.hovering_resizable:
                if self.hovering_resizable:
                    self.on_enter_resizable()
                else:
                    self.on_leave_resizable()

    def check_resizable_side(self, x, y):
        # Add small performance increase when distance is too high
        # for possible hovering
        if abs(self.x - x) > self.width + self.resizable_border_offset:
            return False
        elif abs(self.y - y) > self.height + self.resizable_border_offset:
            return False

        startx = self.x - self.resizable_border_offset
        endx = self.right + self.resizable_border_offset
        starty = self.y - self.resizable_border_offset
        endy = self.top + self.resizable_border_offset
        if self.resizable_left:
            self.resizing_left = False
            if startx <= x <= startx + self.resizable_border:
                if starty <= y <= endy:
                    self.resizing_left = True
        if self.resizable_right and not self.resizing_left:
            self.resizing_right = False
            if endx - self.resizable_border <= x <= endx:
                if starty <= y <= endy:
                    self.resizing_right = True
        if self.resizable_up:
            self.resizing_up = False
            if endy - self.resizable_border <= y <= endy:
                if startx <= x <= endx:
                    self.resizing_up = True
        if self.resizable_down and not self.resizing_up:
            self.resizing_down = False
            if starty <= y <= starty + self.resizable_border:
                if startx <= x <= endx:
                    self.resizing_down = True

        if any((self.resizing_left, self.resizing_right,
                self.resizing_up, self.resizing_down)):
            if self.cursor:
                self.cursor.change_side(
                    self.resizing_left, self.resizing_right,
                    self.resizing_up, self.resizing_down)
            return True
        else:
            return False

    def on_touch_down(self, touch):
        if not self.hovering_resizable:
            return super(ResizableBehavior, self).on_touch_down(touch)

        if self.resize_lock:
            return super(ResizableBehavior, self).on_touch_down(touch)

        if not any([
            self.resizing_right, self.resizing_left,
            self.resizing_down, self.resizing_up
        ]):
            return super(ResizableBehavior, self).on_touch_down(touch)

        self.oldpos = list(self.pos)
        self.oldsize = list(self.size)
        self.resizing = True
        self.cursor.grab(self)
        return True

    def on_touch_move(self, touch):
        if not self.resizing:
            return super(ResizableBehavior, self).on_touch_move(touch)
        self.resize_widget(touch)

    def resize_widget(self, touch):
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

        self.check_min_max_size(touch)
        return True

    def check_min_max_size(self, touch):
        # Resizes widgets back to min / max when smaller / bigger
        # Resets position only when it's necessary
        if self.min_resizable_width:
            if self.width < self.min_resizable_width:
                if self.pos[0] != self.oldpos[0]:
                    self.width = self.min_resizable_width
                    self.pos[0] = self.oldpos[0] + self.oldsize[0] - self.width
                else:
                    self.width = self.min_resizable_width

        if self.max_resizable_width:
            if self.width > self.max_resizable_width:
                if self.pos[0] != self.oldpos[0]:
                    self.width = self.max_resizable_width
                    self.pos[0] = self.oldpos[0] + self.oldsize[0] - self.width
                else:
                    self.width = self.max_resizable_width

        if self.min_resizable_height:
            if self.height < self.min_resizable_height:
                if self.pos[1] != self.oldpos[1]:
                    self.height = self.min_resizable_height
                    self.pos[1] = (
                        self.oldpos[1] + self.oldsize[1] - self.height)
                else:
                    self.height = self.min_resizable_height

        if self.max_resizable_height:
            if self.height > self.max_resizable_height:
                if self.pos[1] != self.oldpos[1]:
                    self.height = self.max_resizable_height
                    self.pos[1] = (
                        self.oldpos[1] + self.oldsize[1] - self.height)
                else:
                    self.height = self.max_resizable_height

    def on_touch_up(self, touch):
        if not self.resizing:
            return super(ResizableBehavior, self).on_touch_up(touch)
        self.resizing = False
        self.resizing_right = False
        self.resizing_left = False
        self.resizing_down = False
        self.resizing_up = False
        self.cursor.ungrab(self)
        self.on_mouse_move(touch.pos)
        return True

    def on_resize_lock(self, obj, locked):
        'Resets behavior to default values when resizing is locked'
        if locked:
            self.resizing = False
            self.resizing_right = False
            self.resizing_left = False
            self.resizing_down = False
            self.resizing_up = False
            Window.show_cursor = True
            self.cursor.ungrab(self)
            self.cursor.hidden = True

    def set_cursor_size(self, size):
        '''Default cursor size is (dp(22), dp(22)).
        Use this method to change it
        '''
        self.cursor.size = size

    def set_cursor_icons(self, hor, deg45, deg90, deg135):
        '''Change cursor icon paths.
        Function takes 4 arguments, first is horizontal,
        next 3 are turned 45, 90, 135 degrees clockwise.
        '''
        self.cursor.resize_icon_paths[0] = hor
        self.cursor.resize_icon_paths[1] = deg45
        self.cursor.resize_icon_paths[2] = deg90
        self.cursor.resize_icon_paths[3] = deg135

    def set_cursor_mode(self, value):
        '''Method takes expects one integer
        0 - Disables the resize cursor
        1 - Default mode, os cursor is hidden and replaced with resize cursor
        when mouse position enters widgets resizable_border
        '''
        if value == 0 and not self.cursor.disabled:
            self.cursor.disabled = True
        elif value == 1 and self.cursor.disabled:
            self.cursor.disabled = False
