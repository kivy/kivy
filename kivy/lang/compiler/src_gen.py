import ast
from collections import deque, defaultdict
from itertools import chain

from kivy.lang.compiler.ast_parse import generate_source
from kivy.lang.compiler.utils import StringPool


class KVCompiler(object):

    ref = False

    rebind = []

    rebind_callback_pool = None

    leaf_callback_pool = None

    leaf_canvas_callback_pool = None

    leaf_clock_callback_pool = None

    binding_store_pool = None

    temp_var_pool = None

    kv_ctx_pool = None

    kv_rule_pool = None

    used_clock_rule = False

    used_canvas_rule = False

    def __init__(self, **kwargs):
        super(KVCompiler, self).__init__(**kwargs)
        self.rebind_callback_pool = StringPool(prefix='__kv_rebind_callback')
        self.leaf_callback_pool = StringPool(prefix='__kv_leaf_callback')
        self.leaf_canvas_callback_pool = StringPool(
            prefix='__kv_leaf_callback_canvas')
        self.leaf_clock_callback_pool = StringPool(
            prefix='__kv_leaf_callback_clock')
        self.binding_store_pool = StringPool(prefix='__kv_bind_store')
        self.temp_var_pool = StringPool(prefix='__kv_temp_val')
        self.kv_ctx_pool = StringPool(prefix='__kv_ctx')
        self.kv_rule_pool = StringPool(prefix='__kv_rule')

    def get_all_parent_nodes_of_leaves(self, trees):
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

    def get_bind_store_names(self, trees):
        pool = self.binding_store_pool
        trees_bind_store_names = [pool.borrow_persistent() for _ in trees]

        nodes_bind_store_names = {
            node: trees_bind_store_names[i]
            for i, tree in enumerate(trees) for node in tree[0]}
        return trees_bind_store_names, nodes_bind_store_names

    def update_names_of_bind_callbacks(
            self, bind_trees, gen_leaf_name, ctx):
        rebind_pool = self.rebind_callback_pool
        leaf_pool = self.leaf_callback_pool
        tree_bind_callback_names = {}
        node_bind_callback_names = {}

        for tree, bind_subtrees, subtrees_node_dep_idx in bind_trees:
            for subtree in bind_subtrees:
                for node in subtree.terminal_attrs:
                    if node.leaf_rule is None:
                        node_subtree = bind_subtrees[
                            subtrees_node_dep_idx[node]]
                        if node_subtree in tree_bind_callback_names:
                            # tree was already assigned rebind function
                            node_bind_callback_names[node] = \
                                tree_bind_callback_names[node_subtree]
                        else:
                            name = rebind_pool.borrow_persistent()
                            node_bind_callback_names[node] = \
                                tree_bind_callback_names[node_subtree] = name

        for rule, rule_nodes in zip(ctx.rules, ctx.transformer.nodes_by_rule):
            if gen_leaf_name:
                name = rule.callback_name = leaf_pool.borrow_persistent()
            else:
                name = rule.callback_name

            for node in rule_nodes:
                if node.leaf_rule is not None:
                    node_bind_callback_names[node] = name
        return tree_bind_callback_names, node_bind_callback_names

    def get_trees_bind_store_name_and_size(
            self, trees_bind_store_names, trees_bind_store_indices):
        bind_store_name_and_size = []
        for name, tree_indices in zip(
                trees_bind_store_names, trees_bind_store_indices):
            bind_store_name_and_size.append((name, len(tree_indices)))
        return bind_store_name_and_size

    def get_bind_store_indices(self, ctx):
        trees_bind_store_indices = []
        node_bind_store_indices = {}

        for tree in ctx.transformer.nodes_by_tree:
            bind_store_indices = {}
            for node in tree:
                if node.leaf_rule is not None or node.rebind:
                    bind_store_indices[node] = len(bind_store_indices)
            trees_bind_store_indices.append(bind_store_indices)

        for item in trees_bind_store_indices:
            node_bind_store_indices.update(item)
        return trees_bind_store_indices, node_bind_store_indices

    def gen_base_rebind_node_local_variable(
            self, src_code, subtree, node, temp_pool, nodes_use_count,
            bind_store_indices, bind_store_names, nodes_original_ref,
            nodes_temp_var_name):
        '''generates the source for getting the value from the bind store
        on which the rebind function was bound, and saves it as a local
        variable to be used by children nodes later in the rebind function.

        Should only be called on the nodes of a subtree and not its
        terminal nodes. Also, should only be called on a node of the subtree,
        if this this is at the root of the rebind function. That means
        we need to lookup the node's root value from the bind store.
        '''
        assert len(node.depends) == 1
        assert node.leaf_rule is None
        assert node.is_attribute
        dep = node.depends[0]
        # this is a root attr, just read its value into var.
        # node_use_count[node] and len(node.depends_on_me)
        # may be different because depends_on_me includes
        # all trees, even those in other rebind funcs, the
        # former only includes those used in this func

        # get temp variable for all deps that depend on this bind store value
        var = temp_pool.borrow(node, nodes_use_count[node])

        # a rebind function could be bound to multiple attr
        # rebind nodes (e.g. `(self.x + other.y).value`) so
        # we need to check if the rebind list has been init
        i = bind_store_indices[node]  # list index of rbind
        bind_store_name = bind_store_names[node]
        assert subtree.n_attr_deps >= 1

        indent = 4
        # only if the tree does have deps, otherwise, there's nothing to lookup
        # in the bind store as it's a global etc.
        if subtree.n_attr_deps > 1:
            src_code.append(
                '{}{} = None'.format(' ' * 4, var))
            # make sure the bind store is not None for the required value
            src_code.append(
                '{0}if {1}[{2}] is not None and {1}[{2}][0] is not None:'.
                format(' ' * 4, bind_store_name, i))
            indent = 8

        # dep_var = temp_pool.borrow(dep, node_use_count[dep] + 1)
        # node_value_var[dep] = dep_var
        # code output could be optimized, but then we'd need
        # to predict which subtrees this rebind func eats
        if dep not in nodes_original_ref:
            assert dep not in nodes_original_ref
            nodes_original_ref[dep] = dep.ref_node
            dep.set_ref_node(ast.Subscript(
                value=ast.Subscript(
                    value=ast.Name(id=bind_store_name, ctx=ast.Load()),
                    slice=ast.Index(value=ast.Num(n=i)), ctx=ast.Load()),
                slice=ast.Index(value=ast.Num(n=0)), ctx=ast.Load()))

        # save node to local variable
        assignment = '{}{} = {}'.format(
            ' ' * indent, var, generate_source(node).rstrip('\r\n'))
        src_code.append(assignment)
        src_code.append('')

        nodes_temp_var_name[node] = var
        assert node not in nodes_original_ref
        nodes_original_ref[node] = node.ref_node
        node.set_ref_node(ast.Name(id=var, ctx=ast.Load()))

    def gen_non_bind_node_local_variable(
            self, src_code, node, temp_pool, nodes_use_count, nodes_original_ref,
            nodes_temp_var_name, indent):
        '''Create the local temp variable when rebinding from a node, provided
        the node is neither a leaf nor a rebindable attribute. E.g. a
        simple addition operation, or even a attribute, but rebind is False
        for that attribute.
        '''
        assert node.leaf_rule is None
        assert node.depends_on_me
        assert not node.is_attribute or not node.rebind
        # to eval node so we can bind or whatever we need to
        # check if the last value(s) is not None for deps
        # but only those that are not locals/globals
        depends = [dep for dep in node.depends if dep.depends]

        # we hit internal rebind node, performs its
        # computation and store it in local var
        assert nodes_use_count[node] >= 1
        var = temp_pool.borrow(node, nodes_use_count[node])

        # if it has no deps, it won't be under a `if`
        # so no need to init variable
        if depends:
            src_code.append('{}{} = None'.format(' ' * indent, var))

            condition = []
            for dep in depends:
                name = nodes_temp_var_name[dep]
                condition.append('{} is not None'.format(name))
            condition = '{}if {}:'.format(' ' * indent, ' and '.join(condition))
            src_code.append(condition)

            indent += 4

        assignment = '{}{} = {}'.format(
            ' ' * indent, var, generate_source(node).rstrip('\r\n'))
        src_code.append(assignment)
        src_code.append('')

        nodes_temp_var_name[node] = var
        assert node not in nodes_original_ref
        nodes_original_ref[node] = node.ref_node
        node.set_ref_node(ast.Name(id=var, ctx=ast.Load()))

        # we are done with this dep here for this node
        for dep in depends:
            temp_pool.return_back(dep)

    def gen_unbind_subtree_bindings(
            self, src_code, subtree, bind_store_indices, bind_store):
        for node in subtree.terminal_attrs:
            # we don't need too check for double visits because
            # each tree contains *all* deps of terminal attrs
            i = bind_store_indices[node]

            src_code.append(
                '{}__kv_bind_ref = {}[{}]'.format(' ' * 4, bind_store, i))
            src_code.append('{}if __kv_bind_ref is not None:'.format(' ' * 4))
            src_code.append(
                '{}__kv_obj, __kv_attr, _, __kv_uid, _, _ = __kv_bind_ref'.
                format(' ' * 8))
            src_code.append(
                '{}if __kv_obj is not None and __kv_uid:'.format(' ' * 8))
            src_code.append(
                '{}__kv_obj.unbind_uid(__kv_attr, __kv_uid)'.format(' ' * 12))
            src_code.append('{}__kv_bind_ref[0] = None'.format(' ' * 12))
            src_code.append('')

    def gen_fbind_for_subtree_nodes_in_rebind_callback(
            self, src_code, nodes, indent, bind_store_indices,
            bind_store_names, dep_name):
        indent2 = indent + 4
        indent3 = indent + 8

        for node in nodes:
            obj_attr = node.ref_node.attr
            i = bind_store_indices[node]
            bind_store_name = bind_store_names[node]

            src_code.append(
                '{}__kv_bind_element = {}[{}]'.format(
                    ' ' * indent2, bind_store_name, i))
            src_code.append(
                '{}if __kv_bind_element is not None:'.format(' ' * indent2))
            bind = '__kv__fbind("{}", __kv_bind_element[2])'.format(obj_attr)
            src_code.append(
                '{}__kv_bind_element[0] = {}'.format(' ' * indent3, dep_name))
            src_code.append(
                '{}__kv_bind_element[3] = {}'.format(' ' * indent3, bind))
            src_code.append('')

    def gen_fbind_for_subtree_nodes_for_initial_bindings(
            self, src_code, nodes, indent, bind_store_indices,
            bind_store_names, dep_name, node_bind_callback_names,
            parent_nodes_of_leaves):
        indent2 = indent + 4

        for node in nodes:
            obj_attr = node.ref_node.attr
            i = bind_store_indices[node]
            bind_store_name = bind_store_names[node]

            callback_name = node_bind_callback_names[node]
            bind = '__kv__fbind("{}", {})'.format(obj_attr, callback_name)
            if node.leaf_rule is None:
                indices = '()'
            else:
                indices = '({}, )'.format(', '.join(
                    map(str, sorted((
                        bind_store_indices[dep]
                        for dep in parent_nodes_of_leaves[node]
                        if dep.leaf_rule is not None or dep.rebind)))
                ))

            src_code.append(
                '{}{}[{}] = [{}, "{}", {}, {}, {}, {}]'.format(
                    ' ' * indent2, bind_store_name, i, dep_name,
                    obj_attr, callback_name, bind, node.count,
                    indices
                ))
            src_code.append('')

    def gen_subtree_bindings(
            self, src_code, subtree, temp_pool, nodes_use_count,
            bind_store_indices, bind_store_names, nodes_original_ref,
            nodes_temp_var_name, node_bind_callback_names,
            init_bindings, parent_nodes_of_leaves=None):
        '''Generates the code that binds all the callbacks associated with this
        subtree.
        '''
        terminal_attrs_by_dep = defaultdict(list)
        # terminal nodes are attributes so by definition they can and must have
        # exactly one dep.
        for node in subtree.terminal_attrs:
            assert len(node.depends) == 1
            terminal_attrs_by_dep[node.depends[0]].append(node)

        for dep, nodes in terminal_attrs_by_dep.items():
            # create forward temp variables for the nodes, if used later
            for node in nodes:
                assert node.leaf_rule is not None or node.rebind
                if node.leaf_rule is None:
                    nodes_temp_var_name[node] = \
                        temp_pool.borrow(node, nodes_use_count[node])

            indent = 0 if init_bindings else 4
            dep_name = nodes_temp_var_name[dep]
            # check if the deps are not None
            if dep.depends:
                # no need to init if not under an if
                for node in nodes:
                    if node.leaf_rule is None:
                        src_code.append(
                            '{}{} = None'.
                            format(' ' * indent, nodes_temp_var_name[node]))

                src_code.append(
                    '{}if {} is not None:'.format(' ' * indent, dep_name))
                indent += 4

            # do we need to create a proxy for the callback?
            fbind_name = 'fbind_proxy' if dep.proxy else 'fbind'
            src_code.append('{}__kv__fbind = getattr({}, "{}", None)'.
                            format(' ' * indent, dep_name, fbind_name))
            src_code.append(
                '{}if __kv__fbind is not None:'.format(' ' * indent))

            if init_bindings:
                self.gen_fbind_for_subtree_nodes_for_initial_bindings(
                    src_code, nodes, indent, bind_store_indices,
                    bind_store_names, dep_name, node_bind_callback_names,
                    parent_nodes_of_leaves)
            else:
                self.gen_fbind_for_subtree_nodes_in_rebind_callback(
                    src_code, nodes, indent, bind_store_indices,
                    bind_store_names, dep_name)

            # create the values of the nodes for use later, using the temp vars
            for node in nodes:
                if node.leaf_rule is None:
                    var = nodes_temp_var_name[node]
                    assignment = '{}{} = {}'.format(
                        ' ' * indent, var, generate_source(node).rstrip('\r\n'))
                    src_code.append(assignment)
                    src_code.append('')

                    assert node not in nodes_original_ref
                    nodes_original_ref[node] = node.ref_node
                    node.set_ref_node(ast.Name(id=var, ctx=ast.Load()))

            if dep.depends:
                for _ in nodes:
                    temp_pool.return_back(dep)

    def gen_subtree_and_children_rebind_callback(
            self, src_code, subtree, nodes_use_count, bind_store_indices,
            bind_store_names, tree_bind_callback_names,
            node_bind_callback_names):
        queue = deque([subtree])
        # we can have a subtree being a child
        # of multiple different subtrees. E.g. self.a.b + self.a.c
        subtrees_visited = set()
        # we keep track of all attrs we visit in the subtree. Because
        # deps are always explored before the children, if we encounter
        # a attr dep that has not been visited, it means its at the root
        # level in the rebind function stored in the rebind list
        terminal_nodes_visited = set()
        nodes_visited = set()
        nodes_temp_var_name = {}
        nodes_original_ref = {}
        capturing_vars = set()

        temp_pool = self.temp_var_pool
        func_def_i = len(src_code)
        src_code.append(None)

        assert subtree.terminal_attrs
        # it's the same for all nodes in a tree
        bind_store = bind_store_names[subtree.terminal_attrs[0]]
        capturing_vars.add(bind_store)

        leaf_callbacks = defaultdict(set)

        while queue:
            current_subtree = queue.popleft()
            if current_subtree in subtrees_visited:
                continue
            subtrees_visited.add(current_subtree)

            queue.extend(current_subtree.depends_on_me)
            terminal_nodes_visited.update(current_subtree.terminal_attrs)

            for node in current_subtree.nodes:
                if node in nodes_visited:
                    continue
                nodes_visited.add(node)

                # we always store stuff in local variables - it's faster
                if not node.depends:
                    assert not node.is_attribute
                    # we found a global or local variable - add its name
                    src = nodes_temp_var_name[node] = node.src
                    if isinstance(node.ref_node, ast.Name):
                        capturing_vars.add(src)
                elif node.rebind and node not in terminal_nodes_visited:
                    self.gen_base_rebind_node_local_variable(
                        src_code, current_subtree, node, temp_pool,
                        nodes_use_count, bind_store_indices,
                        bind_store_names, nodes_original_ref,
                        nodes_temp_var_name)
                elif node.rebind:
                    assert node in nodes_temp_var_name, 'should already ' \
                        'have been created in terminal node stage'
                else:
                    self.gen_non_bind_node_local_variable(
                        src_code, node, temp_pool, nodes_use_count,
                        nodes_original_ref, nodes_temp_var_name, indent=4)

            # unbind
            self.gen_unbind_subtree_bindings(
                src_code, current_subtree,
                bind_store_indices, bind_store)

            for node in current_subtree.terminal_attrs:
                if node.leaf_rule is not None:
                    i = bind_store_indices[node]
                    bind_store_name = bind_store_names[node]
                    f_location = '{}[{}]'.format(bind_store_name, i)
                    leaf_callbacks[
                        node_bind_callback_names[node]].add(f_location)

            self.gen_subtree_bindings(
                src_code, current_subtree, temp_pool,
                nodes_use_count, bind_store_indices, bind_store_names,
                nodes_original_ref, nodes_temp_var_name,
                node_bind_callback_names, init_bindings=False)

        for name, locations in leaf_callbacks.items():
            src_code.append(
                '{}__kv_callback = {}'.format(' ' * 4, ' or '.join(locations)))
            src_code.append('{}if __kv_callback is not None:'.format(' ' * 4))
            src_code.append('{}__kv_callback[2]()'.format(' ' * 8))
            src_code.append('')
        for node, origin_node in nodes_original_ref.items():
            node.set_ref_node(origin_node)

        s = ', '.join('{0}={0}'.format(item) for item in sorted(capturing_vars))
        s = ', {}'.format(s) if s else ''
        func_def = 'def {}(*__kv_largs{}):'.format(
            tree_bind_callback_names[subtree], s)
        src_code[func_def_i] = func_def

    def gen_rebind_callbacks(
            self, ctx_name, trees, tree_bind_callback_names,
            node_bind_callback_names, trees_bind_store_indices,
            trees_bind_store_names, nodes_bind_store_names,
            trees_bind_store_name_and_size):
        src_code = []

        for name, n in trees_bind_store_name_and_size:
            src_code.append('{} = [None, ] * {}'.format(name, n))
        src_code.append('')

        s = ', '.join(item[0] for item in trees_bind_store_name_and_size)
        if s:
            src_code.append(
                '{}.bind_stores_by_tree = ({}, )'.format(ctx_name, s))
        else:
            src_code.append('{}.bind_stores_by_tree = ()'.format(ctx_name))
        src_code.append('')

        for tree_bind_store_indices, bind_store, (
                    tree, bind_subtrees, subtrees_node_dep_idx) in zip(
                trees_bind_store_indices, trees_bind_store_names, trees):
            # count the number of places each node is used. E.g. in
            # `self.x + self.y`, `self` is used twice. Keep in mind that nodes
            # are unique
            nodes_use_count = defaultdict(int)
            for node in tree:
                for dep in node.depends:
                    assert dep.leaf_rule is None, 'a dep cannot be a leaf, duh'
                    nodes_use_count[dep] += 1

            for subtree in bind_subtrees:
                # we create a rebind func for each subtree that roots in attr
                if not subtree.n_attr_deps:
                    # It means that all the deps are not attributes, meaning
                    # thet are e.g. variables etc, so that we never create a
                    # rebind func for them
                    # see further down why len(node.depends_on_me) is correct
                    for node in subtree.nodes:
                        nodes_use_count[node] -= len(node.depends_on_me)
                    continue

                func_src_code = []
                self.gen_subtree_and_children_rebind_callback(
                    func_src_code, subtree, nodes_use_count,
                    tree_bind_store_indices, nodes_bind_store_names,
                    tree_bind_callback_names, node_bind_callback_names)

                # remove all that depend on the node because either the dep
                # is in the same subtree, or it's in the terminal of the
                # subtree. In the latter case, binding and attr eval happens
                # in this subtree iteration, so this node won't be used again
                for node in subtree.nodes:
                    nodes_use_count[node] -= len(node.depends_on_me)
                src_code.extend(func_src_code)

            for node, count in nodes_use_count.items():
                assert not count, '{}, {} should be zero'.format(node, count)

        s = ', '.join(
            tree_bind_callback_names[subtree]
            for _, subtrees, _ in trees for subtree in subtrees
            if subtree.n_attr_deps)
        comma = ', ' if s else ''
        src_code.append('{}.rebind_functions = ({}{})'.format(
            ctx_name, s, comma))
        src_code.append('')
        return src_code

    def gen_leaf_rules(
            self, ctx, ctx_name, create_rules, nodes_bind_store_names,
            node_bind_store_indices):
        rule_creation = []
        rule_finalization = []
        kv_rule_pool = self.kv_rule_pool

        for rule_idx, (rule, rule_nodes) in enumerate(
                zip(ctx.rules, ctx.transformer.nodes_by_rule)):
            name = kv_rule_pool.borrow_persistent()
            if create_rules:
                if rule.delay is None:
                    delay_arg = 'None'
                elif rule.delay == 'canvas':
                    delay_arg = '"canvas"'
                else:
                    delay_arg = '{}'.format(rule.delay)

                rule_creation.append('{} = __KVRule()'.format(name))
                rule_creation.append('{}.delay = {}'.format(name, delay_arg))
                if rule.name:
                    rule_creation.append(
                        '{}.name = "{}"'.format(name, rule.name))
                rule_creation.append('{}.add_rule({})'.format(ctx_name, name))

                if rule.with_var_name_ast is not None:
                    rule.with_var_name_ast.id = name

                if rule_nodes:
                    rule_finalization.append(
                        '{}.callback = {}'.format(name, rule.callback_name))
            else:
                rule_creation.append(
                    '{} = {}.rules[{}]'.format(name, ctx_name, rule_idx))

            leaf_indices_by_store_names = defaultdict(list)
            for node in rule_nodes:
                if node.leaf_rule is not None:
                    leaf_indices_by_store_names[
                        nodes_bind_store_names[node]].append(
                        node_bind_store_indices[node])

            bind_stores = (
                '({}, ({}, ))'.format(
                    name, ', '.join(map(str, sorted(indices))))
                for name, indices in leaf_indices_by_store_names.items())

            if rule_nodes:
                rule_finalization.append(
                    '{}.bind_stores = ({}, )'.
                    format(name, ', '.join(bind_stores)))

            rule_creation.append('')
            rule_finalization.append('')

        return rule_creation, rule_finalization

    def gen_leaf_callbacks(self, ctx):
        src_code = []
        canvas_pool = self.leaf_canvas_callback_pool
        clock_pool = self.leaf_clock_callback_pool
        for rule_idx, (rule, rule_nodes) in enumerate(
                zip(ctx.rules, ctx.transformer.nodes_by_rule)):
            if not rule_nodes:
                continue

            name = None
            if rule.with_var_name_ast is not None:
                name = rule.with_var_name_ast.id
                rule.captures.add(name)

            delay = rule.delay
            callback_name = rule.callback_name
            if delay is None:
                proxy_callback_name = callback_name
            elif delay == 'canvas':
                proxy_callback_name = canvas_pool.borrow_persistent()
                self.used_canvas_rule = True
            else:
                proxy_callback_name = clock_pool.borrow_persistent()
                self.used_clock_rule = True

            s = ', '.join(
                '{0}={0}'.format(name) for name in sorted(rule.captures))
            s = ', {}'.format(s) if s else ''
            func_def = 'def {}(*__kv_largs{}):'.format(proxy_callback_name, s)

            src_code.append(func_def)
            if name is not None:
                src_code.append('{}{}.largs = __kv_largs'.format(' ' * 4, name))

            for line in rule.src.splitlines():
                src_code.append('{}{}'.format(' ' * 4, line))
            src_code.append('')

            if delay is None:
                continue
            elif delay == 'canvas':
                func_def = 'def {}(*__kv_largs, __kv_canvas_item=[{}, ' \
                    'None, None]):'.format(callback_name, proxy_callback_name)
                body = '{}__kv_add_graphics_callback(__kv_canvas_item, ' \
                    '__kv_largs)'.format(' ' * 4)
                src_code.append(func_def)
                src_code.append(body)
                src_code.append('')
            else:
                line = '{} = __kv_Clock.create_trigger({}, {})'.\
                    format(callback_name, proxy_callback_name, delay)
                src_code.append(line)
                src_code.append('')

        return src_code

    def gen_initial_bindings_for_tree(
            self, src_code, tree, subtrees, bind_store_indices,
            bind_store_names, node_bind_callback_names, parent_nodes_of_leaves):
        # we keep track of all attrs we visit in the subtree. Because
        # deps are always explored before the children, if we encounter
        # a attr dep that has not been visited, it means its at the root
        # level in the rebind function stored in the rebind list
        terminal_nodes_visited = set()
        nodes_visited = set()
        nodes_temp_var_name = {}
        nodes_original_ref = {}

        temp_pool = self.temp_var_pool
        # it's the same for all nodes in a tree
        assert subtrees

        nodes_use_count = defaultdict(int)
        for node in tree:
            for dep in node.depends:
                assert dep.leaf_rule is None, 'a dep cannot be a leaf, duh'
                nodes_use_count[dep] += 1

        for subtree in subtrees:
            assert subtree.terminal_attrs
            terminal_nodes_visited.update(subtree.terminal_attrs)

            for node in subtree.nodes:
                if node in nodes_visited:
                    continue
                nodes_visited.add(node)

                # we always store stuff in local variables - it's faster
                if not node.depends:
                    assert not node.is_attribute
                    # we found a global or local variable - add its name
                    nodes_temp_var_name[node] = node.src
                elif node.rebind:
                    assert node in terminal_nodes_visited
                    assert node in nodes_temp_var_name, 'should already ' \
                        'have been created in terminal node stage'
                else:
                    self.gen_non_bind_node_local_variable(
                        src_code, node, temp_pool, nodes_use_count,
                        nodes_original_ref, nodes_temp_var_name, indent=0)

            self.gen_subtree_bindings(
                src_code, subtree, temp_pool,
                nodes_use_count, bind_store_indices, bind_store_names,
                nodes_original_ref, nodes_temp_var_name,
                node_bind_callback_names, init_bindings=True,
                parent_nodes_of_leaves=parent_nodes_of_leaves)

            for node in subtree.nodes:
                nodes_use_count[node] -= len(node.depends_on_me)

        for node, count in nodes_use_count.items():
            assert not count, '{}, {} should be zero'.format(node, count)

        for node, origin_node in nodes_original_ref.items():
            node.set_ref_node(origin_node)

    def gen_initial_bindings(
            self, ctx, trees, node_bind_callback_names,
            trees_bind_store_indices, nodes_bind_store_names,
            exec_rules_after_binding):
        parent_nodes_of_leaves = self.get_all_parent_nodes_of_leaves(trees)
        src_code = []

        for tree_bind_store_indices, (tree, bind_subtrees, _) in zip(
                trees_bind_store_indices, trees):

            self.gen_initial_bindings_for_tree(
                src_code, tree, bind_subtrees,
                tree_bind_store_indices, nodes_bind_store_names,
                node_bind_callback_names, parent_nodes_of_leaves)

        if exec_rules_after_binding:
            for rule in ctx.rules:
                src_code.append('{}()'.format(rule.callback_name))
        src_code.append('')

        return src_code

    def gen_temp_vars_creation_deletion(self):
        # we must create the variables at the root indentation so that we can
        # delete it at the root indentation at the end, in case some of the
        # variables are only actually used under conditionals, so we make sure
        # it always exists.
        variables = list(sorted(chain(
            self.temp_var_pool.get_used_items(),
            self.kv_rule_pool.get_all_items())))

        if variables:
            var_create = ' = '.join(variables)
            var_clear = ', '.join(variables)
            return ['{} = None'.format(var_create), ''], [
                'del {}'.format(var_clear), '']
        return [], []

    def generate_bindings(
            self, ctx, ctx_name, create_rules, exec_rules_after_binding):
        if not ctx_name:
            ctx_name = self.kv_ctx_pool.borrow_persistent()

        trees = self.compute_attr_bindings(ctx)

        trees_bind_store_names, nodes_bind_store_names = \
            self.get_bind_store_names(trees)
        tree_bind_callback_names, node_bind_callback_names = \
            self.update_names_of_bind_callbacks(trees, create_rules, ctx)
        trees_bind_store_indices, node_bind_store_indices = \
            self.get_bind_store_indices(ctx)
        trees_bind_store_name_and_size = \
            self.get_trees_bind_store_name_and_size(
                trees_bind_store_names, trees_bind_store_indices)

        funcs = self.gen_rebind_callbacks(
            ctx_name, trees, tree_bind_callback_names, node_bind_callback_names,
            trees_bind_store_indices, trees_bind_store_names,
            nodes_bind_store_names, trees_bind_store_name_and_size)

        rule_creation, rule_finalization = self.gen_leaf_rules(
            ctx, ctx_name, create_rules, nodes_bind_store_names,
            node_bind_store_indices)

        if create_rules:
            res = self.gen_leaf_callbacks(ctx)
            funcs.extend(res)

        res = self.gen_initial_bindings(
            ctx, trees, node_bind_callback_names,
            trees_bind_store_indices, nodes_bind_store_names,
            exec_rules_after_binding)
        funcs.extend(res)

        return ctx_name, funcs, rule_creation, rule_finalization
