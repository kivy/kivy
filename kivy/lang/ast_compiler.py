import inspect
import ast
import textwrap
from collections import deque, defaultdict
import astor
from astor.code_gen import SourceGenerator
from astor.source_repr import split_lines


class StringPool(object):

    pool = []

    prefix = 'var'

    tokens = {}

    def __init__(self, prefix='var'):
        super(StringPool, self).__init__()
        self.pool = []
        self.prefix = prefix
        self.tokens = {}

    def borrow(self, token, count=1):
        if token in self.tokens:
            item = self.tokens[token]
            item[2] += count
            return item[0]

        name = None
        for i, name in enumerate(self.pool):
            if name is not None:
                break

        if name is None:
            name = '{}_{}'.format(self.prefix, len(self.pool))
            i = len(self.pool)
            self.pool.append(None)
        else:
            self.pool[i] = None

        self.tokens[token] = [name, i, count]
        return name

    def borrow_persistent(self):
        return self.borrow(object())

    def return_back(self, token):
        item = self.tokens[token]
        if item[2] == 1:  # last usage
            del self.tokens[token]
            self.pool[item[1]] = item[0]
            return 0
        else:
            item[2] -= 1
            if item[2] < 0:
                raise Exception('{} is negative'.format(token))
            return item[2]

    def get_used_items(self):
        return self.pool


class KVCompiler(object):

    ref = False

    rebind = []

    rebind_func_pool = None

    binding_store_pool = None

    def __init__(self, **kwargs):
        super(KVCompiler, self).__init__(**kwargs)
        self.rebind_func_pool = StringPool(prefix='__kv_rebind_callback')
        self.binding_store_pool = StringPool(prefix='__kv_bind_store')

    def compute_attr_bindings(self, ctx):
        trees_attr_subtree = []
        for tree in ctx.transformer.nodes_by_tree:
            visited = set()
            attr_subtree = []
            term_subtree_indices = {}
            for node in tree:
                if node.leaf_rule is not None or node in visited:
                    continue
                subtree = node.get_attribute_subtree()
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
                if node.is_attribute and node not in visited:
                    subtree = attr_subtree[term_subtree_indices[node]]
                    visited.update(subtree.terminal_attrs)
                    for dep in subtree.nodes:
                        if dep.is_attribute:
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
                        node_bind_func_names[node] = 'cheese'  # node.leaf_rule
        return tree_bind_func_names, node_bind_func_names

    def get_trees_attr_bind_indices(self, ctx):
        trees_bind_indices = []
        for tree in ctx.transformer.nodes_by_tree:
            attr_list_indices = {}
            for node in tree:
                if node.is_attribute:
                    attr_list_indices[node] = len(attr_list_indices)
            trees_bind_indices.append(attr_list_indices)
        return trees_bind_indices

    def get_bind_funcs(
            self, trees, tree_bind_func_names, node_bind_func_names,
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
                        elif node.is_attribute and node not in attrs_visited:
                            assert len(node.depends) == 1
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
                        elif node.is_attribute:
                            assert node in node_value_var, 'should already ' \
                                'have been created in terminal node stage'
                        else:
                            assert node.leaf_rule is None
                            assert node.depends_on_me
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

                        func_src_code.append('{}if {}[{}] is not None:'.format(' ' * 4, bind_store, i))
                        func_src_code.append('{}__kv_bind_ref = __kv_obj, __kv_attr, __kv_uid = {}[{}]'.format(' ' * 8, bind_store, i))
                        func_src_code.append('{}if __kv_obj is not None and __kv_uid:'.format(' ' * 8))
                        func_src_code.append('{}__kv_obj.unbind_uid(__kv_attr, __kv_uid)'.format(' ' * 12))
                        func_src_code.append('{}__kv_bind_ref[0] = None'.format(' ' * 12))
                        func_src_code.append('')

                    terminal_attrs_by_dep = defaultdict(list)
                    for node in current_subtree.terminal_attrs:
                        assert len(node.depends) == 1
                        terminal_attrs_by_dep[node.depends[0]].append(node)

                    for dep, nodes in terminal_attrs_by_dep.items():
                        for node in nodes:
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

                        func_src_code.append('{}__kv__fbind = getattr({}, "fbind", None)'.format(' ' * indent, dep_name))
                        func_src_code.append('{}if __kv__fbind is not None:'.format(' ' * indent))
                        indent2 = indent + 4
                        indent3 = indent + 8

                        for node in nodes:
                            obj_attr = node.ref_node.attr
                            i = attr_bind_indices[node]
                            func_src_code.append('{}if {}[{}] is not None:'.format(' ' * indent2, bind_store, i))
                            bind = '__kv__fbind("{}", {})'.format(obj_attr, node_bind_func_names[node])
                            func_src_code.append('{}{}[{}] = [{}, "{}", {}]'.format(' ' * indent3, bind_store, i, dep_name, obj_attr, bind))
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

                # remove all that depend on the node because either the dep
                # is in the same subtree, or it's in the terminal of the
                # subtree. In the latter case, binding and attr eval happens
                # in this subtree iteration, so this node won't be used again
                for node in subtree.nodes:
                    node_use_count[node] -= len(node.depends_on_me)
                processed_subtrees.add(current_subtree)
                for node, origin_node in node_original_ref.items():
                    node.set_ref_node(origin_node)
                func_src_code.append('')
                src_code.extend(func_src_code)

        for node, count in node_use_count.items():
            assert not count, '{}, {} should be zero'.format(node, count)
        return src_code

    def get_init_bindings(self, rules_nodes, node_bind_func_names,
            nodes_attr_bind_indices, nodes_bind_store_map, bind_stores_size):
        temp_pool = StringPool(prefix='__kv_temp_val')
        original_ref_node = {}
        node_value_var = {}

        pre_src_code = []
        for name, n in bind_stores_size:
            pre_src_code.append('{} = [None, ] * {}'.format(name, n))
        pre_src_code.append('')

        src_code = []
        for rule_nodes in rules_nodes:
            rule_src_code = []
            for group in ASTNodeRef.group_by_required_deps_ordered(rule_nodes):
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

                    rebind_nodes = [node for node in group if node.is_attribute]
                    if rebind_nodes:
                        assert len(deps) == 1
                        dep_name = node_value_var[node.depends[0]]
                        rule_src_code.append('{}__kv__fbind = getattr({}, "fbind", None)'.format(' ' * indent, dep_name))
                        rule_src_code.append('{}if __kv__fbind is not None:'.format(' ' * indent))
                        indent2 = indent + 4

                        for node in rebind_nodes:
                            obj_attr = node.ref_node.attr
                            i = nodes_attr_bind_indices[node]
                            bind_store = nodes_bind_store_map[node]
                            bind = '__kv__fbind("{}", {})'.format(obj_attr, node_bind_func_names[node])
                            rule_src_code.append('{}{}[{}] = [{}, "{}", {}]'.format(' ' * indent2, bind_store, i, dep_name, obj_attr, bind))
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
            src_code.append(rule_src_code)

        var_clear = ', '.join(temp_pool.get_used_items())
        post_src_code = ['del {}'.format(var_clear)]

        for node, origin_node in original_ref_node.items():
            node.set_ref_node(origin_node)

        return pre_src_code, src_code, post_src_code

    def exec_bindings(self, ctx, local_vars, globals_vars):
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
        rules_nodes = ctx.transformer.nodes_by_rule
        funcs = self.get_bind_funcs(
            trees, tree_bind_func_names, node_bind_func_names,
            trees_attr_bind_indices, trees_bind_store)
        bind_stores_size = []
        for name, tree_indices in zip(trees_bind_store, trees_attr_bind_indices):
            bind_stores_size.append((name, len(tree_indices)))
        print('\n'.join(funcs))
        pre_src, src, post_src = self.get_init_bindings(
            rules_nodes, node_bind_func_names,
            nodes_attr_bind_indices, nodes_bind_store_map, bind_stores_size)
        print('\n'.join(pre_src))
        for rule in src:
            print('\n'.join(rule))
        print('\n'.join(post_src))


class KVCtx(object):

    bind_list = []

    callback = None

    transformer = None

    def __init__(self, **kwargs):
        super(KVCtx, self).__init__(**kwargs)
        self.bind_list = []
        self.transformer = ParseKVBindTransformer()

    def __call__(self, *args, **kwargs):
        self.add_rule(*args, **kwargs)
        return self

    def add_rule(self, callback, binds):
        self.callback = callback
        if isinstance(binds, str):
            nodes = [ast.parse(binds)]
        else:
            nodes = [ast.parse(bind) for bind in binds]

        self.transformer.update_tree(nodes, self)


class BindSubTreeNode(object):

    nodes = []

    terminal_attrs = []

    n_attr_deps = 0

    depends_on_me = []

    terminates_with_leafs_only = True

    def __init__(self, nodes, terminal_attrs):
        super(BindSubTreeNode, self).__init__()
        self.nodes = nodes
        self.terminal_attrs = terminal_attrs
        self.depends_on_me = []

    def __repr__(self):
        return 'Nodes: {' + '}, {'.join(map(repr, self.nodes)) + \
            '}\nTerminal nodes: {' + \
            '}, {'.join(map(repr, self.terminal_attrs)) + '}'


class ASTNodeRef(ast.AST):

    original_node = None

    ref_node = None

    src = ''
    '''
    Not set for final attribute nodes because we never evaluate the node.
    '''

    is_attribute = False

    depends_on_me = []

    depends = []

    count = 0

    leaf_rule = None
    # only attrs can be leaf

    my_tree = []

    code_frag = []
    '''Can be used for anything.
    '''

    def __init__(self, is_attribute):
        super(ASTNodeRef, self).__init__()
        self.is_attribute = is_attribute
        self.depends_on_me = []
        self.depends = []

    def get_attribute_subtree(self):
        # these trees have no cycles, and are directed, even if you remove their
        # directionality, there could be cycles.
        # Algo: start with the node add its deps_on_me to the stack, then mark
        # it saying that we already explored all its dependencies. Working
        # through the stack, for each node we adds its depends_on_me (i.e. its
        # children) and its depends (i.e. parents) to the stack. Children are
        # only added to the stack if they are not attr, otherwise it's added as
        # terminals. parents are only added if not visited or if the node is a
        # attr we don't add parents at all. A node whose children are visited
        # or has none is removed from the stack.
        assert self.depends_on_me, 'we must end with a attr node and this ' \
            'should not have been called on a leaf node.'
        visited = set([self])
        forward_queue = deque()
        backward_stack = deque()
        terminal_nodes = []
        explored = [self]

        for dep in self.depends_on_me:
            if dep.is_attribute:
                terminal_nodes.append(dep)
            else:
                forward_queue.append(dep)

        while forward_queue:
            assert not backward_stack
            # there could be some visited nodes, but we leave them in case
            # their children has not been visited. Visited nodes will be
            # filtered out in backward_stack anyway
            backward_stack.extend(forward_queue)
            forward_queue.clear()
            for item in backward_stack:
                for dep in item.depends_on_me:
                    if dep.is_attribute:
                        # a atrr has only a single parent node () so it could
                        # not have been visited previously if we are its dep
                        assert dep not in visited
                        terminal_nodes.append(dep)
                    else:
                        # It seems possible that a node could be visited as a
                        # parent as well as a child, but it will be filtered
                        # out in the backward_stack
                        forward_queue.append(dep)

            while backward_stack:
                node = backward_stack[0]
                if node in visited:
                    backward_stack.popleft()
                    continue
                all_done = True

                for dep in node.depends:
                    if dep not in visited:
                        if dep.is_attribute:
                            explored.append(dep)
                            visited.add(dep)
                        else:
                            all_done = False
                            backward_stack.appendleft(dep)

                if all_done:
                    explored.append(node)
                    visited.add(node)
                    backward_stack.popleft()

        return BindSubTreeNode(explored, terminal_nodes)

    def set_ref_node(self, node):
        self._attributes = node._attributes
        self._fields = node._fields
        self.ref_node = node

    @staticmethod
    def group_by_required_deps_ordered(nodes):
        grouped_nodes = []
        deps_idx = {}

        for node in nodes:
            key = tuple(node.depends)
            if key in deps_idx:
                grouped_nodes[deps_idx[key]].append(node)
            else:
                deps_idx[key] = len(grouped_nodes)
                grouped_nodes.append([node])

        return grouped_nodes

    def __repr__(self):
        return '{} - is_attr: {}, count: {}, ' \
            'leaf: {}, depends_on_me({}): {}, , depends({}): {}'.\
            format(
                self.src, self.is_attribute, self.count,
                self.leaf_rule is not None, len(self.depends_on_me),
                [node.src for node in self.depends_on_me], len(self.depends),
                [node.src for node in self.depends])


class RefSourceGenerator(SourceGenerator):

    def visit_ASTNodeRef(self, node, *largs, **kwargs):
        return self.visit(node.ref_node, *largs, **kwargs)


def generate_source(node):
    generator = RefSourceGenerator(indent_with=' ' * 4)
    generator.visit(node)

    generator.result.append('\n')
    if set(generator.result[0]) == set('\n'):
        generator.result[0] = ''

    return ''.join(split_lines(generator.result, maxline=2 ** 32 - 1))


class ParseKVBindTransformer(ast.NodeTransformer):

    src_node_map = {}

    under_attr = False

    nodes_by_rule = []

    nodes_by_tree = []

    src_nodes = []

    current_processing_node = None

    visited = set()

    current_rule = None

    def __init__(self):
        super(ParseKVBindTransformer, self).__init__()
        self.src_node_map = {}
        self.nodes_by_tree = []
        self.nodes_by_rule = []
        self.visited = set()

    def update_tree(self, nodes, rule):
        self.current_rule = rule
        self.src_nodes = src_nodes = []
        self.nodes_by_rule.append(src_nodes)
        for node in nodes:
            self.visit(node)

    def generic_visit(self, node, is_attribute=False, is_final_attribute=False):
        if node in self.visited:
            return node
        self.visited.add(node)

        if self.under_attr and isinstance(node, ast.expr):
            current_processing_node = self.current_processing_node
            new_node = True
            self.current_processing_node = ret_node = ASTNodeRef(
                is_attribute)
            node = super(ParseKVBindTransformer, self).generic_visit(node)
            self.current_processing_node = current_processing_node
            if is_final_attribute:
                # final nodes are not evaluated anywhere so we don't need
                # their source. Also, they are all unique so we don't
                # de-duplicate
                assert is_attribute
                assert current_processing_node is None
                ret_node.set_ref_node(node)
                ret_node.count += 1
                ret_node.leaf_rule = self.current_rule
                self.src_nodes.append(ret_node)
                for dep in ret_node.depends:
                    dep.depends_on_me.append(ret_node)
            else:
                src = generate_source(node).rstrip('\r\n')
                # either we already saw a tree with a unique root path to this node
                if src in self.src_node_map:
                    # if we did, replace the re-occurrence with the node of the
                    # first occurrence. Abandon ret_node, everything there is
                    # redundant
                    new_node = False
                    ret_node = self.src_node_map[src]
                else:
                    # if we didn't, create a node representing this path
                    ret_node.set_ref_node(node)
                    ret_node.src = src
                    self.src_node_map[src] = ret_node
                    self.src_nodes.append(ret_node)
                    for dep in ret_node.depends:
                        dep.depends_on_me.append(ret_node)

                ret_node.count += 1
                # if it's None, we hit the final (root) expr of the tree
                if ret_node not in current_processing_node.depends:
                    current_processing_node.depends.append(ret_node)

            if new_node:
                if not ret_node.depends:
                    tree = ret_node.my_tree = [[ret_node], [None]]
                    tree[1][0] = tree
                    self.nodes_by_tree.append(tree[0])
                else:
                    ret_node.my_tree = tree = ret_node.depends[0].my_tree
                    for dep in ret_node.depends[1:]:
                        if dep.my_tree[0] is tree[0]:
                            continue

                        self.nodes_by_tree.remove(dep.my_tree[0])
                        tree[0].extend(dep.my_tree[0])
                        tree[1].extend(dep.my_tree[1])
                        for item in dep.my_tree[1]:
                            item[0] = tree[0]
                    tree[0].append(ret_node)
        else:
            ret_node = super(ParseKVBindTransformer, self).generic_visit(node)
        return ret_node

    def visit_Attribute(self, node):
        if self.under_attr:
            return self.generic_visit(node, is_attribute=True)

        self.under_attr = True
        node = self.generic_visit(
            node, is_attribute=True, is_final_attribute=True)
        self.under_attr = False
        return node

    # def visit_Name(self, node):
    #     return super(ParseKVBindTransformer, self).generic_visit(node)

    # def visit_Num(self, node):
    #     return super(ParseKVBindTransformer, self).generic_visit(node)
    #
    # def visit_Bytes(self, node):
    #     return super(ParseKVBindTransformer, self).generic_visit(node)
    #
    # def visit_NameConstant(self, node):
    #     return super(ParseKVBindTransformer, self).generic_visit(node)
    #
    # def visit_Str(self, node):
    #     return super(ParseKVBindTransformer, self).generic_visit(node)

    def visit_DictComp(self, node):
        return node

    def visit_GeneratorExp(self, node):
        return node

    def visit_Lambda(self, node):
        return node

    def visit_ListComp(self, node):
        return node

    def visit_SetComp(self, node):
        return node


class ParseBindTransformer(ast.NodeTransformer):

    stack = []

    items = []

    list_name = 'item'

    tmp_vars = []

    def __init__(self, list_name, *largs, **kwargs):
        super(ParseBindTransformer, self).__init__(*largs, **kwargs)
        self.items = []
        self.list_name = list_name
        self.stack = deque()
        self.tmp_vars = []

    def visit_Subscript(self, node):
        if not isinstance(node.ctx, ast.Load):
            return self.generic_visit(node)
        self.stack.append([])
        self.generic_visit(node.slice)
        item = self.stack.pop()
        if item:
            self.items.append(item)

        # ret_node = ast.Subscript(
        #     value=ast.Subscript(
        #         value=ast.Name(id=self.list_name, ctx=ast.Load()),
        #         slice=ast.Index(value=ast.Num(n=len(self.items))),
        #         ctx=ast.Load()),
        #     slice=ast.Index(value=ast.Num(n=5)),
        #     ctx=ast.Store()
        # )

        name = ''
        if isinstance(node.value, ast.Attribute):
            value = self.generic_visit(node.value.value)
            name = node.value.attr
        else:
            value = self.generic_visit(node.value)

        new_node = ast.Assign(
            targets=[ast.Name(id='sd', ctx=ast.Store())],
            value=value)
        self.items.append(astor.to_source(new_node))

        ret_node.ctx = ast.Load()

        return ret_node

    def visit_Attribute(self, node):
        node = self.generic_visit(node)
        if not isinstance(node.ctx, ast.Load):
            return node

        ret_node = ast.Subscript(
            value=ast.Subscript(
                value=ast.Name(id=self.list_name, ctx=ast.Load()),
                slice=ast.Index(value=ast.Num(n=len(self.items))),
                ctx=ast.Load()),
            slice=ast.Index(value=ast.Num(n=5)),
            ctx=ast.Store()
        )
        new_node = ast.Assign(
            targets=[ret_node],
            value=node)
        self.items.append(astor.to_source(new_node))
        ret_node.ctx = ast.Load()
        return ret_node

    def visit_BinOp(self, node):
        pass

    def visit_Compare(self, node):
        pass

    def visit_IfExp(self, node):
        pass

    def visit_DictComp(self, node):
        return node

    def visit_GeneratorExp(self, node):
        return node

    def visit_Lambda(self, node):
        return node

    def visit_ListComp(self, node):
        return node

    def visit_SetComp(self, node):
        return node


class StaticKVLangTransformer(ast.NodeTransformer):

    def generic_visit(self, node):
        # print(ast.dump(node))
        return super(KVLangTransformer, self).generic_visit(node)

    # def visit_AugAssign(self, node):
    #     #print(ast.dump(node))
    #     # if not isinstance(node.op, ast.MatMult):
    #     #     return node
    #     #print(ast.dump(node))
    #     #print(node.target.value.id, node.target.attr, node.value)
    #     return node

    def visit_With(self, node):
        items = []
        for item in node.items:
            expr = item.context_expr
            if not isinstance(expr, ast.Call):
                continue
            func = expr.func

            if isinstance(func, ast.Name
                          ) and func.id.lower().startswith('kvbind'):
                items.append(func)
            elif isinstance(func, ast.Attribute
                            ) and func.attr.lower().startswith('kvbind'):
                items.append(func)

        self.process_with_body(items, node.body)
        return node

    def process_with_body(self, with_calls, with_body):
        print(with_body)

if __name__ == '__main__':
    code = '''
    (self.abs + my_home / 2 + other.fruit + b"fruit" + other.fruit * myself).cheese + my_home + (self.abs + my_home / 2 + other.fruit + other.fruit * myself).salad + self.abs
    '''
    # src = inspect.getsource(binds)
    # src = textwrap.dedent(src)
    # ast.fix_missing_locations(tree)
    # tree = ast.parse(textwrap.dedent(code))
    # trans = ParseKVBindTransformer()
    # trans.update_tree(tree)
    # print('\n\n\n')
    # for node in trans.src_nodes:
    #     print(repr(node))
    # exit()

    from kivy.uix.widget import Widget
    def build_kv():
        w = Widget()
        w2 = Widget()
        w3 = Widget()
        w2.add_widget(w)
        name = 'cryo'
        count = 33

        def get_w3(*largs):
            return w3
        items = defaultdict(get_w3)
        compiler = KVCompiler()
        ctx = KVCtx()

        def manage_x(instance, value):
            w.x = items[w.parent.width + len(name) / 2 + w2.height + len(b"fruit") +
                   w2.height * count].width + count + items[w.parent.width + len(name) / 2 + w2.height + len(b"fruit") +
                   w2.height * count].x + w.y
            print('updated w.x to ', w.x, "w's parent is", w.parent)
        ctx.add_rule(
            manage_x,
            'items[w.parent.width + len(name) / 2 + w2.height + len(b"fruit") + '
            'w2.height * count].width + count + items[w.parent.width + len(name) / 2 '
            '+ w2.height + len(b"fruit") + w2.height * count].x + w.y'
        )

        def manage_y(instance, value):
            w.y = w.parent.y + w.height
            print('updated w.y to ', w.y)
        ctx.add_rule(manage_y, 'w.parent.y + w.x')

        compiler.exec_bindings(ctx, locals(), globals())

        w3.add_widget(w2)
        ctx = KVCtx()

        def manage_w2_y(instance, value):
            w2.y = w2.parent.y + w2.height
            print('updated w2.y to ', w2.y)
        ctx.add_rule(manage_w2_y, '(w2.parent.y + w2.parent.x).z')

        compiler.exec_bindings(ctx, locals(), globals())

    build_kv()
