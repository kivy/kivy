import ast
from collections import deque, defaultdict
import astor
from astor.code_gen import SourceGenerator
from astor.source_repr import split_lines

from kivy.lang.compiler.kv_context import KVCtx, KVParserRule


class KVException(Exception):
    pass


class KVCompilerParserException(KVException):
    pass


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


class ASTBindNodeRef(ast.AST):

    original_node = None

    ref_node = None

    src = ''
    '''
    Not set for final attribute nodes because we never evaluate the node.
    '''

    is_attribute = False

    rebind = False

    proxy = False

    depends_on_me = []

    depends = []

    count = 0
    '''The number of times this node is used as a parent node. E.g. in
    `self.obj.x + self.obj.y`, `self.obj` has a count of two.
    '''

    leaf_rule = None
    # only attrs can be leaf

    my_tree = []
    '''Keeps track of the tree the node is in. E.g. `self.x + obj.y` contains
    two independent trees.
    '''

    def __init__(self, is_attribute):
        super(ASTBindNodeRef, self).__init__()
        self.is_attribute = is_attribute
        self.depends_on_me = []
        self.depends = []

    def get_rebind_or_leaf_subtree(self):
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
            if dep.leaf_rule is not None or dep.rebind:
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
                    if dep.leaf_rule is not None or dep.rebind:
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

        return BindSubTreeNode(explored, terminal_nodes)

    def set_ref_node(self, node):
        self._attributes = node._attributes
        self._fields = node._fields
        self.ref_node = node

    @staticmethod
    def group_by_required_deps_ordered(nodes):
        '''Groups the nodes into groups based on their deps. All nodes with the
        same deps are grouped together. The order of nodes is preserved as given
        in `nodes` such that the first occurrence of nodes with unique deps are
        ordered in the order they occur in nodes.
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

    def __repr__(self):
        return '{} - is_attr: {}, count: {}, ' \
            'leaf: {}, depends_on_me({}): {}, , depends({}): {}'.\
            format(
                self.src, self.is_attribute, self.count,
                self.leaf_rule is not None, len(self.depends_on_me),
                [node.src for node in self.depends_on_me], len(self.depends),
                [node.src for node in self.depends])


class ASTRuleCtxNodePlaceholder(ast.AST):

    src_lines = []


class ASTNodeList(ast.AST):

    nodes = []


class RefSourceGenerator(SourceGenerator):

    def visit_ASTBindNodeRef(self, node, *largs, **kwargs):
        return self.visit(node.ref_node, *largs, **kwargs)

    def visit_ASTNodeList(self, node, *largs, **kwargs):
        for item in node.nodes:
            self.visit(item, *largs, **kwargs)

    def visit_ASTRuleCtxNodePlaceholder(self, node, *largs, **kwargs):
        self.newline(extra=1)
        lines = ['\n', ] * (len(node.src_lines) * 2)
        for i, line in enumerate(node.src_lines):
            lines[2 * i] = line
        self.write(*lines)

    def visit_DoNothingAST(self, node, *largs, **kwargs):
        pass



def generate_source(node):
    generator = RefSourceGenerator(indent_with=' ' * 4)
    generator.visit(node)

    generator.result.append('\n')
    if set(generator.result[0]) == set('\n'):
        generator.result[0] = ''

    return ''.join(split_lines(generator.result, maxline=2 ** 32 - 1))


class NotWhiteListed(Exception):
    pass


class ParseKVBindTransformer(ast.NodeTransformer):
    # no Name node that is a Store shall be saved in any of the trees. It's not
    # included anyway because it cannot be an expression, but we should not
    # include either way because in the KV decorator we use all Name for
    # capturing and making them readonly. This assumes that they are all Load.

    src_node_map = {}

    under_attr = False

    nodes_by_rule = []

    nodes_by_tree = []

    src_nodes = []

    current_processing_node = None

    visited = set()

    current_rule = None

    whitelist = None

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
            whitelist = self.whitelist
            if whitelist is not None and not is_attribute and node.__class__.__name__ not in whitelist:
                raise NotWhiteListed

            current_processing_node = self.current_processing_node
            new_node = True
            self.current_processing_node = ret_node = ASTBindNodeRef(
                is_attribute)

            try:
                node = super(ParseKVBindTransformer, self).generic_visit(node)
            finally:
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
        try:
            node = self.generic_visit(
                node, is_attribute=True, is_final_attribute=True)
        except NotWhiteListed:
            # we don't care about the state of node, it'll not be used anyway
            pass
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


class ParseKVFunctionTransformer(ast.NodeTransformer):
    '''The most important things is that we cannot allow a kv rule to be
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
        ast.If, ast.For, ast.While, ast.Try, ast.Suite, ast.FunctionDef,
        ast.AsyncFor, ast.AsyncFunctionDef, ast.ExceptHandler, ast.ClassDef,
        ast.While, ast.Try}

    known_ast = {
        ast.AST, ast.operator, ast.Add, ast.alias, ast.boolop, ast.And, ast.arg,
        ast.arguments, ast.stmt, ast.Assert, ast.Assign, ast.AsyncFor,
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
        ast.Mod, ast.Module, ast.Mult, ast.Name, ast.NameConstant, ast.Nonlocal,
        ast.Not, ast.NotEq, ast.NotIn, ast.Num, ast.Or, ast.Param, ast.Pass,
        ast.Pow, ast.Raise, ast.Return, ast.RShift, ast.Set, ast.SetComp,
        ast.Slice, ast.Starred, ast.Store, ast.Str, ast.Sub, ast.Subscript,
        ast.Suite, ast.Try, ast.Tuple, ast.UAdd, ast.UnaryOp, ast.USub,
        ast.While, ast.With, ast.withitem, ast.Yield, ast.YieldFrom}

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
                'Multiple with statements not allowed for {}'.format(func_name))

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

        ctx = KVCtx()
        transformer = ParseKVBindTransformer()
        ctx.set_kv_binding_ast_transformer(transformer, self.kv_syntax)

        previous_ctx_info = self.current_ctx_info
        ctx_info = self.current_ctx_info = {
            'ctx': ctx, 'args': args, 'keywords': keywords,
            'rules': [], 'node': node,
            'assign_target_node': ast.Name(id='__xxx', ctx=ast.Store()),
            'before_ctx': ASTRuleCtxNodePlaceholder(),
            'after_ctx': ASTRuleCtxNodePlaceholder()}
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
            rule.src = generate_source(rule_info['body']).strip('\r\n')
            ctx.add_rule(rule)

        targets = [ctx_info['assign_target_node']]
        if assigned_var:
            targets.append(assigned_var)

        assign_node = ast.Assign(
            targets=targets,
            value=ast.Call(func=ast.Name(id=self.kv_ctx_cls_name, ctx=ast.Load()),
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
                            'Cannot parse {}, must be one of canvas/number/None'
                            .format(val.value))
                elif isinstance(val, ast.Str):
                    if val.s != 'canvas':
                        raise KVCompilerParserException(
                            'Cannot parse {}, must be one of canvas/number/None'
                            .format(val.s))
                    delay = val.s
                elif isinstance(val, ast.Num):
                    delay = val.n
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

        rule = self.current_rule_info = {
            'node': node, 'binds': list(args),
            'from_with': True, 'body': None,
            'locals': set(), 'captures': set(), 'currently_locals': None,
            'possibly_locals': set(), 'rule': KVParserRule(
                delay=delay, name=name)}
        rule['args_binds'] = rule['binds']
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
                    isinstance(previous_rule_info['rule'].delay, (int, float))
                    and delay is None):
                raise KVCompilerParserException(
                    'A rule can only have a single delay type (one of '
                    'canvas/number/None). The rule delay type was previously '
                    'declared as {}, but was attempted to be redefined to {}'.
                    format(previous_rule_info['rule'].delay, delay))
            self.visit(node.value)
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
                    if val in current_rule['possibly_locals']:
                        raise KVCompilerParserException(
                            'variable {} may or may not have been set within a '
                            'conditional or loop and is therefore not allowed '
                            'in KV. Make sure the variable is always defined'.
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
                    if node.id in current_rule['possibly_locals']:
                        raise KVCompilerParserException(
                            'variable {} may or may not have been set within a '
                            'conditional or loop and is therefore not allowed '
                            'in KV. Make sure the variable is always defined'.
                            format(node.id))
                    current_rule['captures'].add(node.id)
            elif isinstance(node.ctx, ast.Store):
                if current_rule['currently_locals'] is None:
                    current_rule['locals'].add(node.id)
                else:
                    current_rule['currently_locals'].add(node.id)
            else:
                # how can we del a var in the callback? What if it was def
                # outside the rule? The callback will freak out. So it's illegal
                # in KV.
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
        current_rule['possibly_locals'].update(current_rule['currently_locals'])

        current_rule['currently_locals'] = set(original) if original else set()
        node.orelse = self.visit(node.orelse)
        current_rule['possibly_locals'].update(current_rule['currently_locals'])

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
            assert item._fields == ('target', 'iter', 'ifs')
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
        current_rule['possibly_locals'].update(current_rule['currently_locals'])

        current_rule['currently_locals'] = set(original) if original else set()
        node.orelse = self.visit(node.orelse)
        current_rule['possibly_locals'].update(current_rule['currently_locals'])

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
        current_rule['possibly_locals'].update(current_rule['currently_locals'])

        current_rule['currently_locals'] = set(original) if original else set()
        node.finalbody = self.visit(node.finalbody)
        current_rule['possibly_locals'].update(current_rule['currently_locals'])

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
        # exception handler vars don't leak out
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
        # no need to update possible locals, because lambda variables don'y leak
        # out to the outside context
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

    pass


class ParseExpressionNameLoadTransformer(ast.NodeTransformer):

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


class VerifyKVCaptureOnExitTransformer(ParseKVFunctionTransformer):
    # we can overwrite e.g. list comp visit because it cannot alter the
    # creation of new rules/ctx. But anything that changes rule or ctx creation
    # is now allowed here as it would make the first and second pass
    # inconsistent

    # why do we need to both process loads in visit_Node and get the captures
    # from the first pass rules? Because imagine a `with` rule containing 2
    # lines: `x = obj; z @= x.y + 10`. Because `x` is a local to the rule,
    # captues will not include x, meaning we'd be free to modify x after
    # the rule. But then the bind will not bind to the same x as in the original
    # rule. That's why here we make any load Name within a rule readonly.
    # The callback is not the problem, because the callback only cares about
    # captures variables and local vars can be changed in the callback.

    ro_ctx_stack = None

    current_read_only_vars = set()

    under_kv_aug_assign = False

    first_pass_rules = None

    first_pass_contexts = None

    current_ctx_stack = []

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
        _, rule_info_0 = self.first_pass_rules.popleft()
        self.current_read_only_vars.update(rule_info_0['captures'])

        t = ParseExpressionNameLoadTransformer()
        for arg in rule_info_0['args_binds']:
            t.visit(arg)
        self.current_read_only_vars.update(t.names)

    def finish_kv_rule(self, ctx_info, rule_info):
        pass

    def visit_AugAssign(self, node):
        # these become a store instead of a load/store
        if isinstance(node.op, ast.MatMult):
            # In case target is a load, we don't want to include it in
            # visit_Name below because the load on the left of the assign is
            # never bound to so there's no reason to make it read only
            node.target = DoNothingAST()
            self.under_kv_aug_assign = True
            ret = super(
                VerifyKVCaptureOnExitTransformer, self).visit_AugAssign(node)
            self.under_kv_aug_assign = False
        elif isinstance(node.op, ast.BitXor):
            node.target = DoNothingAST()
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
            if node.id in self.current_read_only_vars:
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
        if node.name in self.current_read_only_vars:
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
            if (name.asname or name.name) in self.current_read_only_vars:
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
                    name_split[0] in self.current_read_only_vars:
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
        # get rule from ctx, in case we have ctx within ctx and the rules are at
        # the end of each ctx so first_pass_rules is then not reliable.
        rule_info_0 = first_ctx_info['rules'][0]
        self.current_read_only_vars.update(rule_info_0['enter_readonly_names'])

    def finish_kv_ctx(self, ctx_info):
        self.current_ctx_stack.popleft()

    def start_kv_rule(self, ctx_info, rule_info):
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
        self.current_read_only_vars.update(rules[i + 1]['enter_readonly_names'])

    def finish_kv_rule(self, ctx_info, rule_info):
        pass

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


def verify_readonly_nodes(tree, transformer, bind_on_enter):
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
    verifier.visit(tree)
    # should have been fully consumed
    assert not verifier.first_pass_contexts
    assert not verifier.first_pass_rules
    assert not verifier.ro_ctx_stack
    assert not verifier.current_ctx_stack
