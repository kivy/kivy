'''
Tree View
=========

.. versionadded:: 1.0.4


:class:`TreeView` is a widget used to represent a tree structure. It is
currently very basic, supporting a minimal feature set.

Introduction
------------

A :class:`TreeView` is populated with :class:`TreeViewNode` instances, but you
cannot use a :class:`TreeViewNode` directly. You must combine it with another
widget, such as :class:`~kivy.uix.label.Label`,
:class:`~kivy.uix.button.Button` or even your own widget. The TreeView
always creates a default root node, based on :class:`TreeViewLabel`.

:class:`TreeViewNode` is a class object containing needed properties for
serving as a tree node. Extend :class:`TreeViewNode` to create custom node
types for use with a :class:`TreeView`.

For constructing your own subclass, follow the pattern of TreeViewLabel which
combines a Label and a TreeViewNode, producing a :class:`TreeViewLabel` for
direct use in a TreeView instance.

To use the TreeViewLabel class, you could create two nodes directly attached
to root::

    tv = TreeView()
    tv.add_node(TreeViewLabel(text='My first item'))
    tv.add_node(TreeViewLabel(text='My second item'))

Or, create two nodes attached to a first::

    tv = TreeView()
    n1 = tv.add_node(TreeViewLabel(text='Item 1'))
    tv.add_node(TreeViewLabel(text='SubItem 1'), n1)
    tv.add_node(TreeViewLabel(text='SubItem 2'), n1)

If you have a large tree structure, perhaps you would need a utility function
to populate the tree view::

    def populate_tree_view(tree_view, parent, node):
        if parent is None:
            tree_node = tree_view.add_node(TreeViewLabel(text=node['node_id'],
                                                         is_open=True))
        else:
            tree_node = tree_view.add_node(TreeViewLabel(text=node['node_id'],
                                                         is_open=True), parent)

        for child_node in node['children']:
            populate_tree_view(tree_view, tree_node, child_node)


    tree = {'node_id': '1',
            'children': [{'node_id': '1.1',
                          'children': [{'node_id': '1.1.1',
                                        'children': [{'node_id': '1.1.1.1',
                                                      'children': []}]},
                                       {'node_id': '1.1.2',
                                        'children': []},
                                       {'node_id': '1.1.3',
                                        'children': []}]},
                          {'node_id': '1.2',
                           'children': []}]}


    class TreeWidget(FloatLayout):
        def __init__(self, **kwargs):
            super(TreeWidget, self).__init__(**kwargs)

            tv = TreeView(root_options=dict(text='Tree One'),
                          hide_root=False,
                          indent_level=4)

            populate_tree_view(tv, None, tree)

            self.add_widget(tv)

The root widget in the tree view is opened by default and has text set as
'Root'. If you want to change that, you can use the
:attr:`TreeView.root_options`
property. This will pass options to the root widget::

    tv = TreeView(root_options=dict(text='My root label'))


Creating Your Own Node Widget
-----------------------------

For a button node type, combine a :class:`~kivy.uix.button.Button` and a
:class:`TreeViewNode` as follows::

    class TreeViewButton(Button, TreeViewNode):
        pass

You must know that, for a given node, only the
:attr:`~kivy.uix.widget.Widget.size_hint_x` will be honored. The allocated
width for the node will depend of the current width of the TreeView and the
level of the node. For example, if a node is at level 4, the width
allocated will be:

    treeview.width - treeview.indent_start - treeview.indent_level * node.level

You might have some trouble with that. It is the developer's responsibility to
correctly handle adapting the graphical representation nodes, if needed.
'''

from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.properties import BooleanProperty, ListProperty, ObjectProperty, \
    AliasProperty, NumericProperty, ReferenceListProperty
from kivy.uix.behaviors import SelectionBehavior
from kivy.core.window import Window


class TreeViewException(Exception):
    '''Exception for errors in the :class:`TreeView`.
    '''
    pass


class TreeViewNode(object):
    '''TreeViewNode class, used to build a node class for a TreeView object.
    '''

    def __init__(self, **kwargs):
        if self.__class__ is TreeViewNode:
            raise TreeViewException('You cannot use directly TreeViewNode.')
        super(TreeViewNode, self).__init__(**kwargs)
        self.bind(is_leaf=self._on_is_leaf, no_selection=self._on_no_selection)

    def _on_is_leaf(self, instance, val):
        tree = self.parent_tree
        if (not val) and tree and tree.select_leaves_only:
            tree.deselect_node(self)
        self.is_selected = False

    def _on_no_selection(self, instance, val):
        tree = self.parent_tree
        if val and tree:
            tree.deselect_node(self)
        self.is_selected = False

    is_leaf = BooleanProperty(True)
    '''Boolean to indicate whether this node is a leaf or not. Used to adjust
    the graphical representation.

    :attr:`is_leaf` is a :class:`~kivy.properties.BooleanProperty` and defaults
    to True. It is automatically set to False when child is added.
    '''

    is_open = BooleanProperty(False)
    '''Boolean to indicate whether this node is opened or not, in case there
    are child nodes. This is used to adjust the graphical representation.

    .. warning::

        This property is automatically set by the :class:`TreeView`. You can
        read but not write it.

    :attr:`is_open` is a :class:`~kivy.properties.BooleanProperty` and defaults
    to False.
    '''

    is_loaded = BooleanProperty(False)
    '''Boolean to indicate whether this node is already loaded or not. This
    property is used only if the :class:`TreeView` uses asynchronous loading.

    :attr:`is_loaded` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    is_selected = BooleanProperty(False)
    '''Boolean to indicate whether this node is selected or not. This is used
    adjust the graphical representation.

    .. warning::

        This property is automatically set by the :class:`TreeView`. You can
        read but not write it.

    :attr:`is_selected` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    no_selection = BooleanProperty(False)
    '''Boolean used to indicate whether selection of the node is allowed or
    not.

    :attr:`no_selection` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    nodes = ListProperty([])
    '''List of nodes. The nodes list is different than the children list. A
    node in the nodes list represents a node on the tree. An item in the
    children list represents the widget associated with the node.

    .. warning::

        This property is automatically set by the :class:`TreeView`. You can
        read but not write it.

    :attr:`nodes` is a :class:`~kivy.properties.ListProperty` and defaults to
    [].
    '''

    parent_node = ObjectProperty(None, allownone=True)
    '''The :class:`TreeViewNode` that is the parent node of this node. This
    attribute is needed because the :attr:`parent` can be None when the node
    is not displayed.

    .. versionadded:: 1.0.7

    :attr:`parent_node` is a :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    '''

    parent_tree = ObjectProperty(None, allownone=True)
    '''The :class:`TreeView` instance of which this is a node. If the node has
    not been added to any tree or if it has been removed it'll be None. This
    is preferd to :attr:`parent`.

    .. versionadded:: 1.8.1

    :attr:`parent_tree` is a :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    '''

    level = NumericProperty(-1)
    '''Level of the node.

    :attr:`level` is a :class:`~kivy.properties.NumericProperty` and defaults
    to -1.
    '''

    color_selected = ListProperty([.3, .3, .3, 1.])
    '''Background color of the node when the node is selected.

    :attr:`color_selected` is a :class:`~kivy.properties.ListProperty` and
    defaults to [.1, .1, .1, 1].
    '''

    odd = BooleanProperty(False)
    '''
    This property is set by the TreeView widget automatically and is read-only.

    :attr:`odd` is a :class:`~kivy.properties.BooleanProperty` and defaults to
    False.
    '''

    odd_color = ListProperty([1., 1., 1., .0])
    '''Background color of odd nodes when the node is not selected.

    :attr:`odd_color` is a :class:`~kivy.properties.ListProperty` and defaults
    to [1., 1., 1., 0.].
    '''

    even_color = ListProperty([0.5, 0.5, 0.5, 0.1])
    '''Background color of even nodes when the node is not selected.

    :attr:`bg_color` is a :class:`~kivy.properties.ListProperty` ans defaults
    to [.5, .5, .5, .1].
    '''


class TreeViewLabel(Label, TreeViewNode):
    '''Combines a :class:`~kivy.uix.label.Label` and a :class:`TreeViewNode` to
    create a :class:`TreeViewLabel` that can be used as a text node in the
    tree.

    See module documentation for more information.
    '''


class TreeView(SelectionBehavior, Widget):
    '''TreeView class. See module documentation for more information.

    .. versionchanged:: 1.8.1

        TreeView has changed to inherit from
        :class:`~kivy.uix.SelectionBehavior`. Before, only a single node could
        be selected, now, multi-node selection is possible. Keyboard selection
        is now also possible.

        In additon, :attr:`selected_node` is deprecated in favor of
        :attr:`selected_nodes`, which lists all the nodes selected.

    :Events:
        `on_node_expand`: (node, )
            Fired when a node is being expanded
        `on_node_collapse`: (node, )
            Fired when a node is being collapsed
    '''

    __events__ = ('on_node_expand', 'on_node_collapse')
    _keyboard = None

    def __init__(self, **kwargs):
        self._trigger_layout = Clock.create_trigger(self._do_layout, -1)
        # in past multiselect was True be default, so if not specfied set it
        # to True. it only takes effect if multiselect is True, making it
        # behave the same as before
        if 'touch_multiselect' not in kwargs:
            self.touch_multiselect = True
        super(TreeView, self).__init__(**kwargs)
        tvlabel = TreeViewLabel(text='Root', is_open=True, level=0)
        for key, value in self.root_options.items():
            setattr(tvlabel, key, value)
        self._root = self.add_node(tvlabel, None)
        self._keyboard = None
        self._update_keyboard()
        self.bind(
            pos=self._trigger_layout,
            size=self._trigger_layout,
            indent_level=self._trigger_layout,
            indent_start=self._trigger_layout,
            keyboard_select=self._update_keyboard)
        self._trigger_layout()

    def __del__(self):
        self.keyboard_select = False
        self._release_keyboard()

    def _update_keyboard(self, *l):
        keyboard = self._keyboard
        if self.keyboard_select:
            if not keyboard:
                keyboard = Window.request_keyboard(self._update_keyboard, self)
                self._keyboard = keyboard
            if keyboard:
                keyboard.bind(on_key_down=self.select_with_key_down,
                              on_key_up=self.select_with_key_up)
        else:
            if keyboard:
                keyboard.unbind(on_key_down=self.select_with_key_down,
                                on_key_up=self.select_with_key_up)
                self._keyboard = None

    def add_node(self, node, parent=None):
        '''Add a new node in the tree.

        :Parameters:
            `node`: instance of a :class:`TreeViewNode`
                Node to add into the tree
            `parent`: instance of a :class:`TreeViewNode`, defaults to None
                Parent node to attach the new node
        '''
        # check if the widget is "ok" for a node
        if not isinstance(node, TreeViewNode):
            raise TreeViewException(
                'The node must be a subclass of TreeViewNode')
        # create node
        if parent is None and self._root:
            parent = self._root
        if parent:
            node.parent_tree = self
            parent.is_leaf = False
            parent.nodes.append(node)
            node.parent_node = parent
            node.level = parent.level + 1
            if self.select_leaves_only:
                self.deselect_node(parent)
        node.bind(size=self._trigger_layout)
        self._trigger_layout()
        return node

    def remove_node(self, node):
        '''Remove a node in a tree.

        .. versionadded:: 1.0.7

        :Parameters:
            `node`: instance of a :class:`TreeViewNode`
                Node to remove from the tree
        '''
        # check if the widget is "ok" for a node
        if not isinstance(node, TreeViewNode):
            raise TreeViewException(
                'The node must be a subclass of TreeViewNode')
        parent = node.parent_node
        if parent is not None:
            self.deselect_node(node)
            nodes = parent.nodes
            if node in nodes:
                nodes.remove(node)
            parent.is_leaf = not bool(len(nodes))
            node.parent_node = None
            node.unbind(size=self._trigger_layout)
            self._trigger_layout()
            node.parent_tree = None

    def on_node_expand(self, node):
        pass

    def on_node_collapse(self, node):
        pass

    def select_node(self, node):
        '''Selects a node in the tree. See
        :meth:`~kivy.uix.SelectionBehavior.select_node`.

        :Parameters:
            `node`: instance of a :class:`TreeViewNode` Node to select.
        '''
        if node.no_selection or (self.select_leaves_only and not node.is_leaf):
            return False
        if super(TreeView, self).select_node(node):
            node.is_selected = True
            return True
        return False

    def deselect_node(self, node):
        '''Deselect a node in the tree. See
        :meth:`~kivy.uix.SelectionBehavior.deselect_node`.

        .. versionadded:: 1.8.1

        :Parameters:
            `node`: instance of a :class:`TreeViewNode` Node to deselect.
        '''
        node.is_selected = False
        super(TreeView, self).deselect_node(node)

    def toggle_node(self, node):
        '''Toggle the state of the node (open/collapsed).
        '''
        node.is_open = not node.is_open
        if node.is_open:
            if self.load_func and not node.is_loaded:
                self._do_node_load(node)
            self.dispatch('on_node_expand', node)
        else:
            self.dispatch('on_node_collapse', node)
        self._trigger_layout()

    def get_node_at_pos(self, pos):
        '''Get the node at the position (x, y).
        '''
        x, y = pos
        for node in self.iterate_open_nodes(self.root):
            if self.x <= x <= self.right and \
               node.y <= y <= node.top:
                return node

    def iterate_open_nodes(self, node=None):
        '''Generator to iterate over expanded nodes.

        To get all the open nodes::

            treeview = TreeView()
            # ... add nodes ...
            for node in treeview.iterate_open_nodes():
                print(node)

        '''
        if not node:
            node = self.root
        if self.hide_root and node is self.root:
            pass
        else:
            yield node
        if not node.is_open:
            return
        f = self.iterate_open_nodes
        for cnode in node.nodes:
            for ynode in f(cnode):
                yield ynode

    def iterate_all_nodes(self, node=None):
        '''Generator to iterate over all nodes, expanded or not.
        '''
        if not node:
            node = self.root
        yield node
        f = self.iterate_all_nodes
        for cnode in node.nodes:
            for ynode in f(cnode):
                yield ynode

    #
    # Private
    #
    def on_load_func(self, instance, value):
        if value:
            Clock.schedule_once(self._do_initial_load)

    def _do_initial_load(self, *largs):
        if not self.load_func:
            return
        self._do_node_load(None)

    def _do_node_load(self, node):
        gen = self.load_func(self, node)
        if node:
            node.is_loaded = True
        if not gen:
            return
        for cnode in gen:
            self.add_node(cnode, node)

    def on_root_options(self, instance, value):
        if not self.root:
            return
        for key, value in value.items():
            setattr(self.root, key, value)

    def _do_layout(self, *largs):
        self.clear_widgets()
        # display only the one who are is_open
        self._do_open_node(self.root)
        # now do layout
        self._do_layout_node(self.root, 0, self.top)
        # now iterate for calculating minimum size
        min_width = min_height = 0
        count = 0
        for node in self.iterate_open_nodes(self.root):
            node.odd = False if count % 2 else True
            count += 1
            min_width = max(min_width, node.width + self.indent_level +
                            node.level * self.indent_level)
            min_height += node.height
        self.minimum_size = (min_width, min_height)

    def _do_open_node(self, node):
        if self.hide_root and node is self.root:
            height = 0
        else:
            self.add_widget(node)
            height = node.height
            if not node.is_open:
                return height
        for cnode in node.nodes:
            height += self._do_open_node(cnode)
        return height

    def _do_layout_node(self, node, level, y):
        if self.hide_root and node is self.root:
            level -= 1
        else:
            node.x = self.x + self.indent_start + level * self.indent_level
            node.top = y
            if node.size_hint_x:
                node.width = (self.width - (node.x - self.x)) \
                    * node.size_hint_x
            y -= node.height
            if not node.is_open:
                return y
        for cnode in node.nodes:
            y = self._do_layout_node(cnode, level + 1, y)
        return y

    def on_touch_down(self, touch):
        if 'button' in touch.profile and touch.button in\
            ('scrollup', 'scrolldown', 'scrollleft', 'scrollright')\
            and self.collide_point(*touch.pos):
            return self.select_with_touch(None, touch)
        node = self.get_node_at_pos(touch.pos)
        if not node:
            return
        if node.disabled:
            return
        # toggle node or selection ?
        if node.x - self.indent_start <= touch.x < node.x:
            self.toggle_node(node)
        elif node.x <= touch.x:
            self.select_with_touch(node, touch)
            node.dispatch('on_touch_down', touch)
        return True

    #
    # Private properties
    #
    _root = ObjectProperty(None)

    #
    # Properties
    #

    minimum_width = NumericProperty(0)
    '''Minimum width needed to contain all children.

    .. versionadded:: 1.0.9

    :attr:`minimum_width` is a :class:`kivy.properties.NumericProperty` and
    defaults to 0.
    '''

    minimum_height = NumericProperty(0)
    '''Minimum height needed to contain all children.

    .. versionadded:: 1.0.9

    :attr:`minimum_height` is a :class:`kivy.properties.NumericProperty` and
    defaults to 0.
    '''

    minimum_size = ReferenceListProperty(minimum_width, minimum_height)
    '''Minimum size needed to contain all children.

    .. versionadded:: 1.0.9

    :attr:`minimum_size` is a :class:`~kivy.properties.ReferenceListProperty`
    of (:attr:`minimum_width`, :attr:`minimum_height`) properties.
    '''

    indent_level = NumericProperty('16dp')
    '''Width used for the indentation of each level except the first level.

    Computation of spacing for each level of tree::

        :attr:`indent_start` + level * :attr:`indent_level`

    :attr:`indent_level` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 16.
    '''

    indent_start = NumericProperty('24dp')
    '''Indentation width of the level 0 / root node. This is mostly the initial
    size to accommodate a tree icon (collapsed / expanded). See
    :attr:`indent_level` for more information about the computation of level
    indentation.

    :attr:`indent_start` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 24.
    '''

    hide_root = BooleanProperty(False)
    '''Use this property to show/hide the initial root node. If True, the root
    node will be appear as a closed node.

    :attr:`hide_root` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    select_leaves_only = BooleanProperty(False)
    '''Determines whether non-leaf nodes are valid selections or not.

    .. versionadded:: 1.8.1

    :attr:`select_leaves_only` :class:`~kivy.properties.BooleanProperty`,
    defaults to False.
    '''

    def get_selected_node(self):
        nodes = self.selected_nodes
        return nodes[0] if len(nodes) else None

    selected_node = AliasProperty(get_selected_node, None,
                                  bind=('selected_nodes', ))
    '''Node selected with :meth:`select_node`.

    .. warning::

        Deprecated, use :attr:`selected_nodes` instead.

    .. versionchanged:: 1.8.1

        Previously, only one node could be selected at any time. This has been
        changed to allow multiple nodes to be selected and read using
        :attr:`selected_nodes`. :attr:`selected_node` remains only for backward
        compatibility and will be removed in version 2.0.0.
        :attr:`selected_node` will still return the first selected node, if
        there are any, or None otherwise.

    :attr:`selected_node` is a :class:`~kivy.properties.AliasProperty` and
    defaults to None. It is read-only.
    '''

    def get_root(self):
        return self._root

    root = AliasProperty(get_root, None, bind=('_root', ))
    '''Root node.

    By default, the root node widget is a :class:`TreeViewLabel` with text
    'Root'. If you want to change the default options passed to the widget
    creation, use the :attr:`root_options` property::

        treeview = TreeView(root_options={
            'text': 'Root directory',
            'font_size': 15})

    :attr:`root_options` will change the properties of the
    :class:`TreeViewLabel` instance. However, you cannot change the class used
    for root node yet.

    :attr:`root` is an :class:`~kivy.properties.AliasProperty` and defaults to
    None. It is read-only. However, the content of the widget can be changed.
    '''

    root_options = ObjectProperty({})
    '''Default root options to pass for root widget. See :attr:`root` property
    for more information about the usage of root_options.

    :attr:`root_options` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to {}.
    '''

    load_func = ObjectProperty(None)
    '''Callback to use for asynchronous loading. If set, asynchronous loading
    will be automatically done. The callback must act as a Python generator
    function, using yield to send data back to the treeview.

    The callback should be in the format::

        def callback(treeview, node):
            for name in ('Item 1', 'Item 2'):
                yield TreeViewLabel(text=name)

    :attr:`load_func` is a :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    '''


if __name__ == '__main__':
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout

    class TestApp(App):

        def build(self):
            box = BoxLayout(orientation='horizontal', spacing=20)
            for i in range(2):
                tv = TreeView(hide_root=True, multiselect=i == 1,
                              touch_multiselect=i == 0,
                              keyboard_select=True,
                              select_leaves_only=i == 0)
                add = tv.add_node
                root = add(TreeViewLabel(text='Level 1, entry 1',
                                         is_open=True))
                for x in range(5):
                    add(TreeViewLabel(text='Element %d' % x), root)
                root2 = add(TreeViewLabel(text='Level 1, entry 2',
                                          is_open=False))
                for x in range(24):
                    add(TreeViewLabel(text='Element %d' % x), root2)
                for x in range(5):
                    add(TreeViewLabel(text='Element %d' % x), root)
                root2 = add(TreeViewLabel(text='Element childs 2',
                                          is_open=False),
                            root)
                for x in range(24):
                    add(TreeViewLabel(text='Element %d' % x), root2)
                box.add_widget(tv)
            return box
    TestApp().run()
