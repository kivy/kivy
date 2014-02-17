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
           'SelectionBehavior')

from kivy.clock import Clock
from kivy.properties import OptionProperty, ObjectProperty, NumericProperty,\
    ReferenceListProperty, BooleanProperty, ListProperty
from weakref import ref
from kivy.config import Config
from kivy.metrics import sp
from functools import partial
from kivy.core.window import Keyboard

# When we are generating documentation, Config doesn't exist
_scroll_timeout = _scroll_distance = 0
if Config:
    _scroll_timeout = Config.getint('widgets', 'scroll_timeout')
    _scroll_distance = Config.getint('widgets', 'scroll_distance')


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


class SelectionBehavior(object):
    '''Selection behavior implements the logic behind keyboard and touch
    selection of selectable widgets contained in the derived widget.
    For example, it could be combined with a :class:`~kivy.uix.GridLayout` to
    add selection to the layout.

    To make the selection work, :meth:`select_node` and :meth:`deselect_node`
    must be overwritten in order affect the selected nodes. By default,
    it doesn't listen to keyboard and touch events, so the derived widget must
    call :meth:`select_with_touch` and :meth:`select_with_key_down` and
    :meth:`select_with_key_up` on events that it wants to pass on for selection
    purposes.

    For example, to add selection to a grid layout which will contain
    :class:`~kivy.uix.Button` widgets::

        class SelectableGrid(SelectionBehavior, GridLayout):

            def __init__(self, **kwargs):
                super(SelectableGrid, self).__init__(**kwargs)
                Window.request_keyboard(None, self).bind(on_key_down=\
                self.select_with_key_down, on_key_up=self.select_with_key_up)

            def select_node(self, node):
                node.background_color = (1, 0, 0, 1)
                return super(SelectableGrid, self).select_node(node)

            def deselect_node(self, node):
                node.background_color = (1, 1, 1, 1)
                super(SelectableGrid, self).deselect_node(node)

    Then, for each button added to the layout, bind on_touch_down of the button
    to :meth:`select_with_touch` to pass on the touch events.

    .. versionadded:: 1.8.1
    '''

    selected_nodes = ListProperty([])
    '''The list of nodes selected with :meth:`select_node`, with touch or with
    the keyboard.

    .. note:

        Multiple nodes can be selected right after another using e.g. the
        keyboard, so when listening to :attr:`selected_nodes` one should be
        aware of this.

    :attr:`selected_nodes` is a :class:`~kivy.properties.ListProperty` and
    defaults to the empty list, []. It is read-only and should not be modified.
    '''

    touch_multiselect = BooleanProperty(False)
    '''Determines whether touch events as processed with
    :meth:`select_with_touch` will add to the selection the currently touched
    node, or if it will clear the selection before adding the node. This allows
    the selection of multiple nodes by simply touching them.

    .. note::

        :attr:`multiselect`, when False, will disable
        :attr:`touch_multiselect`.

    :attr:`touch_multiselect` is a :class:`~kivy.properties.BooleanProperty`,
    defaults to False.
    '''

    multiselect = BooleanProperty(False)
    '''Determines whether multiple nodes can be selected. If enabled, keyboard
    shift and ctrl selection, optionally combined with touch will be able to
    select multiple widgets in the normally expected manner. This overwrites
    :attr:`touch_multiselect` when False.

    :attr:`multiselect` is a :class:`~kivy.properties.BooleanProperty`
    , defaults to False.
    '''

    keyboard_select = BooleanProperty(False)
    ''' Whether the keybaord can be used for selection.

    The derived widget is responsible for forwarding keyboard events with
    :meth:`select_with_key_down`, so it is its responsibilty to use this
    to decide whether to forward these events. On its own,
    :class:`SelectionBehavior` will ignore :attr:`keyboard_select`.

    :attr:`keyboard_select` is a :class:`~kivy.properties.BooleanProperty`
    , defaults to False.
    '''

    page_count = NumericProperty(10)
    '''Determines by how much is selected node is moved up or down, relative
    to position of the last selected node, when pageup or pagedown is pressed.

    :attr:`page_count` is a :class:`~kivy.properties.NumericProperty`,
    defaults to 10.
    '''

    up_count = NumericProperty(1)
    '''Determines by how much is selected node is moved up or down, relative
    to position of the last selected node, when the up or down arrow is
    pressed.

    :attr:`up_count` is a :class:`~kivy.properties.NumericProperty`,
    defaults to 1.
    '''

    right_count = NumericProperty(1)
    '''Determines by how much is selected node is moved up or down, relative
    to position of the last selected node, when the right or left arrow is
    pressed.

    :attr:`right_count` is a :class:`~kivy.properties.NumericProperty`,
    defaults to 1.
    '''

    _anchor = None  # the last anchor node selected (e.g. shift relative node)
    _last_selected_node = None  # the absolute last node selected
    _ctrl_down = False
    _shift_down = False
    _key_list = []  # keyboard keys already processed
    _scroll_codes = {'scrollup': (Keyboard.keycodes['down'], 'down'),
                     'scrolldown': (Keyboard.keycodes['up'], 'up'),
                     'scrollleft': (Keyboard.keycodes['right'], 'right'),
                     'scrollright': (Keyboard.keycodes['left'], 'left')}

    def __init__(self, **kwargs):
        super(SelectionBehavior, self).__init__(**kwargs)

        def ensure_single_select(*l):
            if (not self.multiselect) and len(self.selected_nodes) > 1:
                self.clear_selection()
        self.bind(multiselect=ensure_single_select)

    def select_with_touch(self, node, touch=None):
        '''Processes a touch on the node. This is called when a node is touched
        and is to be used for selection. Depending on the keyboard keys pressed
        and the configuration, it could select or deslect this and other nodes
        in the selectable nodes list, :meth:`get_selectable_nodes`.

        :Parameters:
            `node`
                The node that recieved the touch. Can be None for a scroll
                type touch.
            `touch`
                Optionally, the touch. Defaults to None.

        :Returns:
            bool, True if the touch was used.
        '''
        multi = self.multiselect
        multiselect = multi and (self._ctrl_down or self.touch_multiselect)
        range_select = multi and self._shift_down

        btns = self._scroll_codes
        if touch and 'button' in touch.profile and touch.button in btns:
            modifiers = []
            if range_select:
                modifiers.append('shift')
            if multiselect:
                modifiers.append('ctrl')
            return self.select_with_key_down(None, btns[touch.button], '',
                                             modifiers)
        if node is None:
            return False

        if (node in self.selected_nodes and (not range_select)):  # selected
            if multiselect:  # ctrl type selection
                self.deselect_node(node)
            else:
                self.clear_selection()
                self.select_node(node)
        elif range_select:  # whether selected or not, select all in range
            self._select_range(multiselect, not multiselect, node=node)
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
            bool, True if the keypress was used.
        '''
        sister_nodes = self.get_selectable_nodes()
        keys = self._key_list
        multi = self.multiselect
        # for keyboard, we have a anchor, and we select everything between
        # anchor and added offset relative to last node
        last_node = self._last_selected_node
        if last_node is None:
            last_node = self._anchor
        if last_node is None:
            idx = 0
        else:
            try:
                idx = sister_nodes.index(last_node)
            except ValueError:
                idx = 0

        if scancode[1] == 'shift':
            self._shift_down = True
            return True
        elif scancode[1] == 'ctrl':
            self._ctrl_down = True
            return True
        elif (multi and 'ctrl' in modifiers and (scancode[1] == 'a'
            or scancode[1] == 'A') and scancode[1] not in keys):
            select = self.select_node
            for node in sister_nodes:
                select(node)
            keys.append(scancode[1])
            return True
        elif scancode[1] == 'pageup':
            idx = max(0, idx - self.page_count)
        elif scancode[1] == 'pagedown':
            idx = min(len(sister_nodes) - 1, idx + self.page_count)
        elif scancode[1] == 'home' and 'home' not in keys:
            idx = 0
            keys.append('home')
        elif scancode[1] == 'end' and 'end' not in keys:
            idx = len(sister_nodes) - 1
            keys.append('end')
        elif scancode[1] == 'up':
            idx = max(0, idx - self.up_count)
        elif scancode[1] == 'down':
            idx = min(len(sister_nodes) - 1, idx + self.up_count)
        elif scancode[1] == 'left':
            idx = max(0, idx - self.right_count)
        elif scancode[1] == 'right':
            idx = min(len(sister_nodes) - 1, idx + self.right_count)
        else:
            return False

        multiselect = multi and 'ctrl' in modifiers
        range_select = multi and 'shift' in modifiers
        if range_select:
            self._select_range(multiselect, True, idx=idx)
        elif not multiselect:
            self.clear_selection()
            self.select_node(sister_nodes[idx])
        return True

    def select_with_key_up(self, keyboard, scancode, **kwargs):
        '''Processes a key release. This must be called when a key that
        :meth:`select_with_key_down` returned True is released.

        The parameters are such that it could be bound directly to the
        on_key_up event of a keyboard.

        :Returns:
            bool, True if the key release was used.
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

    def _select_range(self, multiselect, keep_anchor, node=None, idx=-1):
        select = self.select_node
        sister_nodes = self.get_selectable_nodes()
        last_node = self._anchor

        if last_node is None:
            idx1 = 0
            last_node = sister_nodes[0]
        else:
            try:
                idx1 = sister_nodes.index(last_node)
            except ValueError:
                # list changed - cannot do select across them
                return
        if node is None:
            idx2 = idx
            node = sister_nodes[idx]
        else:
            try:    # just in case
                idx2 = sister_nodes.index(node)
            except ValueError:
                return

        if idx1 > idx2:
            idx1, idx2 = idx2, idx1
        if not multiselect:
            self.clear_selection()
        for item in sister_nodes[idx1:idx2 + 1]:
            select(item)

        if keep_anchor:
            self._anchor = last_node
        else:
            self._anchor = node  # in case idx was reversed, reset
        self._last_selected_node = node

    def clear_selection(self):
        ''' Deselects all the currently selected nodes.
        '''
        deselect = self.deselect_node
        nodes = self.selected_nodes
        self._anchor = None
        # empty beforehand so lookup in deselect will be fast
        self.selected_nodes = []
        for node in nodes:
            deselect(node)

    def get_selectable_nodes(self):
        ''' Returns a list of the nodes that can be selected. It should be
        overwritten by the derived widget to return the correct list.

        This list is used to determine which nodes to select with group
        selection. E.g. the first element in the list will be selected when
        home is pressed, pagedown will move (or add to, if shift is held) the
        selection from the current position by :attr:`page_count` nodes
        starting from the position of the currently selected node in this list
        and so on.

        .. note::

            It is safe to dynamically change this list including removing,
            adding, or re-arranging its elements. Nodes can be selected even
            if they are not on this list. And selected nodes
            removed from the list will remain selected until
            :meth:`deselect_node` is called.

        Defaults to returning :attr:`~kivy.uix.Widget.children` in reverse
        order (because layouts display their elements in reverse order).
        '''
        return self.children[::-1]  # to make it work by default for layouts

    def select_node(self, node):
        ''' Selects a node.

        It is called by the controller when it selects a node and should be
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

        It is called by the controller when it deselects a node and should be
        called from the outside to deselect a node directly. The derived widget
        should overwrite this method and change the node to its unselected
        state when this is called

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
        if self._anchor == node:
            self._anchor = None
