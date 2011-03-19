'''
Tree View
=========

.. versionadded:: 1.0.4

.. warning::

    This widget is still experimental, and his API is subject to change in a
    future version.

:class:`TreeView` is a widget to represent tree list. It's currently very basic,
but support the minimal features set to be usable.

'''

from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.properties import BooleanProperty, ListProperty, ObjectProperty, \
        StringProperty, AliasProperty


class TreeViewLabel(Label):
    '''TreeViewLabel class, used for TreeView widget. See module documentation
    for more information
    '''

    is_leaf = BooleanProperty(False)
    '''Boolean to indicate if this node is a leaf or not, used to adjust
    graphical representation.

    .. warning::

        This property is automatically setted by the :class:`TreeView`. You can
        read it but not write on it.

    :data:`is_leaf` is a :class:`~kivy.properties.BooleanProperty`, default to
    False.
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


class TreeViewException(Exception):
    '''Exception for errors in the :class:`TreeView`
    '''
    pass


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
        self._root = self.add_node(
            TreeViewLabel(text='Root', is_open=True), None)

    def add_node(self, widget, parent=None):
        # check if the widget is "ok" for a node
        if not hasattr(widget, 'is_leaf'):
            raise TreeViewException('Missing is_leaf property')
        if not hasattr(widget, 'is_selected'):
            raise TreeViewException('Missing is_selected property')
        if not hasattr(widget, 'is_open'):
            raise TreeViewException('Missing is_open property')
        # create node
        node = {'nodes': [], 'widget': widget}
        if parent is None and self._root:
            parent = self._root
        if parent:
            parent['nodes'].append(node)
        self._trigger_layout()
        return node

    def on_node_expand(self, node):
        pass

    def on_node_collapse(self, node):
        pass

    def select_node(self, node):
        '''Select a node in the tree
        '''
        if self._selected_node:
            self._selected_node['widget'].is_selected = False
        node['widget'].is_selected = True
        self._selected_node = node

    def toggle_node(self, node):
        '''Toggle the state of the node (open/collapse)
        '''
        widget = node['widget']
        widget.is_open = not widget.is_open
        if widget.is_open:
            self.dispatch('on_node_expand', node)
        else:
            self.dispatch('on_node_collapse', node)
        self._trigger_layout()

    def get_node_at_pos(self, pos):
        '''Get a node a at the position (x, y)
        '''
        x, y = pos
        for node in self.iterate_node(self.root):
            widget = node['widget']
            if self.x <= x <= self.right and \
               widget.y <= y <= widget.top:
                return node

    def iterate_node(self, node):
        '''Generator to iterate over expanded nodes
        '''
        yield node
        if not node['widget'].is_open:
            return
        for cnode in node['nodes']:
            for ynode in self.iterate_node(cnode):
                yield ynode

    #
    # Private
    #
    def on_root_label(self, instance, value):
        if not self.root:
            return
        self.root['widget'].text = value

    def on_size(self, instance, value):
        self._trigger_layout()

    def on_root_options(self, instance, value):
        for key, value in value.iteritems():
            setattr(self.root['widget'], key, value)

    def _trigger_layout(self):
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
        for node in self.iterate_node(self.root):
            widget = node['widget']
            min_width = max(min_width, widget.width + 24 + node['level'] * 24)
            min_height += widget.height
        self._minimum_size = (min_width, min_height)

    def _do_open_node(self, node):
        widget = node['widget']
        self.add_widget(widget)
        height = widget.height
        widget.is_leaf = not bool(len(node['nodes']))
        if not widget.is_open:
            return height
        for cnode in node['nodes']:
            height += self._do_open_node(cnode)
        return height

    def _do_layout_node(self, node, level, y):
        widget = node['widget']
        node['level'] = level
        widget.x = self.x + 24 + level * 24
        widget.top = y
        y -= widget.height
        if not widget.is_open:
            return y
        for cnode in node['nodes']:
            y = self._do_layout_node(cnode, level + 1, y)
        return y

    def on_touch_down(self, touch):
        node = self.get_node_at_pos(touch.pos)
        if not node:
            return
        # toggle node or selection ?
        widget = node['widget']
        if widget.x - 24 <= touch.x < widget.x:
            self.toggle_node(node)
        elif widget.x <= touch.x:
            self.select_node(node)
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
            tv = TreeView()
            add = tv.add_node
            root = add(TreeViewLabel(text='Element 0'))
            for x in xrange(5):
                add(TreeViewLabel(text='Element %d' % x), root)
            root2 = add(TreeViewLabel(text='Element childs 1', is_open=False),
                        root)
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
