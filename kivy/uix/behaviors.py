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
    specify the inheritance in this order, the behavior will not work because
    the behavior methods are overwritten by the class method listed first.

    Similarly, if you combine a behavior class with a class which
    requires the use of the methods also defined by the behavior class, the
    resulting class may not function properly. E.g. combining a ButtonBehavior
    with a Slider, both of which require the on_touch_up methods, the resulting
    class will not work.

'''

__all__ = ('ButtonBehavior', 'ToggleButtonBehavior', 'DragBehavior',
           'FocusBehavior', 'CompoundSelectionBehavior')

from kivy.clock import Clock
from kivy.properties import OptionProperty, ObjectProperty, NumericProperty,\
    ReferenceListProperty, BooleanProperty, ListProperty, AliasProperty
from kivy.config import Config
from kivy.metrics import sp
from kivy.base import EventLoop
from kivy.logger import Logger
from functools import partial
from weakref import ref
from time import time
import string

# When we are generating documentation, Config doesn't exist
_scroll_timeout = _scroll_distance = 0
_is_desktop = False
_keyboard_mode = 'system'
if Config:
    _scroll_timeout = Config.getint('widgets', 'scroll_timeout')
    _scroll_distance = Config.getint('widgets', 'scroll_distance')
    _is_desktop = Config.getboolean('kivy', 'desktop')
    _keyboard_mode = Config.get('kivy', 'keyboard_mode')


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

    MIN_STATE_TIME = 0.035
    '''The minimum period of time which the widget must remain in the
    `'down'` state.

    :attr:`MIN_STATE_TIME` is a float.
    '''

    always_release = BooleanProperty(True)
    '''This determines if the widget fires a `on_release` event if
    the touch_up is outside the widget.

    ..versionadded:: 1.9.0

    :attr:`always_release` is a :class:`~kivy.properties.BooleanProperty`,
    defaults to `True`.
    '''

    def __init__(self, **kwargs):
        self.register_event_type('on_press')
        self.register_event_type('on_release')
        super(ButtonBehavior, self).__init__(**kwargs)
        self.__state_event = None
        self.__touch_time = None
        self.bind(state=self.cancel_event)

    def _do_press(self):
        self.state = 'down'

    def _do_release(self, *args):
        self.state = 'normal'

    def cancel_event(self, *args):
        if self.__state_event:
            self.__state_event.cancel()
            self.__state_event = None

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
        self.__touch_time = time()
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

        if (not self.always_release
                and not self.collide_point(*touch.pos)):
            self.state = 'normal'
            return

        touchtime = time() - self.__touch_time
        if touchtime < self.MIN_STATE_TIME:
            self.__state_event = Clock.schedule_once(
                self._do_release, self.MIN_STATE_TIME - touchtime)
        else:
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

    allow_no_selection = BooleanProperty(True)
    '''This specifies whether the checkbox in group allows everything to
    be deselected.

    ..versionadded::1.9.0

    :attr:`allow_no_selection` is a :class:`BooleanProperty` defaults to
    `True`
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
        if (not self.allow_no_selection and
            self.group and self.state == 'down'):
            return
        self._release_group(self)
        self.state = 'normal' if self.state == 'down' else 'down'

    def _do_release(self, *args):
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
    :attr:`focus_next` and :attr:`focus_previous` defaults to `None`,
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


    .. versionadded:: 1.9.0

    .. warning::

        This code is still experimental, and its API is subject to change in a
        future version.
    '''

    _requested_keyboard = False
    _keyboard = ObjectProperty(None, allownone=True)
    _keyboards = {}

    ignored_touch = []
    '''A list of touches that should not be used to defocus. After on_touch_up,
    every touch that is not in :attr:`ignored_touch` will defocus all the
    focused widgets, if, the config keyboard mode is not multi. Touches on
    focusable widgets that were used to focus are automatically added here.

    Example usage::

        class Unfocusable(Widget):

            def on_touch_down(self, touch):
                if self.collide_point(*touch.pos):
                    FocusBehavior.ignored_touch.append(touch)

    Notice that you need to access this as class, not instance variable.
    '''

    def _set_keyboard(self, value):
        focus = self.focus
        keyboard = self._keyboard
        keyboards = FocusBehavior._keyboards
        if keyboard:
            self.focus = False    # this'll unbind
            if self._keyboard:  # remove assigned keyboard from dict
                del keyboards[keyboard]
        if value and not value in keyboards:
            keyboards[value] = None
        self._keyboard = value
        self.focus = focus

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

    .. note::

        When Config's `keyboard_mode` is multi, each new touch is considered
        a touch by a different user and will focus (if clicked on a
        focusable) with a new keyboard. Already focused elements will not lose
        their focus (even if clicked on a unfocusable).

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
        better to set :attr:`focus` to False.

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

    focus = BooleanProperty(False)
    '''Whether the instance currently has focus.

    Setting it to True, will bind to and/or request the keyboard, and input
    will be forwarded to the instance. Setting it to False, will unbind
    and/or release the keyboard. For a given keyboard, only one widget can
    have its focus, so focusing one will automatically unfocus the other
    instance holding its focus.

    :attr:`focus` is a :class:`~kivy.properties.BooleanProperty`, defaults to
    False.
    '''

    focused = focus
    '''An alias of :attr:`focus`.

    :attr:`focused` is a :class:`~kivy.properties.BooleanProperty`, defaults to
    False.

    .. warning::
        :attr:`focused` is an alias of :attr:`focus` and will be removed in
        2.0.0.
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

    keyboard_mode = OptionProperty('auto', options=('auto', 'managed'))
    '''How the keyboard visibility should be managed (auto will have standard
    behaviour to show/hide on focus, managed requires setting keyboard_visible
    manually, or calling the helper functions ``show_keyboard()``
    and ``hide_keyboard()``.

    :attr:`keyboard_mode` is an :class:`~kivy.properties.OptionsProperty` and
    defaults to 'auto'. Can be one of 'auto' or 'managed'.
    '''

    input_type = OptionProperty('text', options=('text', 'number', 'url',
                                                 'mail', 'datetime', 'tel',
                                                 'address'))
    '''The kind of input keyboard to request.

    .. versionadded:: 1.8.0

    :attr:`input_type` is an :class:`~kivy.properties.OptionsProperty` and
    defaults to 'text'. Can be one of 'text', 'number', 'url', 'mail',
    'datetime', 'tel', 'address'.
    '''

    unfocus_on_touch = BooleanProperty(_keyboard_mode not in
                                       ('multi', 'systemandmulti'))
    '''Whether a instance should lose focus when clicked outside the instance.

    When a user clicks on a widget that is focus aware and shares the same
    keyboard as the this widget (which in the case of only one keyboard, are
    all focus aware widgets), then as the other widgets gains focus, this
    widget loses focus. In addition to that, if this property is `True`,
    clicking on any widget other than this widget, will remove focus form this
    widget.

    :attr:`unfocus_on_touch` is a :class:`~kivy.properties.BooleanProperty`,
    defaults to `False` if the `keyboard_mode` in :attr:`~kivy.config.Config`
    is `'multi'` or `'systemandmulti'`, otherwise it defaults to `True`.
    '''

    def __init__(self, **kwargs):
        self._old_focus_next = None
        self._old_focus_previous = None
        super(FocusBehavior, self).__init__(**kwargs)

        self._keyboard_mode = _keyboard_mode
        self.bind(focus=self._on_focus, disabled=self._on_focusable,
                  is_focusable=self._on_focusable,
                  focus_next=self._set_on_focus_next,
                  focus_previous=self._set_on_focus_previous)

    def _on_focusable(self, instance, value):
        if self.disabled or not self.is_focusable:
            self.focus = False

    def _on_focus(self, instance, value, *largs):
        if self.keyboard_mode == 'auto':
            if value:
                self._bind_keyboard()
            else:
                self._unbind_keyboard()

    def _ensure_keyboard(self):
        if self._keyboard is None:
            self._requested_keyboard = True
            keyboard = self._keyboard =\
                EventLoop.window.request_keyboard(
                    self._keyboard_released, self, input_type=self.input_type)
            keyboards = FocusBehavior._keyboards
            if keyboard not in keyboards:
                keyboards[keyboard] = None

    def _bind_keyboard(self):
        self._ensure_keyboard()
        keyboard = self._keyboard

        if not keyboard or self.disabled or not self.is_focusable:
            self.focus = False
            return
        keyboards = FocusBehavior._keyboards
        old_focus = keyboards[keyboard]  # keyboard should be in dict
        if old_focus:
            old_focus.focus = False
            # keyboard shouldn't have been released here, see keyboard warning
        keyboards[keyboard] = self
        keyboard.bind(on_key_down=self.keyboard_on_key_down,
                      on_key_up=self.keyboard_on_key_up,
                      on_textinput=self.keyboard_on_textinput)

    def _unbind_keyboard(self):
        keyboard = self._keyboard
        if keyboard:
            keyboard.unbind(on_key_down=self.keyboard_on_key_down,
                            on_key_up=self.keyboard_on_key_up,
                            on_textinput=self.keyboard_on_textinput)
            if self._requested_keyboard:
                keyboard.release()
                self._keyboard = None
                self._requested_keyboard = False
                del FocusBehavior._keyboards[keyboard]
            else:
                FocusBehavior._keyboards[keyboard] = None

    def keyboard_on_textinput(self, window, text):
        pass

    def _keyboard_released(self):
        self.focus = False

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return
        if (not self.disabled and self.is_focusable and
            ('button' not in touch.profile or
             not touch.button.startswith('scroll'))):
            self.focus = True
            FocusBehavior.ignored_touch.append(touch)
        return super(FocusBehavior, self).on_touch_down(touch)

    @staticmethod
    def _handle_post_on_touch_up(touch):
        ''' Called by window after each touch has finished.
        '''
        touches = FocusBehavior.ignored_touch
        if touch in touches:
            touches.remove(touch)
            return
        for focusable in list(FocusBehavior._keyboards.values()):
            if focusable is None or not focusable.unfocus_on_touch:
                continue
            focusable.focus = False

    def _get_focus_next(self, focus_dir):
        current = self
        walk_tree = 'walk' if focus_dir is 'focus_next' else 'walk_reverse'

        while 1:
            # if we hit a focusable, walk through focus_xxx
            while getattr(current, focus_dir) is not None:
                current = getattr(current, focus_dir)
                if current is self or current is StopIteration:
                    return None  # make sure we don't loop forever
                if current.is_focusable and not current.disabled:
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
                if current.is_focusable and not current.disabled:
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
                self.focus = False

                next.focus = True

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
            self.focus = False
            return True
        return False

    def show_keyboard(self):
        '''
        Convenience function to show the keyboard in managed mode.
        '''
        if self.keyboard_mode == 'managed':
            self._bind_keyboard()

    def hide_keyboard(self):
        '''
        Convenience function to hide the keyboard in managed mode.
        '''
        if self.keyboard_mode == 'managed':
            self._unbind_keyboard()


class CompoundSelectionBehavior(object):
    '''Selection behavior implements the logic behind keyboard and touch
    selection of selectable widgets managed by the derived widget.
    For example, it could be combined with a
    :class:`~kivy.uix.gridlayout.GridLayout` to add selection to the layout.

    At its core, it keeps a dynamic list of widgets that can be selected.
    Then, as the touches and keyboard input are passed in, it selects one or
    more of the widgets based on these inputs. For example, it uses the mouse
    scroll and keyboard up/down buttons to scroll through the list of widgets.
    Multiselection can also be achieved using the keyboard shift and ctrl keys.
    Finally, in addition to the up/down type keyboard inputs, it can also
    accepts letters from the kayboard to be used to select nodes with
    associated strings that start with those letters, similar to how files
    are selected by a file browser.

    When the controller needs to select a node it calls :meth:`select_node` and
    :meth:`deselect_node`. Therefore, they must be overwritten in order affect
    the selected nodes. By default, the class doesn't listen to keyboard and
    touch events, therefore, the derived widget must call
    :meth:`select_with_touch`, :meth:`select_with_key_down`, and
    :meth:`select_with_key_up` on events that it wants to pass on for selection
    purposes.

    For example, to add selection to a grid layout which will contain
    :class:`~kivy.uix.Button` widgets::

        class SelectableGrid(CompoundSelectionBehavior, GridLayout):

            def __init__(self, **kwargs):
                super(CompoundSelectionBehavior, self).__init__(**kwargs)
                keyboard = Window.request_keyboard(None, self)
                keyboard.bind(on_key_down=self.select_with_key_down,
                on_key_up=self.select_with_key_up)

            def select_node(self, node):
                node.background_color = (1, 0, 0, 1)
                return super(CompoundSelectionBehavior, self).select_node(node)

            def deselect_node(self, node):
                node.background_color = (1, 1, 1, 1)
                super(CompoundSelectionBehavior, self).deselect_node(node)

    Then, for each button added to the layout, bind on_touch_down of the button
    to :meth:`select_with_touch` to pass on the touch events.

    .. versionadded:: 1.9.0

    .. warning::

        This code is still experimental, and its API is subject to change in a
        future version.
    '''

    selected_nodes = ListProperty([])
    '''The list of selected nodes.

    .. note:

        Multiple nodes can be selected right after another using e.g. the
        keyboard, so when listening to :attr:`selected_nodes` one should be
        aware of this.

    :attr:`selected_nodes` is a :class:`~kivy.properties.ListProperty` and
    defaults to the empty list, []. It is read-only and should not be modified.
    '''

    touch_multiselect = BooleanProperty(False)
    '''A special touch mode which determines whether touch events, as
    processed with :meth:`select_with_touch`, will add to the selection the
    currently touched node, or if it will clear the selection before adding the
    node. This allows the selection of multiple nodes by simply touching them.
    This is different than :attr:`multiselect`, because when this is True
    simply touching an unselected node will select it, even if e.g. ctrl is not
    pressed. If this is False, however, ctrl is required to be held in order to
    add to selection when :attr:`multiselect` is True.

    .. note::

        :attr:`multiselect`, when False, will disable
        :attr:`touch_multiselect`.

    :attr:`touch_multiselect` is a :class:`~kivy.properties.BooleanProperty`,
    defaults to False.
    '''

    multiselect = BooleanProperty(False)
    '''Determines whether multiple nodes can be selected. If enabled, keyboard
    shift and ctrl selection, optionally combined with touch, for example, will
    be able to select multiple widgets in the normally expected manner.
    This dominates :attr:`touch_multiselect` when False.

    :attr:`multiselect` is a :class:`~kivy.properties.BooleanProperty`
    , defaults to False.
    '''

    keyboard_select = BooleanProperty(True)
    ''' Whether the keybaord can be used for selection. If False, keyboard
    inputs will be ignored.

    :attr:`keyboard_select` is a :class:`~kivy.properties.BooleanProperty`
    , defaults to True.
    '''

    page_count = NumericProperty(10)
    '''Determines by how much the selected node is moved up or down, relative
    to position of the last selected node, when pageup (or pagedown) is
    pressed.

    :attr:`page_count` is a :class:`~kivy.properties.NumericProperty`,
    defaults to 10.
    '''

    up_count = NumericProperty(1)
    '''Determines by how much the selected node is moved up or down, relative
    to position of the last selected node, when the up (or down) arrow on the
    keyboard is pressed.

    :attr:`up_count` is a :class:`~kivy.properties.NumericProperty`,
    defaults to 1.
    '''

    right_count = NumericProperty(1)
    '''Determines by how much the selected node is moved up or down, relative
    to position of the last selected node, when the right (or left) arrow on
    the keyboard is pressed.

    :attr:`right_count` is a :class:`~kivy.properties.NumericProperty`,
    defaults to 1.
    '''

    scroll_count = NumericProperty(0)
    '''Determines by how much the selected node is moved up or down, relative
    to position of the last selected node, when the mouse scroll wheel is
    scrolled.

    :attr:`right_count` is a :class:`~kivy.properties.NumericProperty`,
    defaults to 0.
    '''

    _anchor = None  # the last anchor node selected (e.g. shift relative node)
    # the idx may be out of sync
    _anchor_idx = 0  # cache indexs in case list hasn't changed
    _last_selected_node = None  # the absolute last node selected
    _last_node_idx = 0
    _ctrl_down = False  # if it's pressed - for e.g. shift selection
    _shift_down = False
    # holds str used to find node, e.g. if word is typed. passed to goto_node
    _word_filter = ''
    _last_key_time = 0  # time since last press, for finding whole strs in node
    _printable = set(string.printable)
    _key_list = []  # keys that are already pressed, to not press continuously
    _offset_counts = {}  # cache of counts for faster access

    def __init__(self, **kwargs):
        super(CompoundSelectionBehavior, self).__init__(**kwargs)

        def ensure_single_select(*l):
            if (not self.multiselect) and len(self.selected_nodes) > 1:
                self.clear_selection()
        self._update_counts()
        self.bind(multiselect=ensure_single_select,
        page_count=self._update_counts, up_count=self._update_counts,
        right_count=self._update_counts, scroll_count=self._update_counts)

    def select_with_touch(self, node, touch=None):
        '''(internal) Processes a touch on the node. This should be called by
        the derived widget when a node is touched and is to be used for
        selection. Depending on the keyboard keys pressed and the
        configuration, it could select or deslect this and other nodes in the
        selectable nodes list, :meth:`get_selectable_nodes`.

        :Parameters:
            `node`
                The node that recieved the touch. Can be None for a scroll
                type touch.
            `touch`
                Optionally, the touch. Defaults to None.

        :Returns:
            bool, True if the touch was used, False otherwise.
        '''
        multi = self.multiselect
        multiselect = multi and (self._ctrl_down or self.touch_multiselect)
        range_select = multi and self._shift_down

        if touch and 'button' in touch.profile and touch.button in\
            ('scrollup', 'scrolldown', 'scrollleft', 'scrollright'):
            node_src, idx_src = self._reslove_last_node()
            node, idx = self.goto_node(touch.button, node_src, idx_src)
            if node == node_src:
                return False
            if range_select:
                self._select_range(multiselect, True, node, idx)
            else:
                if not multiselect:
                    self.clear_selection()
                self.select_node(node)
            return True
        if node is None:
            return False

        if (node in self.selected_nodes and (not range_select)):  # selected
            if multiselect:
                self.deselect_node(node)
            else:
                self.clear_selection()
                self.select_node(node)
        elif range_select:
            # keep anchor only if not multislect (ctrl-type selection)
            self._select_range(multiselect, not multiselect, node, 0)
        else:   # it's not selected at this point
            if not multiselect:
                self.clear_selection()
            self.select_node(node)
        return True

    def select_with_key_down(self, keyboard, scancode, codepoint, modifiers,
                             **kwargs):
        '''Processes a key press. This is called when a key press is to be used
        for selection. Depending on the keyboard keys pressed and the
        configuration, it could select or deslect nodes or node ranges
        from the selectable nodes list, :meth:`get_selectable_nodes`.

        The parameters are such that it could be bound directly to the
        on_key_down event of a keyboard. Therefore, it is safe to be called
        repeatedly when the key is held down as is done by the keyboard.

        :Returns:
            bool, True if the keypress was used, False otherwise.
        '''
        if not self.keyboard_select:
            return False
        keys = self._key_list
        multi = self.multiselect
        node_src, idx_src = self._reslove_last_node()

        if scancode[1] == 'shift':
            self._shift_down = True
        elif scancode[1] == 'ctrl':
            self._ctrl_down = True
        elif (multi and 'ctrl' in modifiers and scancode[1] in ('a', 'A')
              and scancode[1] not in keys):
            sister_nodes = self.get_selectable_nodes()
            select = self.select_node
            for node in sister_nodes:
                select(node)
            keys.append(scancode[1])
        else:
            if scancode[1] in self._printable:
                if time() - self._last_key_time <= 1.:
                    self._word_filter += scancode[1]
                else:
                    self._word_filter = scancode[1]
                self._last_key_time = time()
                node, idx = self.goto_node(self._word_filter, node_src,
                                           idx_src)
            else:
                node, idx = self.goto_node(scancode[1], node_src, idx_src)
            if node == node_src:
                return False

            multiselect = multi and 'ctrl' in modifiers
            if multi and 'shift' in modifiers:
                self._select_range(multiselect, True, node, idx)
            else:
                if not multiselect:
                    self.clear_selection()
                self.select_node(node)
            return True
        return False

    def select_with_key_up(self, keyboard, scancode, **kwargs):
        '''(internal) Processes a key release. This must be called by the
        derived widget when a key that :meth:`select_with_key_down` returned
        True is released.

        The parameters are such that it could be bound directly to the
        on_key_up event of a keyboard.

        :Returns:
            bool, True if the key release was used, False otherwise.
        '''
        if scancode[1] == 'shift':
            self._shift_down = False
        elif scancode[1] == 'ctrl':
            self._ctrl_down = False
        else:
            try:
                self._key_list.remove(scancode[1])
                return True
            except ValueError:
                return False
        return True

    def _update_counts(self, *largs):
        # doesn't invert indices here
        pc = self.page_count
        uc = self.up_count
        rc = self.right_count
        sc = self.scroll_count
        self._offset_counts = {'pageup': -pc, 'pagedown': pc, 'up': -uc,
        'down': uc, 'right': rc, 'left': -rc, 'scrollup': sc,
        'scrolldown': -sc, 'scrollright': -sc, 'scrollleft': sc}

    def _reslove_last_node(self):
        # for offset selection, we have a anchor, and we select everything
        # between anchor and added offset relative to last node
        sister_nodes = self.get_selectable_nodes()
        if not len(sister_nodes):
            return None, 0
        last_node = self._last_selected_node
        last_idx = self._last_node_idx
        end = len(sister_nodes) - 1

        if last_node is None:
            last_node = self._anchor
            last_idx = self._anchor_idx
        if last_node is None:
            return sister_nodes[end], end
        if last_idx > end or sister_nodes[last_idx] != last_node:
            try:
                return last_node, sister_nodes.index(last_node)
            except ValueError:
                return sister_nodes[end], end
        return last_node, last_idx

    def _select_range(self, multiselect, keep_anchor, node, idx):
        '''Selects a range between self._anchor and node or idx.
        If multiselect, it'll add to selection, otherwise it will unselect
        everything before selecting the range. This is only called if
        self.multiselect is True.
        If keep anchor is False, the anchor is moved to node. This should
        always be True of keyboard selection.
        '''
        select = self.select_node
        sister_nodes = self.get_selectable_nodes()
        end = len(sister_nodes) - 1
        last_node = self._anchor
        last_idx = self._anchor_idx

        if last_node is None:
            last_idx = end
            last_node = sister_nodes[end]
        else:
            if last_idx > end or sister_nodes[last_idx] != last_node:
                try:
                    last_idx = sister_nodes.index(last_node)
                except ValueError:
                    # list changed - cannot do select across them
                    return
        if idx > end or sister_nodes[idx] != node:
            try:    # just in case
                idx = sister_nodes.index(node)
            except ValueError:
                return

        if last_idx > idx:
            last_idx, idx = idx, last_idx
        if not multiselect:
            self.clear_selection()
        for item in sister_nodes[last_idx:idx + 1]:
            select(item)

        if keep_anchor:
            self._anchor = last_node
            self._anchor_idx = last_idx
        else:
            self._anchor = node  # in case idx was reversed, reset
            self._anchor_idx = idx
        self._last_selected_node = node
        self._last_node_idx = idx

    def clear_selection(self):
        ''' Deselects all the currently selected nodes.
        '''
        # keep the anchor and last selected node
        deselect = self.deselect_node
        nodes = self.selected_nodes
        # empty beforehand so lookup in deselect will be fast
        self.selected_nodes = []
        for node in nodes:
            deselect(node)

    def get_selectable_nodes(self):
        '''(internal) Returns a list of the nodes that can be selected. It can
        be overwritten by the derived widget to return the correct list.

        This list is used to determine which nodes to select with group
        selection. E.g. the last element in the list will be selected when
        home is pressed, pagedown will move (or add to, if shift is held) the
        selection from the current position by negative :attr:`page_count`
        nodes starting from the position of the currently selected node in
        this list and so on. Still, nodes can be selected even if they are not
        in this list.

        .. note::

            It is safe to dynamically change this list including removing,
            adding, or re-arranging its elements. Nodes can be selected even
            if they are not on this list. And selected nodes removed from the
            list will remain selected until :meth:`deselect_node` is called.

        .. warning::

            Layouts display their children in the reverse order. That is, the
            contents of :attr:`~kivy.uix.widget.Widget.children` is displayed
            form right to left, bottom to top. Therefore, internally, the
            indices of the elements returned by this function is reversed to
            make it work by default for most layouts so that the final result
            is that e.g. home, although it will select the last element on this
            list, visually it'll select the first element when counting from
            top to bottom and left to right. If this behavior is not desired,
            a reversed list should be returned instead.

        Defaults to returning :attr:`~kivy.uix.widget.Widget.children`.
        '''
        return self.children

    def goto_node(self, key, last_node, last_node_idx):
        '''(internal) Used by the controller to get the node at the position
        indicated by key. The key can be keyboard inputs, e.g. pageup,
        or scroll inputs from the mouse scroll wheel, e.g. scrollup.
        Last node is the last node selected and is used to find the resulting
        node. For example, if the key is up, the returned node is one node
        up from the last node.

        It can be overwritten by the derived widget.

        :Parameters:
            `key`
                str, the string used to find the desired node. It can be any
                of the keyboard keys, as well as the mouse scrollup,
                scrolldown, scrollright, and scrollleft strings. If letters
                are typed in quick succession, the letters will be combined
                before it's passed in as key and can be used to find nodes that
                have an associated string that starts with those letters.
            `last_node`
                The last node that was selected.
            `last_node_idx`
                The cached index of the last node selected in the
                :meth:`get_selectable_nodes` list. If the list hasn't changed
                it saves having to look up the index of `last_node` in that
                list.

        :Returns:
            tuple, the node targeted by key and its index in the
            :meth:`get_selectable_nodes` list. Returning
            `(last_node, last_node_idx)` indicates a node wasn't found.
        '''
        sister_nodes = self.get_selectable_nodes()
        end = len(sister_nodes) - 1
        counts = self._offset_counts
        if end == -1:
            return last_node, last_node_idx
        if last_node_idx > end or sister_nodes[last_node_idx] != last_node:
            try:    # just in case
                last_node_idx = sister_nodes.index(last_node)
            except ValueError:
                return last_node, last_node_idx

        try:
            idx = max(min(-counts[key] + last_node_idx, end), 0)
            return sister_nodes[idx], idx
        except KeyError:
            pass
        if key == 'home':
            return sister_nodes[end], end
        elif key == 'end':
            return sister_nodes[0], 0
        else:
            return last_node, last_node_idx

    def select_node(self, node):
        ''' Selects a node.

        It is called by the controller when it selects a node and can be
        called from the outside to select a node directly. The derived widget
        should overwrite this method and change the node to its selected state
        when this is called

        :Parameters:
            `node`
                The node to be selected.

        :Returns:
            bool, True if the node was selected, False otherwise.

        .. warning::

            This method must be called by the derived widget using super if it
            is overwritten.
        '''
        nodes = self.selected_nodes
        if (not self.multiselect) and len(nodes):
            self.clear_selection()
        if node not in nodes:
            nodes.append(node)
        self._anchor = node
        self._last_selected_node = node
        return True

    def deselect_node(self, node):
        ''' Deselects a possibly selected node.

        It is called by the controller when it deselects a node and can also
        be called from the outside to deselect a node directly. The derived
        widget should overwrite this method and change the node to its
        unselected state when this is called

        :Parameters:
            `node`
                The node to be deselected.

        .. warning::

            This method must be called by the derived widget using super if it
            is overwritten.
        '''
        try:
            self.selected_nodes.remove(node)
        except ValueError:
            pass
