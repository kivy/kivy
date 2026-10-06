'''
Runtime tests for kv control statements (if/elif/else, for, slot, factory).

These cover the builder stage; pure parsing is tested in
``test_lang_parser_control.py``.
'''

import unittest

from kivy.lang import Builder
from kivy.lang.builder import BuilderException
from kivy.lang.parser import _handlers


def texts(widget):
    '''Texts of the children in document order.'''
    return [c.text for c in reversed(widget.children)]


def by_text(widget):
    return {c.text: c for c in reversed(widget.children)}


class IfRuntimeTestCase(unittest.TestCase):

    def test_initial_branch_and_switching(self):
        root = Builder.load_string('''
BoxLayout:
    expanded: True
    Label:
        text: 'first'
    if self.expanded:
        Label:
            text: 'open'
        Label:
            text: 'open2'
    else:
        Label:
            text: 'closed'
    Label:
        text: 'last'
''')
        self.assertEqual(texts(root), ['first', 'open', 'open2', 'last'])
        root.expanded = False
        self.assertEqual(texts(root), ['first', 'closed', 'last'])
        root.expanded = True
        self.assertEqual(texts(root), ['first', 'open', 'open2', 'last'])

    def test_if_without_else_builds_nothing_when_false(self):
        root = Builder.load_string('''
BoxLayout:
    show: False
    if self.show:
        Label:
            text: 'maybe'
''')
        self.assertEqual(texts(root), [])
        root.show = True
        self.assertEqual(texts(root), ['maybe'])
        root.show = False
        self.assertEqual(texts(root), [])

    def test_elif_chain(self):
        root = Builder.load_string('''
BoxLayout:
    state: 'a'
    if self.state == 'a':
        Label:
            text: 'A'
    elif self.state == 'b':
        Label:
            text: 'B'
    else:
        Label:
            text: 'other'
''')
        self.assertEqual(texts(root), ['A'])
        root.state = 'b'
        self.assertEqual(texts(root), ['B'])
        root.state = 'zzz'
        self.assertEqual(texts(root), ['other'])

    def test_two_sibling_chains_keep_positions(self):
        root = Builder.load_string('''
BoxLayout:
    a: False
    b: True
    if self.a:
        Label:
            text: 'A'
    Label:
        text: 'mid'
    if self.b:
        Label:
            text: 'B'
''')
        self.assertEqual(texts(root), ['mid', 'B'])
        root.a = True
        self.assertEqual(texts(root), ['A', 'mid', 'B'])
        root.b = False
        self.assertEqual(texts(root), ['A', 'mid'])

    def test_nested_if(self):
        root = Builder.load_string('''
BoxLayout:
    outer: True
    inner: False
    if self.outer:
        Label:
            text: 'pre'
        if self.inner:
            Label:
                text: 'deep'
''')
        self.assertEqual(texts(root), ['pre'])
        root.inner = True
        self.assertEqual(texts(root), ['pre', 'deep'])
        root.outer = False
        self.assertEqual(texts(root), [])
        root.outer = True
        self.assertEqual(texts(root), ['pre', 'deep'])

    def test_branch_content_bindings_work_and_die_with_branch(self):
        root = Builder.load_string('''
BoxLayout:
    show: True
    n: 0
    if self.show:
        Label:
            text: str(root.n)
''')
        label = root.children[0]
        root.n = 5
        self.assertEqual(label.text, '5')
        root.show = False
        root.n = 9
        self.assertEqual(label.text, '5')  # unbound on destroy
        root.show = True
        self.assertEqual(root.children[0].text, '9')

    def test_no_handler_leak_on_rebuild(self):
        root = Builder.load_string('''
BoxLayout:
    show: True
    if self.show:
        Label:
            text: 'x'
''')
        baseline = set(_handlers)
        for _ in range(30):
            root.show = False
            root.show = True
        # anything new in the registry must belong to the live subtree
        live = {w.uid for w in root.walk(restrict=True)}
        leaked = set(_handlers) - baseline - live
        self.assertEqual(leaked, set())

    def test_condition_can_use_sibling_ids(self):
        root = Builder.load_string('''
BoxLayout:
    Label:
        id: lbl
        text: 'off'
    if lbl.text == 'on':
        Label:
            text: 'visible'
''')
        self.assertEqual(texts(root), ['off'])
        lbl = root.ids.lbl
        lbl.text = 'on'
        self.assertEqual(texts(root), ['on', 'visible'])

    def test_if_in_class_rule(self):
        Builder.load_string('''
<TogglePanel@BoxLayout>:
    open: True
    if self.open:
        Label:
            text: 'content'
''')
        from kivy.factory import Factory
        panel = Factory.TogglePanel()
        self.assertEqual(texts(panel), ['content'])
        panel.open = False
        self.assertEqual(texts(panel), [])

    def test_no_kv_post_for_widgets_destroyed_during_apply(self):
        # a widget built by a control statement and torn down again before
        # the apply finishes (here: its own on_parent flips the condition)
        # must never receive on_kv_post
        seen = []
        from kivy.uix.label import Label

        class GhostLabel(Label):
            def on_kv_post(self, base_widget):
                seen.append(self.text)

        root = Builder.load_string('''
BoxLayout:
    show: True
    if self.show:
        GhostLabel:
            text: 'ghost'
            on_parent: root.show = False
''')
        self.assertEqual(texts(root), [])
        self.assertEqual(seen, [])

    def test_on_kv_post_dispatched_for_dynamic_builds(self):
        seen = []
        from kivy.uix.label import Label

        class PostLabel(Label):
            def on_kv_post(self, base_widget):
                seen.append(self.text)

        root = Builder.load_string('''
BoxLayout:
    show: False
    if self.show:
        PostLabel:
            text: 'dyn'
''')
        self.assertEqual(seen, [])
        root.show = True
        self.assertEqual(seen, ['dyn'])


class IfBodyRuntimeTestCase(unittest.TestCase):
    '''An ``if`` block is a full rule body applied to the host widget:
    besides children it may carry properties, canvas and handlers.'''

    def test_conditional_property_over_reactive_base(self):
        # a branch adds an ordinary binding while active; it coexists with
        # the unconditional one (which stays live) and resolves by reactivity
        # order. Leaving the branch does not revert the value: the base
        # re-wins only on its next dependency change (one-way binding).
        root = Builder.load_string('''
BoxLayout:
    cond: False
    base_src: 10
    a: self.base_src * 2
    if self.cond:
        a: 999
''')
        self.assertEqual(root.a, 20)
        root.cond = True
        self.assertEqual(root.a, 999)
        # branch leaves -> no immediate revert, the last value is kept...
        root.cond = False
        self.assertEqual(root.a, 999)
        # ...and the base binding re-wins when its dependency next changes
        root.base_src = 100
        self.assertEqual(root.a, 200)

    def test_branch_only_property_keeps_last_value(self):
        # no unconditional rule for the property -> one-way: leaving the
        # branch does not revert, the latest set value is kept
        from kivy.uix.boxlayout import BoxLayout
        from kivy.properties import NumericProperty, BooleanProperty

        class KeepLast(BoxLayout):
            b = NumericProperty(0)
            cond = BooleanProperty(False)

        Builder.load_string('''
<KeepLast>:
    if self.cond:
        b: 777
''', filename='test_keeplast.kv')
        try:
            w = KeepLast()
            self.assertEqual(w.b, 0)
            w.cond = True
            self.assertEqual(w.b, 777)
            w.cond = False
            self.assertEqual(w.b, 777)
        finally:
            Builder.unload_file('test_keeplast.kv')

    def test_else_branch_property(self):
        root = Builder.load_string('''
BoxLayout:
    cond: False
    label: ''
    if self.cond:
        label: 'on'
    else:
        label: 'off'
''')
        self.assertEqual(root.label, 'off')
        root.cond = True
        self.assertEqual(root.label, 'on')
        root.cond = False
        self.assertEqual(root.label, 'off')

    def test_two_parallel_blocks_resolve_by_reactivity(self):
        # two independent if-blocks driving one property is the power-user
        # parallel-binding case: the most recently applied write wins, and a
        # block leaving does not restore another block's value (one-way).
        root = Builder.load_string('''
BoxLayout:
    a: False
    b: False
    v: 1
    if self.a:
        v: 2
    if self.b:
        v: 3
''')
        self.assertEqual(root.v, 1)
        root.a = True
        self.assertEqual(root.v, 2)
        root.b = True              # most recent write wins
        self.assertEqual(root.v, 3)
        root.b = False             # leaving does not revert to the other
        self.assertEqual(root.v, 3)

    def test_nested_if_property(self):
        # nested branches apply their value on activation; leaving a branch
        # is one-way (no revert), as for any parallel binding
        root = Builder.load_string('''
BoxLayout:
    outer: False
    inner: False
    v: 0
    if self.outer:
        v: 1
        if self.inner:
            v: 2
''')
        self.assertEqual(root.v, 0)
        root.outer = True
        self.assertEqual(root.v, 1)
        root.inner = True
        self.assertEqual(root.v, 2)
        root.inner = False          # nested block torn down, value kept
        self.assertEqual(root.v, 2)
        root.outer = False          # outer block torn down, value kept
        self.assertEqual(root.v, 2)

    def test_property_with_children_in_same_branch(self):
        root = Builder.load_string('''
BoxLayout:
    cond: False
    title: 'none'
    if self.cond:
        title: 'shown'
        Label:
            text: 'child'
''')
        self.assertEqual(root.title, 'none')
        self.assertEqual(texts(root), [])
        root.cond = True
        self.assertEqual(root.title, 'shown')
        self.assertEqual(texts(root), ['child'])
        root.cond = False
        self.assertEqual(root.title, 'shown')   # one-way: value kept
        self.assertEqual(texts(root), [])        # children torn down

    def test_conditional_handler(self):
        root = Builder.load_string('''
BoxLayout:
    cond: False
    fired: 0
    if self.cond:
        on_touch_down: self.fired += 1
''')
        root.dispatch('on_touch_down', None)
        self.assertEqual(root.fired, 0)
        root.cond = True
        root.dispatch('on_touch_down', None)
        self.assertEqual(root.fired, 1)
        root.cond = False
        root.dispatch('on_touch_down', None)
        self.assertEqual(root.fired, 1)

    def test_conditional_canvas_mount_and_binding(self):
        from kivy.graphics import Color, InstructionGroup

        root = Builder.load_string('''
BoxLayout:
    cond: False
    cval: 0.5
    if self.cond:
        canvas:
            Color:
                rgba: 1, 0, 0, self.cval
            Rectangle:
                size: self.size
''')
        groups = [c for c in root.canvas.children
                  if isinstance(c, InstructionGroup)]
        self.assertEqual(groups, [])
        root.cond = True
        groups = [c for c in root.canvas.children
                  if isinstance(c, InstructionGroup)]
        self.assertEqual(len(groups), 1)

        def find_color(group):
            for instr in group.children:
                if isinstance(instr, Color):
                    return instr
            return None
        color = find_color(groups[0])
        self.assertIsNotNone(color)
        root.cval = 0.9
        Builder.sync()              # canvas bindings are delayed
        self.assertAlmostEqual(color.rgba[3], 0.9)
        root.cond = False
        groups = [c for c in root.canvas.children
                  if isinstance(c, InstructionGroup)]
        self.assertEqual(groups, [])

    def test_branch_creates_missing_property(self):
        # a property only ever set inside a branch is created on demand
        root = Builder.load_string('''
BoxLayout:
    cond: True
    if self.cond:
        brand_new: 42
''')
        self.assertEqual(root.brand_new, 42)

    def test_no_handler_leak_on_property_rebuild(self):
        root = Builder.load_string('''
BoxLayout:
    cond: True
    base_src: 1
    a: self.base_src * 2
    if self.cond:
        a: self.base_src + 5
''')
        for _ in range(30):
            root.cond = False
            root.cond = True
        live = len(_handlers.get(root.uid, {}).get('a', ()))
        # base and active branch coexist (parallel bindings) and do not leak
        self.assertEqual(live, 2)
        root.cond = False
        # the branch binding is removed; the base remains
        self.assertEqual(len(_handlers.get(root.uid, {}).get('a', ())), 1)


class ForRuntimeTestCase(unittest.TestCase):

    def test_initial_build_in_order(self):
        root = Builder.load_string('''
BoxLayout:
    items: ['a', 'b', 'c']
    Label:
        text: 'head'
    for item in self.items:
        Label:
            text: item
    Label:
        text: 'tail'
''')
        self.assertEqual(texts(root), ['head', 'a', 'b', 'c', 'tail'])

    def test_positional_keys_reuse_unchanged_prefix(self):
        root = Builder.load_string('''
BoxLayout:
    items: ['a', 'b']
    for item in self.items:
        Label:
            text: item
''')
        first = by_text(root)
        root.items = ['a', 'b', 'c']
        second = by_text(root)
        self.assertEqual(texts(root), ['a', 'b', 'c'])
        self.assertIs(first['a'], second['a'])
        self.assertIs(first['b'], second['b'])

    def test_keyed_reorder_preserves_identity(self):
        root = Builder.load_string('''
BoxLayout:
    items: ['a', 'b', 'c']
    for item in self.items:
        key: item
        Label:
            text: item
''')
        before = by_text(root)
        root.items = ['c', 'a', 'b']
        after = by_text(root)
        self.assertEqual(texts(root), ['c', 'a', 'b'])
        for k in 'abc':
            self.assertIs(before[k], after[k])

    def test_keyed_remove_and_add(self):
        root = Builder.load_string('''
BoxLayout:
    items: ['a', 'b', 'c']
    for item in self.items:
        key: item
        Label:
            text: item
''')
        before = by_text(root)
        root.items = ['c', 'd']
        after = by_text(root)
        self.assertEqual(texts(root), ['c', 'd'])
        self.assertIs(before['c'], after['c'])

    def test_empty_iterable_and_refill(self):
        root = Builder.load_string('''
BoxLayout:
    items: []
    for item in self.items:
        Label:
            text: item
    Label:
        text: 'end'
''')
        self.assertEqual(texts(root), ['end'])
        root.items = ['x']
        self.assertEqual(texts(root), ['x', 'end'])
        root.items = []
        self.assertEqual(texts(root), ['end'])

    def test_tuple_target_and_filter(self):
        root = Builder.load_string('''
BoxLayout:
    items: ['a', 'b', 'c']
    for item, i in zip(self.items, range(99)) if item != 'b':
        Label:
            text: '%s%d' % (item, i)
''')
        self.assertEqual(texts(root), ['a0', 'c2'])

    def test_loop_variable_in_handler(self):
        root = Builder.load_string('''
BoxLayout:
    items: ['a', 'b']
    picked: ''
    for item in self.items:
        Button:
            text: item
            on_press: root.picked = item
''')
        button_a = by_text(root)['a']
        button_a.dispatch('on_press', None)
        self.assertEqual(root.picked, 'a')

    def test_loop_target_shadows_metric_helper(self):
        # 'dp' is a metric helper in the global kv context; as a loop
        # target it must resolve to the loop value in child property
        # expressions, not the helper function
        root = Builder.load_string('''
BoxLayout:
    items: ['x', 'y']
    for dp in self.items:
        Label:
            text: dp
''')
        self.assertEqual(texts(root), ['x', 'y'])

    def test_loop_target_shadows_global_in_handler(self):
        # same precedence must hold on the handler eval path
        root = Builder.load_string('''
BoxLayout:
    items: ['x', 'y']
    picked: ''
    for dp in self.items:
        Button:
            text: dp
            on_press: root.picked = dp
''')
        by_text(root)['y'].dispatch('on_press', None)
        self.assertEqual(root.picked, 'y')

    def test_loop_target_self_reshadowed_by_child_widget(self):
        # a loop target named 'self' is shadowed again by each child
        # widget's own 'self', so 'self.x' refers to the widget
        root = Builder.load_string('''
BoxLayout:
    names: ['a', 'b']
    for self in self.names:
        Label:
            text: self.__class__.__name__
''')
        self.assertEqual(texts(root), ['Label', 'Label'])

    def test_nested_for_loop_scopes_compose(self):
        # inner loop sees its own and the enclosing loop's variables
        root = Builder.load_string('''
BoxLayout:
    rows: [['a', 'b'], ['c']]
    for row in self.rows:
        for cell in row:
            Label:
                text: '%s:%s' % (len(row), cell)
''')
        self.assertEqual(texts(root), ['2:a', '2:b', '1:c'])

    def test_multiple_children_per_iteration(self):
        root = Builder.load_string('''
BoxLayout:
    items: ['a', 'b']
    for item in self.items:
        Label:
            text: item + '1'
        Label:
            text: item + '2'
''')
        self.assertEqual(texts(root), ['a1', 'a2', 'b1', 'b2'])

    def test_for_inside_if(self):
        root = Builder.load_string('''
BoxLayout:
    show: True
    items: ['x', 'y']
    if self.show:
        for item in self.items:
            Label:
                text: item
    Label:
        text: 'end'
''')
        self.assertEqual(texts(root), ['x', 'y', 'end'])
        root.items = ['x', 'y', 'z']
        self.assertEqual(texts(root), ['x', 'y', 'z', 'end'])
        root.show = False
        self.assertEqual(texts(root), ['end'])
        root.show = True
        self.assertEqual(texts(root), ['x', 'y', 'z', 'end'])

    def test_if_inside_for_reacts_per_item(self):
        from kivy.uix.widget import Widget
        from kivy.properties import StringProperty, BooleanProperty

        class FItem(Widget):
            name = StringProperty('')
            special = BooleanProperty(False)

        root = Builder.load_string('''
BoxLayout:
    models: []
    for item in self.models:
        Label:
            text: item.name
        if item.special:
            Label:
                text: item.name + '!'
''')
        a = FItem(name='a')
        b = FItem(name='b', special=True)
        root.models = [a, b]
        self.assertEqual(texts(root), ['a', 'b', 'b!'])
        a.special = True
        self.assertEqual(texts(root), ['a', 'a!', 'b', 'b!'])
        b.special = False
        self.assertEqual(texts(root), ['a', 'a!', 'b'])

    def test_nested_for(self):
        root = Builder.load_string('''
BoxLayout:
    rows: [['a', 'b'], ['c']]
    for row in self.rows:
        for cell in row:
            Label:
                text: cell
''')
        self.assertEqual(texts(root), ['a', 'b', 'c'])
        root.rows = [['x'], ['y', 'z']]
        self.assertEqual(texts(root), ['x', 'y', 'z'])

    def test_duplicate_key_raises(self):
        root = Builder.load_string('''
BoxLayout:
    items: ['a', 'b']
    for item in self.items:
        key: item
        Label:
            text: item
''')
        with self.assertRaises(BuilderException) as cm:
            root.items = ['a', 'a']
        self.assertIn('duplicate', str(cm.exception))

    def test_unhashable_key_raises(self):
        root = Builder.load_string('''
BoxLayout:
    items: []
    for item in self.items:
        key: item
        Label:
            text: str(item)
''')
        with self.assertRaises(BuilderException) as cm:
            root.items = [['unhashable']]
        self.assertIn('hashable', str(cm.exception))

    def test_cross_widget_reentrant_rebuild(self):
        # a handler firing during one widget's build mutates state that
        # another widget's node (sharing the same class rule) watches;
        # the second rebuild must be deferred, not re-enter _apply_rule
        root = Builder.load_string('''
<ReentryRow@BoxLayout>:
    items: []
    poke: False
    for item in self.items:
        Label:
            text: str(item)
            on_parent:
                (setattr(root.parent.children[0], 'items', ['p'])
                if root.poke and root.parent
                and not root.parent.children[0].items else None)
BoxLayout:
    ReentryRow:
    ReentryRow:
''')
        row1, row2 = root.children[1], root.children[0]
        row1.poke = True
        row1.items = ['a']
        self.assertEqual(texts(row1), ['a'])
        self.assertEqual(texts(row2), ['p'])

    def test_pure_append_does_not_detach_existing(self):
        root = Builder.load_string('''
BoxLayout:
    items: ['a', 'b']
    for item in self.items:
        key: item
        Label:
            text: item
''')
        removals = []
        orig = root.remove_widget

        def tracking_remove(w):
            removals.append(w)
            orig(w)

        root.remove_widget = tracking_remove
        root.items = ['a', 'b', 'c']
        self.assertEqual(removals, [])
        self.assertEqual(texts(root), ['a', 'b', 'c'])

    def test_no_handler_leak_on_updates(self):
        root = Builder.load_string('''
BoxLayout:
    items: []
    for item in self.items:
        Label:
            text: item
''')
        root.items = ['a', 'b', 'c']
        baseline = set(_handlers)
        for i in range(30):
            root.items = ['a', str(i)]
            root.items = ['a', 'b', 'c']
        # anything new in the registry must belong to the live subtree
        live = {w.uid for w in root.walk(restrict=True)}
        leaked = set(_handlers) - baseline - live
        self.assertEqual(leaked, set())

    def test_for_body_local_is_reactive_intermediate(self):
        # a for body property is an iteration-local reactive value, not a
        # host property: it is computed per iteration and read by the body
        from kivy.factory import Factory
        from kivy.uix.label import Label
        from kivy.properties import NumericProperty

        class QItem(Label):
            qty = NumericProperty(0)

        Builder.load_string('''
<LocReact@BoxLayout>:
    items: []
    for it in self.items:
        doubled: it.qty * 2
        Label:
            text: str(doubled)
''', filename='locreact.kv')
        try:
            w = Factory.LocReact()
            a, b = QItem(qty=1), QItem(qty=5)
            w.items = [a, b]
            self.assertEqual(texts(w), ['2', '10'])
            # changing a dependency recomputes the local, which updates the
            # widget that reads it
            a.qty = 9
            self.assertEqual(texts(w), ['18', '10'])
            # the local is NOT a host property
            self.assertFalse(hasattr(w, 'doubled'))
        finally:
            Builder.unload_file('locreact.kv')

    def test_for_body_local_value_is_shared_within_iteration(self):
        # a `[]` local is one object per iteration, shared by every
        # reference in that iteration; different iterations get their own
        from kivy.factory import Factory
        Builder.load_string('''
<LocShared@BoxLayout>:
    items: [1, 2]
    for it in self.items:
        bucket: []
        Label:
            tag: bucket
        Label:
            tag: bucket
''', filename='locshared.kv')
        try:
            w = Factory.LocShared()
            a, b, c, d = list(reversed(w.children))
            self.assertIs(a.tag, b.tag)        # shared within iteration 0
            self.assertIs(c.tag, d.tag)        # shared within iteration 1
            self.assertIsNot(a.tag, c.tag)     # distinct across iterations
            a.tag.append(99)                   # mutation is visible to both
            self.assertEqual(b.tag, [99])
            self.assertEqual(c.tag, [])
        finally:
            Builder.unload_file('locshared.kv')

    def test_if_inside_for_reads_loop_local(self):
        # an if branch inside a for sees the loop's locals
        from kivy.factory import Factory
        Builder.load_string('''
<IfLocal@BoxLayout>:
    items: []
    for n in self.items:
        big: n > 2
        if big:
            Label:
                text: 'big:' + str(n)
        else:
            Label:
                text: 'small:' + str(n)
''', filename='iflocal.kv')
        try:
            w = Factory.IfLocal()
            w.items = [1, 5]
            self.assertEqual(texts(w), ['small:1', 'big:5'])
        finally:
            Builder.unload_file('iflocal.kv')

    def test_local_references_earlier_local(self):
        from kivy.factory import Factory
        Builder.load_string('''
<LocChain@BoxLayout>:
    items: [10, 20]
    for x in self.items:
        a: x + 1
        b: a * 100
        Label:
            text: str(b)
''', filename='locchain.kv')
        try:
            w = Factory.LocChain()
            self.assertEqual(texts(w), ['1100', '2100'])
        finally:
            Builder.unload_file('locchain.kv')

    def test_same_key_new_value_keeps_widgets_and_redispatches(self):
        # reconciliation rule: same key => same widgets; the new loop values
        # are re-dispatched through the existing bindings, so live widget
        # state survives an item being replaced under a stable key
        root = Builder.load_string('''
BoxLayout:
    tasks: [{'uid': 1, 'txt': 'a'}, {'uid': 2, 'txt': 'b'}]
    for task in self.tasks:
        key: task['uid']
        Label:
            text: task['txt']
''')
        first = list(reversed(root.children))
        self.assertEqual(texts(root), ['a', 'b'])
        root.tasks = [{'uid': 1, 'txt': 'a2'}, {'uid': 2, 'txt': 'b'}]
        self.assertEqual(texts(root), ['a2', 'b'])
        self.assertEqual(list(reversed(root.children)), first)

    def test_conditional_local_in_for(self):
        # nearest-scope rule: a property in an ``if`` inside a ``for`` is an
        # iteration-local bound while the branch is active; it starts None,
        # keeps its last value when the branch leaves (one-way), and never
        # touches the host
        from kivy.uix.widget import Widget
        from kivy.properties import NumericProperty

        class CItem(Widget):
            n = NumericProperty(0)

        root = Builder.load_string('''
BoxLayout:
    models: []
    for it in self.models:
        if it.n > 2:
            biglabel: 'big ' + str(it.n)
        Label:
            text: biglabel or 'none'
''')
        a = CItem(n=1)
        root.models = [a]
        self.assertEqual(texts(root), ['none'])
        a.n = 5
        self.assertEqual(texts(root), ['big 5'])
        a.n = 1
        self.assertEqual(texts(root), ['big 5'])  # one-way: last value kept
        self.assertFalse(hasattr(root, 'biglabel'))

    def test_non_iterable_raises_with_kv_context(self):
        # Python semantics: iterating a non-iterable raises; the error must
        # carry the kv rule location, not surface as a bare TypeError
        from kivy.uix.boxlayout import BoxLayout
        from kivy.properties import ObjectProperty

        class AnyItems(BoxLayout):
            items = ObjectProperty((1,))

        Builder.load_string('''
<AnyItems>:
    for x in self.items:
        Label:
            text: str(x)
''', filename='anyitems.kv')
        try:
            w = AnyItems()
            self.assertEqual(texts(w), ['1'])
            with self.assertRaises(BuilderException) as cm:
                w.items = 5
            self.assertIn('not iterable', str(cm.exception))
        finally:
            Builder.unload_file('anyitems.kv')


class FactoryRuntimeTestCase(unittest.TestCase):
    '''``factory expr:`` builds a single child widget whose class comes from
    an expression (a class object or a Factory name), rebuilt reactively when
    the class changes; the block body is applied to the instance.'''

    def test_build_by_name_and_rebuild_on_change(self):
        from kivy.factory import Factory
        Builder.load_string('''
<DynByName@BoxLayout>:
    which: 'Button'
    caption: 'hi'
    factory self.which:
        text: root.caption
''', filename='dyn_name.kv')
        try:
            w = Factory.DynByName()
            self.assertEqual(type(w.children[0]).__name__, 'Button')
            self.assertEqual(w.children[0].text, 'hi')
            # changing the class rebuilds with the new type, body re-applied
            w.which = 'Label'
            self.assertEqual(type(w.children[0]).__name__, 'Label')
            self.assertEqual(w.children[0].text, 'hi')
        finally:
            Builder.unload_file('dyn_name.kv')

    def test_class_object_value(self):
        from kivy.factory import Factory
        from kivy.uix.label import Label
        Builder.load_string('''
<DynByCls@BoxLayout>:
    klass: None
    factory self.klass:
        text: 'z'
''', filename='dyn_cls.kv')
        try:
            w = Factory.DynByCls()
            self.assertEqual(len(w.children), 0)   # None -> nothing
            w.klass = Label
            self.assertEqual(type(w.children[0]).__name__, 'Label')
            self.assertEqual(w.children[0].text, 'z')
        finally:
            Builder.unload_file('dyn_cls.kv')

    def test_body_property_reactive_and_identity_stable(self):
        from kivy.factory import Factory
        Builder.load_string('''
<DynBody@BoxLayout>:
    caption: 'a'
    factory 'Label':
        text: root.caption
''', filename='dyn_body.kv')
        try:
            w = Factory.DynBody()
            child = w.children[0]
            self.assertEqual(child.text, 'a')
            # body prop is reactive; the widget is NOT rebuilt (class same)
            w.caption = 'b'
            self.assertEqual(child.text, 'b')
            self.assertIs(w.children[0], child)
        finally:
            Builder.unload_file('dyn_body.kv')

    def test_factory_inside_for(self):
        from kivy.factory import Factory
        from kivy.uix.label import Label
        from kivy.uix.button import Button
        Builder.load_string('''
<DynForm@BoxLayout>:
    rows: []
    for row in self.rows:
        factory row['cls']:
            text: row['text']
''', filename='dyn_form.kv')
        try:
            w = Factory.DynForm()
            w.rows = [{'cls': Label, 'text': 'a'},
                      {'cls': Button, 'text': 'b'}]
            kids = list(reversed(w.children))
            self.assertEqual(
                [(type(k).__name__, k.text) for k in kids],
                [('Label', 'a'), ('Button', 'b')])
        finally:
            Builder.unload_file('dyn_form.kv')

    def test_factory_with_children(self):
        from kivy.factory import Factory
        Builder.load_string('''
<DynPanel@BoxLayout>:
    factory 'BoxLayout':
        orientation: 'vertical'
        Label:
            text: 'a'
        Label:
            text: 'b'
''', filename='dyn_panel.kv')
        try:
            w = Factory.DynPanel()
            inner = w.children[0]
            self.assertEqual(inner.orientation, 'vertical')
            self.assertEqual(texts(inner), ['a', 'b'])
        finally:
            Builder.unload_file('dyn_panel.kv')

    def test_factory_keeps_document_position(self):
        from kivy.factory import Factory
        Builder.load_string('''
<DynPos@BoxLayout>:
    which: 'Label'
    Label:
        text: 'before'
    factory self.which:
        text: 'mid'
    Label:
        text: 'after'
''', filename='dyn_pos.kv')
        try:
            w = Factory.DynPos()
            self.assertEqual(texts(w), ['before', 'mid', 'after'])
            w.which = 'Button'
            self.assertEqual(texts(w), ['before', 'mid', 'after'])
            self.assertEqual(type(by_text(w)['mid']).__name__, 'Button')
        finally:
            Builder.unload_file('dyn_pos.kv')

    def test_factory_widget_is_collected(self):
        import gc
        import weakref
        from kivy.factory import Factory
        Builder.load_string('''
<DynGc@BoxLayout>:
    which: 'Label'
    factory self.which:
        text: 'x'
''', filename='dyn_gc.kv')
        try:
            w = Factory.DynGc()
            w.which = 'Button'
            ref = weakref.ref(w)
            del w
            gc.collect()
            self.assertIsNone(ref())
        finally:
            Builder.unload_file('dyn_gc.kv')

    def test_factory_unknown_class_raises_with_context(self):
        from kivy.factory import Factory
        Builder.load_string('''
<DynBad@BoxLayout>:
    which: 'Label'
    factory self.which:
        text: 'x'
''', filename='dyn_bad.kv')
        try:
            w = Factory.DynBad()
            with self.assertRaises(BuilderException) as cm:
                w.which = 'NoSuchWidgetClass'
            self.assertIn('NoSuchWidgetClass', str(cm.exception))
        finally:
            Builder.unload_file('dyn_bad.kv')


class ControlIdRuntimeTestCase(unittest.TestCase):
    '''Reactive ids inside control blocks: an id in an ``if`` is reachable
    across the rule and is None while its branch is inactive; an id in a
    ``for`` is iteration-local, reachable only by that iteration's content.'''

    def test_if_id_nullable_reactive_reachable_outside(self):
        from kivy.factory import Factory
        Builder.load_string('''
<IdEditor@BoxLayout>:
    editing: False
    if self.editing:
        TextInput:
            id: field
    Button:
        disabled: field is None
''', filename='ideditor.kv')
        try:
            w = Factory.IdEditor()
            btn = [c for c in w.children
                   if c.__class__.__name__ == 'Button'][0]
            self.assertTrue(btn.disabled)        # inactive branch -> None
            w.editing = True
            self.assertFalse(btn.disabled)       # mounted -> reachable
            w.editing = False
            self.assertTrue(btn.disabled)        # unmounted -> None again
            w.editing = True
            self.assertFalse(btn.disabled)       # and back
        finally:
            Builder.unload_file('ideditor.kv')

    def test_if_id_does_not_leak_into_root_ids(self):
        from kivy.factory import Factory
        Builder.load_string('''
<IdNoLeak@BoxLayout>:
    flag: True
    if self.flag:
        Label:
            id: hidden
''', filename='idnoleak.kv')
        try:
            w = Factory.IdNoLeak()
            # the reactive id must not appear in root.ids (it would blink)
            self.assertNotIn('hidden', w.ids)
        finally:
            Builder.unload_file('idnoleak.kv')

    def test_for_id_reachable_by_sibling_in_iteration(self):
        from kivy.factory import Factory
        Builder.load_string('''
<IdRows@BoxLayout>:
    items: ['a', 'b']
    for it in self.items:
        Label:
            id: lab
            text: it
        Button:
            text: 'echo:' + lab.text
''', filename='idrows.kv')
        try:
            w = Factory.IdRows()
            self.assertEqual(
                texts(w), ['a', 'echo:a', 'b', 'echo:b'])
            # the iteration-local id is not exposed on root.ids
            self.assertNotIn('lab', w.ids)
        finally:
            Builder.unload_file('idrows.kv')

    def test_id_in_if_inside_for_is_iteration_local(self):
        from kivy.factory import Factory
        Builder.load_string('''
<IdIfFor@BoxLayout>:
    items: []
    for n in self.items:
        if n > 0:
            Label:
                id: pos
                text: 'p' + str(n)
        Button:
            text: 'has' if pos is not None else 'none'
''', filename='idiffor.kv')
        try:
            w = Factory.IdIfFor()
            w.items = [5, -1]
            # iter 0: pos mounted -> 'has'; iter 1: branch off -> None
            self.assertEqual(texts(w), ['p5', 'has', 'none'])
        finally:
            Builder.unload_file('idiffor.kv')

    def test_complementary_chains_can_share_an_id(self):
        # `if cond:` / `if not cond:` may define the same id: the id follows
        # whichever branch is mounted, and a chain tearing down after the
        # other one mounted must not clobber the freshly set id (the reset
        # is compare-and-set: only the widget that owns the value clears it)
        from kivy.factory import Factory
        Builder.load_string('''
<TwoChains@BoxLayout>:
    cond: True
    if self.cond:
        Label:
            id: face
            text: 'yes'
    if not self.cond:
        Label:
            id: face
            text: 'no'
    Button:
        text: face.text if face else '?'
''', filename='twochains.kv')
        try:
            w = Factory.TwoChains()
            btn = [c for c in w.children
                   if c.__class__.__name__ == 'Button'][0]
            self.assertEqual(btn.text, 'yes')
            w.cond = False
            self.assertEqual(btn.text, 'no')
            w.cond = True
            self.assertEqual(btn.text, 'yes')
        finally:
            Builder.unload_file('twochains.kv')

    def test_if_id_widget_is_collected(self):
        import gc
        import weakref
        from kivy.factory import Factory
        Builder.load_string('''
<IdGc@BoxLayout>:
    flag: True
    if self.flag:
        Label:
            id: thing
    Button:
        disabled: thing is None
''', filename='idgc.kv')
        try:
            w = Factory.IdGc()
            w.flag = False
            w.flag = True
            ref = weakref.ref(w)
            del w
            gc.collect()
            self.assertIsNone(ref())
        finally:
            Builder.unload_file('idgc.kv')


class SlotRuntimeTestCase(unittest.TestCase):

    def setUp(self):
        Builder.load_string('''
<SlotCard@BoxLayout>:
    Label:
        text: 'top'
    slot header:
        Label:
            text: 'fallback-header'
    slot:
    Label:
        text: 'bottom'
''', filename='test_slot_runtime.kv')

    def tearDown(self):
        Builder.unload_file('test_slot_runtime.kv')

    def test_fallback_when_instantiated_from_python(self):
        from kivy.factory import Factory
        card = Factory.SlotCard()
        self.assertEqual(texts(card), ['top', 'fallback-header', 'bottom'])

    def test_fallback_not_built_when_filled(self):
        # the fallback build is deferred until the apply chain ends, so
        # providing a fill means the fallback widgets are never created
        # and never receive on_kv_post
        from kivy.uix.label import Label
        posts = []

        class PostProbe(Label):
            def on_kv_post(self, base_widget):
                posts.append((self.text, self.parent is not None))

        Builder.load_string('''
<ProbeCard@BoxLayout>:
    slot header:
        PostProbe:
            text: 'fallback'
''', filename='test_slot_probe.kv')
        try:
            root = Builder.load_string('''
BoxLayout:
    ProbeCard:
        slot header:
            PostProbe:
                text: 'fill'
''')
            self.assertEqual(texts(root.children[0]), ['fill'])
            self.assertEqual(posts, [('fill', True)])
        finally:
            Builder.unload_file('test_slot_probe.kv')

    def test_named_fill_and_routed_plain_children(self):
        root = Builder.load_string('''
BoxLayout:
    title: 'Title'
    SlotCard:
        slot header:
            Label:
                text: root.title
        Label:
            text: 'body1'
        Label:
            text: 'body2'
''')
        card = root.children[0]
        self.assertEqual(
            texts(card), ['top', 'Title', 'body1', 'body2', 'bottom'])
        root.title = 'New'
        self.assertEqual(
            texts(card), ['top', 'New', 'body1', 'body2', 'bottom'])

    def test_explicit_default_fill_block(self):
        root = Builder.load_string('''
BoxLayout:
    SlotCard:
        slot:
            Label:
                text: 'explicit-body'
''')
        self.assertEqual(
            texts(root.children[0]),
            ['top', 'fallback-header', 'explicit-body', 'bottom'])

    def test_subclass_fill_overrides_base_and_instance_wins(self):
        Builder.load_string('''
<FancySlotCard@SlotCard>:
    slot header:
        Label:
            text: 'fancy-header'
''', filename='test_slot_runtime_sub.kv')
        try:
            from kivy.factory import Factory
            fancy = Factory.FancySlotCard()
            self.assertEqual(
                texts(fancy), ['top', 'fancy-header', 'bottom'])
            root = Builder.load_string('''
BoxLayout:
    FancySlotCard:
        slot header:
            Label:
                text: 'instance-header'
''')
            self.assertEqual(
                texts(root.children[0]),
                ['top', 'instance-header', 'bottom'])
        finally:
            Builder.unload_file('test_slot_runtime_sub.kv')

    def test_mixing_default_fill_block_and_plain_children_raises(self):
        with self.assertRaises(BuilderException) as cm:
            Builder.load_string('''
BoxLayout:
    SlotCard:
        slot:
            Label:
                text: 'in-block'
        Label:
            text: 'plain'
''')
        self.assertIn('cannot mix', str(cm.exception))

    def test_id_on_routed_children_raises(self):
        # implicitly routed plain children cannot carry an id (the parser
        # cannot know they will be routed); an explicit ``slot:`` fill block
        # is the supported spelling (see test below)
        with self.assertRaises(BuilderException) as cm:
            Builder.load_string('''
BoxLayout:
    SlotCard:
        Label:
            id: nope
            text: 'body'
''')
        self.assertIn('routed into a slot', str(cm.exception))

    def test_id_in_explicit_fill_is_reactive_scoped(self):
        # an id in an explicit slot fill block is a reactive id on the rule
        # providing the fill, reachable by that rule's other expressions
        root = Builder.load_string('''
BoxLayout:
    SlotCard:
        slot header:
            TextInput:
                id: head_input
    Button:
        disabled: head_input is None
''')
        btn = root.children[0]
        self.assertFalse(btn.disabled)
        self.assertNotIn('head_input', root.ids)

    def test_slot_inside_if_branch(self):
        Builder.load_string('''
<IfSlotPanel@BoxLayout>:
    show: True
    if self.show:
        Label:
            text: 'pre'
        slot extra:
            Label:
                text: 'extra-fallback'
''', filename='test_slot_runtime_if.kv')
        try:
            root = Builder.load_string('''
BoxLayout:
    IfSlotPanel:
        slot extra:
            Label:
                text: 'injected'
''')
            panel = root.children[0]
            self.assertEqual(texts(panel), ['pre', 'injected'])
            panel.show = False
            self.assertEqual(texts(panel), [])
            panel.show = True
            self.assertEqual(texts(panel), ['pre', 'injected'])
        finally:
            Builder.unload_file('test_slot_runtime_if.kv')

    def test_slot_forwarding_through_fill(self):
        Builder.load_string('''
<WrapCard@SlotCard>:
    slot header:
        Label:
            text: 'wrap-pre'
        slot title_extra:
''', filename='test_slot_runtime_fwd.kv')
        try:
            from kivy.factory import Factory
            wrap = Factory.WrapCard()
            self.assertEqual(texts(wrap), ['top', 'wrap-pre', 'bottom'])
            root = Builder.load_string('''
BoxLayout:
    WrapCard:
        slot title_extra:
            Label:
                text: 'forwarded'
''')
            self.assertEqual(
                texts(root.children[0]),
                ['top', 'wrap-pre', 'forwarded', 'bottom'])
        finally:
            Builder.unload_file('test_slot_runtime_fwd.kv')

    def test_unknown_slot_name_renders_as_definition_and_warns(self):
        # filling a name the class never defined degrades to declaring a
        # new insertion point; instance children are logically appended
        # after the class rule's children, so it renders at the end. Since
        # an instance-level definition can never be filled, this is almost
        # always a typo, so a warning is logged.
        with self.assertLogs('kivy', level='WARNING') as logs:
            root = Builder.load_string('''
BoxLayout:
    SlotCard:
        slot typo_name:
            Label:
                text: 'oops'
''')
        card = root.children[0]
        self.assertEqual(
            texts(card), ['top', 'fallback-header', 'bottom', 'oops'])
        self.assertTrue(any('typo_name' in m for m in logs.output))

    def test_failed_apply_leaves_no_stale_rulectx(self):
        # a BuilderException escaping mid-apply must not leave entries in
        # Builder.rulectx; a stale entry breaks BuilderBase.create_from
        # (used by the kivy_app test fixture) for every later caller
        with self.assertRaises(BuilderException):
            Builder.load_string('''
BoxLayout:
    SlotCard:
        Label:
            id: nope
''')
        self.assertEqual(dict(Builder.rulectx), {})

    def test_widgets_without_slots_unaffected(self):
        root = Builder.load_string('''
BoxLayout:
    Label:
        text: 'plain'
    BoxLayout:
        Label:
            text: 'nested'
''')
        self.assertEqual(root.children[1].text, 'plain')
        self.assertEqual(texts(root.children[0]), ['nested'])


class SlotScopeRuntimeTestCase(unittest.TestCase):
    '''Slot-scoped locals: property lines in a slot definition are evaluated
    in the defining rule's context and exposed to fallback and fill content
    through the reserved ``slot`` name, so a shell class can hand values to
    whatever content ends up in the hole (cascading slot props).'''

    def setUp(self):
        Builder.load_string('''
<ScopedCard@BoxLayout>:
    count: 3
    slot header:
        summary: 'items: ' + str(root.count)
        Label:
            text: slot.summary
''', filename='scoped_card.kv')

    def tearDown(self):
        Builder.unload_file('scoped_card.kv')

    def test_fallback_reads_slot_local(self):
        from kivy.factory import Factory
        card = Factory.ScopedCard()
        self.assertEqual(texts(card), ['items: 3'])
        card.count = 5
        self.assertEqual(texts(card), ['items: 5'])

    def test_fill_reads_slot_local_from_defining_context(self):
        # the local is computed by the defining rule (root == the ScopedCard)
        # even when the content comes from a fill written elsewhere
        root = Builder.load_string('''
BoxLayout:
    ScopedCard:
        count: 7
        slot header:
            Label:
                text: '<' + slot.summary + '>'
''')
        card = root.children[0]
        self.assertEqual(texts(card), ['<items: 7>'])
        card.count = 9
        self.assertEqual(texts(card), ['<items: 9>'])


class ControlStatementGCTestCase(unittest.TestCase):
    '''A widget that uses control statements must stay garbage-collectable:
    the control nodes hold the children they build (whose ``.parent`` points
    back at the host), so they must live on the host, not in a global
    registry that would pin the whole subtree forever.'''

    def _collected(self, kv):
        import gc
        import weakref
        from kivy.factory import Factory
        Builder.load_string(kv, filename='gc_probe.kv')
        try:
            w = Factory.GcProbe()
            # exercise any reactive content so a branch/iteration is built
            w.flag = not w.flag
            w.flag = not w.flag
            ref = weakref.ref(w)
            del w
            gc.collect()
            # nodes live on the widget (no uid-keyed registries to leak)
            return ref() is None, True
        finally:
            Builder.unload_file('gc_probe.kv')

    def test_if_widget_is_collected(self):
        collected, clean = self._collected('''
<GcProbe@BoxLayout>:
    flag: True
    v: 0
    if self.flag:
        v: 1
        Label:
            text: 'x'
''')
        self.assertTrue(collected)
        self.assertTrue(clean)

    def test_for_widget_is_collected(self):
        collected, _ = self._collected('''
<GcProbe@BoxLayout>:
    flag: True
    items: [1, 2, 3]
    for x in self.items:
        Label:
            text: str(x)
''')
        self.assertTrue(collected)

    def test_slot_widget_is_collected(self):
        collected, _ = self._collected('''
<GcProbe@BoxLayout>:
    flag: True
    slot body:
        Label:
            text: 'fallback'
''')
        self.assertTrue(collected)

    def test_many_rows_collected_after_clear(self):
        import gc
        import weakref
        from kivy.factory import Factory
        from kivy.uix.boxlayout import BoxLayout
        Builder.load_string('''
<GcRow@BoxLayout>:
    label: '?'
    if self.label:
        Label:
            text: root.label
''', filename='gc_rows.kv')
        try:
            container = BoxLayout()
            refs = []
            for i in range(20):
                row = Factory.GcRow()
                row.label = 'row %d' % i
                container.add_widget(row)
                refs.append(weakref.ref(row))
            del row
            container.clear_widgets()
            gc.collect()
            alive = sum(1 for r in refs if r() is not None)
            self.assertEqual(alive, 0)
        finally:
            Builder.unload_file('gc_rows.kv')


def _canvas_types(canvas):
    '''Flatten a canvas (descending into instruction groups) to the list of
    instruction class names, in draw order. ``BindTexture`` is dropped: kv
    auto-adds it alongside textured instructions (Rectangle/Line) and it is
    not part of what the rule declares.'''
    from kivy.graphics import InstructionGroup
    out = []
    for instr in canvas.children:
        if isinstance(instr, InstructionGroup):
            out += _canvas_types(instr)
        elif type(instr).__name__ != 'BindTexture':
            out.append(type(instr).__name__)
    return out


def _canvas_leaves(canvas):
    '''Flatten a canvas (descending into groups) to the list of leaf
    instruction *instances* in draw order, dropping kv's auto-added
    ``BindTexture``. Used to assert instruction identity across reconciles.'''
    from kivy.graphics import InstructionGroup
    out = []
    for instr in canvas.children:
        if isinstance(instr, InstructionGroup):
            out += _canvas_leaves(instr)
        elif type(instr).__name__ != 'BindTexture':
            out.append(instr)
    return out


class CanvasControlRuntimeTestCase(unittest.TestCase):
    '''``if`` and ``for`` work inside a canvas block, managing graphics
    instructions reactively and in document position.'''

    def test_for_in_canvas_builds_and_reacts(self):
        from kivy.factory import Factory
        Builder.load_string('''
<ForCanvas@Widget>:
    pts: [1, 2, 3]
    canvas:
        Color:
        for p in self.pts:
            Rectangle:
''', filename='for_canvas.kv')
        try:
            w = Factory.ForCanvas()
            self.assertEqual(
                _canvas_types(w.canvas),
                ['Color', 'Rectangle', 'Rectangle', 'Rectangle'])
            w.pts = [1, 2]
            self.assertEqual(
                _canvas_types(w.canvas), ['Color', 'Rectangle', 'Rectangle'])
            w.pts = []
            self.assertEqual(_canvas_types(w.canvas), ['Color'])
        finally:
            Builder.unload_file('for_canvas.kv')

    def test_canvas_for_keyed_preserves_instruction_identity(self):
        # with `key:` a canvas `for` keeps/moves/rebuilds per-iteration
        # instruction groups instead of rebuilding wholesale
        from kivy.factory import Factory
        Builder.load_string('''
<KeyedForCanvas@Widget>:
    items: [1, 2, 3]
    canvas:
        Color:
        for it in self.items:
            key: it
            Line:
                points: (it, it)
''', filename='keyed_for_canvas.kv')
        try:
            w = Factory.KeyedForCanvas()
            leaves = _canvas_leaves(w.canvas)
            self.assertEqual([type(i).__name__ for i in leaves],
                             ['Color', 'Line', 'Line', 'Line'])
            color = leaves[0]
            lines = leaves[1:]            # for keys 1, 2, 3 in order

            # reorder: same Line objects, new draw order
            w.items = [3, 1, 2]
            self.assertEqual(
                _canvas_leaves(w.canvas),
                [color, lines[2], lines[0], lines[1]])

            # remove a key: its Line is gone, the others are untouched
            w.items = [3, 1]
            self.assertEqual(
                _canvas_leaves(w.canvas), [color, lines[2], lines[0]])

            # add a key: a fresh Line, the kept ones still identical
            w.items = [3, 1, 9]
            after = _canvas_leaves(w.canvas)
            self.assertEqual(after[:3], [color, lines[2], lines[0]])
            self.assertEqual(type(after[3]).__name__, 'Line')
            self.assertNotIn(after[3], lines)
        finally:
            Builder.unload_file('keyed_for_canvas.kv')

    def test_canvas_for_keyed_no_op_on_unchanged(self):
        from kivy.factory import Factory
        Builder.load_string('''
<KeyedForCanvas2@Widget>:
    items: [1, 2]
    tick: 0
    canvas:
        for it in self.items:
            key: it
            Line:
''', filename='keyed_for_canvas2.kv')
        try:
            w = Factory.KeyedForCanvas2()
            before = _canvas_leaves(w.canvas)
            # reassigning an equal list must not rebuild the instructions
            w.items = [1, 2]
            self.assertEqual(_canvas_leaves(w.canvas), before)
        finally:
            Builder.unload_file('keyed_for_canvas2.kv')

    def test_if_in_canvas_switches_instructions(self):
        from kivy.factory import Factory
        Builder.load_string('''
<IfCanvas@Widget>:
    on: False
    canvas:
        Color:
        if self.on:
            Rectangle:
        else:
            Line:
''', filename='if_canvas.kv')
        try:
            w = Factory.IfCanvas()
            self.assertEqual(_canvas_types(w.canvas), ['Color', 'Line'])
            w.on = True
            self.assertEqual(_canvas_types(w.canvas), ['Color', 'Rectangle'])
            w.on = False
            self.assertEqual(_canvas_types(w.canvas), ['Color', 'Line'])
        finally:
            Builder.unload_file('if_canvas.kv')

    def test_canvas_control_keeps_document_position(self):
        # instructions after the control block stay after it
        from kivy.factory import Factory
        Builder.load_string('''
<PosCanvas@Widget>:
    pts: []
    canvas:
        Color:
        for p in self.pts:
            Rectangle:
        Line:
''', filename='pos_canvas.kv')
        try:
            w = Factory.PosCanvas()
            self.assertEqual(_canvas_types(w.canvas), ['Color', 'Line'])
            w.pts = [1, 2]
            self.assertEqual(
                _canvas_types(w.canvas),
                ['Color', 'Rectangle', 'Rectangle', 'Line'])
        finally:
            Builder.unload_file('pos_canvas.kv')

    def test_nested_for_in_if_in_canvas(self):
        from kivy.factory import Factory
        Builder.load_string('''
<NestCanvas@Widget>:
    on: True
    pts: [1, 2]
    canvas:
        if self.on:
            Color:
            for p in self.pts:
                Line:
''', filename='nest_canvas.kv')
        try:
            w = Factory.NestCanvas()
            self.assertEqual(
                _canvas_types(w.canvas), ['Color', 'Line', 'Line'])
            w.pts = [1, 2, 3]
            self.assertEqual(
                _canvas_types(w.canvas), ['Color', 'Line', 'Line', 'Line'])
            w.on = False
            self.assertEqual(_canvas_types(w.canvas), [])
            w.on = True
            self.assertEqual(
                _canvas_types(w.canvas), ['Color', 'Line', 'Line', 'Line'])
        finally:
            Builder.unload_file('nest_canvas.kv')

    def test_instruction_property_binding_in_canvas_control(self):
        from kivy.factory import Factory
        from kivy.graphics import Color, InstructionGroup
        Builder.load_string('''
<BindCanvas@Widget>:
    on: True
    alpha: 0.5
    canvas:
        if self.on:
            Color:
                rgba: 1, 0, 0, self.alpha
''', filename='bind_canvas.kv')
        try:
            w = Factory.BindCanvas()

            def find_color(canvas):
                for instr in canvas.children:
                    if isinstance(instr, InstructionGroup):
                        c = find_color(instr)
                        if c is not None:
                            return c
                    elif isinstance(instr, Color):
                        return instr
                return None
            color = find_color(w.canvas)
            self.assertIsNotNone(color)
            w.alpha = 0.9
            Builder.sync()        # canvas bindings are delayed
            self.assertAlmostEqual(color.rgba[3], 0.9)
        finally:
            Builder.unload_file('bind_canvas.kv')

    def test_no_handler_leak_on_canvas_rebuild(self):
        from kivy.factory import Factory
        Builder.load_string('''
<LeakCanvas@Widget>:
    pts: [1]
    canvas:
        for p in self.pts:
            Color:
                rgba: 1, 0, 0, p
''', filename='leak_canvas.kv')
        try:
            w = Factory.LeakCanvas()
            for i in range(30):
                w.pts = [1, 2, 3]
                w.pts = [1]
            n = sum(len(v) for v in _handlers.get(w.uid, {}).values())
            # one live Color binding per current instruction (here 1)
            self.assertLessEqual(n, 1)
        finally:
            Builder.unload_file('leak_canvas.kv')

    def test_canvas_control_widget_is_collected(self):
        import gc
        import weakref
        from kivy.factory import Factory
        Builder.load_string('''
<GcCanvas@Widget>:
    pts: [1, 2, 3]
    canvas:
        for p in self.pts:
            Rectangle:
''', filename='gc_canvas.kv')
        try:
            w = Factory.GcCanvas()
            w.pts = [1, 2]
            ref = weakref.ref(w)
            del w
            gc.collect()
            self.assertIsNone(ref())
        finally:
            Builder.unload_file('gc_canvas.kv')


class ControlRegressionTestCase(unittest.TestCase):
    '''Regression tests pinning behaviors that once broke.'''

    def test_cross_rule_base_coexists_with_branch(self):
        # base in the class rule, conditional override in the subclass rule:
        # they coexist like ordinary stacked-rule bindings -- the branch wins
        # while active, and the base (still live) re-wins on its next change
        from kivy.factory import Factory
        Builder.load_string('''
<CRBase@BoxLayout>:
    src: 1
    foo: self.src * 10
<CRSub@CRBase>:
    cond: False
    if self.cond:
        foo: 999
''', filename='crbase.kv')
        try:
            w = Factory.CRSub()
            self.assertEqual(w.foo, 10)     # class-rule base
            w.cond = True
            self.assertEqual(w.foo, 999)    # subclass-rule branch overrides
            w.cond = False
            # one-way: no immediate revert; the class-rule base stays bound
            self.assertEqual(w.foo, 999)
            w.src = 5
            self.assertEqual(w.foo, 50)     # base re-wins on its next change
        finally:
            Builder.unload_file('crbase.kv')

    def test_ignored_const_base_not_reasserted(self):
        from kivy.uix.boxlayout import BoxLayout
        from kivy.properties import NumericProperty, BooleanProperty

        class IgnConst(BoxLayout):
            foo = NumericProperty(0)
            cond = BooleanProperty(False)

        Builder.load_string('''
<IgnConst>:
    foo: 7
    if self.cond:
        foo: 99
''', filename='ignconst.kv')
        try:
            w = IgnConst(foo=42)            # python value preserved by apply
            self.assertEqual(w.foo, 42)
            w.cond = True
            self.assertEqual(w.foo, 99)
            w.cond = False
            # the suppressed constant 7 must NOT be re-asserted; with no live
            # base the branch's last value is kept (one-way binding)
            self.assertEqual(w.foo, 99)
        finally:
            Builder.unload_file('ignconst.kv')

    def test_reapply_resets_control_nodes(self):
        from kivy.factory import Factory
        Builder.load_string('''
<ReApply@BoxLayout>:
    flag: True
    if self.flag:
        Label:
''', filename='reapply.kv')
        try:
            w = Factory.ReApply()
            n1 = len(w._kv_control_nodes)
            self.assertEqual(n1, 1)
            Builder.unbind_widget(w.uid)
            Builder.apply(w)
            self.assertEqual(len(w._kv_control_nodes), n1)  # not duplicated
        finally:
            Builder.unload_file('reapply.kv')

    def test_constant_key_reports_duplicate_not_typeerror(self):
        with self.assertRaises(BuilderException) as cm:
            Builder.load_string('''
BoxLayout:
    items: [1, 2]
    for x in self.items:
        key: 5
        Label:
            text: str(x)
''')
        self.assertIn('duplicate', str(cm.exception))

    def test_for_body_local_does_not_touch_host_property(self):
        # a for-body local is iteration-scoped and never writes the host
        # property of the same name (which keeps tracking its own binding)
        root = Builder.load_string('''
BoxLayout:
    src: 10
    n: self.src * 2
    items: [100, 200]
    for i in self.items:
        n: i
        Label:
            text: str(n)
''')
        self.assertEqual(root.n, 20)        # host n untouched by the local
        self.assertEqual(texts(root), ['100', '200'])
        root.src = 5
        self.assertEqual(root.n, 10)        # host binding still live

    def test_for_local_scopes_unbound_on_iteration_removal(self):
        # each iteration's scope object owns the local bindings; removing an
        # iteration tears its scope down (no leftover handler entries)
        from kivy.lang.parser import _handlers
        root = Builder.load_string('''
BoxLayout:
    offset: 0
    items: [1, 2, 3]
    for i in self.items:
        key: i
        n: i + root.offset
        Label:
            text: str(n)
''')
        def n_scopes():
            return sum(1 for uid in list(_handlers) if 'n' in _handlers[uid])

        before = n_scopes()
        root.items = [1, 3]                 # remove the middle iteration
        # exactly one iteration scope (and its 'n' binding) is torn down
        self.assertEqual(before - n_scopes(), 1)

    def test_for_with_props_widget_is_collected(self):
        import gc
        import weakref
        from kivy.factory import Factory
        Builder.load_string('''
<ForPropGc@BoxLayout>:
    n: 0
    items: [1, 2]
    for i in self.items:
        n: i
        Label:
            text: str(i)
''', filename='forpropgc.kv')
        try:
            w = Factory.ForPropGc()
            ref = weakref.ref(w)
            del w
            gc.collect()
            self.assertIsNone(ref())
        finally:
            Builder.unload_file('forpropgc.kv')

    def test_exception_mid_canvas_build_leaves_clean_rulectx(self):
        from kivy.lang.builder import Builder as B
        from kivy.factory import Factory
        Builder.load_string('''
<BadCanvas@Widget>:
    zero: 0
    canvas:
        for i in [1, 2]:
            Color:
                rgba: 1 / self.zero, 0, 0, 1
''', filename='badcanvas.kv')
        try:
            with self.assertRaises(BuilderException):
                Factory.BadCanvas()      # canvas build divides by zero
            self.assertEqual(dict(B.rulectx), {})
        finally:
            B.unload_file('badcanvas.kv')


class CanvasRegressionTestCase(unittest.TestCase):

    def test_clear_inside_canvas_control_does_not_crash(self):
        from kivy.factory import Factory
        Builder.load_string('''
<ClearCanvas@Widget>:
    on: True
    canvas:
        if self.on:
            Color:
            Clear
            Color:
''', filename='clearcanvas.kv')
        try:
            w = Factory.ClearCanvas()    # must not raise
            w.on = False
            w.on = True
        finally:
            Builder.unload_file('clearcanvas.kv')

    def test_control_in_canvas_before_and_after(self):
        from kivy.factory import Factory
        Builder.load_string('''
<BACanvas@Widget>:
    pts: [1, 2]
    canvas.before:
        for p in self.pts:
            Rectangle:
    canvas.after:
        if self.pts:
            Line:
''', filename='bacanvas.kv')
        try:
            w = Factory.BACanvas()
            self.assertEqual(
                _canvas_types(w.canvas.before), ['Rectangle', 'Rectangle'])
            self.assertEqual(_canvas_types(w.canvas.after), ['Line'])
            w.pts = [1]
            self.assertEqual(_canvas_types(w.canvas.before), ['Rectangle'])
        finally:
            Builder.unload_file('bacanvas.kv')

    def test_branch_canvas_zorder_follows_document_order(self):
        from kivy.factory import Factory
        Builder.load_string('''
<ZOrder@Widget>:
    a: False
    b: False
    if self.a:
        canvas:
            Scale:
    if self.b:
        canvas:
            Rotate:
''', filename='zorder.kv')
        try:
            w = Factory.ZOrder()
            # activate the later block (b) first, then a: a's group must
            # still draw before b's, following document order
            w.b = True
            w.a = True
            self.assertEqual(_canvas_types(w.canvas), ['Scale', 'Rotate'])
        finally:
            Builder.unload_file('zorder.kv')

    def test_canvas_for_skips_rebuild_when_unchanged(self):
        from kivy.factory import Factory
        Builder.load_string('''
<ForSkip@Widget>:
    pts: [1, 2]
    canvas:
        for p in self.pts:
            Rectangle:
''', filename='forskip.kv')
        try:
            w = Factory.ForSkip()
            before = list(w.canvas.children)
            w.pts = [1, 2]               # equal value -> no rebuild
            self.assertEqual(list(w.canvas.children), before)  # same objects
        finally:
            Builder.unload_file('forskip.kv')


if __name__ == '__main__':
    unittest.main()
