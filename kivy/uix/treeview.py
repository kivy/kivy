'''
Tree View
=========

.. versionadded:: 1.0.4

.. warning::

    This widget is still experimental, and his API is subject to change in a
    future version.

:class:`TreeView` is a widget to represent a tree structure. It is currently
very basic, supporting a minimal feature set.

Introduction
------------

A :class:`TreeView` is populated with :class:`TreeViewNode` instances, but you
cannot use a :class:`TreeViewNode` directly. You must combine it with another
widget, such as :class:`~kivy.uix.label.Label`,
:class:`~kivy.uix.button.Button`... or even your own widget. The TreeView
always creates a default root node, based on :class:`TreeViewLabel`.

:class:`TreeViewNode` is a class object containing needed properties for
serving as a tree node. Extend TreeViewNode to create custom a custom node
type for use with :class:`TreeView`.

For constructing your own subclass, follow the pattern of TreeViewLabel, which
combines Label and TreeViewNode, producing :class:`TreeViewLabel` for direct
use in a TreeView instance.

To use the TreeViewLabel class, you could create two nodes, directly attached
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
to populate the tree view, as with::

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

The root widget in the tree view is opened by default, and has a text set as
'Root'. If you want to change that, you can use :data:`TreeView.root_options`
property. This will pass options to the root widget::

    tv = TreeView(root_options=dict(text='My root label'))


Creating Your Own Node Widget
-----------------------------

For a button node type, combine :class:`~kivy.uix.button.Button` +
:class:`TreeViewNode` like this::

    class TreeViewButton(Button, TreeViewNode):
        pass

You must know that, for a given node, only the
:data:`~kivy.uix.widget.Widget.size_hint_x` will be honored. The allocated
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


class TreeViewException(Exception):
    '''Exception for errors in the :class:`TreeView`.
    '''
    pass


class TreeViewNode(object):
    '''TreeViewNode class, used to build node class for TreeView object.
    '''

    def __init__(self, **kwargs):
        if self.__class__ is TreeViewNode:
            raise TreeViewException('You cannot use directly TreeViewNode.')
        super(TreeViewNode, self).__init__(**kwargs)

    is_leaf = BooleanProperty(True)
    '''Boolean to indicate if this node is a leaf or not. Used to adjust
    graphical representation.

    :data:`is_leaf` is a :class:`~kivy.properties.BooleanProperty`, defaults to
    True, and automatically set to False when child is added.
    '''

    is_open = BooleanProperty(False)
    '''Boolean to indicate if this node is opened or not, in case if there are
    child nodes. This is used to adjust graphical representation.

    .. warning::

        This property is automatically set by the :class:`TreeView`. You can
        read but not write it.

    :data:`is_open` is a :class:`~kivy.properties.BooleanProperty`, defaults to
    False.
    '''

    is_loaded = BooleanProperty(False)
    '''Boolean to indicate if this node is already loaded or not. This property
    is used only if the :class:`TreeView` uses asynchronous loading.

    :data:`is_loaded` is a :class:`~kivy.properties.BooleanProperty`, default
    to False
    '''

    is_selected = BooleanProperty(False)
    '''Boolean to indicate if this node is selected or not. This is used for
    graphical representation.

    .. warning::

        This property is automatically set by the :class:`TreeView`. You can
        read but not write it.

    :data:`is_selected` is a :class:`~kivy.properties.BooleanProperty`, default
    to False.
    '''

    no_selection = BooleanProperty(False)
    '''Boolean to indicate if we allow selection of the node or not.

    :data:`no_selection` is a :class:`~kivy.properties.BooleanProperty`,
    defaults to False
    '''

    nodes = ListProperty([])
    '''List of nodes. The nodes list is different than the children list. A
    node in the nodes list represents a node on the tree. An item in the
    children list represents the widget associated with the node.

    .. warning::

        This property is automatically set by the :class:`TreeView`. You can
        read but not write it.

    :data:`nodes` is a :class:`~kivy.properties.ListProperty`, defaults to [].
    '''

    parent_node = ObjectProperty(None, allownone=True)
    '''Parent node. This attribute is needed because :data:`parent` can be None
    when the node is not displayed.

    .. versionadded:: 1.0.7

    :data:`parent_node` is a :class:`~kivy.properties.ObjectProperty`, default
    to None.
    '''

    level = NumericProperty(-1)
    '''Level of the node.

    :data:`level` is a :class:`~kivy.properties.NumericProperty`, defaults to
    -1.
    '''

    color_selected = ListProperty([.3, .3, .3, 1.])
    '''Background color of the node when the node is selected.

    :data:`color_selected` is a :class:`~kivy.properties.ListProperty`,
    defaults to [.1, .1, .1, 1]
    '''

    odd = BooleanProperty(False)
    '''
    This property is set by the TreeView widget automatically. Read-only.
    :data:`odd` is a :class:`~kivy.properties.BooleanProperty`, defaults to
    False.
    '''

    odd_color = ListProperty([1., 1., 1., .0])
    '''Background color of odd nodes when the node is not selected.

    :data:`bg_color` is a :class:`~kivy.properties.ListProperty`, default
    to [1., 1., 1., 0.].
    '''

    even_color = ListProperty([0.5, 0.5, 0.5, 0.1])
    '''Background color of even nodes when the node is not selected.

    :data:`bg_color` is a :class:`~kivy.properties.ListProperty`, default
    to [.5, .5, .5, .1].
    '''


class TreeViewLabel(Label, TreeViewNode):
    '''Combine :class:`~kivy.uix.label.Label` and :class:`TreeViewNode` to
    create a :class:`TreeViewLabel`, that can be used as a text node in the
    tree.

    See module documentation for more information.
    '''


class TreeView(Widget):
    '''TreeView class. See module documentation for more information.

    :Events:
        `on_node_expand`: (node, )
            Fired when a node is being expanded
        `on_node_collapse`: (node, )
            Fired when a node is being collapsed
    '''

    __events__ = ('on_node_expand', 'on_node_collapse')

    def __init__(self, **kwargs):
        self._trigger_layout = Clock.create_trigger(self._do_layout, -1)
        super(TreeView, self).__init__(**kwargs)
        tvlabel = TreeViewLabel(text='Root', is_open=True, level=0)
        for key, value in self.root_options.items():
            setattr(tvlabel, key, value)
        self._root = self.add_node(tvlabel, None)
        self.bind(
            pos=self._trigger_layout,
            size=self._trigger_layout,
            indent_level=self._trigger_layout,
            indent_start=self._trigger_layout)
        self._trigger_layout()

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
            parent.is_leaf = False
            parent.nodes.append(node)
            node.parent_node = parent
            node.level = parent.level + 1
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
            nodes = parent.nodes
            if node in nodes:
                nodes.remove(node)
            parent.is_leaf = not bool(len(nodes))
            node.parent_node = None
            node.unbind(size=self._trigger_layout)
            self._trigger_layout()

    def on_node_expand(self, node):
        pass

    def on_node_collapse(self, node):
        pass

    def select_node(self, node):
        '''Select a node in the tree.
        '''
        if node.no_selection:
            return
        if self._selected_node:
            self._selected_node.is_selected = False
        node.is_selected = True
        self._selected_node = node

    def toggle_node(self, node):
        '''Toggle the state of the node (open/collapse).
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
        '''Get a node at the position (x, y).
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
                node.width = (self.width - (node.x - self.x)) * node.size_hint_x
            y -= node.height
            if not node.is_open:
                return y
        for cnode in node.nodes:
            y = self._do_layout_node(cnode, level + 1, y)
        return y

    def on_touch_down(self, touch):
        node = self.get_node_at_pos(touch.pos)
        if not node:
            return
        if node.disabled:
            return
        # toggle node or selection ?
        if node.x - self.indent_start <= touch.x < node.x:
            self.toggle_node(node)
        elif node.x <= touch.x:
            self.select_node(node)
            node.dispatch('on_touch_down', touch)
        return True

    #
    # Private properties
    #
    _root = ObjectProperty(None)

    _selected_node = ObjectProperty(None)

    #
    # Properties
    #

    minimum_width = NumericProperty(0)
    '''Minimum width needed to contain all children.

    .. versionadded:: 1.0.9

    :data:`minimum_width` is a :class:`kivy.properties.NumericProperty`,
    defaults to 0.
    '''

    minimum_height = NumericProperty(0)
    '''Minimum height needed to contain all children.

    .. versionadded:: 1.0.9

    :data:`minimum_height` is a :class:`kivy.properties.NumericProperty`,
    defaults to 0.
    '''

    minimum_size = ReferenceListProperty(minimum_width, minimum_height)
    '''Minimum size needed to contain all children.

    .. versionadded:: 1.0.9

    :data:`minimum_size` is a :class:`~kivy.properties.ReferenceListProperty`
    of (:data:`minimum_width`, :data:`minimum_height`) properties.
    '''

    indent_level = NumericProperty('16dp')
    '''Width used for identation of each level, except the first level.

    Computation of spacing for eaching level of tree is::

        :data:`indent_start` + level * :data:`indent_level`

    :data:`indent_level` is a :class:`~kivy.properties.NumericProperty`,
    defaults to 16.
    '''

    indent_start = NumericProperty('24dp')
    '''Indentation width of the level 0 / root node. This is mostly the initial
    size to accommodate a tree icon (collapsed / expanded). See
    :data:`indent_level` for more information about the computation of level
    indentation.

    :data:`indent_start` is a :class:`~kivy.properties.NumericProperty`,
    defaults to 24.
    '''

    hide_root = BooleanProperty(False)
    '''Use this property to show/hide the initial root node. If True, the root
    node will be appear as a closed node.

    :data:`hide_root` is a :class:`~kivy.properties.BooleanProperty`, defaults
    to False.
    '''

    def get_selected_node(self):
        return self._selected_node

    selected_node = AliasProperty(get_selected_node, None,
                                  bind=('_selected_node', ))
    '''Node selected by :meth:`TreeView.select_node`, or by touch.

    :data:`selected_node` is a :class:`~kivy.properties.AliasProperty`, defaults
    to None, and is read-only.
    '''

    def get_root(self):
        return self._root

    root = AliasProperty(get_root, None, bind=('_root', ))
    '''Root node.

    By default, the root node widget is a :class:`TreeViewLabel`, with text
    'Root'. If you want to change the default options passed to the widget
    creation, use the :data:`root_options` property::

        treeview = TreeView(root_options={
            'text': 'Root directory',
            'font_size': 15})

    :data:`root_options` will change the properties of the
    :class:`TreeViewLabel` instance. However, you cannot change the class used
    for root node yet.

    :data:`root` is a :class:`~kivy.properties.AliasProperty`, defaults to
    None, and is read-only. However, the content of the widget can be changed.
    '''

    root_options = ObjectProperty({})
    '''Default root options to pass for root widget. See :data:`root` property
    for more information about the usage of root_options.

    :data:`root_options` is a :class:`~kivy.properties.ObjectProperty`, default
    to {}.
    '''

    load_func = ObjectProperty(None)
    '''Callback to use for asynchronous loading. If set, asynchronous loading
    will be automatically done. The callback must act as a Python generator
    function, using yield to send data back to the treeview.

    The callback should be in the format::

        def callback(treeview, node):
            for name in ('Item 1', 'Item 2'):
                yield TreeViewLabel(text=name)

    :data:`load_func` is a :class:`~kivy.properties.ObjectProperty`, defaults
    to None.
    '''


if __name__ == '__main__':
    from kivy.app import App

    class TestApp(App):

        def build(self):
            tv = TreeView(hide_root=True)
            add = tv.add_node
            root = add(TreeViewLabel(text='Level 1, entry 1', is_open=True))
            for x in range(5):
                add(TreeViewLabel(text='Element %d' % x), root)
            root2 = add(TreeViewLabel(text='Level 1, entry 2', is_open=False))
            for x in range(24):
                add(TreeViewLabel(text='Element %d' % x), root2)
            for x in range(5):
                add(TreeViewLabel(text='Element %d' % x), root)
            root2 = add(TreeViewLabel(text='Element childs 2', is_open=False),
                        root)
            for x in range(24):
                add(TreeViewLabel(text='Element %d' % x), root2)
            return tv
    TestApp().run()
