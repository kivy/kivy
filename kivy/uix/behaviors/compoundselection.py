'''
Compound Selection Behavior
===========================

The :class:`~kivy.uix.behaviors.compoundselection.CompoundSelectionBehavior`
`mixin <https://en.wikipedia.org/wiki/Mixin>`_ class implements the logic
behind keyboard and touch selection of selectable widgets managed by the
derived widget. For example, it can be combined with a
:class:`~kivy.uix.gridlayout.GridLayout` to add selection to the layout.

Compound selection concepts
---------------------------

At its core, it keeps a dynamic list of widgets that can be selected.
Then, as the touches and keyboard input are passed in, it selects one or
more of the widgets based on these inputs. For example, it uses the mouse
scroll and keyboard up/down buttons to scroll through the list of widgets.
Multiselection can also be achieved using the keyboard shift and ctrl keys.

Finally, in addition to the up/down type keyboard inputs, compound selection
can also accept letters from the keyboard to be used to select nodes with
associated strings that start with those letters, similar to how files
are selected by a file browser.

Selection mechanics
-------------------

When the controller needs to select a node, it calls :meth:`select_node` and
:meth:`deselect_node`. Therefore, they must be overwritten in order alter
node selection. By default, the class doesn't listen for keyboard or
touch events, so the derived widget must call
:meth:`select_with_touch`, :meth:`select_with_key_down`, and
:meth:`select_with_key_up` on events that it wants to pass on for selection
purposes.

Example
-------

To add selection to a grid layout which will contain
:class:`~kivy.uix.Button` widgets. For each button added to the layout, you
need to bind the :attr:`~kivy.uix.widget.Widget.on_touch_down` of the button
to :meth:`select_with_touch` to pass on the touch events::

    from kivy.uix.behaviors.compoundselection import CompoundSelectionBehavior
    from kivy.uix.button import Button
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.behaviors import FocusBehavior
    from kivy.core.window import Window
    from kivy.app import App


    class SelectableGrid(FocusBehavior, CompoundSelectionBehavior, GridLayout):

        def keyboard_on_key_down(self, window, keycode, text, modifiers):
            """Based on FocusBehavior that provides automatic keyboard
            access, key presses will be used to select children.
            """
            if super(SelectableGrid, self).keyboard_on_key_down(
                window, keycode, text, modifiers):
                return True
            if self.select_with_key_down(window, keycode, text, modifiers):
                return True
            return False

        def keyboard_on_key_up(self, window, keycode):
            """Based on FocusBehavior that provides automatic keyboard
            access, key release will be used to select children.
            """
            if super(SelectableGrid, self).keyboard_on_key_up(window, keycode):
                return True
            if self.select_with_key_up(window, keycode):
                return True
            return False

        def add_widget(self, widget, *args, **kwargs):
            """ Override the adding of widgets so we can bind and catch their
            *on_touch_down* events. """
            widget.bind(on_touch_down=self.button_touch_down,
                        on_touch_up=self.button_touch_up)
            return super(SelectableGrid, self)\
                .add_widget(widget, *args, **kwargs)

        def button_touch_down(self, button, touch):
            """ Use collision detection to select buttons when the touch occurs
            within their area. """
            if button.collide_point(*touch.pos):
                self.select_with_touch(button, touch)

        def button_touch_up(self, button, touch):
            """ Use collision detection to de-select buttons when the touch
            occurs outside their area and *touch_multiselect* is not True. """
            if not (button.collide_point(*touch.pos) or
                    self.touch_multiselect):
                self.deselect_node(button)

        def select_node(self, node):
            node.background_color = (1, 0, 0, 1)
            return super(SelectableGrid, self).select_node(node)

        def deselect_node(self, node):
            node.background_color = (1, 1, 1, 1)
            super(SelectableGrid, self).deselect_node(node)

        def on_selected_nodes(self, grid, nodes):
            print("Selected nodes = {0}".format(nodes))


    class TestApp(App):
        def build(self):
            grid = SelectableGrid(cols=3, rows=2, touch_multiselect=True,
                                  multiselect=True)
            for i in range(0, 6):
                grid.add_widget(Button(text="Button {0}".format(i)))
            return grid


    TestApp().run()


.. warning::

    This code is still experimental, and its API is subject to change in a
    future version.

'''

__all__ = ('CompoundSelectionBehavior', )

from time import time
from os import environ

from kivy.properties import NumericProperty, BooleanProperty, ListProperty


if 'KIVY_DOC' not in environ:
    from kivy.config import Config
    _is_desktop = Config.getboolean('kivy', 'desktop')
else:
    _is_desktop = False


class CompoundSelectionBehavior(object):
    '''The Selection behavior `mixin <https://en.wikipedia.org/wiki/Mixin>`_
    implements the logic behind keyboard and touch
    selection of selectable widgets managed by the derived widget. Please see
    the :mod:`compound selection behaviors module
    <kivy.uix.behaviors.compoundselection>` documentation
    for more information.

    .. versionadded:: 1.9.0
    '''

    selected_nodes = ListProperty([])
    '''The list of selected nodes.

    .. note::

        Multiple nodes can be selected right after one another e.g. using the
        keyboard. When listening to :attr:`selected_nodes`, one should be
        aware of this.

    :attr:`selected_nodes` is a :class:`~kivy.properties.ListProperty` and
    defaults to the empty list, []. It is read-only and should not be modified.
    '''

    touch_multiselect = BooleanProperty(False)
    '''A special touch mode which determines whether touch events, as
    processed by :meth:`select_with_touch`, will add the currently touched
    node to the selection, or if it will clear the selection before adding the
    node. This allows the selection of multiple nodes by simply touching them.

    This is different from :attr:`multiselect` because when it is True,
    simply touching an unselected node will select it, even if ctrl is not
    pressed. If it is False, however, ctrl must be pressed in order to
    add to the selection when :attr:`multiselect` is True.

    .. note::

        :attr:`multiselect`, when False, will disable
        :attr:`touch_multiselect`.

    :attr:`touch_multiselect` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to False.
    '''

    multiselect = BooleanProperty(False)
    '''Determines whether multiple nodes can be selected. If enabled, keyboard
    shift and ctrl selection, optionally combined with touch, for example, will
    be able to select multiple widgets in the normally expected manner.
    This dominates :attr:`touch_multiselect` when False.

    :attr:`multiselect` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    touch_deselect_last = BooleanProperty(not _is_desktop)
    '''Determines whether the last selected node can be deselected when
    :attr:`multiselect` or :attr:`touch_multiselect` is False.

    .. versionadded:: 1.10.0

    :attr:`touch_deselect_last` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to True on mobile, False on desktop platforms.
    '''

    keyboard_select = BooleanProperty(True)
    '''Determines whether the keyboard can be used for selection. If False,
    keyboard inputs will be ignored.

    :attr:`keyboard_select` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to True.
    '''

    page_count = NumericProperty(10)
    '''Determines by how much the selected node is moved up or down, relative
    to the position of the last selected node, when pageup (or pagedown) is
    pressed.

    :attr:`page_count` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 10.
    '''

    up_count = NumericProperty(1)
    '''Determines by how much the selected node is moved up or down, relative
    to the position of the last selected node, when the up (or down) arrow on
    the keyboard is pressed.

    :attr:`up_count` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 1.
    '''

    right_count = NumericProperty(1)
    '''Determines by how much the selected node is moved up or down, relative
    to the position of the last selected node, when the right (or left) arrow
    on the keyboard is pressed.

    :attr:`right_count` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 1.
    '''

    scroll_count = NumericProperty(0)
    '''Determines by how much the selected node is moved up or down, relative
    to the position of the last selected node, when the mouse scroll wheel is
    scrolled.

    :attr:`right_count` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.
    '''

    nodes_order_reversed = BooleanProperty(True)
    ''' (Internal) Indicates whether the order of the nodes as displayed top-
    down is reversed compared to their order in :meth:`get_selectable_nodes`
    (e.g. how the children property is reversed compared to how
    it's displayed).
    '''

    text_entry_timeout = NumericProperty(1.)
    '''When typing characters in rapid succession (i.e. the time difference since
    the last character is less than :attr:`text_entry_timeout`), the keys get
    concatenated and the combined text is passed as the key argument of
    :meth:`goto_node`.

    .. versionadded:: 1.10.0
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
    _key_list = []  # keys that are already pressed, to not press continuously
    _offset_counts = {}  # cache of counts for faster access

    def __init__(self, **kwargs):
        super(CompoundSelectionBehavior, self).__init__(**kwargs)
        self._key_list = []

        def ensure_single_select(*l):
            if (not self.multiselect) and len(self.selected_nodes) > 1:
                self.clear_selection()
        update_counts = self._update_counts
        update_counts()
        fbind = self.fbind
        fbind('multiselect', ensure_single_select)
        fbind('page_count', update_counts)
        fbind('up_count', update_counts)
        fbind('right_count', update_counts)
        fbind('scroll_count', update_counts)

    def select_with_touch(self, node, touch=None):
        '''(internal) Processes a touch on the node. This should be called by
        the derived widget when a node is touched and is to be used for
        selection. Depending on the keyboard keys pressed and the
        configuration, it could select or deslect this and other nodes in the
        selectable nodes list, :meth:`get_selectable_nodes`.

        :Parameters:
            `node`
                The node that received the touch. Can be None for a scroll
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
            node_src, idx_src = self._resolve_last_node()
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
                selected_node_count = len(self.selected_nodes)
                self.clear_selection()
                if not self.touch_deselect_last or selected_node_count > 1:
                    self.select_node(node)
        elif range_select:
            # keep anchor only if not multiselect (ctrl-type selection)
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
        configuration, it could select or deselect nodes or node ranges
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
        node_src, idx_src = self._resolve_last_node()
        text = scancode[1]

        if text == 'shift':
            self._shift_down = True
        elif text in ('ctrl', 'lctrl', 'rctrl'):
            self._ctrl_down = True
        elif (multi and 'ctrl' in modifiers and text in ('a', 'A') and
              text not in keys):
            sister_nodes = self.get_selectable_nodes()
            select = self.select_node
            for node in sister_nodes:
                select(node)
            keys.append(text)
        else:
            s = text
            if len(text) > 1:
                d = {'divide': '/', 'mul': '*', 'substract': '-', 'add': '+',
                     'decimal': '.'}
                if text.startswith('numpad'):
                    s = text[6:]
                    if len(s) > 1:
                        if s in d:
                            s = d[s]
                        else:
                            s = None
                else:
                    s = None

            if s is not None:
                if s not in keys:  # don't keep adding while holding down
                    if time() - self._last_key_time <= self.text_entry_timeout:
                        self._word_filter += s
                    else:
                        self._word_filter = s
                    keys.append(s)

                self._last_key_time = time()
                node, idx = self.goto_node(self._word_filter, node_src,
                                           idx_src)
            else:
                self._word_filter = ''
                node, idx = self.goto_node(text, node_src, idx_src)

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
        self._word_filter = ''
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
        elif scancode[1] in ('ctrl', 'lctrl', 'rctrl'):
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

    def _resolve_last_node(self):
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
                return last_node, self.get_index_of_node(last_node,
                                                         sister_nodes)
            except ValueError:
                return sister_nodes[end], end
        return last_node, last_idx

    def _select_range(self, multiselect, keep_anchor, node, idx):
        '''Selects a range between self._anchor and node or idx.
        If multiselect is True, it will be added to the selection, otherwise
        it will unselect everything before selecting the range. This is only
        called if self.multiselect is True.
        If keep anchor is False, the anchor is moved to node. This should
        always be True for keyboard selection.
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
                    last_idx = self.get_index_of_node(last_node, sister_nodes)
                except ValueError:
                    # list changed - cannot do select across them
                    return
        if idx > end or sister_nodes[idx] != node:
            try:    # just in case
                idx = self.get_index_of_node(node, sister_nodes)
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
        for node in nodes[:]:
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
            indices of the elements returned by this function are reversed to
            make it work by default for most layouts so that the final result
            is consistent e.g. home, although it will select the last element
            in this list visually, will select the first element when
            counting from top to bottom and left to right. If this behavior is
            not desired, a reversed list should be returned instead.

        Defaults to returning :attr:`~kivy.uix.widget.Widget.children`.
        '''
        return self.children

    def get_index_of_node(self, node, selectable_nodes):
        '''(internal) Returns the index of the `node` within the
        `selectable_nodes` returned by :meth:`get_selectable_nodes`.
        '''
        return selectable_nodes.index(node)

    def goto_node(self, key, last_node, last_node_idx):
        '''(internal) Used by the controller to get the node at the position
        indicated by key. The key can be keyboard inputs, e.g. pageup,
        or scroll inputs from the mouse scroll wheel, e.g. scrollup.
        'last_node' is the last node selected and is used to find the resulting
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
                last_node_idx = self.get_index_of_node(last_node, sister_nodes)
            except ValueError:
                return last_node, last_node_idx

        is_reversed = self.nodes_order_reversed
        if key in counts:
            count = -counts[key] if is_reversed else counts[key]
            idx = max(min(count + last_node_idx, end), 0)
            return sister_nodes[idx], idx
        elif key == 'home':
            if is_reversed:
                return sister_nodes[end], end
            return sister_nodes[0], 0
        elif key == 'end':
            if is_reversed:
                return sister_nodes[0], 0
            return sister_nodes[end], end
        else:
            return last_node, last_node_idx

    def select_node(self, node):
        ''' Selects a node.

        It is called by the controller when it selects a node and can be
        called from the outside to select a node directly. The derived widget
        should overwrite this method and change the node state to selected
        when called.

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
        if node in nodes:
            return False

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
            return True
        except ValueError:
            return False
