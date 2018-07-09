import inspect
import ast
import textwrap
from collections import deque, defaultdict
from itertools import chain

from kivy.lang.compiler.ast_parse import generate_source, ASTNodeRef
from kivy.lang.compiler.utils import StringPool


class KVCompiler(object):

    ref = False

    rebind = []

    rebind_func_pool = None

    binding_store_pool = None

    exec_rules_before_binding = False

    def __init__(self, **kwargs):
        super(KVCompiler, self).__init__(**kwargs)
        self.rebind_func_pool = StringPool(prefix='__kv_rebind_callback')
        self.binding_store_pool = StringPool(prefix='__kv_bind_store')

    def get_leaves_dependencies(self, trees):
        node_deps = {}
        for tree, _, _ in trees:
            for node in tree:
                if node.leaf_rule is None:
                    continue

                node_deps[node] = None
                stack = deque(node.depends)
                stack.append(node)
                while stack:
                    first = stack[0]
                    if first not in node_deps:
                        stack.extendleft(first.depends)
                        # next time we see it, its deps will be ready
                        node_deps[first] = None
                    elif node_deps[first] is None:
                        item = node_deps[first] = set(chain(*(node_deps[dep] for dep in first.depends)))
                        item.add(first)
                        stack.popleft()
                    else:
                        stack.popleft()

        return node_deps

    def compute_attr_bindings(self, ctx):
        trees_attr_subtree = []
        for tree in ctx.transformer.nodes_by_tree:
            visited = set()
            attr_subtree = []
            term_subtree_indices = {}
            for node in tree:
                if node.leaf_rule is not None or node in visited:
                    continue
                subtree = node.get_rebind_or_leaf_subtree()
                for term in subtree.terminal_attrs:
                    if term.leaf_rule is None:
                        subtree.terminates_with_leafs_only = False
                    term_subtree_indices[term] = len(attr_subtree)
                attr_subtree.append(subtree)
                visited.update(subtree.nodes)

            ordered_attr_subtrees = []
            visited = set()
            ordered_subtree_dep_indices = {}
            for node in tree:
                if (node.leaf_rule is not None or node.rebind) and node not in visited:
                    subtree = attr_subtree[term_subtree_indices[node]]
                    visited.update(subtree.terminal_attrs)
                    for dep in subtree.nodes:
                        assert dep.leaf_rule is None
                        if dep.rebind:
                            subtree.n_attr_deps += 1
                            ordered_subtree_dep_indices[dep] = len(
                                ordered_attr_subtrees)
                    ordered_attr_subtrees.append(subtree)

            for subtree in ordered_attr_subtrees:
                for term in subtree.terminal_attrs:
                    # every terminal node that isn't a leaf is a dep somewhere
                    if not term.leaf_rule:
                        subtree.depends_on_me.append(
                            ordered_attr_subtrees[
                                ordered_subtree_dep_indices[term]])

            trees_attr_subtree.append(
                (tree, ordered_attr_subtrees, ordered_subtree_dep_indices))
        return trees_attr_subtree

    def get_bind_func_names(self, attr_trees):
        func_pool = self.rebind_func_pool
        tree_bind_func_names = {}
        node_bind_func_names = {}

        for tree, attr_subtrees, subtree_dep_indices in attr_trees:
            for subtree in attr_subtrees:
                for node in subtree.terminal_attrs:
                    if node.leaf_rule is None:
                        node_tree = attr_subtrees[subtree_dep_indices[node]]
                        if node_tree in tree_bind_func_names:
                            # tree was already assigned rebind function
                            node_bind_func_names[node] = tree_bind_func_names[node_tree]
                        else:
                            func = func_pool.borrow(
                                len(func_pool.get_used_items()))
                            node_bind_func_names[node] = \
                                tree_bind_func_names[node_tree] = func
                    else:
                        node_bind_func_names[node] = node.leaf_rule['callback_name']
        return tree_bind_func_names, node_bind_func_names

    def get_trees_attr_bind_indices(self, ctx):
        trees_bind_indices = []
        for tree in ctx.transformer.nodes_by_tree:
            attr_list_indices = {}
            for node in tree:
                if node.leaf_rule is not None or node.rebind:
                    attr_list_indices[node] = len(attr_list_indices)
            trees_bind_indices.append(attr_list_indices)
        return trees_bind_indices

    def get_bind_funcs(
            self, ctx_name, trees, tree_bind_func_names, node_bind_func_names,
            trees_attr_bind_indices, trees_bind_store):
        src_code = []

        for attr_bind_indices, bind_store, (
                    tree, attr_subtrees, subtree_dep_indices) in zip(
                trees_attr_bind_indices, trees_bind_store, trees):
            # count the number of places each node is used. E.g. in
            # `self.x + self.y`, `self` is used twice. Keep in mind that nodes
            # are unique
            node_use_count = defaultdict(int)
            for node in tree:
                for dep in node.depends:
                    assert dep.leaf_rule is None, 'a dep cannot be a leaf, duh'
                    node_use_count[dep] += 1

            processed_subtrees = set()
            for subtree in attr_subtrees:
                # we create a rebind func for each subtree that roots in attr
                if not subtree.n_attr_deps:
                    # It means that all the deps are not attributes, meaning
                    # thet are e.g. variables etc, so that we never create a
                    # rebind func for them
                    # see further down why len(node.depends_on_me) is correct
                    for node in subtree.nodes:
                        node_use_count[node] -= len(node.depends_on_me)
                    continue

                queue = deque([subtree])
                # we can have a subtree being a child
                # of multiple different subtrees. E.g. self.a.b + self.a.c
                subtree_visited = set()
                # we keep track of all attrs we visit in the subtree. Because
                # deps are always explored before the children, if we encounter
                # a attr dep that has not been visited, it means its at the root
                # level in the rebind function stored in the rebind list
                attrs_visited = set()
                node_visited = set()
                node_value_var = {}
                node_original_ref = {}
                temp_pool = StringPool(prefix='__kv_temp_val')
                func_src_code = ['def {}(*__kv_largs):'.format(tree_bind_func_names[subtree])]

                leaf_callbacks = []

                while queue:
                    current_subtree = queue.popleft()
                    if current_subtree in subtree_visited:
                        continue
                    subtree_visited.add(current_subtree)

                    queue.extend(current_subtree.depends_on_me)
                    attrs_visited.update(current_subtree.terminal_attrs)

                    for node in current_subtree.nodes:
                        if node in node_visited:
                            continue
                        node_visited.add(node)

                        # we always store stuff in local variables - it's faster
                        if not node.depends:
                            assert not node.is_attribute
                            # we found a global or local variable - add its name
                            node_value_var[node] = node.src
                        elif node.rebind and node not in attrs_visited:
                            assert len(node.depends) == 1
                            assert node.leaf_rule is None
                            assert node.is_attribute
                            dep = node.depends[0]
                            # this is a root attr, just read its value into var.
                            # node_use_count[node] and len(node.depends_on_me)
                            # may be different because depends_on_me includes
                            # all trees, even those in other rebind funcs, the
                            # former only includes those used in this func
                            var = temp_pool.borrow(node, node_use_count[node])

                            # a rebind function could be bound to multiple attr
                            # rebind nodes (e.g. `(self.x + other.y).value`) so
                            # we need to check if the rebind list has been init
                            i = attr_bind_indices[node]  # list index of rbind
                            assert current_subtree.n_attr_deps >= 1
                            indent = 4
                            if current_subtree.n_attr_deps > 1:
                                func_src_code.append(
                                    '{}{} = None'.format(' ' * 4, var))
                                func_src_code.append('{0}if {1}[{2}] is not None and {1}[{2}][0] is not None:'.format(' ' * 4, bind_store, i))
                                indent = 8

                            # dep_var = temp_pool.borrow(dep, node_use_count[dep] + 1)
                            # node_value_var[dep] = dep_var
                            # code output could be optimized, but then we'd need
                            # to predict which subtrees this rebind func eats
                            if dep not in node_original_ref:
                                assert dep not in node_original_ref
                                node_original_ref[dep] = dep.ref_node
                                dep.set_ref_node(ast.Subscript(
                                    value=ast.Subscript(
                                        value=ast.Name(id=bind_store, ctx=ast.Load()),
                                        slice=ast.Index(value=ast.Num(n=i)), ctx=ast.Load()),
                                    slice=ast.Index(value=ast.Num(n=0)), ctx=ast.Load()))

                            # func_src_code.append('{}{} = {}[{}]'.format(' ' * indent, dep_var, bind_store, i))
                            # temp_pool.return_back(dep)

                            assignment = '{}{} = {}'.format(' ' * indent, var, generate_source(node).rstrip('\r\n'))
                            func_src_code.append(assignment)
                            func_src_code.append('')

                            node_value_var[node] = var
                            assert node not in node_original_ref
                            node_original_ref[node] = node.ref_node
                            node.set_ref_node(ast.Name(id=var, ctx=ast.Load()))
                        elif node.rebind:
                            assert node in node_value_var, 'should already ' \
                                'have been created in terminal node stage'
                        else:
                            assert node.leaf_rule is None
                            assert node.depends_on_me
                            assert not node.is_attribute or not node.rebind
                            # to eval node so we can bind or whatever we need to
                            # check if the last value(s) is not None for deps
                            # but only those that are not locals/globals
                            depends = [dep for dep in node.depends if dep.depends]

                            indent = 4
                            # we hit internal rebind node, performs its
                            # computation and store it in local var
                            assert node_use_count[node] >= 1
                            var = temp_pool.borrow(node, node_use_count[node])

                            # if it has no deps, it won't be under a `if`
                            # so no need to init variable
                            if depends:
                                func_src_code.append('{}{} = None'.format(' ' * 4, var))

                                indent = 8
                                condition = []
                                for dep in depends:
                                    name = node_value_var[dep]
                                    condition.append('{} is not None'.format(name))
                                condition = '{}if {}:'.format(' ' * 4, ' and '.join(condition))
                                func_src_code.append(condition)

                            assignment = '{}{} = {}'.format(' ' * indent, var, generate_source(node).rstrip('\r\n'))
                            func_src_code.append(assignment)
                            func_src_code.append('')

                            node_value_var[node] = var
                            assert node not in node_original_ref
                            node_original_ref[node] = node.ref_node
                            node.set_ref_node(ast.Name(id=var, ctx=ast.Load()))
                            for dep in depends:
                                temp_pool.return_back(dep)

                    # unbind
                    for node in current_subtree.terminal_attrs:
                        # we don't need too check for double visits because
                        # each tree contains *all* deps of terminal attrs
                        i = attr_bind_indices[node]

                        func_src_code.append('{}__kv_bind_ref = {}[{}]'.format(' ' * 4, bind_store, i))
                        func_src_code.append('{}if __kv_bind_ref is not None:'.format(' ' * 4))
                        func_src_code.append('{}__kv_obj, __kv_attr, _, __kv_uid, _, _ = __kv_bind_ref'.format(' ' * 8))
                        func_src_code.append('{}if __kv_obj is not None and __kv_uid:'.format(' ' * 8))
                        func_src_code.append('{}__kv_obj.unbind_uid(__kv_attr, __kv_uid)'.format(' ' * 12))
                        func_src_code.append('{}__kv_bind_ref[0] = None'.format(' ' * 12))
                        func_src_code.append('')

                        if node.leaf_rule is not None and node_bind_func_names[node] not in leaf_callbacks:
                            leaf_callbacks.append(node_bind_func_names[node])

                    terminal_attrs_by_dep = defaultdict(list)
                    for node in current_subtree.terminal_attrs:
                        assert len(node.depends) == 1
                        terminal_attrs_by_dep[node.depends[0]].append(node)

                    for dep, nodes in terminal_attrs_by_dep.items():
                        for node in nodes:
                            assert node.leaf_rule is not None or node.rebind
                            if node.leaf_rule is None:
                                node_value_var[node] = temp_pool.borrow(node, node_use_count[node])

                        indent = 4
                        dep_name = node_value_var[dep]
                        if dep.depends:
                            # no need to init if not under an if
                            for node in nodes:
                                if node.leaf_rule is None:
                                    func_src_code.append('{}{} = None'.format(' ' * 4, node_value_var[node]))

                            func_src_code.append('{}if {} is not None:'.format(' ' * 4, dep_name))
                            indent = 8

                        fbind_name = 'fbind_proxy' if dep.proxy else 'fbind'
                        func_src_code.append('{}__kv__fbind = getattr({}, "{}", None)'.format(' ' * indent, dep_name, fbind_name))
                        func_src_code.append('{}if __kv__fbind is not None:'.format(' ' * indent))
                        indent2 = indent + 4
                        indent3 = indent + 8

                        for node in nodes:
                            obj_attr = node.ref_node.attr
                            i = attr_bind_indices[node]
                            func_src_code.append('{}__kv_bind_element = {}[{}]'.format(' ' * indent2, bind_store, i))
                            func_src_code.append('{}if __kv_bind_element is not None:'.format(' ' * indent2))
                            bind = '__kv__fbind("{}", {})'.format(obj_attr, node_bind_func_names[node])
                            func_src_code.append('{}__kv_bind_element[0] = {}'.format(' ' * indent3, dep_name))
                            func_src_code.append('{}__kv_bind_element[3] = {}'.format(' ' * indent3, bind))
                            func_src_code.append('')

                        for node in nodes:
                            if node.leaf_rule is None:
                                var = node_value_var[node]
                                assignment = '{}{} = {}'.format(' ' * indent, var, generate_source(node).rstrip('\r\n'))
                                func_src_code.append(assignment)
                                func_src_code.append('')

                                assert node not in node_original_ref
                                node_original_ref[node] = node.ref_node
                                node.set_ref_node(ast.Name(id=var, ctx=ast.Load()))

                        if dep.depends:
                            for _ in nodes:
                                temp_pool.return_back(dep)

                for callback in leaf_callbacks:
                    func_src_code.append('{}{}()'.format(' ' * 4, callback))
                func_src_code.append('')

                # remove all that depend on the node because either the dep
                # is in the same subtree, or it's in the terminal of the
                # subtree. In the latter case, binding and attr eval happens
                # in this subtree iteration, so this node won't be used again
                for node in subtree.nodes:
                    node_use_count[node] -= len(node.depends_on_me)
                processed_subtrees.add(current_subtree)
                for node, origin_node in node_original_ref.items():
                    node.set_ref_node(origin_node)
                src_code.extend(func_src_code)

        src_code.append('{}.rebind_functions = ({}, )'.format(
            ctx_name,
            ', '.join(
                tree_bind_func_names[subtree]
                for _, subtrees, _ in trees for subtree in subtrees
                if subtree.n_attr_deps
            ),
        ))
        src_code.append('')

        for node, count in node_use_count.items():
            assert not count, '{}, {} should be zero'.format(node, count)
        return src_code

    def get_init_bindings(
            self, create_rules, ctx_name, trees, rules, rules_nodes,
            node_bind_func_names, nodes_attr_bind_indices, nodes_bind_store_map,
            bind_stores_size):
        assert rules
        temp_pool = StringPool(prefix='__kv_temp_val')
        original_ref_node = {}
        node_value_var = {}
        exec_rules_before_binding = self.exec_rules_before_binding

        leaves_deps = self.get_leaves_dependencies(trees)

        pre_src_code = []
        for name, n in bind_stores_size:
            pre_src_code.append('{} = [None, ] * {}'.format(name, n))
        pre_src_code.append('{}.bind_stores_by_tree = ({}, )'.format(ctx_name, ', '.join((item[0] for item in bind_stores_size))))
        pre_src_code.append('')
        if create_rules:
            pre_src_code.append('__kv_get_rule_cls = {}.get_rule_cls()'.format(ctx_name))
            pre_src_code.append('')

        src_code = []
        for rule_i, (rule, rule_nodes) in enumerate(zip(rules, rules_nodes)):
            rule_src_code = []
            delay = rule['delay']
            if create_rules:
                delay_arg = 'None' if delay is None else '"{}"'.format(delay)
                rule_src_code.append(
                    '__kv_rule = {"name": "{}", "delay": {}, "exec_rule": {})'.
                    format(rule['name'], delay_arg, rule['exec_rule']))
                rule_src_code.append('{}.add_rule(__kv_rule, "{}")'.format(ctx_name, rule['callback_name']))
            else:
                rule_src_code.append('__kv_rule = {}.rules[{}]'.format(ctx_name, rule_i))

            rule_src_code.append('__kv_rule["callback"] = {}'.format(rule['callback_name']))

            leaf_indices_and_store = defaultdict(list)
            for node in rule_nodes:
                if node.leaf_rule is not None:
                    leaf_indices_and_store[nodes_bind_store_map[node]].append(nodes_attr_bind_indices[node])
            bind_stores = (
                '({}, ({}, ))'.format(name, ', '.join(map(str, sorted(indices))))
                for name, indices in leaf_indices_and_store.items())
            rule_src_code.append('__kv_rule["bind_stores"] = ({}, )'.format(', '.join(bind_stores)))

            grouped_rules = ASTNodeRef.group_by_required_deps_ordered(rule_nodes)

            if rule['exec_rule'] and exec_rules_before_binding:
                rule_src_code.append('{}()'.format(rule['callback_name']))
                rule_src_code.append('')

            for group in grouped_rules:
                deps = group[0].depends
                if not deps:
                    for node in group:
                        assert not node.is_attribute
                        # we found a global or local variable, just add its name
                        node_value_var[node] = node.src
                else:
                    # add check if the last value(s) is not None
                    checked_deps = [dep for dep in deps if dep.depends]

                    var_names = []
                    for node in group:
                        if node.leaf_rule is None:
                            assert node.depends_on_me
                            var = temp_pool.borrow(node, len(node.depends_on_me))
                            var_names.append(var)
                            if checked_deps:
                                rule_src_code.append('{} = None'.format(var))

                    indent = 0
                    if checked_deps:
                        condition = []
                        for dep in checked_deps:
                            name = node_value_var[dep]
                            condition.append('{} is not None'.format(name))
                        condition = 'if {}:'.format(' and '.join(condition))
                        rule_src_code.append(condition)

                        indent = 4

                    bind_nodes = [node for node in group if node.leaf_rule is not None or node.rebind]
                    if bind_nodes:
                        assert len(deps) == 1
                        dep_name = node_value_var[deps[0]]
                        fbind_name = 'fbind_proxy' if deps[0].proxy else 'fbind'
                        rule_src_code.append('{}__kv__fbind = getattr({}, "{}", None)'.format(' ' * indent, dep_name, fbind_name))
                        rule_src_code.append('{}if __kv__fbind is not None:'.format(' ' * indent))
                        indent2 = indent + 4

                        for node in bind_nodes:
                            obj_attr = node.ref_node.attr
                            i = nodes_attr_bind_indices[node]
                            bind_store = nodes_bind_store_map[node]
                            func_name = node_bind_func_names[node]
                            bind = '__kv__fbind("{}", {})'.format(obj_attr, func_name)
                            if node.leaf_rule is None:
                                indices = '()'
                            else:
                                indices = '({}, )'.format(', '.join(map(
                                    str, sorted((
                                        nodes_attr_bind_indices[dep] for dep in
                                        leaves_deps[node]
                                        if dep.leaf_rule is not None or dep.rebind)))))
                            rule_src_code.append(
                                '{}{}[{}] = [{}, "{}", {}, {}, {}, {}]'.format(
                                    ' ' * indent2, bind_store, i, dep_name,
                                    obj_attr, func_name, bind, node.count,
                                    indices
                                ))
                            rule_src_code.append('')

                    i = 0
                    for node in group:
                        if node.leaf_rule is None:
                            var = var_names[i]
                            assignment = '{}{} = {}'.format(' ' * indent, var, generate_source(node).rstrip('\r\n'))
                            rule_src_code.append(assignment)
                            rule_src_code.append('')

                            node_value_var[node] = var
                            assert node not in original_ref_node
                            original_ref_node[node] = node.ref_node
                            node.set_ref_node(ast.Name(id=var, ctx=ast.Load()))
                            i += 1

                    for dep in node.depends:
                        if dep.depends:
                            for _ in group:
                                temp_pool.return_back(dep)

            if rule['exec_rule'] and not exec_rules_before_binding:
                rule_src_code.append('{}()'.format(rule['callback_name']))
                rule_src_code.append('')
            src_code.append(rule_src_code)

        var_clear = ', '.join(temp_pool.get_used_items())
        post_src_code = ['del __kv_rule, {}'.format(var_clear), '']

        for node, origin_node in original_ref_node.items():
            node.set_ref_node(origin_node)

        return pre_src_code, src_code, post_src_code

    def generate_bindings(self, ctx, ctx_name):
        bind_store_pool = self.binding_store_pool
        trees = self.compute_attr_bindings(ctx)
        trees_bind_store = [bind_store_pool.borrow_persistent() for _ in trees]
        nodes_bind_store_map = {
            node: trees_bind_store[i]
            for i, tree in enumerate(trees) for node in tree[0]}
        tree_bind_func_names, node_bind_func_names = self.get_bind_func_names(
            trees)
        trees_attr_bind_indices = self.get_trees_attr_bind_indices(ctx)
        nodes_attr_bind_indices = {}
        for item in trees_attr_bind_indices:
            nodes_attr_bind_indices.update(item)

        funcs = self.get_bind_funcs(
            ctx_name, trees, tree_bind_func_names, node_bind_func_names,
            trees_attr_bind_indices, trees_bind_store)
        bind_stores_size = []
        for name, tree_indices in zip(trees_bind_store, trees_attr_bind_indices):
            bind_stores_size.append((name, len(tree_indices)))

        pre_src, src, post_src = self.get_init_bindings(
            False, ctx_name, trees, ctx.rules, ctx.transformer.nodes_by_rule,
            node_bind_func_names, nodes_attr_bind_indices, nodes_bind_store_map,
            bind_stores_size)

        return funcs, pre_src, (item for rule in src for item in rule), post_src
