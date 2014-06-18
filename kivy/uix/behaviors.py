'''
Behaviors
=========

.. versionadded:: 1.8.0

This module implements behaviors that can be mixed with existing base widgets.
For example, if you want to add a "button" capability to an `Image`, you could
do::


    class IconButton(ButtonBehavior, Image):
        pass

.. note::

    The behavior class must always be _before_ the widget class. If you don't
    specify the inheritance in this order, the behavior will not work.

'''

__all__ = ('ButtonBehavior', 'ToggleButtonBehavior', 'DragBehavior',
           'FocusBehavior')

from kivy.clock import Clock
from kivy.properties import OptionProperty, ObjectProperty,\
    NumericProperty, ReferenceListProperty, BooleanProperty, AliasProperty
from kivy.config import Config
from kivy.metrics import sp
from kivy.base import EventLoop
from kivy.logger import Logger
from functools import partial
from weakref import ref

# When we are generating documentation, Config doesn't exist
_scroll_timeout = _scroll_distance = 0
_is_desktop = False
if Config:
    _scroll_timeout = Config.getint('widgets', 'scroll_timeout')
    _scroll_distance = Config.getint('widgets', 'scroll_distance')
    _is_desktop = Config.getboolean('kivy', 'desktop')


class ButtonBehavior(object):
    '''Button behavior.

    :Events:
        `on_press`
            Fired when the button is pressed.
        `on_release`
            Fired when the button is released (i.e. the touch/click that
            pressed the button goes away).
    '''

    state = OptionProperty('normal', options=('normal', 'down'))
    '''State of the button, must be one of 'normal' or 'down'.
    The state is 'down' only when the button is currently touched/clicked,
    otherwise 'normal'.

    :attr:`state` is an :class:`~kivy.properties.OptionProperty`.
    '''

    last_touch = ObjectProperty(None)
    '''Contains the last relevant touch received by the Button. This can
    be used in `on_press` or `on_release` in order to know which touch
    dispatched the event.

    .. versionadded:: 1.8.0

    :attr:`last_touch` is a :class:`~kivy.properties.ObjectProperty`,
    defaults to None.
    '''

    def __init__(self, **kwargs):
        self.register_event_type('on_press')
        self.register_event_type('on_release')
        super(ButtonBehavior, self).__init__(**kwargs)

    def _do_press(self):
        self.state = 'down'

    def _do_release(self):
        self.state = 'normal'

    def on_touch_down(self, touch):
        if super(ButtonBehavior, self).on_touch_down(touch):
            return True
        if touch.is_mouse_scrolling:
            return False
        if not self.collide_point(touch.x, touch.y):
            return False
        if self in touch.ud:
            return False
        touch.grab(self)
        touch.ud[self] = True
        self.last_touch = touch
        self._do_press()
        self.dispatch('on_press')
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            return True
        if super(ButtonBehavior, self).on_touch_move(touch):
            return True
        return self in touch.ud

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return super(ButtonBehavior, self).on_touch_up(touch)
        assert(self in touch.ud)
        touch.ungrab(self)
        self.last_touch = touch
        self._do_release()
        self.dispatch('on_release')
        return True

    def on_press(self):
        pass

    def on_release(self):
        pass

    def trigger_action(self, duration=0.1):
        '''Trigger whatever action(s) have been bound to the button by calling
        both the on_press and on_release callbacks.

        This simulates a quick button press without using any touch events.

        Duration is the length of the press in seconds. Pass 0 if you want
        the action to happen instantly.

        .. versionadded:: 1.8.0
        '''
        self._do_press()
        self.dispatch('on_press')

        def trigger_release(dt):
            self._do_release()
            self.dispatch('on_release')
        if not duration:
            trigger_release(0)
        else:
            Clock.schedule_once(trigger_release, duration)


class ToggleButtonBehavior(ButtonBehavior):
    '''ToggleButton behavior, see ToggleButton module documentation for more
    information.

    .. versionadded:: 1.8.0
    '''

    __groups = {}

    group = ObjectProperty(None, allownone=True)
    '''Group of the button. If None, no group will be used (button is
    independent). If specified, :attr:`group` must be a hashable object, like
    a string. Only one button in a group can be in 'down' state.

    :attr:`group` is a :class:`~kivy.properties.ObjectProperty`
    '''

    def __init__(self, **kwargs):
        self._previous_group = None
        super(ToggleButtonBehavior, self).__init__(**kwargs)

    def on_group(self, *largs):
        groups = ToggleButtonBehavior.__groups
        if self._previous_group:
            group = groups[self._previous_group]
            for item in group[:]:
                if item() is self:
                    group.remove(item)
                    break
        group = self._previous_group = self.group
        if group not in groups:
            groups[group] = []
        r = ref(self, ToggleButtonBehavior._clear_groups)
        groups[group].append(r)

    def _release_group(self, current):
        if self.group is None:
            return
        group = self.__groups[self.group]
        for item in group[:]:
            widget = item()
            if widget is None:
                group.remove(item)
            if widget is current:
                continue
            widget.state = 'normal'

    def _do_press(self):
        self._release_group(self)
        self.state = 'normal' if self.state == 'down' else 'down'

    def _do_release(self):
        pass

    @staticmethod
    def _clear_groups(wk):
        # auto flush the element when the weak reference have been deleted
        groups = ToggleButtonBehavior.__groups
        for group in list(groups.values()):
            if wk in group:
                group.remove(wk)
                break

    @staticmethod
    def get_widgets(groupname):
        '''Return the widgets contained in a specific group. If the group
        doesn't exist, an empty list will be returned.

        .. important::

            Always release the result of this method! In doubt, do::

                l = ToggleButtonBehavior.get_widgets('mygroup')
                # do your job
                del l

        .. warning::

            It's possible that some widgets that you have previously
            deleted are still in the list. Garbage collector might need
            more elements before flushing it. The return of this method
            is informative, you've been warned!
        '''
        groups = ToggleButtonBehavior.__groups
        if groupname not in groups:
            return []
        return [x() for x in groups[groupname] if x()][:]


class DragBehavior(object):
    '''Drag behavior. When combined with a widget, dragging in the rectangle
    defined by :attr:`drag_rectangle` will drag the widget.

    For example, to make a popup which is draggable by its title do::

        from kivy.uix.behaviors import DragBehavior
        from kivy.uix.popup import Popup

        class DragPopup(DragBehavior, Popup):
            pass

    And in .kv do::
        <DragPopup>:
            drag_rectangle: self.x, self.y+self._container.height, self.width,\
            self.height - self._container.height
            drag_timeout: 10000000
            drag_distance: 0

    .. versionadded:: 1.8.0
    '''

    drag_distance = NumericProperty(_scroll_distance)
    '''Distance to move before dragging the :class:`DragBehavior`, in pixels.
    As soon as the distance has been traveled, the :class:`DragBehavior` will
    start to drag, and no touch event will go to children.
    It is advisable that you base this value on the dpi of your target device's
    screen.

    :attr:`drag_distance` is a :class:`~kivy.properties.NumericProperty`,
    defaults to 20 (pixels), according to the default value of scroll_distance
    in user configuration.
    '''

    drag_timeout = NumericProperty(_scroll_timeout)
    '''Timeout allowed to trigger the :attr:`drag_distance`, in milliseconds.
    If the user has not moved :attr:`drag_distance` within the timeout,
    dragging will be disabled, and the touch event will go to the children.

    :attr:`drag_timeout` is a :class:`~kivy.properties.NumericProperty`,
    defaults to 55 (milliseconds), according to the default value of
    scroll_timeout in user configuration.
    '''

    drag_rect_x = NumericProperty(0)
    '''X position of the axis aligned bounding rectangle where dragging
    is allowed. In window coordinates.

    :attr:`drag_rect_x` is a :class:`~kivy.properties.NumericProperty`,
    defaults to 0.
    '''

    drag_rect_y = NumericProperty(0)
    '''Y position of the axis aligned bounding rectangle where dragging
    is allowed. In window coordinates.

    :attr:`drag_rect_Y` is a :class:`~kivy.properties.NumericProperty`,
    defaults to 0.
    '''

    drag_rect_width = NumericProperty(100)
    '''Width of the axis aligned bounding rectangle where dragging is allowed.

    :attr:`drag_rect_width` is a :class:`~kivy.properties.NumericProperty`,
    defaults to 100.
    '''

    drag_rect_height = NumericProperty(100)
    '''Height of the axis aligned bounding rectangle where dragging is allowed.

    :attr:`drag_rect_height` is a :class:`~kivy.properties.NumericProperty`,
    defaults to 100.
    '''

    drag_rectangle = ReferenceListProperty(drag_rect_x, drag_rect_y,
                                           drag_rect_width, drag_rect_height)
    '''Position and size of the axis aligned bounding rectangle where dragging
    is allowed.

    :attr:`drag_rectangle` is a :class:`~kivy.properties.ReferenceListProperty`
    of (:attr:`drag_rect_x`, :attr:`drag_rect_y`, :attr:`drag_rect_width`,
    :attr:`drag_rect_height`) properties.
    '''

    def __init__(self, **kwargs):
        self._drag_touch = None
        super(DragBehavior, self).__init__(**kwargs)

    def _get_uid(self, prefix='sv'):
        return '{0}.{1}'.format(prefix, self.uid)

    def on_touch_down(self, touch):
        xx, yy, w, h = self.drag_rectangle
        x, y = touch.pos
        if not self.collide_point(x, y):
            touch.ud[self._get_uid('svavoid')] = True
            return super(DragBehavior, self).on_touch_down(touch)
        if self._drag_touch or ('button' in touch.profile and
                                touch.button.startswith('scroll')) or\
                not ((xx < x <= xx + w) and (yy < y <= yy + h)):
            return super(DragBehavior, self).on_touch_down(touch)

        # no mouse scrolling, so the user is going to drag with this touch.
        self._drag_touch = touch
        uid = self._get_uid()
        touch.grab(self)
        touch.ud[uid] = {
            'mode': 'unknown',
            'dx': 0,
            'dy': 0}
        Clock.schedule_once(self._change_touch_mode,
                            self.drag_timeout / 1000.)
        return True

    def on_touch_move(self, touch):
        if self._get_uid('svavoid') in touch.ud or\
                self._drag_touch is not touch:
            return super(DragBehavior, self).on_touch_move(touch) or\
                self._get_uid() in touch.ud
        if touch.grab_current is not self:
            return True

        uid = self._get_uid()
        ud = touch.ud[uid]
        mode = ud['mode']
        if mode == 'unknown':
            ud['dx'] += abs(touch.dx)
            ud['dy'] += abs(touch.dy)
            if ud['dx'] > sp(self.drag_distance):
                mode = 'drag'
            if ud['dy'] > sp(self.drag_distance):
                mode = 'drag'
            ud['mode'] = mode
        if mode == 'drag':
            self.x += touch.dx
            self.y += touch.dy
        return True

    def on_touch_up(self, touch):
        if self._get_uid('svavoid') in touch.ud:
            return super(DragBehavior, self).on_touch_up(touch)

        if self._drag_touch and self in [x() for x in touch.grab_list]:
            touch.ungrab(self)
            self._drag_touch = None
            ud = touch.ud[self._get_uid()]
            if ud['mode'] == 'unknown':
                super(DragBehavior, self).on_touch_down(touch)
                Clock.schedule_once(partial(self._do_touch_up, touch), .1)
        else:
            if self._drag_touch is not touch:
                super(DragBehavior, self).on_touch_up(touch)
        return self._get_uid() in touch.ud

    def _do_touch_up(self, touch, *largs):
        super(DragBehavior, self).on_touch_up(touch)
        # don't forget about grab event!
        for x in touch.grab_list[:]:
            touch.grab_list.remove(x)
            x = x()
            if not x:
                continue
            touch.grab_current = x
            super(DragBehavior, self).on_touch_up(touch)
        touch.grab_current = None

    def _change_touch_mode(self, *largs):
        if not self._drag_touch:
            return
        uid = self._get_uid()
        touch = self._drag_touch
        ud = touch.ud[uid]
        if ud['mode'] != 'unknown':
            return
        touch.ungrab(self)
        self._drag_touch = None
        super(DragBehavior, self).on_touch_down(touch)
        return


class FocusBehavior(object):
    '''Implements keyboard focus behavior. When combined with other
    FocusBehavior widgets it allows one to cycle focus among them by pressing
    tab. In addition, upon gaining focus the instance will automatically
    receive keyboard input.

    Focus, very different then selection, is intimately tied with the keyboard;
    each keyboard can focus on zero or one widgets, and each widget can only
    have the focus of one keyboard. However, multiple keyboards can focus
    simultaneously on different widgets. When escape is hit, the widget having
    the focus of that keyboard will de-focus.

    In essence, focus is implemented as a doubly linked list, where each
    node holds a (weak) reference to the instance before it and after it,
    as visualized when cycling through the nodes using tab (forward) or
    shift+tab (backward). If previous or next widget is not specified,
    :attr:`focus_next` and :attr:`focus_previous` default to `None`,
    which means that the children list and parents are walked to find
    the next focusable widget, unless :attr:`focus_next` or
    :attr:`focus_previous` is set to the `StopIteration` class, in which case
    focus stops there.

    For example, to cycle focus between :class:`~kivy.uix.button.Button`
    elements of a :class:`~kivy.uix.gridlayout.GridLayout`::

        class FocusButton(FocusBehavior, Button):
            pass

        grid = GridLayout(cols=4)
        for i in range(40):
            grid.add_widget(FocusButton(text=str(i)))
        # clicking on a widget will activate focus, and tab can now be used
        # to cycle through


    .. versionadded:: 1.8.1
        This code is still experimental, and its API is subject to change in a
        future version.
    '''

    _win = None
    _requested_keyboard = False
    _keyboard = ObjectProperty(None, allownone=True)
    _keyboards = {}

    def _set_keyboard(self, value):
        focused = self.focused
        keyboard = self._keyboard
        keyboards = FocusBehavior._keyboards
        if keyboard:
            self.focused = False    # this'll unbind
            if self._keyboard:  # remove assigned keyboard from dict
                del keyboards[keyboard]
        if value and not value in keyboards:
            keyboards[value] = None
        self._keyboard = value
        self.focused = focused

    def _get_keyboard(self):
        return self._keyboard
    keyboard = AliasProperty(_get_keyboard, _set_keyboard,
                             bind=('_keyboard', ))
    '''The keyboard to bind, or bound to the widget when focused.

    When None, a keyboard is requested and released whenever the widget comes
    into and out of focus. If not None, it must be a keyboard, which gets
    bound and unbound from the widget whenever it's in or out of focus. It is
    useful only when more than one keyboard is available, so it is recommended
    to be set to None when only one keyboard is available

    If more than one keyboard is available, whenever an instance get focused
    a new keyboard will be requested if None. Unless, the other instances lose
    focus (e.g. if tab was used), a new keyboard will appear. When this is
    undesired, the keyboard property can be used. For example, if there are
    two users with two keyboards, then each keyboard can be assigned to
    different groups of instances of FocusBehavior, ensuring that within
    each group, only one FocusBehavior will have focus, and will receive input
    from the correct keyboard. see `keyboard_mode` in :mod:`~kivy.config` for
    information on the keyboard modes.

    :attr:`keyboard` is a :class:`~kivy.properties.AliasProperty`, defaults to
    None.

    .. note:

        If the keyboard property is set, that keyboard will be used when the
        instance gets focused. If widgets with different keyboards are linked
        through :attr:`focus_next` and :attr:`focus_previous`, then as they are
        tabbed through, different keyboards will become active. Therefore,
        typically it's undesirable to link instances which are assigned
        different keyboards.

    .. note:

        When an instance has focus, setting keyboard to None will remove the
        current keyboard, but will then try to get a keyboard back. It is
        better to set :attr:`focused` to False.

    .. warning:

        When assigning a keyboard, the keyboard must not be released while
        it is still assigned to an instance. Similarly, the keyboard created
        by the instance on focus and assigned to :attr:`keyboard` if None,
        will be released by the instance when the instance loses focus.
        Therefore, it is not safe to assign this keyboard to another instance's
        :attr:`keyboard`.
    '''

    is_focusable = BooleanProperty(_is_desktop)
    '''Whether the instance can become focused. If focused, it'll lose focus
    when set to False.

    :attr:`is_focusable` is a :class:`~kivy.properties.BooleanProperty`,
    defaults to True on a desktop (i.e. desktop is True in
    :mod:`~kivy.config`), False otherwise.
    '''

    focused = BooleanProperty(False)
    '''Whether the instance currently has focus.

    Setting it to True, will bind to and/or request the keyboard, and input
    will be forwarded to the instance. Setting it to False, will unbind
    and/or release the keyboard. For a given keyboard, only one widget can
    have its focus, so focusing one will automatically unfocus the other
    instance holding its focus.

    :attr:`focused` is a :class:`~kivy.properties.BooleanProperty`, defaults to
    False.
    '''

    def _set_on_focus_next(self, instance, value):
        ''' If changing code, ensure following code is not infinite loop:
        widget.focus_next = widget
        widget.focus_previous = widget
        widget.focus_previous = widget2
        '''
        next = self._old_focus_next
        if next is value:   # prevent infinite loop
            return

        if isinstance(next, FocusBehavior):
            next.focus_previous = None
        self._old_focus_next = value
        if value is None or value is StopIteration:
            return
        if not isinstance(value, FocusBehavior):
            raise ValueError('focus_next accepts only objects based'
                             ' on FocusBehavior, or the StopIteration class.')
        value.focus_previous = self

    focus_next = ObjectProperty(None, allownone=True)
    '''The :class:`FocusBehavior` instance to acquire focus when
    tab is pressed when this instance has focus, if not `None` or
    `'StopIteration'`.

    When tab is pressed, focus cycles through all the :class:`FocusBehavior`
    widgets that are linked through :attr:`focus_next` and are focusable. If
    :attr:`focus_next` is `None`, it instead walks the children lists to find
    the next focusable widget. Finally, if :attr:`focus_next` is
    the `StopIteration` class, focus won't move forward, but end here.

    .. note:

        Setting :attr:`focus_next` automatically sets :attr:`focus_previous`
        of the other instance to point to this instance, if not None or
        `StopIteration`. Similarly, if it wasn't None or `StopIteration`, it
        also sets the :attr:`focus_previous` property of the instance
        previously in :attr:`focus_next` to `None`. Therefore, it is only
        required to set one side of the :attr:`focus_previous`,
        :attr:`focus_next`, links since the other side will be set
        automatically.

    :attr:`focus_next` is a :class:`~kivy.properties.ObjectProperty`, defaults
    to `None`.
    '''

    def _set_on_focus_previous(self, instance, value):
        prev = self._old_focus_previous
        if prev is value:
            return

        if isinstance(prev, FocusBehavior):
            prev.focus_next = None
        self._old_focus_previous = value
        if value is None or value is StopIteration:
            return
        if not isinstance(value, FocusBehavior):
            raise ValueError('focus_previous accepts only objects based'
                             ' on FocusBehavior, or the StopIteration class.')
        value.focus_next = self

    focus_previous = ObjectProperty(None, allownone=True)
    '''The :class:`FocusBehavior` instance to acquire focus when
    shift+tab is pressed on this instance, if not None or `StopIteration`.

    When shift+tab is pressed, focus cycles through all the
    :class:`FocusBehavior` widgets that are linked through
    :attr:`focus_previous` and are focusable. If :attr:`focus_previous` is
    `None', it instead walks the children tree to find the
    previous focusable widget. Finally, if :attr:`focus_previous` is the
    `StopIteration` class, focus won't move backward, but end here.

    .. note:

        Setting :attr:`focus_previous` automatically sets :attr:`focus_next`
        of the other instance to point to this instance, if not None or
        `StopIteration`. Similarly, if it wasn't None or `StopIteration`, it
        also sets the :attr:`focus_next` property of the instance previously in
        :attr:`focus_previous` to `None`. Therefore, it is only required
        to set one side of the :attr:`focus_previous`, :attr:`focus_next`,
        links since the other side will be set automatically.

    :attr:`focus_previous` is a :class:`~kivy.properties.ObjectProperty`,
    defaults to  `None`.
    '''

    def __init__(self, **kwargs):
        self._old_focus_next = None
        self._old_focus_previous = None
        super(FocusBehavior, self).__init__(**kwargs)

        self.bind(focused=self._on_focused, disabled=self._on_focusable,
                  is_focusable=self._on_focusable,
                  # don't be at mercy of child calling super
                  on_touch_down=self._focus_on_touch_down,
                  focus_next=self._set_on_focus_next,
                  focus_previous=self._set_on_focus_previous)

    def _on_focusable(self, instance, value):
        if self.disabled or not self.is_focusable:
            self.focused = False

    def _on_focused(self, instance, value, *largs):
        if value:
            self._bind_keyboard()
        else:
            self._unbind_keyboard()

    def _ensure_keyboard(self):
        if self._keyboard is None:
            win = self._win
            if not win:
                self._win = win = EventLoop.window
            if not win:
                Logger.warning('FocusBehavior: '
                'Cannot focus the element, unable to get root window')
                return
            self._requested_keyboard = True
            keyboard = self._keyboard =\
                win.request_keyboard(self._keyboard_released, self)
            keyboards = FocusBehavior._keyboards
            if keyboard not in keyboards:
                keyboards[keyboard] = None

    def _bind_keyboard(self):
        self._ensure_keyboard()
        keyboard = self._keyboard

        if not keyboard or self.disabled or not self.is_focusable:
            self.focused = False
            return
        keyboards = FocusBehavior._keyboards
        old_focus = keyboards[keyboard]  # keyboard should be in dict
        if old_focus:
            old_focus.focused = False
            # keyboard shouldn't have been released here, see keyboard warning
        keyboards[keyboard] = self
        keyboard.bind(on_key_down=self.keyboard_on_key_down,
                      on_key_up=self.keyboard_on_key_up)

    def _unbind_keyboard(self):
        keyboard = self._keyboard
        if keyboard:
            keyboard.unbind(on_key_down=self.keyboard_on_key_down,
                            on_key_up=self.keyboard_on_key_up)
            if self._requested_keyboard:
                keyboard.release()
                self._keyboard = None
                self._requested_keyboard = False
                del FocusBehavior._keyboards[keyboard]
            else:
                FocusBehavior._keyboards[keyboard] = None

    def _keyboard_released(self):
        self.focused = False

    def _focus_on_touch_down(self, instance, touch):
        if not self.disabled and self.is_focusable and\
            self.collide_point(*touch.pos) and ('button' not in touch.profile
            or not touch.button.startswith('scroll')):
            self.focused = True
        return False

    def _get_focus_next(self, focus_dir):
        current = self
        walk_tree = 'walk' if focus_dir is 'focus_next' else 'walk_reverse'

        while 1:
            # if we hit a focusable, walk through focus_xxx
            while getattr(current, focus_dir) is not None:
                current = getattr(current, focus_dir)
                if current is self or current is StopIteration:
                    return None  # make sure we don't loop forever
                if current.is_focusable:
                    return current

            # hit unfocusable, walk widget tree
            itr = getattr(current, walk_tree)(loopback=True)
            if focus_dir is 'focus_next':
                next(itr)  # current is returned first  when walking forward
            for current in itr:
                if isinstance(current, FocusBehavior):
                    break
            # why did we stop
            if isinstance(current, FocusBehavior):
                if current is self:
                    return None
                if current.is_focusable:
                    return current
            else:
                return None

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        '''The method bound to the keyboard when the instance has focus.

        When the instance becomes focused, this method is bound to the
        keyboard and will be called for every input press. The parameters are
        the same as :meth:`kivy.core.window.WindowBase.on_key_down`.

        When overwriting the method in the derived widget, super should be
        called to enable tab cycling. If the derived widget wishes to use tab
        for its own purposes, it can call super at the end after it is done if
        it didn't consume tab.

        Similar to other keyboard functions, it should return True if the
        key was consumed.
        '''
        if keycode[1] == 'tab':  # deal with cycle
            if ['shift'] == modifiers:
                next = self._get_focus_next('focus_previous')
            else:
                next = self._get_focus_next('focus_next')
            if next:
                self.focused = False
                next.focused = True
            return True
        return False

    def keyboard_on_key_up(self, window, keycode):
        '''The method bound to the keyboard when the instance has focus.

        When the instance becomes focused, this method is bound to the
        keyboard and will be called for every input release. The parameters are
        the same as :meth:`kivy.core.window.WindowBase.on_key_up`.

        When overwriting the method in the derived widget, super should be
        called to enable de-focusing on escape. If the derived widget wishes
        to use escape for its own purposes, it can call super at the end after
        it is done if it didn't consume escape.

        See :meth:`on_key_down`
        '''
        if keycode[1] == 'escape':
            self.focused = False
            return True
        return False
