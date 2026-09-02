'''
Tests for parsing kv control statements (if/elif/else, for, slot, factory).

These only cover the parser stage (:class:`kivy.lang.parser.Parser`);
builder/runtime behavior is tested separately.
'''

import unittest

from kivy.lang.parser import Parser, ParserControlRule, ParserException


def parse_rule(kv):
    '''Parse kv content and return the first rule.'''
    return Parser(content=kv).rules[0][1]


class ControlStatementParseTestCase(unittest.TestCase):

    def assert_parse_error(self, kv, message_part):
        with self.assertRaises(ParserException) as cm:
            Parser(content=kv)
        self.assertIn(message_part, str(cm.exception))

    def test_if_chain_merged_into_branches(self):
        rule = parse_rule('''
<W@Widget>:
    if self.expanded:
        Label:
            text: 'open'
    elif self.collapsed:
        Label:
            text: 'mid'
    else:
        Label:
            text: 'closed'
''')
        self.assertTrue(rule.has_controls)
        self.assertEqual(len(rule.children), 1)
        ctl = rule.children[0]
        self.assertIsInstance(ctl, ParserControlRule)
        self.assertEqual(ctl.kind, 'if')
        self.assertEqual(
            [b.cond_src for b in ctl.branches],
            ['self.expanded', 'self.collapsed', None])
        self.assertEqual([len(b.children) for b in ctl.branches], [1, 1, 1])
        self.assertEqual(
            ctl.selector_prop.value,
            '0 if (self.expanded) else 1 if (self.collapsed) else 2')
        self.assertIn(['self', 'expanded'], ctl.selector_prop.watched_keys)
        self.assertIn(['self', 'collapsed'], ctl.selector_prop.watched_keys)

    def test_if_without_else_selects_minus_one(self):
        ctl = parse_rule('''
<W@Widget>:
    if self.x:
        Label:
''').children[0]
        self.assertEqual(ctl.selector_prop.value, '0 if (self.x) else -1')

    def test_two_sibling_if_chains_stay_separate(self):
        rule = parse_rule('''
<W@Widget>:
    if self.a:
        Label:
    if self.b:
        Label:
    else:
        Label:
''')
        self.assertEqual(len(rule.children), 2)
        self.assertEqual(len(rule.children[0].branches), 1)
        self.assertEqual(len(rule.children[1].branches), 2)

    def test_widget_between_if_and_else_is_an_error(self):
        self.assert_parse_error('''
<W@Widget>:
    if self.a:
        Label:
    Label:
    else:
        Label:
''', '"else" must immediately follow')

    def test_for_with_tuple_target_filter_and_key(self):
        ctl = parse_rule('''
<W@Widget>:
    for item, index in enumerate(self.items) if item.visible:
        key: item.uid
        Label:
            text: str(item)
''').children[0]
        self.assertEqual(ctl.kind, 'for')
        self.assertEqual(ctl.target_names, ['item', 'index'])
        self.assertEqual(
            ctl.iterator_prop.value,
            '[(item, index,) for item, index in (enumerate(self.items))'
            ' if (item.visible)]')
        self.assertEqual(ctl.key_prop.value, 'item.uid')
        self.assertEqual(len(ctl.children), 1)

    def test_for_watched_keys_exclude_loop_targets(self):
        ctl = parse_rule('''
<W@Widget>:
    for item in self.items if item.visible and root.active:
        key: item.uid
        Label:
''').children[0]
        self.assertEqual(
            sorted(map(tuple, ctl.iterator_prop.watched_keys)),
            [('root', 'active'), ('self', 'items')])
        self.assertIsNone(ctl.key_prop.watched_keys)

    def test_for_star_target(self):
        ctl = parse_rule('''
<W@Widget>:
    for first, *rest in self.rows:
        Label:
''').children[0]
        self.assertEqual(ctl.target_names, ['first', 'rest'])

    def test_slot_named_and_default(self):
        rule = parse_rule('''
<W@Widget>:
    slot header:
        Label:
    slot:
''')
        named, default = rule.children
        self.assertEqual(named.kind, 'slot')
        self.assertEqual(named.slot_name, 'header')
        self.assertEqual(len(named.children), 1)
        self.assertEqual(default.slot_name, '')
        self.assertEqual(default.children, [])

    def test_nested_controls(self):
        rule = parse_rule('''
<W@Widget>:
    for row in self.rows:
        BoxLayout:
            if row.title:
                Label:
                    text: row.title
''')
        outer = rule.children[0]
        box = outer.children[0]
        self.assertTrue(box.has_controls)
        self.assertEqual(box.children[0].kind, 'if')

    def test_colon_inside_condition_braces(self):
        ctl = parse_rule('''
<W@Widget>:
    if {1: 2}.get(self.x):
        Label:
''').children[0]
        self.assertEqual(ctl.branches[0].cond_src, '{1: 2}.get(self.x)')

    def test_bare_lambda_colon_in_header(self):
        # the block colon is the last depth-0 colon, so a bare lambda's own
        # colon stays inside the header
        ctl = parse_rule('''
<W@Widget>:
    if lambda: 1:
        Label:
''').children[0]
        self.assertEqual(ctl.branches[0].cond_src, 'lambda: 1')

    def test_scoped_id_cannot_be_app(self):
        # unlike a static id, a scoped id rewrites its references, so `app`
        # would silently hijack the app proxy
        self.assert_parse_error('''
<W@Widget>:
    if self.x:
        Label:
            id: app
''', 'cannot be "self", "root" or "app"')

    def test_trailing_comment_after_colon(self):
        ctl = parse_rule('''
<W@Widget>:
    if self.x:  # visible?
        Label:
''').children[0]
        self.assertEqual(ctl.branches[0].cond_src, 'self.x')

    def test_keyword_prefixed_names_still_parse_as_rules(self):
        # 'format', 'iffy', 'forward' must not be mistaken for keywords
        rule = parse_rule('''
<W@Widget>:
    format: 'png'
    iffy: 1
    forward: True
''')
        self.assertFalse(rule.has_controls)
        self.assertEqual(
            sorted(rule.properties), ['format', 'forward', 'iffy'])

    def test_orphan_else(self):
        self.assert_parse_error('''
<W@Widget>:
    Label:
    else:
        Label:
''', '"else" must immediately follow')

    def test_orphan_elif(self):
        self.assert_parse_error('''
<W@Widget>:
    elif self.x:
        Label:
''', '"elif" must immediately follow')

    def test_else_after_else(self):
        self.assert_parse_error('''
<W@Widget>:
    if self.x:
        Label:
    else:
        Label:
    else:
        Label:
''', '"else" must immediately follow')

    def test_else_after_for(self):
        self.assert_parse_error('''
<W@Widget>:
    for x in self.items:
        Label:
    else:
        Label:
''', '"else" after "for" is not supported')

    def test_non_control_keywords_rejected(self):
        # while/match/case are not kv control statements; they fall through to
        # the ordinary class/property path and are rejected as invalid names.
        # Nothing is reserved: adding such a statement later is additive,
        # exactly like this feature itself.
        for kw in ('while', 'match', 'case'):
            self.assert_parse_error('''
<W@Widget>:
    %s self.x:
        Label:
''' % kw, 'Invalid property name')

    def test_keyword_named_bare_properties_still_parse(self):
        # bare names that are Python keywords elsewhere stay plain kv
        # properties
        rule = parse_rule('''
<W@Widget>:
    match: 1
    case: 2
''')
        self.assertEqual(sorted(rule.properties), ['case', 'match'])

    def test_top_level_control_forbidden(self):
        self.assert_parse_error('''
if True:
    Label:
''', 'not allowed at the top level')

    def test_walrus_forbidden(self):
        self.assert_parse_error('''
<W@Widget>:
    if (y := self.x):
        Label:
''', 'assignment expressions')

    def test_loop_target_may_shadow_reserved_names(self):
        # loop targets form their own scope and may shadow any name,
        # including self/root/app and the metric helpers (resolved at
        # runtime; here we only assert the parser accepts them)
        for name in ('self', 'root', 'app', 'dp', 'cm', 'rgba'):
            ctl = parse_rule('''
<W@Widget>:
    for %s in self.items:
        Label:
''' % name).children[0]
            self.assertEqual(ctl.target_names, [name])

    def test_key_must_precede_widgets(self):
        # "key:" is a property; like all kv properties it must come before
        # the block's child widgets (kv rejects any property after a child)
        self.assert_parse_error('''
<W@Widget>:
    for item in self.items:
        Label:
        key: item.uid
''', 'Invalid data after declaration')

    def test_property_inside_if_allowed(self):
        rule = parse_rule('''
<W@Widget>:
    if self.x:
        text: 'hi'
''')
        branch = rule.children[0].branches[0]
        self.assertIn('text', branch.properties)
        self.assertEqual(branch.children, [])

    def test_property_inside_for_is_a_local(self):
        # a for body property is an iteration-local: extracted out of
        # ``properties`` into ``locals`` with a scope key, and references to
        # it rewritten to attribute access on that scope
        rule = parse_rule('''
<W@Widget>:
    for i in self.items:
        doubled: i * 2
        Label:
            text: str(doubled)
''')
        ctl = rule.children[0]
        self.assertNotIn('doubled', ctl.properties)
        self.assertEqual([n for n, _ in ctl.locals], ['doubled'])
        self.assertIsNotNone(ctl.scope_key)
        # the child reference is rewritten to <scope>.doubled
        child = ctl.children[0]
        self.assertIn(ctl.scope_key, child.properties['text'].value)

    def test_for_with_only_a_local_and_no_child_forbidden(self):
        self.assert_parse_error('''
<W@Widget>:
    for i in self.items:
        n: i
''', 'requires at least one child widget')

    def test_for_handler_and_canvas_still_forbidden(self):
        self.assert_parse_error('''
<W@Widget>:
    for i in self.items:
        on_x: print(i)
        Label:
''', 'event handlers are not allowed')

    def test_property_in_if_inside_for_is_conditional_local(self):
        # nearest-scope rule: a property line binds to the nearest enclosing
        # scope, so in an ``if`` nested in a ``for`` it is an iteration-local
        # (bound while the branch is active), not a host property
        rule = parse_rule('''
<W@Widget>:
    for n in self.items:
        if n > 2:
            label: 'big ' + str(n)
        Label:
            text: label or ''
''')
        ctl = rule.children[0]
        self.assertIn('label', ctl.scope_names)
        self.assertNotIn('label', [x for x, _ in ctl.locals])
        child = ctl.children[-1]
        self.assertIn(ctl.scope_key, child.properties['text'].value)

    def test_handler_in_if_inside_for_forbidden(self):
        # nesting context semantics: an ``if`` under a ``for`` follows the
        # for-body content rules, so host handlers stay forbidden
        self.assert_parse_error('''
<W@Widget>:
    for i in self.items:
        if i:
            on_touch_down: pass
            Label:
        Label:
''', 'event handlers are not allowed')

    def test_canvas_in_if_inside_for_forbidden(self):
        self.assert_parse_error('''
<W@Widget>:
    for i in self.items:
        if i:
            canvas:
                Color:
            Label:
        Label:
''', 'canvas is not allowed')

    def test_local_and_id_name_clash_is_error(self):
        # one name cannot be driven by both a local binding and an id: both
        # writers would stay live (this is not Python shadowing)
        self.assert_parse_error('''
<W@Widget>:
    for i in self.items:
        total: i * 2
        Label:
            id: total
''', 'clashes')

    def test_property_inside_slot_is_slot_local(self):
        # a slot definition property is a slot-scoped local, evaluated in the
        # defining rule's context and exposed to fallback and fill content as
        # an attribute of the reserved ``slot`` name
        rule = parse_rule('''
<W@Widget>:
    title: 'x'
    slot header:
        summary: self.title.upper()
        Label:
            text: slot.summary
''')
        ctl = rule.children[0]
        self.assertEqual([n for n, _ in ctl.locals], ['summary'])
        self.assertNotIn('summary', ctl.properties)

    def test_full_body_inside_if_allowed(self):
        # children + property + canvas + handler all live in one branch
        rule = parse_rule('''
<W@Widget>:
    if self.x:
        my_prop: self.width
        on_touch_down: pass
        canvas:
            Color:
        Label:
    else:
        my_prop: 0
''')
        ctl = rule.children[0]
        on_branch, off_branch = ctl.branches
        self.assertIn('my_prop', on_branch.properties)
        self.assertEqual(len(on_branch.handlers), 1)
        self.assertIsNotNone(on_branch.canvas_root)
        self.assertEqual(len(on_branch.children), 1)
        self.assertIn('my_prop', off_branch.properties)

    def test_id_inside_if_forbidden(self):
        self.assert_parse_error('''
<W@Widget>:
    if self.x:
        id: nope
        Label:
''', '"id" is not allowed')

    def test_id_inside_if_is_reactive_scoped(self):
        # a widget id inside an if is redirected onto a rule-level scope
        # object so it can mount/unmount reactively; references to it are
        # reachable across the whole rule
        rule = parse_rule('''
<W@Widget>:
    if self.x:
        Label:
            id: nope
    Button:
        disabled: nope is None
''')
        self.assertIsNotNone(rule.id_scope_key)
        self.assertEqual(rule.id_scope_names, ['nope'])
        lbl = rule.children[0].branches[0].children[0]
        self.assertIsNone(lbl.id)               # the static id is cleared
        self.assertEqual(lbl.scope_id, (rule.id_scope_key, 'nope'))
        # the sibling reference was rewritten onto the scope
        btn = rule.children[1]
        self.assertIn(rule.id_scope_key, btn.properties['disabled'].value)

    def test_id_inside_for_is_iteration_scoped(self):
        # a widget id inside a for is redirected onto the per-iteration scope
        rule = parse_rule('''
<W@Widget>:
    for it in self.items:
        Label:
            id: lab
        Button:
            text: lab.text
''')
        ctl = rule.children[0]
        self.assertIsNotNone(ctl.scope_key)
        self.assertEqual(ctl.id_scope_names, ['lab'])
        self.assertEqual(ctl.children[0].scope_id, (ctl.scope_key, 'lab'))
        self.assertIn(ctl.scope_key, ctl.children[1].properties['text'].value)

    def test_id_inside_slot_is_rule_scoped(self):
        # an id on slot content (definition fallback or explicit fill block)
        # is a reactive id on the rule providing that content
        rule = parse_rule('''
<W@Widget>:
    slot header:
        Label:
            id: head
    Button:
        disabled: head is None
''')
        self.assertEqual(rule.id_scope_names, ['head'])
        lbl = rule.children[0].children[0]
        self.assertIsNone(lbl.id)
        self.assertEqual(lbl.scope_id, (rule.id_scope_key, 'head'))
        self.assertIn(rule.id_scope_key,
                      rule.children[1].properties['disabled'].value)

    def test_id_inside_factory_body_forbidden(self):
        self.assert_parse_error('''
<W@Widget>:
    factory 'Label':
        Label:
            id: nope
''', '"id" is not allowed')

    def test_id_deep_inside_if_is_collected(self):
        rule = parse_rule('''
<W@Widget>:
    if self.x:
        BoxLayout:
            BoxLayout:
                Label:
                    id: deep
''')
        self.assertEqual(rule.id_scope_names, ['deep'])

    def test_id_outside_control_block_still_allowed(self):
        rule = parse_rule('''
<W@Widget>:
    Label:
        id: fine
    if self.x:
        Label:
''')
        self.assertEqual(rule.children[0].id, 'fine')

    def test_handler_inside_if_allowed(self):
        rule = parse_rule('''
<W@Widget>:
    if self.x:
        on_touch_down: pass
        Label:
''')
        branch = rule.children[0].branches[0]
        self.assertEqual(len(branch.handlers), 1)
        self.assertEqual(branch.handlers[0].name, 'on_touch_down')

    def test_handler_inside_for_forbidden(self):
        self.assert_parse_error('''
<W@Widget>:
    for i in self.items:
        on_touch_down: pass
        Label:
''', 'event handlers are not allowed')

    def test_canvas_inside_if_allowed(self):
        rule = parse_rule('''
<W@Widget>:
    if self.x:
        canvas:
            Color:
        Label:
''')
        branch = rule.children[0].branches[0]
        self.assertIsNotNone(branch.canvas_root)

    def test_canvas_inside_for_forbidden(self):
        self.assert_parse_error('''
<W@Widget>:
    for i in self.items:
        canvas:
            Color:
        Label:
''', 'canvas is not allowed')

    def test_control_inside_canvas_allowed(self):
        rule = parse_rule('''
<W@Widget>:
    canvas:
        Color:
        for p in self.points:
            Line:
                points: p
        if self.selected:
            Rectangle:
''')
        children = rule.canvas_root.children
        self.assertEqual(children[0].name, 'Color')
        self.assertEqual(children[1].kind, 'for')
        self.assertTrue(children[1].in_canvas)
        self.assertEqual(children[2].kind, 'if')
        self.assertTrue(children[2].in_canvas)

    def test_property_inside_canvas_control_forbidden(self):
        self.assert_parse_error('''
<W@Widget>:
    canvas:
        if self.x:
            foo: 1
            Color:
''', 'only graphics instructions are allowed')

    def test_control_under_canvas_instruction_forbidden(self):
        self.assert_parse_error('''
<W@Widget>:
    canvas:
        Rectangle:
            if self.x:
                Color:
''', 'not allowed under a graphics instruction')

    def test_key_outside_for_forbidden(self):
        self.assert_parse_error('''
<W@Widget>:
    if self.x:
        key: 1
        Label:
''', '"key:" is only allowed inside a "for" block')

    def test_empty_if_body(self):
        self.assert_parse_error('''
<W@Widget>:
    if self.x:
    Label:
''', 'requires at least one child widget')

    def test_empty_for_body(self):
        self.assert_parse_error('''
<W@Widget>:
    for x in self.items:
    Label:
''', 'requires at least one child widget')

    def test_missing_colon(self):
        self.assert_parse_error('''
<W@Widget>:
    if self.x
        Label:
''', "expected ':'")

    def test_inline_body_forbidden(self):
        self.assert_parse_error('''
<W@Widget>:
    if self.x: Label()
''', "unexpected content after ':'")

    def test_if_without_condition(self):
        self.assert_parse_error('''
<W@Widget>:
    if:
        Label:
''', 'requires a condition expression')

    def test_else_with_expression(self):
        self.assert_parse_error('''
<W@Widget>:
    if self.x:
        Label:
    else self.y:
        Label:
''', '"else" takes no expression')

    def test_multiple_for_clauses_forbidden(self):
        self.assert_parse_error('''
<W@Widget>:
    for x in self.a for y in self.b:
        Label:
''', 'single "for ... in ..." clause')

    def test_async_for_forbidden(self):
        self.assert_parse_error('''
<W@Widget>:
    async for x in self.items:
        Label:
''', '')

    def test_invalid_slot_name(self):
        for name in ('1bad', 'two words', 'if'):
            self.assert_parse_error('''
<W@Widget>:
    slot %s:
        Label:
''' % name, 'invalid slot name')

    def test_factory_parses_class_expression_and_body(self):
        rule = parse_rule('''
<W@Widget>:
    which: 'Button'
    factory self.which:
        text: root.caption
        Label:
            text: 'inner'
''')
        self.assertTrue(rule.has_controls)
        ctl = rule.children[-1]
        self.assertIsInstance(ctl, ParserControlRule)
        self.assertEqual(ctl.kind, 'factory')
        self.assertEqual(ctl.class_prop.value, 'self.which')
        self.assertIn(['self', 'which'], ctl.class_prop.watched_keys)
        # the body is a full widget rule applied to the instance
        self.assertIn('text', ctl.properties)
        self.assertEqual(len(ctl.children), 1)

    def test_factory_requires_expression(self):
        self.assert_parse_error('''
<W@Widget>:
    factory:
        Label:
''', '"factory" requires an expression')

    def test_factory_in_canvas_forbidden(self):
        self.assert_parse_error('''
<W@Widget>:
    canvas:
        factory self.which:
            Color:
''', 'cannot be declared inside canvas')

    def test_factory_walrus_forbidden(self):
        self.assert_parse_error('''
<W@Widget>:
    factory (x := self.which):
        Label:
''', 'assignment expressions')


if __name__ == '__main__':
    unittest.main()
