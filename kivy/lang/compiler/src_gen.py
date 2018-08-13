'''
KV Compiler Source Code Generation
====================================

Generates the compiled KV source code.
'''

import ast
from collections import defaultdict
from itertools import chain

from kivy.lang.compiler.ast_parse import generate_source, BindSubGraph, \
    ASTBindNodeRef
from kivy.lang.compiler.utils import StringPool

__all__ = ('KVCompiler', )


class KVCompiler(object):
    '''
    The compiler that generates all the source code.

    This class is not part of the public API.
    '''

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

    used_weak_method = False

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

    def gen_base_rebind_node_local_variable(
            self, src_code, subgraph, node, temp_pool, nodes_use_count,
            nodes_original_ref, nodes_temp_var_name, bind_store_name):
        '''generates the source for getting the value from the bind store
        on which the rebind function was bound, and saves it as a local
        variable to be used by children nodes later in the rebind function.

        Should only be called on the nodes of a subgraph and not its
        terminal nodes. Also, should only be called on a node of the subgraph,
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
        # all graphs, even those in other rebind funcs, the
        # former only includes those used in this func

        # get temp variable for all deps that depend on this bind store value
        var = temp_pool.borrow(node, nodes_use_count[node])

        # a rebind function could be bound to multiple attr
        # rebind nodes (e.g. `(self.x + other.y).value`) so
        # we need to check if the rebind list has been init
        i = subgraph.bind_store_rebind_nodes_indices[node]  # rebind list index
        assert subgraph.n_rebind_deps >= 1

        indent = 4
        # only if the graph does have deps, otherwise, there's nothing to
        # lookup in the bind store as it's a global etc.
        if subgraph.n_rebind_deps > 1:
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
        # to predict which subgraphs this rebind func eats
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
            ' ' * indent, var, generate_source(node))
        src_code.append(assignment)
        src_code.append('')

        nodes_temp_var_name[node] = var
        assert node not in nodes_original_ref
        nodes_original_ref[node] = node.ref_node
        node.set_ref_node(ast.Name(id=var, ctx=ast.Load()))

    def gen_non_bind_node_local_variable(
            self, src_code, node, temp_pool, nodes_use_count,
            nodes_original_ref, nodes_temp_var_name, indent):
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
            condition = '{}if {}:'.format(
                ' ' * indent, ' and '.join(condition))
            src_code.append(condition)

            indent += 4

        assignment = '{}{} = {}'.format(
            ' ' * indent, var, generate_source(node))
        src_code.append(assignment)
        src_code.append('')

        nodes_temp_var_name[node] = var
        assert node not in nodes_original_ref
        nodes_original_ref[node] = node.ref_node
        node.set_ref_node(ast.Name(id=var, ctx=ast.Load()))

        # we are done with this dep here for this node
        for dep in depends:
            temp_pool.return_back(dep)

    def gen_unbind_subgraph_bindings(
            self, src_code, subgraph, bind_store_name):
        for node in subgraph.terminal_nodes:
            # we don't need too check for double visits because
            # each graph contains *all* deps of terminal attrs
            for i in node.bind_store_indices:
                src_code.append(
                    '{}__kv_bind_ref = {}[{}]'.format(
                        ' ' * 4, bind_store_name, i))
                src_code.append(
                    '{}if __kv_bind_ref is not None:'.format(' ' * 4))
                src_code.append(
                    '{}__kv_obj, __kv_attr, _, __kv_uid, _, _ = __kv_bind_ref'.
                    format(' ' * 8))
                src_code.append(
                    '{}if __kv_obj is not None and __kv_uid:'.format(' ' * 8))
                src_code.append(
                    '{}__kv_obj.unbind_uid(__kv_attr, __kv_uid)'.
                    format(' ' * 12))
                src_code.append('{}__kv_bind_ref[0] = None'.format(' ' * 12))
                src_code.append('')

    def gen_fbind_for_subgraph_nodes_in_rebind_callback(
            self, src_code, nodes, indent, dep_name, bind_store_name, proxy):
        indent2 = indent + 4
        indent3 = indent + 8
        bind_callback = '__kv_bind_element[2]'
        if proxy:
            bind_callback = '__kv_WeakMethod(__kv_bind_element[2], True)'

        for node in nodes:
            obj_attr = node.ref_node.attr
            for i in node.bind_store_indices:
                src_code.append(
                    '{}__kv_bind_element = {}[{}]'.format(
                        ' ' * indent2, bind_store_name, i))
                src_code.append(
                    '{}if __kv_bind_element is not None:'.
                    format(' ' * indent2))
                bind = '__kv__fbind("{}", {})'.format(obj_attr, bind_callback)
                src_code.append(
                    '{}__kv_bind_element[0] = {}'.
                    format(' ' * indent3, dep_name))
                src_code.append(
                    '{}__kv_bind_element[3] = {}'.format(' ' * indent3, bind))
                src_code.append('')

    def gen_fbind_for_subgraph_nodes_for_initial_bindings(
            self, src_code, nodes, indent, dep_name, parent_nodes_of_leaves,
            store_indices_count, var_none, bind_store_name, proxy):
        indent2 = indent + 4

        for node in nodes:
            obj_attr = node.ref_node.attr
            assert node.count == sum(
                store_indices_count[j] for j in node.bind_store_indices)
            for i, callback_name in zip(
                    node.bind_store_indices, node.callback_names):
                bind_callback = callback_name
                if proxy:
                    bind_callback = \
                        '__kv_WeakMethod({}, True)'.format(callback_name)

                bind = '__kv__fbind("{}", {})'.format(obj_attr, bind_callback)
                if var_none:
                    bind = 'None'

                if node.leaf_rule is None:
                    indices = '()'
                else:
                    indices = '({}, )'.format(', '.join(map(str, sorted(
                        parent_nodes_of_leaves[node]))))

                src_code.append(
                    '{}{}[{}] = [{}, "{}", {}, {}, {}, {}]'.format(
                        ' ' * indent2, bind_store_name, i, dep_name,
                        obj_attr, callback_name, bind, store_indices_count[i],
                        indices
                    ))
                src_code.append('')

    def gen_subgraph_bindings(
            self, src_code, subgraph, temp_pool, nodes_use_count,
            nodes_original_ref, nodes_temp_var_name, init_bindings,
            bind_store_name, parent_nodes_of_leaves=None,
            store_indices_count=None):
        '''Generates the code that binds all the callbacks associated with this
        subgraph.
        '''
        terminal_nodes_by_dep = defaultdict(list)
        # terminal nodes are attributes so by definition they can and must have
        # exactly one dep.
        for node in subgraph.terminal_nodes:
            assert len(node.depends) == 1
            terminal_nodes_by_dep[node.depends[0]].append(node)

        for dep, nodes in terminal_nodes_by_dep.items():
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
            self.used_weak_method = self.used_weak_method or dep.proxy
            fbind_name = 'fbind_proxy' if dep.proxy else 'fbind'
            src_code.append('{}__kv__fbind = getattr({}, "{}", None)'.
                            format(' ' * indent, dep_name, fbind_name))
            src_code.append(
                '{}if __kv__fbind is not None:'.format(' ' * indent))

            else_bind = []
            if init_bindings:
                self.gen_fbind_for_subgraph_nodes_for_initial_bindings(
                    src_code, nodes, indent, dep_name, parent_nodes_of_leaves,
                    store_indices_count, False, bind_store_name, dep.proxy)

                src_code.append(
                    '{}else:'.format(' ' * indent))
                self.gen_fbind_for_subgraph_nodes_for_initial_bindings(
                    src_code, nodes, indent, dep_name, parent_nodes_of_leaves,
                    store_indices_count, True, bind_store_name, dep.proxy)

                if dep.depends:
                    else_bind.append(
                        '{}else:'.format(' ' * 0))
                    self.gen_fbind_for_subgraph_nodes_for_initial_bindings(
                        else_bind, nodes, 0, dep_name, parent_nodes_of_leaves,
                        store_indices_count, True, bind_store_name, dep.proxy)
            else:
                self.gen_fbind_for_subgraph_nodes_in_rebind_callback(
                    src_code, nodes, indent, dep_name, bind_store_name,
                    dep.proxy)

            # create the values of the nodes for use later, using the temp vars
            for node in nodes:
                if node.leaf_rule is None:
                    var = nodes_temp_var_name[node]
                    assignment = '{}{} = {}'.format(
                        ' ' * indent, var, generate_source(node))
                    src_code.append(assignment)
                    src_code.append('')

                    assert node not in nodes_original_ref
                    nodes_original_ref[node] = node.ref_node
                    node.set_ref_node(ast.Name(id=var, ctx=ast.Load()))

            src_code.extend(else_bind)
            if dep.depends:
                for _ in nodes:
                    temp_pool.return_back(dep)

    def gen_subgraph_and_children_rebind_callback(
            self, src_code, subgraph, bind_store_name):
        '''
        The subgraph is composed of root nodes and leaf nodes and is
        of course a directed graph because the containing graph is directed.

        All the leaf nodes (called terminal nodes here) are attribute nodes.
        They are either rebind nodes (to which we bind a rebind function, e.g.
        for `self.widget.x`, it is the `self` node with property `widget`),
        or are leaf nodes (to which we bind a rule, e.g. `self.widget` with `x`
        property in the example above).

        All the root nodes, called simply nodes, are either attribute nodes
        that are rebind, or are literals or captured global/local/nonlocal
        variables. This means, that we can compute the value of any of the
        terminal nodes using just the nodes of the subgraph. We don't need
        anything else!

        **Task**: Given a subgraph, find all the nodes in the larger graph that
        depend (are children) of the terminal nodes in the subgraph. We then
        bind a single rebind function, that updates all the nodes in the
        dependency graph of the subgraph, whenever any of the root nodes
        of the subgraph is changed.

        This means we unbind, and then rebind to any new values discovered.

        At the end of the rebind callback, we also executed all (once) the
        rules that contain any of the nodes encountered along the way. This
        ensures the rule(s) are properly executed when any of the rebind
        node change.

        **Algorithm**: The overall algorithm is pretty simple, we start with
        the subgraph added to a queue. Then we (1) remove the first subgraph
        from the queue (2) add all the subgraphs that depend on (are children
        of) this subgraph to the queue, (3) use the subgraph if it has not
        already been used in a previous iteration of the loop.

        The exact details of how each subgraph is "used", is defined in the
        function.
        '''
        # we keep track of all attrs we visit in the subgraph. Because
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

        assert subgraph.terminal_nodes
        assert subgraph.n_rebind_deps
        # it's the same for all subgraphs in a graph
        capturing_vars.add(bind_store_name)

        leaf_callbacks = defaultdict(set)
        subgraphs = subgraph.get_subgraph_and_children_subgraphs()
        nodes_use_count = BindSubGraph.\
            compute_nodes_dependency_count_for_subgraphs(subgraphs)

        for current_subgraph in subgraphs:
            terminal_nodes_visited.update(current_subgraph.terminal_nodes)
            for node in current_subgraph.nodes:
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
                    # there are no cycles, so any node from `nodes` will be
                    # seen only once
                    self.gen_base_rebind_node_local_variable(
                        src_code, current_subgraph, node, temp_pool,
                        nodes_use_count, nodes_original_ref,
                        nodes_temp_var_name, bind_store_name)
                elif node.rebind:
                    assert node in nodes_temp_var_name, 'should already ' \
                        'have been created in terminal node stage'
                else:
                    self.gen_non_bind_node_local_variable(
                        src_code, node, temp_pool, nodes_use_count,
                        nodes_original_ref, nodes_temp_var_name, indent=4)

            # unbind
            self.gen_unbind_subgraph_bindings(
                src_code, current_subgraph, bind_store_name)

            # collect all the locations where a leaf callback is saved. Then
            # we execute the callback at the end of rebind, only if at least
            # of the bindings to the leaf callback is alive, i.e. is not None.
            for node in current_subgraph.terminal_nodes:
                if node.leaf_rule is not None:
                    assert len(node.bind_store_indices) == 1
                    assert len(node.callback_names) == 1
                    i = node.bind_store_indices[0]
                    f_location = '{}[{}]'.format(bind_store_name, i)
                    leaf_callbacks[node.callback_names[0]].add(f_location)

            self.gen_subgraph_bindings(
                src_code, current_subgraph, temp_pool, nodes_use_count,
                nodes_original_ref, nodes_temp_var_name, False,
                bind_store_name)
            current_subgraph.remove_from_count(nodes_use_count)

        for node, count in nodes_use_count.items():
            assert not count, '{}, {} should be zero'.format(node, count)

        for name, locations in leaf_callbacks.items():
            src_code.append(
                '{}__kv_callback = {}'.format(' ' * 4, ' or '.join(locations)))
            src_code.append('{}if __kv_callback is not None:'.format(' ' * 4))
            src_code.append('{}__kv_callback[2]()'.format(' ' * 8))
            src_code.append('')
        for node, origin_node in nodes_original_ref.items():
            node.set_ref_node(origin_node)

        s = ', '.join(
            '{0}={0}'.format(item) for item in sorted(capturing_vars))
        s = ', {}'.format(s) if s else ''
        func_def = 'def {}(*__kv_largs{}):'.format(
            subgraph.rebind_callback_name, s)
        src_code[func_def_i] = func_def

    def gen_rebind_callbacks(
            self, ctx_name, nodes, subgraphs, bind_store_name,
            bind_store_size):

        if bind_store_name is not None:
            src_code = [
                '{} = [None, ] * {}'.format(bind_store_name, bind_store_size),
                '{}.bind_store = {}'.format(ctx_name, bind_store_name),
                '']
        else:
            src_code = ['{}.bind_store = None'.format(ctx_name), '']

        # count the number of places each node is used. E.g. in
        # `self.x + self.y`, `self` is used twice. Keep in mind that nodes
        # are unique
        nodes_use_count = BindSubGraph.compute_nodes_dependency_count(nodes)
        for subgraph in subgraphs:
            # we create a rebind func for each subgraph that roots in attr
            if not subgraph.n_rebind_deps:
                # It means that all the deps are not attributes, meaning
                # thet are e.g. variables etc, so that we never create a
                # rebind func for them
                # see further down why len(node.depends_on_me) is correct
                subgraph.remove_from_count(nodes_use_count)
                continue

            func_src_code = []
            self.gen_subgraph_and_children_rebind_callback(
                func_src_code, subgraph, bind_store_name)

            # remove all that depend on the node because either the dep
            # is in the same subgraph, or it's in the terminal of the
            # subgraph. In the latter case, binding and attr eval happens
            # in this subgraph iteration, so this node won't be used again
            subgraph.remove_from_count(nodes_use_count)
            src_code.extend(func_src_code)

        for node, count in nodes_use_count.items():
            assert not count, '{}, {} should be zero'.format(node, count)

        s = ', '.join(sorted(
            subgraph.rebind_callback_name
            for subgraph in subgraphs if subgraph.rebind_callback_name))
        comma = ', ' if s else ''
        src_code.append('{}.rebind_functions = ({}{})'.format(
            ctx_name, s, comma))
        src_code.append('')
        return src_code

    def gen_leaf_rules(self, ctx, ctx_name, create_rules, bind_store_name):
        rule_creation = []
        rule_finalization = []
        kv_rule_pool = self.kv_rule_pool
        canvas_pool = self.leaf_canvas_callback_pool
        clock_pool = self.leaf_clock_callback_pool

        for rule_idx, (rule, rule_nodes) in enumerate(
                zip(ctx.rules, ctx.transformer.nodes_by_rule)):
            name = kv_rule_pool.borrow_persistent()
            if create_rules:
                delay = rule.delay

                if delay is None:
                    delay_arg = 'None'
                elif delay == 'canvas':
                    delay_arg = '"canvas"'
                else:
                    delay_arg = '{}'.format(rule.delay)

                rule_creation.append('{} = __KVRule()'.format(name))
                rule_creation.append('{}.delay = {}'.format(name, delay_arg))
                if rule.name:
                    rule_creation.append(
                        '{}.name = "{}"'.format(name, rule.name))
                else:
                    rule_creation.append('{}.name = None'.format(name))
                rule_creation.append('{}.add_rule({})'.format(ctx_name, name))

                if rule.with_var_name_ast is not None:
                    rule.with_var_name_ast.id = name

                if rule_nodes:
                    callback_name = rule.callback_name
                    if delay is None:
                        _callback_name = callback_name
                    elif delay == 'canvas':
                        _callback_name = canvas_pool.borrow_persistent()
                        self.used_canvas_rule = True
                    else:
                        _callback_name = clock_pool.borrow_persistent()
                        self.used_clock_rule = True
                    rule._callback_name = _callback_name

                    rule_finalization.append(
                        '{}.callback = {}'.format(name, callback_name))
                    if callback_name != _callback_name:
                        rule_finalization.append(
                            '{}._callback = {}'.format(name, _callback_name))
                        assert rule.delay is not None
                    else:
                        rule_finalization.append(
                            '{}._callback = None'.format(name))
                else:
                    rule_finalization.append('{}.callback = None'.format(name))
                    rule_finalization.append(
                        '{}._callback = None'.format(name))
            else:
                rule_creation.append(
                    '{} = {}.rules[{}]'.format(name, ctx_name, rule_idx))

            leaf_indices = []
            for node in rule_nodes:
                if node.leaf_rule is not None:
                    assert len(node.bind_store_indices) == 1, "it's a leaf"
                    leaf_indices.append(node.bind_store_indices[0])

            if rule_nodes:
                assert leaf_indices
                assert bind_store_name
                rule_finalization.append(
                    '{}.bind_store = {}'.format(name, bind_store_name))
                rule_finalization.append(
                    '{}.bind_store_leaf_indices = ({}, )'.format(
                        name, ', '.join(map(str, sorted(leaf_indices)))))
            else:
                rule_finalization.append('{}.bind_store = None'.format(name))
                rule_finalization.append(
                    '{}.bind_store_leaf_indices = None'.format(name))

            rule_creation.append('')
            rule_finalization.append('')

        return rule_creation, rule_finalization

    def gen_leaf_callbacks(self, ctx):
        src_code = []
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
            _callback_name = rule._callback_name

            s = ', '.join(
                '{0}={0}'.format(name) for name in sorted(rule.captures))
            s = ', {}'.format(s) if s else ''
            func_def = 'def {}(*__kv_largs{}):'.format(_callback_name, s)

            src_code.append(func_def)
            if name is not None:
                src_code.append(
                    '{}{}.largs = __kv_largs'.format(' ' * 4, name))

            for line in rule.src.splitlines():
                src_code.append('{}{}'.format(' ' * 4, line))
            src_code.append('')

            if delay is None:
                continue
            elif delay == 'canvas':
                func_def = 'def {}(*__kv_largs, __kv_canvas_item=[{}, ' \
                    'None, None]):'.format(callback_name, _callback_name)
                body = '{}__kv_add_graphics_callback(__kv_canvas_item, ' \
                    '__kv_largs)'.format(' ' * 4)
                src_code.append(func_def)
                src_code.append(body)
                src_code.append('')
            else:
                line = '{} = __kv_Clock.create_trigger({}, {})'.\
                    format(callback_name, _callback_name, delay)
                src_code.append(line)
                src_code.append('')

        return src_code

    def gen_initial_bindings(
            self, ctx, nodes, subgraphs, exec_rules_after_binding,
            bind_store_name):
        leaf_parents_indices = ASTBindNodeRef.\
            get_all_bind_store_indices_for_leaf_and_parents(nodes)
        store_indices_count = ASTBindNodeRef.\
            get_num_binds_for_bind_store_indices(leaf_parents_indices)
        src_code = []

        # we keep track of all attrs we visit in the subgraph. Because
        # deps are always explored before the children, if we encounter
        # a attr dep that has not been visited, it means its at the root
        # level in the rebind function stored in the rebind list
        terminal_nodes_visited = set()
        nodes_visited = set()
        nodes_temp_var_name = {}
        nodes_original_ref = {}

        temp_pool = self.temp_var_pool
        # it's the same for all nodes in a graph
        assert subgraphs

        nodes_use_count = BindSubGraph.compute_nodes_dependency_count(nodes)
        for subgraph in subgraphs:
            assert subgraph.terminal_nodes
            terminal_nodes_visited.update(subgraph.terminal_nodes)

            for node in subgraph.nodes:
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

            self.gen_subgraph_bindings(
                src_code, subgraph, temp_pool,
                nodes_use_count, nodes_original_ref, nodes_temp_var_name,
                True, bind_store_name,
                parent_nodes_of_leaves=leaf_parents_indices,
                store_indices_count=store_indices_count)

            subgraph.remove_from_count(nodes_use_count)

        for node, count in nodes_use_count.items():
            assert not count, '{}, {} should be zero'.format(node, count)

        for node, origin_node in nodes_original_ref.items():
            node.set_ref_node(origin_node)

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
        assert not self.temp_var_pool.get_num_borrowed()
        variables = list(sorted(chain(
            self.temp_var_pool.get_available_items(),
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

        subgraphs = BindSubGraph.get_ordered_subgraphs(ctx.transformer)

        bind_store_size = BindSubGraph.\
            populate_bind_store_size_indices_and_callback_names(
                subgraphs, create_rules, ctx.rules, ctx.transformer,
                self.rebind_callback_pool, self.leaf_callback_pool)

        bind_store_name = None
        if bind_store_size:
            bind_store_name = self.binding_store_pool.borrow_persistent()
        nodes = list(chain(*ctx.transformer.nodes_by_rule))

        funcs = self.gen_rebind_callbacks(
            ctx_name, nodes, subgraphs, bind_store_name, bind_store_size)

        rule_creation, rule_finalization = self.gen_leaf_rules(
            ctx, ctx_name, create_rules, bind_store_name)

        if create_rules:
            res = self.gen_leaf_callbacks(ctx)
            funcs.extend(res)

        if subgraphs:
            assert nodes
        else:
            assert not nodes

        if subgraphs:
            res = self.gen_initial_bindings(
                ctx, nodes, subgraphs, exec_rules_after_binding,
                bind_store_name)
            funcs.extend(res)

        return ctx_name, funcs, rule_creation, rule_finalization
