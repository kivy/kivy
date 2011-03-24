'''
Tree View
=========

.. versionadded:: 1.0.4

.. warning::

    This widget is still experimental, and his API is subject to change in a
    future version.

:class:`TreeView` is a widget to represent tree list. It's currently very basic,
but support the minimal features set to be usable.

Introduction to the TreeView
----------------------------

A :class:`TreeView` is populated with :class:`TreeViewNode`, but you cannot use
directly a :class:`TreeViewNode`. You must combine it with another widget, such
as :class:`~kivy.uix.label.Label`, :class:`~kivy.uix.button.Button`... or even
your own widget. The TreeView always create a default root node, based on
:class:`TreeViewLabel`.

The :class:`TreeViewNode` is just an class object that hold the needed property
to successful use the other class as a node for the Tree. You can read the next
section about how to create custom node to be used in the :class:`TreeView`.

For you, we have combine Label + TreeViewNode: the result is a
:class:`TreeViewLabel`, that you can directly use as a node in the Tree.

For example, you can create 2 nodes, directly attached to root::

    tv = TreeView()
    tv.add_node(TreeViewLabel(text='My first item'))
    tv.add_node(TreeViewLabel(text='My second item'))

If you want to create 2 nodes attached to another one, you can do::

    tv = TreeView()
    n1 = tv.add_node(TreeViewLabel(text='Item 1'))
    tv.add_node(TreeViewLabel(text='SubItem 1'), n1)
    tv.add_node(TreeViewLabel(text='SubItem 2'), n1)

The default root widget is always opened, and have a default text 'Root'. If you
want to change that, you can use :data:`TreeView.root_options` property. This
will pass options to the root widget::

    tv = TreeView(root_options=dict(text='My root label'))


Create your own node widget
---------------------------

If you want to create a button node for example, you can just combine
:class:`~kivy.uix.button.Button` + :class:`TreeViewNode` like this::

    class TreeViewButton(Button, TreeViewNode):
        pass

You must know that only the :data:`~kivy.uix.widget.Widget.size_hint_x` will be
honored. The allocated width will depend of the current width of the TreeView
and the level of the node. For example, if your node is at level 4, the width
allocated will be:

    treeview.width - treeview.indent_start - treeview.indent_level * node.level

You might have some trouble with that, it's on your side to correctly handle
that case, and adapt the graphical representation of your node if needed
'''

from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.properties import BooleanProperty, ListProperty, ObjectProperty, \
        AliasProperty, NumericProperty


class TreeViewException(Exception):
    '''Exception for errors in the :class:`TreeView`
    '''
    pass


class TreeViewNode(object):
    '''TreeViewNode class, used to build node class for TreeView object.
    '''

    def __init__(self, **kwargs):
        if self.__class__ is TreeViewNode:
            raise TreeViewException('You cannot use directly TreeViewNode.')
        super(TreeViewNode, self).__init__(**kwargs)

    def get_is_leaf(self):
        return not bool(len(self.nodes))

    is_leaf = AliasProperty(get_is_leaf, None, bind=('nodes', ))
    '''Boolean to indicate if this node is a leaf or not, used to adjust
    graphical representation.

    :data:`is_leaf` is a :class:`~kivy.properties.AliasProperty`, default to
    False, and read-only.
    '''

    is_open = BooleanProperty(False)
    '''Boolean to indicate if this node is opened or not, in case if he contain
    children nodes. This is used for graphical representation.

    .. warning::

        This property is automatically setted by the :class:`TreeView`. You can
        read it but not write on it.

    :data:`is_open` is a :class:`~kivy.properties.BooleanProperty`, default to
    False.
    '''

    is_selected = BooleanProperty(False)
    '''Boolean to indicate if this node is selected or not. This is used for
    graphical representation.

    .. warning::

        This property is automatically setted by the :class:`TreeView`. You can
        read it but not write on it.

    :data:`is_selected` is a :class:`~kivy.properties.BooleanProperty`, default
    to False.
    '''

    no_selection = BooleanProperty(False)
    '''Boolean to indicate if we allow selection of the node or not.

    :data:`no_selection` is a :class:`~kivy.properties.BooleanProperty`,
    default to False
    '''

    nodes = ListProperty([])
    '''List of nodes. The nodes list is differents than children. Nodes
    represent a node on the tree, while children represent the widget associated
    to the current node.

    .. warning::

        This property is automatically setted by the :class:`TreeView`. You can
        read it, but not write on it.

    :data:`nodes` is a :class:`~kivy.properties.ListProperty`, default to [].
    '''

    level = NumericProperty(-1)
    '''Level of the node.

    :data:`level` is a :class:`~kivy.properties.NumericProperty`, default to -1.
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
            Fired when a node is being expended
        `on_node_collapse`: (node, )
            Fired when a node is being collapsed
    '''

    def __init__(self, **kwargs):
        self.register_event_type('on_node_expand')
        self.register_event_type('on_node_collapse')
        super(TreeView, self).__init__(**kwargs)
        tvlabel = TreeViewLabel(text='Root', is_open=True, level=0)
        for key, value in self.root_options.iteritems():
            setattr(tvlabel, key, value)
        self._root = self.add_node(tvlabel, None)
        self.bind(
            pos=self._trigger_layout,
            size=self._trigger_layout,
            indent_level=self._trigger_layout,
            indent_start=self._trigger_layout)
        self._trigger_layout()

    def add_node(self, node, parent=None):
        # check if the widget is "ok" for a node
        if not isinstance(node, TreeViewNode):
            raise TreeViewException(
                'The node must be a subclass of TreeViewNode')
        # create node
        if parent is None and self._root:
            parent = self._root
        if parent:
            parent.nodes.append(node)
            node.level = parent.level + 1
        node.bind(size=self._trigger_layout)
        self._trigger_layout()
        return node

    def on_node_expand(self, node):
        pass

    def on_node_collapse(self, node):
        pass

    def select_node(self, node):
        '''Select a node in the tree
        '''
        if node.no_selection:
            return
        if self._selected_node:
            self._selected_node.is_selected = False
        node.is_selected = True
        self._selected_node = node

    def toggle_node(self, node):
        '''Toggle the state of the node (open/collapse)
        '''
        node.is_open = not node.is_open
        if node.is_open:
            self.dispatch('on_node_expand', node)
        else:
            self.dispatch('on_node_collapse', node)
        self._trigger_layout()

    def get_node_at_pos(self, pos):
        '''Get a node a at the position (x, y).
        '''
        x, y = pos
        for node in self.iterate_open_nodes(self.root):
            if self.x <= x <= self.right and \
               node.y <= y <= node.top:
                return node

    def iterate_open_nodes(self, node=None):
        '''Generator to iterate over expanded nodes.
        Example for get all the node opened::

            treeview = TreeView()
            # ... add nodes ...
            for node in treeview.iterate_open_nodes():
                print node
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
        '''Generate to iterate over all nodes, expanded or not.
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
    def on_root_options(self, instance, value):
        if not self.root:
            return
        for key, value in value.iteritems():
            setattr(self.root, key, value)

    def _trigger_layout(self, *largs):
        Clock.unschedule(self._do_layout)
        Clock.schedule_once(self._do_layout)

    def _do_layout(self, *largs):
        self.clear_widgets()
        # display only the one who are is_open
        self._do_open_node(self.root)
        # now do layout
        self._do_layout_node(self.root, 0, self.top)
        # now iterate for calculating minimum size
        min_width = min_height = 0
        for node in self.iterate_open_nodes(self.root):
            min_width = max(min_width, node.width + self.indent_level +
                            node.level * self.indent_level)
            min_height += node.height
        self._minimum_size = (min_width, min_height)

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

    _minimum_size = ListProperty([0, 0])

    _selected_node = ObjectProperty(None)

    #
    # Properties
    #
    indent_level = NumericProperty(16)
    '''Width used for identation of each level, except the first level.

    Computation of spacing for eaching level of tree is::

        :data:`indent_start` + level * :data:`indent_level`

    :data:`indent_level` is a :class:`~kivy.properties.NumericProperty`,
    default to 16.
    '''

    indent_start = NumericProperty(24)
    '''Indentation width of the level 0 / root node. This is mostly the initial
    size to put an tree icon (collapsed / expanded). See :data:`indent_level`
    for more information about the computation of level indentation.

    :data:`indent_start` is a :class:`~kivy.properties.NumericProperty`,
    default to 24.
    '''

    hide_root = BooleanProperty(False)
    '''Use this property to show/hide the initial root node. If True, the root
    node will be always considerate as an open node

    :data:`hide_root` is a :class:`~kivy.properties.BooleanProperty`, default to
    False.
    '''

    def get_selected_node(self):
        return self._selected_node

    selected_node = AliasProperty(get_selected_node, None,
                                  bind=('_selected_node', ))
    '''Node selected by :func:`TreeView.select_node`, or by touch.

    :data:`selected_node` is a :class:`~kivy.properties.AliasProperty`, default
    to None, and is read-only.
    '''

    def get_root(self):
        return self._root

    root = AliasProperty(get_root, None, bind=('_root', ))
    '''Root node.

    By default, the root node widget is a :class:`TreeViewLabel`, with the label
    'Root'. If you want to change the default options passed to the widget
    creation, you can use :data:`root_options` property::

        treeview = TreeView(root_options={
            'text': 'Root directory',
            'font_size': 15})

    :data:`root_options` will change the properties of the
    :class:`TreeViewLabel` instance. However, you cannot change the class used
    for root node yet.

    :data:`root` is a :class:`~kivy.properties.AliasProperty`, default to
    None, and is read-only. However, the content of the widget can be changed.
    '''

    root_options = ObjectProperty({})
    '''Default root options to pass for root widget. See :data:`root` property
    for more information about the usage of root_options.

    :data:`root_options` is a :class:`~kivy.properties.ObjectProperty`, default
    to {}.
    '''

if __name__ == '__main__':
    from kivy.app import App

    class TestApp(App):

        def build(self):
            tv = TreeView(hide_root=True)
            add = tv.add_node
            root = add(TreeViewLabel(text='Level 1, entry 1', is_open=True))
            for x in xrange(5):
                add(TreeViewLabel(text='Element %d' % x), root)
            root2 = add(TreeViewLabel(text='Level 1, entry 2', is_open=False))
            for x in xrange(24):
                add(TreeViewLabel(text='Element %d' % x), root2)
            for x in xrange(5):
                add(TreeViewLabel(text='Element %d' % x), root)
            root2 = add(TreeViewLabel(text='Element childs 2', is_open=False),
                        root)
            for x in xrange(24):
                add(TreeViewLabel(text='Element %d' % x), root2)
            return tv
    TestApp().run()
