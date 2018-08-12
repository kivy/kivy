'''
KV Parser
===========

Parses source code contains KV rules and contexts.
'''

import ast
from collections import deque, defaultdict
from astor.code_gen import SourceGenerator
from astor.source_repr import split_lines

from kivy.lang.compiler.kv_context import KVParserCtx, KVParserRule

__all__ = (
    'KVException', 'KVCompilerParserException', 'parse_expr_ast',
    'BindSubGraph',
    'ASTBindNodeRef', 'ASTStrPlaceholder', 'ASTNodeList',
    'RefSourceGenerator', 'generate_source', 'ParseCheckWhitelisted',
    'ParseKVBindTransformer', 'ParseKVFunctionTransformer',
    'DoNothingAST', 'ParseExpressionNameLoadTransformer',
    'VerifyKVCaptureOnExitTransformer',
    'VerifyKVCaptureOnEnterTransformer', 'verify_readonly_nodes')


def parse_expr_ast(expr_str):
    '''Takes a expression string (i.e. can be represented by `ast.Expr` type),
    e.g. `"self.x"`, and returns the AST node that directly corresponds to that
    expression (i.e. it's not wrapped in a Module like `ast.parse`).

    E.g.:

    >>> ast.dump(parse_expr_ast('self.x'))
    "Attribute(value=Name(id='self', ctx=Load()), attr='x', ctx=Load())"
    '''
    body = ast.parse(expr_str).body[0]
    if not isinstance(body, ast.Expr):
        raise ValueError(
            'Function takes only source code that represents an expression '
            '(ast.Expr)')
    return body.value


class KVException(Exception):
    '''
    Raised when something goes wrong with KV compilation or loading.
    '''
    pass


class KVCompilerParserException(KVException):
    '''
    Raised when something goes wrong with KV parsing.
    '''
    pass


class BindSubGraph(object):
    '''
    A minimal rebind/leaf constrained subgraph from the bind graph.
    '''

    nodes = []

    terminal_nodes = []

    n_rebind_deps = 0
    '''The number of rebind nodes in :attr:`nodes`.
    '''

    depends_on_me = []

    terminates_with_leafs_only = True

    rebind_callback_name = None
    '''There is one rebind callback for each subtree, provided there are at
    least one rebind attribute as a node in `nodes` (i.e. n_rebind_deps is
    non-zero) in which case there are none.
    '''

    bind_store_rebind_nodes_indices = {}
    '''The nodes that are in the `nodes` of the subgraph, and maps to the
    index in `callback_names` and `bind_store_indices` where this subgraph was
    bound to in the bind store. I.e. the index in bind store, where each node
    bind a rebind function that is the rebind created for this subgraph.
    '''

    def __init__(self, nodes, terminal_nodes):
        super(BindSubGraph, self).__init__()
        self.nodes = nodes
        self.terminal_nodes = terminal_nodes
        self.depends_on_me = []
        self.bind_store_rebind_nodes_indices = {}

    def __repr__(self):
        base = '<Subgraph -- # attr deps: {}, leafs_only?: {}\n'.format(
            self.n_rebind_deps, self.terminates_with_leafs_only)
        return base + \
            'Nodes({}): {{'.format(len(self.nodes)) + \
            '}\n    {'.join(map(repr, self.nodes)) + \
            '}}\nTerminal nodes({}): {{'.format(len(self.terminal_nodes)) + \
            '}\n    {'.join(map(repr, self.terminal_nodes)) + \
            '}>'

    @classmethod
    def get_subgraphs(cls, nodes):
        # consider the graph made by rule (x.y + x.z).q + x.y.k
        # we have to compute *all* the subtgraphs first before we can merge
        # because consider this graph: a->b->c, a->d->c, d->e->c, f->d
        # and you'll see what I mean
        all_subgraphs = []
        unique_subgraphs = []
        for node in nodes:
            # leafs cannot have their own subgraph
            if node.leaf_rule is not None:
                continue
            # if it's also not a rebind node, then either it's a base node,
            # e.g. a local/global/nonlocal/number etc, in which case it has
            # no depends and we need to make a subgraph starting from it,
            # or if it has depends then it's after some other node, and
            # we'd have encountered it already in another subgraph so don't
            # generate one again
            if not node.rebind and node.depends:
                continue
            all_subgraphs.extend(node.get_rebind_or_leaf_subgraph())

        subgraphs_grouped_by_nodes = defaultdict(list)
        for subgraph in all_subgraphs:
            assert subgraph.nodes
            subgraphs_grouped_by_nodes[tuple(subgraph.nodes)].append(
                subgraph)

        for subgraphs in subgraphs_grouped_by_nodes.values():
            terminal_nodes = list({
                node for subgraph in subgraphs
                for node in subgraph.terminal_nodes})
            subgraph = subgraphs[0]
            subgraph.terminal_nodes = terminal_nodes
            unique_subgraphs.append(subgraph)
        return unique_subgraphs

    @classmethod
    def get_ordered_subgraphs(cls, nodes):
        # consider the graph made by rule (x.y + x.z).q + x.y.k - we cannot
        # look at the subgraph created by
        subgraphs = cls.get_subgraphs(nodes)
        # for every terminal node in a subgraph, it's the index of the
        # subgraph in subgraphs
        terminal_nodes_subgraphs_idx = {}
        # fill in terminal_nodes_subgraphs_idx
        for i, subgraph in enumerate(subgraphs):
            for terminal_node in subgraph.terminal_nodes:
                if terminal_node.leaf_rule is None:
                    subgraph.terminates_with_leafs_only = False
                terminal_nodes_subgraphs_idx[terminal_node] = i

        # we reorder the subgraphs so that if we process the subgraphs in
        # the reordered order, when every subgraph will have all its deps
        # in terminal nodes of subgraphs previous to it in the list, or
        # the deps will be in `nodes` of the subgraph (e.g. for
        # non-attribute dep nodes).
        ordered_subgraphs = []
        visited = set()
        # to compute what subgraphs are children (depend on) a subgraph, we
        # store for every rebind node, the subgraphs it appears in its
        # `nodes` list
        subgraphs_containing_rebind_node = defaultdict(list)
        # in graph, nodes are ordered according to their position in the
        # graph such that a node never depends on a node later in the graph
        # list, but subsequent nodes may depend on previous nodes
        for node in nodes:
            # unvisited leaf or rebind node -- find it's subgraph in which
            # it's a terminal node. Because all terminal nodes of the
            # subgraph share the same `nodes` dependencies, and since by
            # the order in `graph` we found a one terminal node whose deps
            # must have already been encountered previously in `graph`.
            # That means we have all the deps for all terminal nodes.
            if (node.leaf_rule is not None or node.rebind) and \
                    node not in visited:
                subgraph = subgraphs[terminal_nodes_subgraphs_idx[node]]

                # so add all terminal nodes to visited and process them
                visited.update(subgraph.terminal_nodes)
                # this is the first time we see this subgraph
                for dep in subgraph.nodes:
                    assert dep.leaf_rule is None
                    if dep.rebind:
                        subgraph.n_rebind_deps += 1
                        # a node can be in `nodes` of multiple subgraphs
                        subgraphs_containing_rebind_node[dep].append(subgraph)
                ordered_subgraphs.append(subgraph)

        # fill in depends_on_me
        for subgraph in ordered_subgraphs:
            depends_on_me = set()
            for terminal_node in subgraph.terminal_nodes:
                # every terminal node that isn't a leaf is a dep of some
                # subgraph and stored in its `nodes`.
                if not terminal_node.leaf_rule:
                    subgraph.depends_on_me.extend(
                        item for item in
                        subgraphs_containing_rebind_node[terminal_node] if
                        item not in depends_on_me)
                    depends_on_me.update(
                        subgraphs_containing_rebind_node[terminal_node])

        return ordered_subgraphs

    @classmethod
    def compute_nodes_dependency_count_for_subgraphs(cls, subgraphs):
        nodes_use_count = defaultdict(int)
        for subgraph in subgraphs:
            for node in subgraph.terminal_nodes:
                # these must all be in nodes
                for dep in node.depends:
                    nodes_use_count[dep] += 1

            for node in subgraph.nodes:
                # add deps of the nodes that are also in the nodes. If
                # rebind, then it won't be in the current nodes. Its deps could
                # be in another subgraph though, but either it's a terminal
                # node somewhere, in which case we'll count it if the subgraph
                # is in our list of subgraphs, otherwise, it's a root node, and
                # its deps our outside our subgraphs, in which case we'll never
                # refer to its deps in in this set of subgraphs, so no count.
                # If not rebind, it'll only be present if it has deps, because
                # the roots of the subgraph must be either rebind nodes, or
                # nodes with no depends e.g. for locals/number etc.
                if node.depends and not node.rebind:
                    for dep in node.depends:
                        nodes_use_count[dep] += 1
        return nodes_use_count

    @classmethod
    def compute_nodes_dependency_count(cls, nodes):
        nodes_use_count = defaultdict(int)
        for node in nodes:
            for dep in node.depends:
                assert dep.leaf_rule is None, 'a dep cannot be a leaf, duh'
                nodes_use_count[dep] += 1
        return nodes_use_count

    def remove_from_count(self, nodes_use_count):
        for node in self.terminal_nodes:
            # these must all be in nodes
            for dep in node.depends:
                nodes_use_count[dep] -= 1

        for node in self.nodes:
            # remove deps of the nodes that are also in the nodes. If
            # rebind, then it won't be in the current nodes. If not rebind,
            # it'll only be present if it has deps, because the roots of the
            # subgraph must be either rebind nodes, or nodes with no depends
            # e.g. for locals/number etc.
            if node.depends and not node.rebind:
                for dep in node.depends:
                    nodes_use_count[dep] -= 1

    def get_subgraph_and_children_subgraphs(self):
        queue = deque([self])
        # we can have a subgraph being a child
        # of multiple different subgraphs. E.g. self.a.b + self.a.c
        subgraphs_visited = set()
        subgraphs = []
        while queue:
            current_subgraph = queue.popleft()
            if current_subgraph in subgraphs_visited:
                continue

            subgraphs_visited.add(current_subgraph)
            queue.extend(current_subgraph.depends_on_me)
            subgraphs.append(current_subgraph)
        return subgraphs


class ASTBindNodeRef(ast.AST):
    '''
    Created by :class:`ParseKVBindTransformer` as it walks the AST graph to
    represent an original `ast.AST` node that we could bind to (e.g. a
    attribute access of a rebind, or leaf node) or a dependency of such a node
    (e.g. a local or global or `Name` etc.).

    E.g. given `self.x + self.y`, when visiting its ast nodes, we create
    corresponding :class:`ASTBindNodeRef` nodes for `self`, `x`, and `y`.

    Subsequently, :attr:`depends` and :attr:`depends_on_me` describes a newly
    constructed ast graph that represents a subgraph of the original ast graph,
    that contains this node.

    E.g. `self.x + other.x` represents two independent subgraphs, one
    with :class:`ASTBindNodeRef` nodes representing `self` and `self.x`,
    and the other with nodes representing `other` and `other.x`.

    After parsing, the graphs created by these nodes are self contained in
    the sense they
    '''

    ref_node = None
    '''The `AST` node that this instance represents.
    '''

    src = ''
    '''
    The :func:`generate_source` generated source representing the
    :attr:`ref_node`. E.g. for the graph `self.x.y + self.z`, if the
    :attr:`ref_node` represents the `x` `Attribute` node, then :attr:`src` will
    be `"self.x"`.

    In the bind graph, this is the primary method we use currently to identify
    node duplicates. I.e. :attr:`ParseKVBindTransformer.src_node_map` keeps a
    mapping from :attr:`src` to the :class:`ASTBindNodeRef` instance that
    represents it for non-:attr:`leaf_rule` nodes. Then, if we encounter a
    source fragment we have seen before, we reuse that node and increment
    :attr:`count`, unless it's a :attr:`leaf_rule`, then we don't re-use but
    always create a new one (except if we have seen this leaf already in that
    rule as tracked by :attr:`ParseKVBindTransformer.nodes_under_leaf`).
    '''

    is_attribute = False
    '''Whether the :class:`ASTBindNodeRef` represents an `ast.Attribute`
    node. These are nodes that we potentially bind to either because it's a
    :attr:`rebind` node or because it's a :attr:`leaf`. '''

    rebind = False
    '''If the node is an :attr:`is_attribute`, and if it's not a
    :attr:`leaf_rule` then it indicates whether this node will be rebound.

    E.g. if a rule is bound to `self.x.y`, then we would need to rebind
    the rule to the `x` attribute if :attr:`rebind` is `True`. In this case,
    if `x` changes, all the nodes that are children of `x` will be
    re-evaluated and e.g. the rule will be rebound so then when the `y` value
    of the new `x` changes the rule will be dispatched.

    :attr:`rebind` may be set after graph parsing is done and is not used
    during parsing (:meth:`ParseKVBindTransformer.update_graph`) in any way.
    '''

    proxy = False
    '''If the node's child is an :attr:`is_attribute`, then it indicates
    whether the object represented by this node must not hold a direct
    reference to the other objects after binding. When `True`, it will hold
    a proxy to the objects.

    E.g. if a rule is bound to `self.x.y`, then we bind to `self.x` and
    potentially to `self`, depending on the :attr:`rebind` value of `self.x`.
    Either way, if `proxy` is True for `self` and/or `self.x`, neither will
    hold a direct ref to any of the binding objects or callbacks. This is
    to prevent the `self` and/or `self.x` objects from keeping the other
    objects from being garbage collected.

    :attr:`proxy` may be set after graph parsing is done and is not used
    during parsing (:meth:`ParseKVBindTransformer.update_graph`) in any way.
    '''

    depends_on_me = []
    '''List of :class:`ASTBindNodeRef` instances that represent ast nodes
    that are children of this node. The :attr:`ASTBindNodeRef.depends` of
    such children must include this node.
    '''

    depends = []
    '''List of :class:`ASTBindNodeRef` instances that represent ast nodes
    that are parents of this node. The :attr:`ASTBindNodeRef.depends_on_me` of
    such parents must include this node.
    '''

    count = 0
    '''The number of unique leaves (:attr:`leaf_rule` is not `None`, not
    counting :attr:`leaf_rule` value duplicates) that this node
    is an ancestor of or 1 if it's a :attr:`leaf_rule`. E.g. in
    `self.obj.x + self.obj.y`, `self.obj` has a count of two as does `self`.
    `y` and `x` both have a :attr:`count` of one.

    :atr:`count` is not the same as len(:attr:`depends_on_me`). Although for
    the the rule `self.x + self.y.z`, the len and :attr:`count` will be the
    same for `self` (2). For rule `self.x[self.x.y].z`, there's only one leaf
    rule so :attr:`count` will be one, yet :attr:`depends_on_me` will contain
    two items for the node representing `self.x`.

    Similarly, if we have two rules, each saying `self.x`, then `self` will
    have a count of two.
    '''

    leaf_rule = None
    '''If :attr:`is_attribute` and it's a leaf node in the ast expression,
    e.g. `x` in `self.x` or `(self.y + self.z).x`, then :attr:`leaf_rule` is
    set to the value of `rule` passed to
    :meth:`ParseKVBindTransformer.update_graph`. That indicates that it's a
    leaf. Otherwise it is `None`.

    The exact value of :attr:`leaf_rule` is not important, we just use it to
    check if it's `None`.
    '''

    my_graph = []
    '''Keeps track of the graph the node is in. E.g. `self.x + obj.y` contains
    two independent graphs.
    '''

    callback_names = []

    bind_store_indices = []

    subgraph_for_terminal_node = None
    '''The subgraph the node appears in as a terminal node. It can only be
    one. Otherwise, either it has shared deps, in which case it would be one
    subgraph as each contains all the deps of every terminal node. Otherwise,
    they don't share deps, which makes no sense.

    Also, nodes that are not rebind, will occur only in one subgraph, so this
    is also set to the subgraph by
    populate_bind_stores_and_indices_and_callback_names. Nodes that are not
    rebind and occur in multiple subgraphs, e.g. a number, such nodes never
    care what subgraph it's in, because it has no rebind in its parent graph
    so the subgraph is the last one it occurred in and.
    '''

    subgraphs_to_bind_store_idx_and_name = {}
    '''Maps a subgraph to the index in `callback_names` and
    `bind_store_indices`, indicating the index in these lists that corresponds
    to the bind for that subgraph.
    '''

    def __init__(self, is_attribute):
        super(ASTBindNodeRef, self).__init__()
        self.is_attribute = is_attribute
        self.depends_on_me = []
        self.depends = []
        self.callback_names = []
        self.bind_store_indices = []
        self.subgraphs_to_bind_store_idx_and_name = {}

    def get_rebind_or_leaf_subgraph(self):
        # these graphs have no cycles, and are directed, even if you remove
        # their directionality, there could be cycles.
        # xxx: update comment
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
        assert self.leaf_rule is None
        assert self.rebind or not self.depends

        subgraphs = []
        for dep_on_me in self.depends_on_me:
            visited = set([self])
            forward_queue = deque()
            backward_stack = deque()
            terminal_nodes = []
            explored = [self]

            if dep_on_me.leaf_rule is not None or dep_on_me.rebind:
                terminal_nodes.append(dep_on_me)
            else:
                forward_queue.append(dep_on_me)

            while forward_queue:
                assert not backward_stack
                # there could be some visited nodes, but we leave them in case
                # their children has not been visited. Visited nodes will be
                # filtered out in backward_stack anyway
                backward_stack.extend(forward_queue)
                forward_queue.clear()
                for item in backward_stack:
                    for dep in item.depends_on_me:
                        if dep.leaf_rule is not None or dep.rebind:
                            # a atrr has only a single parent node () so it
                            # could not have been visited previously if we are
                            # its dep
                            assert dep not in visited
                            terminal_nodes.append(dep)
                        else:
                            # It seems possible that a node could be visited as
                            # a parent as well as a child, but it will be
                            # filtered out in the backward_stack
                            forward_queue.append(dep)

                while backward_stack:
                    node = backward_stack[0]
                    if node in visited:
                        backward_stack.popleft()
                        continue
                    all_done = True

                    for dep in node.depends:
                        if dep not in visited:
                            if dep.rebind:
                                explored.append(dep)
                                visited.add(dep)
                            else:
                                all_done = False
                                backward_stack.appendleft(dep)

                    if all_done:
                        explored.append(node)
                        visited.add(node)
                        backward_stack.popleft()

            subgraphs.append(BindSubGraph(explored, terminal_nodes))
        return subgraphs

    def set_ref_node(self, node):
        self._attributes = node._attributes
        self._fields = node._fields
        self.ref_node = node

    @staticmethod
    def group_by_required_deps_ordered(nodes):
        '''Groups the nodes into groups based on their deps. All nodes with the
        same deps are grouped together. The order of nodes is preserved as
        given in `nodes` such that the first occurrence of nodes with unique
        deps are ordered in the order they occur in nodes.
        '''
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

    @classmethod
    def get_all_bind_store_indices_for_leaf_and_parents(cls, nodes):
        node_deps = {}
        for node in nodes:
            if node.leaf_rule is None:
                continue

            node_deps[node] = None
            stack = deque(node.depends)
            # notice append right not left here. It has to be last at start
            stack.append(node)
            while stack:
                first = stack[0]
                # node of the deps of first can be a leaf, by definition
                if first not in node_deps:
                    # we have not processed the first previously at all so
                    # add its deps to the top of stack so that when we
                    # arrive again to this node, all the deps of the
                    # current's deps will have been computed, and we just
                    # need to merge them.
                    stack.extendleft(first.depends)
                    # next time we see it, its deps will be ready
                    node_deps[first] = None
                elif node_deps[first] is None:
                    # all the deps of the first is done because it's the
                    # second time we encounter it, just merge them.
                    subgraph = first.subgraph_for_terminal_node
                    node_deps[first] = merged = set()
                    for dep in first.depends:
                        # get deps of deps
                        merged.update(node_deps[dep])
                        if not dep.bind_store_indices:
                            # it's not a rebind/leaf node
                            continue
                        # get index of the dep
                        i = dep.subgraphs_to_bind_store_idx_and_name[
                            subgraph]
                        i = dep.bind_store_indices[i]
                        merged.add(i)
                    stack.popleft()
                else:
                    # we have seen it previously, e.g. as co-dep of
                    # multiple nodes, e.g. in a triangle graph a->b->c and
                    # a->c, we'll see a twice
                    stack.popleft()
            assert len(node.bind_store_indices) == 1
            node_deps[node].add(node.bind_store_indices[0])

        return node_deps

    @classmethod
    def get_num_binds_for_bind_store_indices(cls, leaf_parents_indices):
        bind_counts = defaultdict(int)
        for node, indices in leaf_parents_indices.items():
            if node.leaf_rule is None:
                continue

            for i in indices:
                bind_counts[i] += 1
        return bind_counts

    def __repr__(self):
        deps_on_me = '}, {'.join(node.src for node in self.depends_on_me)
        deps = '}, {'.join(node.src for node in self.depends)
        return '<Node {} -- is_attr?: {}, rebind?: {}, proxy?: {}, count: {},'\
            ' leaf?: {}, depends_on_me({}): {{{}}}, depends({}): {{{}}}>'.\
            format(
                self.src, self.is_attribute, self.rebind, self.proxy,
                self.count, self.leaf_rule is not None,
                len(self.depends_on_me), deps_on_me, len(self.depends), deps)


class ASTStrPlaceholder(ast.AST):
    '''
    An AST node that represents a list of strings that is added to
    the source code when generated to source. They are implicitly indented to
    the indentation level of the node they are contained in.

    Useful for dumping strings rather than having to create AST nodes for all
    the source code manually. E.g.:

    >>> node = ASTStrPlaceholder()
    >>> node.src_lines = ['self.x', 'name = self.y']
    >>> generate_source(node)
    'self.x\nname = self.y'
    >>> # then
    >>> if_node = ast.parse('if self.z:\\n    55')
    >>> ast.dump(if_node)
    "Module(body=[If(test=Attribute(value=Name(id='self', ctx=Load()), \
attr='z', ctx=Load()), body=[Expr(value=Num(n=55))], orelse=[])])"
    >>> if_node.body[0].body[0].value = node
    >>> generate_source(if_node)
    'if self.z:\\n\\n    self.x\\n    name = self.y'
    '''

    src_lines = []

    def __init__(self, *largs, **kwargs):
        super(ASTStrPlaceholder, self).__init__(*largs, **kwargs)
        self.src_lines = []


class ASTNodeList(ast.AST):
    '''
    AST node that represents a list of AST nodes.

    E.g.:

    >>> node1 = ast.parse('self.x')
    >>> node2 = ast.parse('self.y')
    >>> node_list = ASTNodeList()
    >>> node_list.nodes = [node1, node2]
    >>> generate_source(node_list)
    'self.x\\nself.y'

    Or:

    >>> node1 = ast.parse('if self.x:\\n    55')
    >>> node2 = ast.parse('name = self.y')
    >>> node_list = ASTNodeList()
    >>> node_list.nodes = [node1, node2]
    >>> generate_source(node_list)
    'if self.x:\\n    55\\nname = self.y'
    '''

    nodes = []
    '''List of ast nodes represented by this node.
    '''

    def __init__(self, *largs, **kwargs):
        super(ASTNodeList, self).__init__(*largs, **kwargs)
        self.nodes = []


class RefSourceGenerator(SourceGenerator):
    '''
    Generates the source code from the custom AST nodes.

    Used with :func:`generate_source` to add custom AST nodes.
    '''

    def visit_ASTBindNodeRef(self, node, *largs, **kwargs):
        return self.visit(node.ref_node, *largs, **kwargs)

    def visit_ASTNodeList(self, node, *largs, **kwargs):
        for item in node.nodes:
            self.visit(item, *largs, **kwargs)

    def visit_ASTStrPlaceholder(self, node, *largs, **kwargs):
        self.newline(extra=1)
        lines = ['\n', ] * (len(node.src_lines) * 2)
        for i, line in enumerate(node.src_lines):
            lines[2 * i] = line
        self.write(*lines)

    def visit_DoNothingAST(self, node, *largs, **kwargs):
        pass


def generate_source(node):
    '''
    Generates the source code string represented by the node based on
    `astor.to_source`.

    As opposed to `astor.to_source`, it understands how to handle our custom
    `AST` classes and removes any trailing newlines.

    E.g.:

    >>> node = ast.parse('self.x + self.y + len("hello")')
    >>> generate_source(node)
    "self.x + self.y + len('hello')"
    '''
    generator = RefSourceGenerator(indent_with=' ' * 4)
    generator.visit(node)

    generator.result.append('\n')
    if set(generator.result[0]) == set('\n'):
        generator.result[0] = ''

    s = ''.join(split_lines(generator.result, maxline=2 ** 32 - 1))
    return s.rstrip('\r\n')


class ParseCheckWhitelisted(ast.NodeTransformer):
    '''Takes a expression node and checks whether any of the expression nodes
    that are part of the node's graph are not in the :attr:`whitelist`.

    For every node encountered, we map the node in
    :attr:`node_has_illegal_parent` to whether the node or any of its parents
    are not whitelisted.

    E.g. `self.x` would map `self` and `self.x` to `False`, while
    `(self.x + self.y).z` would map `self`, `self.x`, `self.y` to `False` and
    `(self.x + self.y)` and `(self.x + self.y).z` to `True` (assuming only
    `Attribute` and `Name` are whitelisted).
    '''

    node_has_illegal_parent = {}
    '''Maps each node in :meth:`check_node_graph` `node`'s graph to whether
    it is or has a non-whitelisted parent.'''

    has_illegal_parent = False
    '''Set by node to True if it or any of its parents are not whitelisted.
    '''

    whitelist = set()
    '''Set of ast class names that are whitelisted. These are strings
    with the exact class names, e.g. `"Attribute"`.'''

    def __init__(self, whitelist):
        self.node_has_illegal_parent = {}
        self.whitelist = whitelist

    def check_node_graph(self, node):
        '''
        Gets called with a node describing a single expression. Doesn't accept
        non-expression nodes, e.g. an assign, Module etc. It then populates
        :attr:`node_has_illegal_parent`.
        '''
        self.has_illegal_parent = False
        return self.visit(node)

    def generic_visit(self, node):
        # we only care about expressions (e.g. ast.Load is ok even if not
        # whitelisted because it may occur in expressions).
        if not isinstance(node, ast.expr):
            return super(ParseCheckWhitelisted, self).generic_visit(node)

        # save the state of our sibling nodes before clearing to get our value
        has_illegal_parent = self.has_illegal_parent
        self.has_illegal_parent = False
        # clear state and now check all the parents of this node to see whether
        # any of them contain a illegal node.
        node = super(ParseCheckWhitelisted, self).generic_visit(node)
        self.node_has_illegal_parent[node] = illegal = \
            node.__class__.__name__ not in self.whitelist or \
            self.has_illegal_parent

        # now we know whether this node or any of its parents are illegal
        # and we set the corresponding value for the node.
        # Next, we save whether we encountered a illegal node so far, including
        # from sibling nodes - this will be used by our child to decide if the
        # child has illegal parents.
        self.has_illegal_parent = has_illegal_parent or illegal
        return node


class ParseKVBindTransformer(ast.NodeTransformer):
    '''
    Transforms and computes all the nodes that should be bound to. It processes
    all the nodes and create the graphs representing the bind rules.

    Algorithm: given ast for e.g. `(self.x + self.y).z + 55, the leaves
    are `z` and `55` and the roots are `self`, `55`. For every node we
    visit, it first processes its parents and then itself. E.g.
    `(self.x + self.y)` is processed before `(self.x + self.y).z`, and
    `self.x`, `self.y` before `(self.x + self.y)`.

    The idea is to find the first node starting from leaves and working up
    the parent graph that are an `Attribute`, e.g. `(self.x + self.y).z`.
    Once we have that, we may need to rebind to all intermediate attribute
    nodes in its parent graph. E.g. for `(self.x + self.y).z`, we may need to
    rebind to `self.x` and `self.y`. We create :class:`ASTBindNodeRef` for
    each node we encounter once we encounter the first `Attribute`.

    So e.g. for `self.x + self.q`, we create 3 `ASTBindNodeRef` nodes - for
    `self`, `self.x`, and `self.q`. Their summation does not happen "under"
    a `Attribute` access, so it is ignored.

    :class:`ASTBindNodeRef` instances describe subgraphs within the larger
    ast graph. As can be seen, :class:`ASTBindNodeRef` points to nodes
    that depend on it (children) and that it depends on (parents)- that defines
    the subgraph that we may need to rebind to.

    Nodes that evaluate to the same string, e.g. in `self.x + self.x`, `self.x`
    occurs twice, but in the graph we create, we only create one node for
    `self` and one node for `self.x`. Similarly, for `self.x + self.y`, only
    3 nodes are created.

    Examples so far, all created one subgraph - but we can have more than one.
    E.g. `self.x + other.x` creates two independent graphs, one for `self.x`
    and one for `other.x`, each composed of two nodes because they share no
    common nodes. But e.g.
    `(self.x + other.y).z` will create one subgraph with 6 nodes, a node for
    each operation because they all happen under the same `Attribute` leaf so
    it describes one graph.

    The key thing to remember is that parent nodes are processed before
    children. This order determines the linear order of the nodes as they
    get added to :attr:`nodes_by_rule`. This means
    that when a node is encountered in the :attr:`nodes_by_rule` lists, all
    their parents are present in the lists
    at indices previous to that node. In other words, if we walk the lists
    linearly, we encounter a node only after all its dependencies. This key
    property is used by the compiler to help reason about the graph order.

    There are two syntax flavors, `"minimal"` and the the full syntax.
    The `"minimal"` version only rebinds to nodes that are attribute access
    or slice access. E.g. `self.x[self.y].z`. The full syntax, allows also
    e.g. `(self.x + other.y).z` and would also rebind to the `z` property of
    `(self.x + other.y)`. The `"minimal"` syntax in this case would only rebind
    to `self.x` and `other.y`.

    This is used by calling :meth:`update_graph` once for each rule, where we
    pass the ast nodes for a rule to that function at once. The idea is to
    create graphs that represent bindings across all the rules, while
    also tracking which rule a (leaf) node came from. E.g. if we had two
    rules - `self.x + self.y`, and `self.x.z + 55 + self.y`, then we
    would create one graph: self -> x, self -> y, x -> z that describes the
    bindings for the rules. Additionally, we would create a leaf from `x`, `y`
    for the first rule, and `z`, `y` for the second. You can see more in the
    visualization module.

    Currently, all comprehensions and lambda are treated as opaque so
    we don't bind to anything within it.
    '''
    # no Name node that is a Store shall be saved in any of the graphs. It's
    # not included anyway because it cannot be an expression, but we should not
    # include either way because in the compiler we use all Name that we
    # encountered here to identify local vars for
    # capturing and making them readonly and verified by the
    # verifier later. That assumes that they are all Load in this stage because
    # we don't check in this class.

    src_node_map = {}
    '''For each non leaf :class:`ASTBindNodeRef` node we create (i.e.
    :attr:`ASTBindNodeRef.leaf_rule` is `None`), we map the source code
    representation of the node (:attr:`ASTBindNodeRef.src`) to the node. E.g.
    for `self.x.y` we create three reference nodes with the corresponding
    representation, `"self"`, `"self.x"`, and `"self.x.y"`.

    This helps find duplicates across all rules, e.g. for `self.x + self.x`, we
    only create two nodes for `"self"` and `"self.x"` the first time we
    encounter them. The second time, we just re-use the existing node for
    `self` and increment its :attr:`ASTBindNodeRef.count`. The second time we
    encounter `self.x` in this rule, we don't create a new leaf because
    :attr:`leaf_nodes_in_rule` tracks the already seen leaf nodes per rule.
    '''

    under_attr = False

    nodes_by_rule = []
    '''For each rule (each time we call :meth:`update_graph`), we add a new
    list here that contains all the :class:`ASTBindNodeRef` that were created
    for this rule. Existing nodes that are re-used from previous rules are
    not added.

    The order is such that if we were to linearly walk across all the lists in
    order in :attr:`nodes_by_rule`, when we a encounter a node, all the parents
    of the node, up to the roots would have been encountered by the time
    we reach the node. This means that the node deps are always encountered
    first. But, unrelated nodes may also be present before reaching the node,
    even if they are not parents.
    '''

    src_nodes = []
    '''During each rule, it creates the list of :class:`ASTBindNodeRef`
    instances that were created due to this rule. Re-used nodes from previous
    rules are not added.
    '''

    current_child_node = None
    '''As we walk the bind graph nodes, for each expression node we create
    a :class:`ASTBindNodeRef` that references the node and add it to
    :attr:`nodes_by_rule`. The node is stored here
    while we explore its parent tree. Then, all the direct parent's of this
    node will point to this node using their
    :attr:`ASTBindNodeRef.depend_on_me` and this node's
    :attr:`ASTBindNodeRef.depends` will point to the parents.
    '''

    visited = set()

    current_rule = None
    '''During the processing of a rule in :meth:`update_graph`, we store
    here the `rule` parameter passed to :meth:`update_graph`. Its value is used
    to set :attr:`ASTBindNodeRef.leaf_rule` for leaf nodes.
    '''

    leaf_nodes_in_rule = set()
    '''For each rule, while the rule is processed it keeps track of the leaf
    nodes in this rule we encountered already. This prevent creating duplicate
    copies of e.g. `self.x + self.x` for the same rule. So if we already saw
    this exact leaf in the rule, we don't add a node for it again.
    '''

    nodes_under_leaf = set()
    '''For every rule and for every leaf, this stores all the nodes that we
    encountered while processing the parents of the leaf.'''

    illegal_parent_check = None
    '''Stores the :class:`ParseCheckWhitelisted` we use to check for
    whitelisted nodes when not all classes are whitelisted. Otherwise, it's
    None.
    '''

    whitelist_opts = {
        'minimal': {
            'Name', 'Num', 'Bytes', 'Str', 'NameConstant', 'Subscript',
            'Attribute'}
    }
    '''For each syntax flavor, the values is a set of the names of AST node
    classes that is allowed to be "under" a `Attribute`. If we encounter a
    non-whitelisted class and :attr:`illegal_parent_check` is not None, the
    nodes between the `Attribute` and illegal node would be dropped from the
    bind graph.
    '''

    def __init__(self, kv_syntax=None):
        super(ParseKVBindTransformer, self).__init__()
        self.src_node_map = {}
        self.nodes_by_rule = []
        self.visited = set()

        if kv_syntax is not None:
            if kv_syntax not in self.whitelist_opts:
                raise ValueError(
                    'kv_syntax can be either None or one of ({}, ), not {}'.
                    format(', '.join(self.whitelist_opts.keys()), kv_syntax))
            self.illegal_parent_check = ParseCheckWhitelisted(
                self.whitelist_opts[kv_syntax])

    def update_graph(self, nodes, rule):
        '''Adds the nodes of the the rule to the existing bind graph.

        It creates a new rule list in :attr:`nodes_by_rule` and all nodes
        newly created due to this rule are added to it.
        '''
        if rule is None:
            raise ValueError('rule cannot be None')

        self.current_rule = rule
        self.src_nodes = src_nodes = []
        self.leaf_nodes_in_rule = set()
        self.nodes_by_rule.append(src_nodes)

        # compute the nodes that are not whitelisted.
        if self.illegal_parent_check is not None:
            for node in nodes:
                self.illegal_parent_check.check_node_graph(node)

        for node in nodes:
            self.visit(node)

    def generic_visit(
            self, node, is_attribute=False, is_final_attribute=False):
        # this is probably not needed anymore because nodes are not visited
        # multiple times
        if node in self.visited:
            return node
        self.visited.add(node)

        # once under an `Attribute`, we save all the nodes that participate
        if self.under_attr and isinstance(node, ast.expr):
            if is_final_attribute:
                self.nodes_under_leaf = set()

            # save the last child, and make yourself the new child
            current_child_node = self.current_child_node
            self.current_child_node = ret_node = ASTBindNodeRef(
                is_attribute)

            try:
                # explore the parents, who will link to current_child_node
                node = super(ParseKVBindTransformer, self).generic_visit(node)
            finally:
                self.current_child_node = current_child_node

            src = generate_source(node)
            # a final attt means that it's e.g. y in self.x.y. In other words,
            # it's not a rebind but is what causes a rule to be executed when
            # dispatched. These are leaf nodes, and we always create them, even
            # if one already existed (unless they are part of the same rule).
            if is_final_attribute:
                # they are all unique so we don't de-duplicate
                assert is_attribute
                assert current_child_node is None

                # we only de-duplicate if the exact leaf occurred already in
                # this rule. This prevents creating identical copies e.g.
                # for a rule `self.x + self.x`.
                if src in self.leaf_nodes_in_rule:
                    # this node will not be added to the graph - remove it from
                    # parents that it was added as a child of while exploring.
                    for item in self.nodes_under_leaf:
                        item.count -= 1
                    return node
                self.leaf_nodes_in_rule.add(src)

                ret_node.set_ref_node(node)
                ret_node.src = src
                ret_node.count += 1
                ret_node.leaf_rule = self.current_rule
                self.src_nodes.append(ret_node)
                # everyone that I depend on, depends on me
                for dep in ret_node.depends:
                    dep.depends_on_me.append(ret_node)
            else:
                # Now we are not a leaf, but some intermediate node to a leaf.
                # Either we already saw a graph with a unique root path to
                # this node
                if src in self.src_node_map:
                    # if we did, replace the re-occurrence with the node of the
                    # first occurrence. Abandon ret_node, everything there is
                    # a duplication of the first occurrence
                    ret_node = self.src_node_map[src]
                    # if we saw the node already under *this* leaf, then the
                    # rule is something like a diamond (self.x[self.x].z or
                    # self.x[self.x.y].z). In that case, don't count self again
                    # because we only bind one rebind callback for any
                    # attribute for each rule.
                    if ret_node not in self.nodes_under_leaf:
                        self.nodes_under_leaf.add(ret_node)
                        # bump the count for this occurrence
                        ret_node.count += 1
                else:
                    # if we didn't, create a node representing this path
                    ret_node.set_ref_node(node)
                    ret_node.src = src
                    self.src_node_map[src] = ret_node
                    self.src_nodes.append(ret_node)
                    # everyone that I depend on, depends on me
                    for dep in ret_node.depends:
                        dep.depends_on_me.append(ret_node)

                    ret_node.count += 1
                    self.nodes_under_leaf.add(ret_node)

                # if it's None, we hit the final (root) expr of the graph
                if ret_node not in current_child_node.depends:
                    current_child_node.depends.append(ret_node)
        else:
            ret_node = super(ParseKVBindTransformer, self).generic_visit(node)
        return ret_node

    def visit_Attribute(self, node):
        if self.under_attr:
            # if it's under an Attribute already, that this node cannot contain
            # non-whitelisted nodes in its parent graph
            return self.generic_visit(node, is_attribute=True)

        # if not whitelisted, then we don't count this attribute.
        if self.illegal_parent_check is not None and \
                self.illegal_parent_check.node_has_illegal_parent[node]:
            # this attribute contains a non-whitelisted node in the parent
            # graph so this won't be rebound.
            return super(ParseKVBindTransformer, self).generic_visit(node)

        self.under_attr = True
        node = self.generic_visit(
            node, is_attribute=True, is_final_attribute=True)
        self.under_attr = False
        return node

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


class ParseKVFunctionTransformer(ast.NodeTransformer):
    '''
    Transforms and parses the KV decorated function and creates all the graphs
    required for the generation of compiled source code.

    Notes:

    The most important things is that we cannot allow a kv rule to be
    conditionally executed because we'd be lying to the user.

    E.g. a return statement is forbidden within a kv context.

    There's another problem to avoid, having callbacks use variables that
    are not available anymore or has changed. Therefore, we capture all the
    variables, local, nonlocal, and global defined before the rule and provide
    it to the callback (side note, that improves speed). Therefore, some
    statements, e.g. a function def contains local variables which is too hard
    to trace, so we don't allow it within a rule at all as we cannot figure
    out which variables need to be captured (yet).

    This transformer is not allowed to change nodes (except trivially), except
    for changing kv rule and ctx from with to plain assignment, and similarly
    from x @= y or x ^= y to x = y.
    '''

    current_ctx_info = None

    current_rule_info = None

    node_classes_within_ctx = None

    context_infos = []
    # contexts are added in the order they are entered, not existed.

    kv_syntax = None

    kv_ctx_cls_name = '__KVCtx'

    rules_by_occurrence = []
    # rules cannot contain other rules, so the order is flat always

    illegal_node_classes_within_ctx = {
        ast.If, ast.For, ast.While, ast.Suite, ast.FunctionDef,
        ast.AsyncFor, ast.AsyncFunctionDef, ast.ExceptHandler, ast.ClassDef}

    known_ast = {
        ast.AST, ast.operator, ast.Add, ast.alias, ast.boolop, ast.And,
        ast.arg, ast.arguments, ast.stmt, ast.Assert, ast.Assign, ast.AsyncFor,
        ast.AsyncFunctionDef, ast.AsyncWith, ast.expr, ast.Attribute,
        ast.AugAssign, ast.expr_context, ast.AugLoad, ast.AugStore, ast.Await,
        ast.BinOp, ast.BitAnd, ast.BitOr, ast.BitXor, ast.BoolOp, ast.Break,
        ast.Bytes, ast.Call, ast.ClassDef, ast.cmpop, ast.Compare,
        ast.comprehension, ast.Continue, ast.Del, ast.Delete, ast.Dict,
        ast.DictComp, ast.Div, ast.Ellipsis, ast.Eq, ast.excepthandler,
        ast.ExceptHandler, ast.Expr, ast.mod, ast.Expression, ast.slice,
        ast.ExtSlice, ast.FloorDiv, ast.For, ast.FunctionDef, ast.GeneratorExp,
        ast.Global, ast.Gt, ast.GtE, ast.If, ast.IfExp, ast.Import,
        ast.ImportFrom, ast.In, ast.Index, ast.Interactive, ast.unaryop,
        ast.Invert, ast.Is, ast.IsNot, ast.keyword, ast.Lambda, ast.List,
        ast.ListComp, ast.Load, ast.LShift, ast.Lt, ast.LtE, ast.MatMult,
        ast.Mod, ast.Module, ast.Mult, ast.Name, ast.NameConstant,
        ast.Nonlocal, ast.Not, ast.NotEq, ast.NotIn, ast.Num, ast.Or,
        ast.Param, ast.Pass, ast.Pow, ast.Raise, ast.Return, ast.RShift,
        ast.Set, ast.SetComp, ast.Slice, ast.Starred, ast.Store, ast.Str,
        ast.Sub, ast.Subscript, ast.Suite, ast.Try, ast.Tuple, ast.UAdd,
        ast.UnaryOp, ast.USub, ast.While, ast.With, ast.withitem,
        ast.Yield, ast.YieldFrom}

    def __init__(self, kv_syntax=None):
        super(ParseKVFunctionTransformer, self).__init__()
        self.context_infos = []
        self.rules_by_occurrence = []

        if kv_syntax is not None:
            if kv_syntax not in ('minimal', ):
                raise ValueError(
                    'kv_syntax can be either None or "minimal", not {}'.
                    format(kv_syntax))
        self.kv_syntax = kv_syntax

    def visit(self, node):
        if isinstance(node, list):
            return [
                None if item is None else
                super(ParseKVFunctionTransformer, self).visit(item)
                for item in node]
        return super(ParseKVFunctionTransformer, self).visit(node)

    def generic_visit(self, node):
        if node.__class__ not in self.known_ast:
            raise KVCompilerParserException(
                'ast class {} not recognized. If it is a new python feature '
                'it will need to be whitelisted'.format(node.__class__))
        classes = self.node_classes_within_ctx
        if classes is not None:
            classes[node.__class__] += 1
        ret_node = super(ParseKVFunctionTransformer, self).generic_visit(node)
        if classes is not None:
            classes[node.__class__] -= 1
        return ret_node

    def visit_With(self, node):
        func_name = None
        args = keywords = assigned_var = None
        for with_item in node.items:
            assert isinstance(with_item, ast.withitem)
            expr = with_item.context_expr
            if not isinstance(expr, ast.Call):
                continue

            f_name = expr.func
            name = None
            if isinstance(f_name, ast.Attribute):
                name = f_name.attr
            elif isinstance(f_name, ast.Name):
                name = f_name.id

            if name in ('KVCtx', 'KVRule'):
                func_name = name
                args = expr.args
                keywords = expr.keywords
                assigned_var = with_item.optional_vars
                break

        if func_name is not None and len(node.items) > 1:
            raise KVCompilerParserException(
                'Multiple with statements not allowed for {}'.
                format(func_name))

        if func_name is None:
            return self.generic_visit(node)

        if func_name == 'KVCtx':
            ret_node = self.process_kv_with_ctx_node(
                node, args, keywords, assigned_var)
        else:
            assert func_name == 'KVRule'
            ret_node = self.process_kv_with_rule_node(
                node, args, keywords, assigned_var)

        return ret_node

    def start_kv_ctx(self, ctx_info):
        pass

    def finish_kv_ctx(self, ctx_info):
        pass

    def process_kv_with_ctx_node(self, node, args, keywords, assigned_var):
        if self.current_rule_info is not None:
            raise KVCompilerParserException('Cannot have context within rule')
        if args or keywords:
            raise KVCompilerParserException(
                'KVCtx takes no positional or keyword arguments currently')

        ctx = KVParserCtx()
        transformer = ParseKVBindTransformer(self.kv_syntax)
        ctx.set_kv_binding_ast_transformer(transformer)

        previous_ctx_info = self.current_ctx_info
        ctx_info = self.current_ctx_info = {
            'ctx': ctx, 'args': args, 'keywords': keywords,
            'rules': [], 'node': node,
            'assign_target_node': ast.Name(id='__xxx', ctx=ast.Store()),
            'before_ctx': ASTStrPlaceholder(),
            'after_ctx': ASTStrPlaceholder()}
        self.start_kv_ctx(ctx_info)
        # they must be added in the order it is entered
        self.context_infos.append(ctx_info)

        previous_node_classes = self.node_classes_within_ctx
        self.node_classes_within_ctx = defaultdict(int)
        ret_nodes = []
        for item in node.body:
            res = self.visit(item)
            if isinstance(res, list):
                ret_nodes.extend(res)
            else:
                ret_nodes.append(res)
        self.finish_kv_ctx(ctx_info)
        self.current_ctx_info = previous_ctx_info
        self.node_classes_within_ctx = previous_node_classes

        for rule_info in ctx_info['rules']:
            rule = rule_info['rule']
            rule.binds = rule_info['binds']
            rule.captures = rule_info['captures']
            rule.src = generate_source(rule_info['body'])
            ctx.add_rule(rule)

        targets = [ctx_info['assign_target_node']]
        if assigned_var:
            targets.append(assigned_var)

        assign_node = ast.Assign(
            targets=targets,
            value=ast.Call(
                func=ast.Name(id=self.kv_ctx_cls_name, ctx=ast.Load()),
                args=[], keywords=[]))

        return [assign_node, ctx_info['before_ctx']] + ret_nodes + [
            ctx_info['after_ctx']]

    def start_kv_rule(self, ctx_info, rule_info):
        self.rules_by_occurrence.append((ctx_info, rule_info))

    def finish_kv_rule(self, ctx_info, rule_info):
        pass

    def process_kv_with_rule_node(self, node, args, keywords, assigned_var):
        ctx_info = self.current_ctx_info
        if ctx_info is None:
            raise KVCompilerParserException(
                'Cannot have KVRule outside of a KVCtx')
        if self.current_rule_info is not None:
            raise KVCompilerParserException('Cannot have rule within rule')

        node_classes = self.node_classes_within_ctx
        assert node_classes is not None
        illegal_classes = set(cls for cls, n in node_classes.items() if n) & \
            self.illegal_node_classes_within_ctx
        if illegal_classes:
            raise KVCompilerParserException(
                'KV rule cannot be under conditionally executing code, the '
                'following code objects were found containing the rule: {}. '
                'You can wrap the rule under a new KV context instead'.
                format(illegal_classes))

        rules = ctx_info['rules']
        name = delay = None
        for keyword in keywords:
            if keyword.arg == 'name':
                val = keyword.value
                if not isinstance(val, ast.Str):
                    raise KVCompilerParserException(
                        'Cannot parse {}, must be a string'.format(val))
                name = val.s
            elif keyword.arg == 'delay':
                val = keyword.value
                if isinstance(val, ast.NameConstant):
                    if val.value is not None:
                        raise KVCompilerParserException(
                            'Cannot parse {}, must be one of '
                            'canvas/number/None'.format(val.value))
                elif isinstance(val, ast.Str):
                    if val.s != 'canvas':
                        raise KVCompilerParserException(
                            'Cannot parse {}, must be one of '
                            'canvas/number/None'.format(val.s))
                    delay = val.s
                elif isinstance(val, ast.Num):
                    delay = val.n
                elif isinstance(val, ast.UnaryOp) and isinstance(
                        val.operand, ast.Num):
                    if isinstance(val.op, ast.USub):
                        delay = -val.operand.n
                    elif isinstance(val.op, ast.UAdd):
                        delay = val.operand.n
                    else:
                        assert False
                else:
                    raise KVCompilerParserException(
                        'Cannot parse {}, must be one of canvas/number/None'.
                        format(val))
            else:
                raise KVCompilerParserException(
                    'Got unrecognized keyword {}'.format(keyword.arg))

        for i, arg in enumerate(args):
            # convert strings bind instructions to ast
            if isinstance(arg, ast.Str):
                mod = ast.parse(arg.s)
                assert len(mod.body) == 1
                args[i] = mod.body[0].value

        # locals are any vars that has been defined originally in the rule,
        # i.e. it was stored before any load.
        # currently_locals, are vars defined within a conditional context, e.g.
        # a if or for loop. At the end of the conditional, currently_locals
        # do not become locals, because locals must be always defined in the
        # rule and if it's defined only in the conditional, that is not the
        # case. For variables that leak out from a conditional context,
        # currently_locals become possibly_locals after the context, indicating
        # the variable may be in a UnboundLocalError situation.
        rule = self.current_rule_info = {
            'node': node, 'binds': list(args),
            'from_with': True, 'body': None,
            'locals': set(), 'captures': set(), 'currently_locals': None,
            'possibly_locals': set(), 'rule': KVParserRule(
                delay=delay, name=name)}
        rule['args_binds'] = list(rule['binds'])
        self.start_kv_rule(ctx_info, rule)

        rule['body'] = node_list = ASTNodeList()
        node_list.nodes = self.visit(node.body)
        rules.append(rule)
        self.finish_kv_rule(ctx_info, rule)
        self.current_rule_info = None

        if assigned_var is not None:
            rule_var_name = rule['rule'].with_var_name_ast = ast.Name(
                id='__xxx', ctx=ast.Load())
            # we don't visit this node. If we did, it'd have to be *before* and
            # outside setting self.current_rule_info to the rule so that the
            # visit to assign name happens in chronological order
            assign_node = ast.Assign(
                targets=[assigned_var], value=rule_var_name)
            node_list = ASTNodeList()
            node_list.nodes = [assign_node] + rule['body'].nodes

        return node_list

    def do_kv_assign(self, node, delay=None):
        ctx_info = self.current_ctx_info
        if ctx_info is None:
            raise KVCompilerParserException(
                'Cannot have KVRule outside of a KVCtx')

        node_classes = self.node_classes_within_ctx
        assert node_classes is not None
        illegal_classes = set(cls for cls, n in node_classes.items() if n) & \
            self.illegal_node_classes_within_ctx
        if illegal_classes:
            raise KVCompilerParserException(
                'KV rule cannot be under conditionally executing code, the '
                'following code objects were found containing the rule: {}'.
                format(illegal_classes))

        previous_rule_info = self.current_rule_info
        if previous_rule_info is None:
            rule = self.current_rule_info = {
                'node': node,
                'binds': [node.value], 'from_with': False,
                'body': None, 'locals': set(), 'captures': set(),
                'currently_locals': None, 'possibly_locals': set(),
                'rule': KVParserRule(delay=delay), 'args_binds': []}
            self.start_kv_rule(ctx_info, rule)

            self.visit(node.value)
            self.visit(node.target)
            ctx_info['rules'].append(rule)
            self.finish_kv_rule(ctx_info, rule)
            self.current_rule_info = None

            assign = ast.Assign(targets=[node.target], value=node.value)
            rule['body'] = assign
            return assign
        else:
            if delay != previous_rule_info['rule'].delay and not (
                    isinstance(previous_rule_info['rule'].delay,
                               (int, float)) and delay is None):
                raise KVCompilerParserException(
                    'A rule can only have a single delay type (one of '
                    'canvas/number/None). The rule delay type was previously '
                    'declared as {}, but was attempted to be redefined to {}'.
                    format(previous_rule_info['rule'].delay, delay))
            self.visit(node.value)
            self.visit(node.target)
            previous_rule_info['binds'].append(node.value)

            return ast.Assign(targets=[node.target], value=node.value)

    def visit_AugAssign(self, node):
        # these become a store instead of a load/store
        if isinstance(node.op, ast.MatMult):
            return self.do_kv_assign(node, None)
        elif isinstance(node.op, ast.BitXor):
            return self.do_kv_assign(node, 'canvas')

        # visit_Name for target process it only as Store, but it should also be
        # proceeded by a load, which we do manually here
        current_rule = self.current_rule_info
        if current_rule is not None:
            if isinstance(node.target, ast.Name):
                val = node.target.id
                if val not in current_rule['locals'] and (
                        current_rule['currently_locals'] is None or
                        val not in current_rule['currently_locals']) and \
                        val not in current_rule['captures']:
                    if False and val in current_rule['possibly_locals']:
                        raise KVCompilerParserException(
                            'variable {} may or may not have been set within a'
                            ' conditional or loop and is therefore not allowed'
                            ' in KV. Make sure the variable is always defined'.
                            format(val))
                    current_rule['captures'].add(val)
        return self.generic_visit(node)

    def visit_Name(self, node):
        current_rule = self.current_rule_info
        if current_rule is not None:
            if isinstance(node.ctx, ast.Load):
                if node.id not in current_rule['locals'] and (
                        current_rule['currently_locals'] is None or
                        node.id not in current_rule['currently_locals']) and \
                        node.id not in current_rule['captures']:
                    if False and node.id in current_rule['possibly_locals']:
                        raise KVCompilerParserException(
                            'variable {} may or may not have been set within a'
                            ' conditional or loop and is therefore not allowed'
                            ' in KV. Make sure the variable is always defined'.
                            format(node.id))
                    current_rule['captures'].add(node.id)
            elif isinstance(node.ctx, ast.Store):
                if current_rule['currently_locals'] is None:
                    current_rule['locals'].add(node.id)
                else:
                    current_rule['currently_locals'].add(node.id)
            else:
                # how can we del a var in the callback? What if it was def
                # outside the rule? The callback will freak out. So it's
                # illegal in KV.
                raise KVCompilerParserException(
                    'A variable cannot be deleted within a KV rule')
        return self.generic_visit(node)

    def visit_Assign(self, node):
        assert set(node._fields) == {'targets', 'value'}
        # the node needs to visit value before targets because e.g.
        # `var = x + var`, we need to know if `var` was already existing in
        # captures before this call
        node.value = self.visit(node.value)
        node.targets = self.visit(node.targets)
        return node

    def visit_ImportFrom(self, node):
        current_rule = self.current_rule_info
        if current_rule is not None:
            for name in node.names:
                assert isinstance(name, ast.alias)
                if current_rule['currently_locals'] is None:
                    current_rule['locals'].add(name.asname or name.name)
                else:
                    current_rule['currently_locals'].add(
                        name.asname or name.name)
        return self.generic_visit(node)

    def visit_Import(self, node):
        current_rule = self.current_rule_info
        if current_rule is not None:
            for name in node.names:
                assert isinstance(name, ast.alias)
                name_split = name.name.split('.')
                if len(name_split) == 1:
                    if current_rule['currently_locals'] is None:
                        current_rule['locals'].add(name_split[0])
                    else:
                        current_rule['currently_locals'].add(name_split[0])
        return self.generic_visit(node)

    def do_loop(self, node, loop='for'):
        current_rule = self.current_rule_info
        if current_rule is None:
            return self.generic_visit(node)

        if loop == 'for':
            assert set(node._fields) == {'target', 'iter', 'body', 'orelse'}
            node.iter = self.visit(node.iter)
        else:
            assert set(node._fields) == {'test', 'body', 'orelse'}
            node.test = self.visit(node.test)

        original = current_rule['currently_locals']
        current_rule['currently_locals'] = set(original) if original else set()
        if loop == 'for':
            node.target = self.visit(node.target)

        node.body = self.visit(node.body)
        current_rule['possibly_locals'].update(
            current_rule['currently_locals'])

        current_rule['currently_locals'] = set(original) if original else set()
        node.orelse = self.visit(node.orelse)
        current_rule['possibly_locals'].update(
            current_rule['currently_locals'])

        current_rule['currently_locals'] = original
        return node

    def visit_For(self, node):
        return self.do_loop(node)

    def visit_AsyncFor(self, node):
        return self.do_loop(node)

    def visit_While(self, node):
        return self.do_loop(node, loop='while')

    def visit_comprehension(self, node):
        assert self.current_rule_info is None, 'it is dealt with below'
        return self.generic_visit(node)

    def do_generators(self, node, current_rule):
        original = current_rule['currently_locals']
        current_rule['currently_locals'] = set(original) if original else set()

        for item in node.generators:
            assert isinstance(item, ast.comprehension)
            assert item._fields == ('target', 'iter', 'ifs') or \
                   item._fields == ('target', 'iter', 'ifs', 'is_async')
            # iter MUST be first because that is before locals are created in
            # the comprehension
            item.iter = self.visit(item.iter)
            item.target = self.visit(item.target)
            item.ifs = self.visit(item.ifs)
        return original

    def do_simple_comp(self, node):
        current_rule = self.current_rule_info
        if current_rule is None:
            return self.generic_visit(node)
        assert set(node._fields) == {'elt', 'generators'}

        original = self.do_generators(node, current_rule)
        node.elt = self.visit(node.elt)
        # no need to update possible locals, because comp variables don'y leak
        # out to the outside context
        current_rule['currently_locals'] = original
        return node

    def visit_ListComp(self, node):
        return self.do_simple_comp(node)

    def visit_SetComp(self, node):
        return self.do_simple_comp(node)

    def visit_GeneratorExp(self, node):
        return self.do_simple_comp(node)

    def visit_DictComp(self, node):
        current_rule = self.current_rule_info
        if current_rule is None:
            return self.generic_visit(node)
        assert set(node._fields) == {'key', 'value', 'generators'}

        original = self.do_generators(node, current_rule)
        node.key = self.visit(node.key)
        node.value = self.visit(node.value)

        # no need to update possible locals, because comp variables don'y leak
        # out to the outside context
        current_rule['currently_locals'] = original
        return node

    def visit_If(self, node):
        current_rule = self.current_rule_info
        if current_rule is None:
            return self.generic_visit(node)

        assert set(node._fields) == {'test', 'body', 'orelse'}
        node.test = self.visit(node.test)

        original = current_rule['currently_locals']
        current_rule['currently_locals'] = set(original) if original else set()
        node.body = self.visit(node.body)
        current_rule['possibly_locals'].update(
            current_rule['currently_locals'])

        current_rule['currently_locals'] = set(original) if original else set()
        node.orelse = self.visit(node.orelse)
        current_rule['possibly_locals'].update(
            current_rule['currently_locals'])

        current_rule['currently_locals'] = original
        return node

    def visit_Try(self, node):
        current_rule = self.current_rule_info
        if current_rule is None:
            return self.generic_visit(node)

        assert set(node._fields) == {'body', 'handlers', 'orelse', 'finalbody'}
        node.body = self.visit(node.body)
        node.handlers = self.visit(node.handlers)

        original = current_rule['currently_locals']
        current_rule['currently_locals'] = set(original) if original else set()
        node.orelse = self.visit(node.orelse)
        current_rule['possibly_locals'].update(
            current_rule['currently_locals'])

        current_rule['currently_locals'] = set(original) if original else set()
        node.finalbody = self.visit(node.finalbody)
        current_rule['possibly_locals'].update(
            current_rule['currently_locals'])

        current_rule['currently_locals'] = original
        return node

    def visit_ExceptHandler(self, node):
        current_rule = self.current_rule_info
        if current_rule is None:
            return self.generic_visit(node)

        assert set(node._fields) == {'type', 'name', 'body'}
        if node.type is not None:
            node.type = self.visit(node.type)

        original = current_rule['currently_locals']
        current_rule['currently_locals'] = set(original) if original else set()
        if node.name is not None:
            current_rule['currently_locals'].add(node.name)
        node.body = self.visit(node.body)
        current_rule['possibly_locals'].update(
            current_rule['currently_locals'])

        current_rule['currently_locals'] = original
        return node

    def visit_Lambda(self, node):
        current_rule = self.current_rule_info
        if current_rule is None:
            return self.generic_visit(node)

        assert set(node._fields) == {'args', 'body'}

        args = node.args
        assert set(args._fields) == {
            'args', 'vararg', 'kwonlyargs', 'kw_defaults', 'kwarg', 'defaults'}

        # these must happen before the others because e.g. lambda y, x=y: 55
        # should not get confused that the seconds y has already been created
        # when the first y is written. So all the keyword values are processed
        # first and added to captured if needed
        args.kw_defaults = [
            None if val is None else self.visit(val)
            for val in args.kw_defaults]
        args.defaults = [
            None if val is None else self.visit(val)
            for val in args.defaults]

        original = current_rule['currently_locals']
        current_rule['currently_locals'] = set(original) if original else set()
        # we don't need to visit the following, because we don't change them
        if args.vararg:
            assert isinstance(args.vararg, ast.arg)
            current_rule['currently_locals'].add(args.vararg.arg)
        if args.kwarg:
            assert isinstance(args.kwarg, ast.arg)
            current_rule['currently_locals'].add(args.kwarg.arg)
        for item in args.args:
            assert isinstance(item, ast.arg)
            current_rule['currently_locals'].add(item.arg)
        for item in args.kwonlyargs:
            assert isinstance(item, ast.arg)
            current_rule['currently_locals'].add(item.arg)

        node.body = self.visit(node.body)
        # no need to update possible locals, because lambda variables don't
        # leak out to the outside context
        current_rule['currently_locals'] = original
        return node

    def visit_illegal_closure_node(self, node):
        if self.current_rule_info is not None:
            raise KVCompilerParserException(
                '{} is not allowed within a KV rule because it '
                'creates a closure with possible nonlocal variables, which '
                'would be ill defined within a KV callback.'.
                format(node.__class__.__name__))
        return self.generic_visit(node)

    def visit_FunctionDef(self, node):
        return self.visit_illegal_closure_node(node)

    def visit_AsyncFunctionDef(self, node):
        return self.visit_illegal_closure_node(node)

    def visit_ClassDef(self, node):
        return self.visit_illegal_closure_node(node)

    def visit_Return(self, node):
        if self.current_ctx_info:
            raise KVCompilerParserException(
                'Return is not allowed within a KV context')
        return self.generic_visit(node)

    def visit_Global(self, node):
        raise KVCompilerParserException(
            'It is illegal to use global in a KV decorated function because '
            'the kv callbacks may fail')

    def visit_Nonlocal(self, node):
        raise KVCompilerParserException(
            'It is illegal to use nonlocal in a KV decorated function because '
            'the kv callbacks may fail')


class DoNothingAST(ast.AST):
    '''An AST node indicating that nothing should generated in the source code.
    '''

    pass


class ParseExpressionNameLoadTransformer(ast.NodeTransformer):
    '''
    AST transformer that finds all the Name nodes in the graph.
    '''

    names = set()

    def __init__(self):
        super(ParseExpressionNameLoadTransformer, self).__init__()
        self.names = set()

    def visit_Lambda(self, node):
        return node

    def visit_ListComp(self, node):
        return node

    def visit_SetComp(self, node):
        return node

    def visit_GeneratorExp(self, node):
        return node

    def visit_DictComp(self, node):
        return node

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.names.add(node.id)
        return node

    def visit_ASTBindNodeRef(self, node, *largs, **kwargs):
        return self.visit(node.ref_node, *largs, **kwargs)


class VerifyKVCaptureOnExitTransformer(ParseKVFunctionTransformer):
    '''
    AST transformer that verifies that captured variables are not modified
    and are read only, for the case where the bindings occur upon KVCtx exit.
    '''
    # we can overwrite e.g. list comp visit because it cannot alter the
    # creation of new rules/ctx. But anything that changes rule or ctx creation
    # is now allowed here as it would make the first and second pass
    # inconsistent

    # why do we need to both process loads in visit_Node and get the captures
    # from the first pass rules? Because imagine a `with` rule containing 2
    # lines: `x = obj; z @= x.y + 10`. Because `x` is a local to the rule,
    # captues will not include x, meaning we'd be free to modify x after
    # the rule. But then the bind will not bind to the same x as in the
    # original rule. That's why here we make any load Name within a rule
    # readonly.
    # The callback is not the problem, because the callback only cares about
    # captures variables and local vars can be changed in the callback.

    ro_ctx_stack = None

    current_read_only_vars = set()

    under_kv_aug_assign = False

    first_pass_rules = None

    first_pass_contexts = None

    current_ctx_stack = []

    current_verify_rule_info = None

    def __init__(self, first_pass_rules, first_pass_contexts, **kwargs):
        super(VerifyKVCaptureOnExitTransformer, self).__init__(**kwargs)
        self.ro_ctx_stack = deque()
        self.current_ctx_stack = deque()
        self.first_pass_rules = deque(first_pass_rules)
        self.first_pass_contexts = deque(first_pass_contexts)

    def start_kv_ctx(self, ctx_info):
        self.first_pass_contexts.popleft()
        self.ro_ctx_stack.appendleft(self.current_read_only_vars)
        self.current_read_only_vars = set(self.current_read_only_vars)

    def finish_kv_ctx(self, ctx_info):
        self.current_read_only_vars = self.ro_ctx_stack.popleft()

    def start_kv_rule(self, ctx_info, rule_info):
        _, rule_info_0 = self.first_pass_rules[0]

        t = ParseExpressionNameLoadTransformer()
        for arg in rule_info_0['args_binds']:
            t.visit(arg)
        self.current_read_only_vars.update(t.names)

        assert self.current_verify_rule_info is None
        self.current_verify_rule_info = rule_info

    def finish_kv_rule(self, ctx_info, rule_info):
        _, rule_info_0 = self.first_pass_rules.popleft()
        self.current_read_only_vars.update(rule_info_0['captures'])
        self.current_verify_rule_info = None

    def visit_AugAssign(self, node):
        # these become a store instead of a load/store
        if isinstance(node.op, ast.MatMult):
            # In case target is a load, we don't want to include it in
            # visit_Name below because the load on the left of the assign is
            # never bound to so there's no reason to make it read only
            self.under_kv_aug_assign = True
            ret = super(
                VerifyKVCaptureOnExitTransformer, self).visit_AugAssign(node)
            self.under_kv_aug_assign = False
        elif isinstance(node.op, ast.BitXor):
            self.under_kv_aug_assign = True
            ret = super(
                VerifyKVCaptureOnExitTransformer, self).visit_AugAssign(node)
            self.under_kv_aug_assign = False
        else:
            # super will check out if Store and we'll see it under visit_Name
            ret = super(
                VerifyKVCaptureOnExitTransformer, self).visit_AugAssign(node)
        return ret

    def visit_Name(self, node):
        if self.under_kv_aug_assign and isinstance(node.ctx, ast.Load):
            self.current_read_only_vars.add(node.id)
        if isinstance(node.ctx, ast.Store) or isinstance(node.ctx, ast.Del):
            if node.id in self.current_read_only_vars or (
                self.current_verify_rule_info is not None and
                    node.id in self.current_verify_rule_info['captures']):
                raise KVCompilerParserException(
                    'A variable that has been used in a KV rule cannot be '
                    'changed until the current context has exited if bindings'
                    ' occur upon context exit. The '
                    'variable that was attempted to be changed is {}'.
                    format(node.id))

        return super(VerifyKVCaptureOnExitTransformer, self).visit_Name(node)

    def visit_ListComp(self, node):
        return node

    def visit_SetComp(self, node):
        return node

    def visit_GeneratorExp(self, node):
        return node

    def visit_DictComp(self, node):
        return node

    def visit_ExceptHandler(self, node):
        if node.name in self.current_read_only_vars or (
            self.current_verify_rule_info is not None and
                node.name in self.current_verify_rule_info['captures']):
            raise KVCompilerParserException(
                'A variable that has been used in a KV rule cannot be '
                'changed until the current context has exited if bindings'
                ' occur upon context exit. The '
                'variable that was attempted to be changed is {}'.
                format(node.name))
        return super(
            VerifyKVCaptureOnExitTransformer, self).visit_ExceptHandler(node)

    def visit_ImportFrom(self, node):
        for name in node.names:
            val = name.asname or name.name
            if val in self.current_read_only_vars or (
                self.current_verify_rule_info is not None and
                    val in self.current_verify_rule_info['captures']):
                raise KVCompilerParserException(
                    'A variable that has been used in a KV rule cannot be '
                    'changed until the current context has exited if bindings'
                    ' occur upon context exit. The '
                    'variable that was attempted to be changed is {}'.
                    format(name.asname or name.name))
        return super(
            VerifyKVCaptureOnExitTransformer, self).visit_ImportFrom(node)

    def visit_Import(self, node):
        for name in node.names:
            name_split = name.name.split('.')
            if len(name_split) == 1 and \
                    (name_split[0] in self.current_read_only_vars or
                     self.current_verify_rule_info is not None and
                     name_split[0] in
                     self.current_verify_rule_info['captures']):
                raise KVCompilerParserException(
                    'A variable that has been used in a KV rule cannot be '
                    'changed until the current context has exited if bindings'
                    ' occur upon context exit. The '
                    'variable that was attempted to be changed is {}'.
                    format(name_split[0]))
        return super(VerifyKVCaptureOnExitTransformer, self).visit_Import(node)

    def visit_Lambda(self, node):
        return node

    def visit_DoNothingAST(self, node):
        return node


class VerifyKVCaptureOnEnterTransformer(VerifyKVCaptureOnExitTransformer):
    '''
    AST transformer that verifies that captured variables are not modified
    and are read only, for the case where the bindings occur upon KVCtx enter.
    '''
    # when binds happen on enter, everything must be available at that point
    # and nothing can change until the corresponding rule is finished.
    # This means that from the ctx enter all subsequent rule's vars are
    # readonly. I.e. after rule n, all vars from rule n + 1 until the last
    # rule of the ctx become readonly. At ctx entrance, *all* rules are
    # readonly.

    def start_kv_ctx(self, ctx_info):
        # first_pass_contexts is ordered by entrance, not exit
        first_ctx_info = self.first_pass_contexts.popleft()
        self.current_ctx_stack.appendleft(first_ctx_info)
        if not first_ctx_info['rules']:
            # there's no rule to pop for this context
            return

        self.ro_ctx_stack.appendleft(self.current_read_only_vars)
        self.current_read_only_vars = set(self.current_read_only_vars)  # seed
        # get rule from ctx, in case we have ctx within ctx and the rules are
        # at the end of each ctx so first_pass_rules is then not reliable.
        rule_info_0 = first_ctx_info['rules'][0]
        self.current_read_only_vars.update(rule_info_0['enter_readonly_names'])

    def finish_kv_ctx(self, ctx_info):
        self.current_ctx_stack.popleft()

    def start_kv_rule(self, ctx_info, rule_info):
        pass

    def finish_kv_rule(self, ctx_info, rule_info):
        # we know which rule was completed, but the next rule in first_pass_
        # rules may not be in this ctx (e.g. if there's a nested ctx before the
        # next rule in this ctx). We need to know what the next rule of the
        # current is, because that is the readonly vars for this context next
        first_ctx_info, first_rule_info = self.first_pass_rules.popleft()
        # we don't need current_ctx_stack, but it's useful for the assert
        assert first_ctx_info is self.current_ctx_stack[0]
        rules = first_ctx_info['rules']
        # rules are unique because of indexing added to them with enter_rule_i
        i = rules.index(first_rule_info)

        if len(rules) - 1 == i:  # last rule
            # jump back to vars from previous ctx
            self.current_read_only_vars = self.ro_ctx_stack.popleft()
            return

        # there are still more rules,
        self.current_read_only_vars = set(self.ro_ctx_stack[0])  # seed RO
        self.current_read_only_vars.update(
            rules[i + 1]['enter_readonly_names'])

    def visit_AugAssign(self, node):
        # aug assign is the same as assign for our purposes because it's a
        # Store that we need to verify when on a Name.
        return ParseKVFunctionTransformer.visit_AugAssign(self, node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store) or isinstance(node.ctx, ast.Del):
            if node.id in self.current_read_only_vars:
                raise KVCompilerParserException(
                    'A variable that has been used in a KV rule cannot be '
                    'changed until the rule is executed, if the '
                    'bindings occur upon context enter. The '
                    'variable that was attempted to be changed is {}'.
                    format(node.id))

        return ParseKVFunctionTransformer.visit_Name(self, node)


def verify_readonly_nodes(graph, transformer, bind_on_enter):
    '''
    Runs the appropriate transformer that verifies that captured and read only
    variables are not modified.
    '''
    if bind_on_enter:
        # compute all the readonly name. For bind on enter, it all
        # happens at the start of the ctx, so everything must valid
        # there and therefore everything becomes readonly
        t = ParseExpressionNameLoadTransformer()
        for ctx_info in transformer.context_infos:
            last = set()
            for i, rule_info in enumerate(ctx_info['rules'][::-1]):
                t.names = set()
                for arg in rule_info['binds']:
                    t.visit(arg)

                last = rule_info['rule'].captures | t.names | last
                rule_info['enter_readonly_names'] = last
                rule_info['enter_rule_i'] = -i  # just has to be unique
        verifier_cls = VerifyKVCaptureOnEnterTransformer
    else:
        verifier_cls = VerifyKVCaptureOnExitTransformer

    verifier = verifier_cls(first_pass_rules=transformer.rules_by_occurrence,
                            first_pass_contexts=transformer.context_infos)
    verifier.visit(graph)
    # should have been fully consumed
    assert not verifier.first_pass_contexts
    assert not verifier.first_pass_rules
    assert not verifier.ro_ctx_stack
    assert not verifier.current_ctx_stack
