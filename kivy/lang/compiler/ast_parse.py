import inspect
import ast
import textwrap
from collections import deque, defaultdict
import astor
from astor.code_gen import SourceGenerator
from astor.source_repr import split_lines


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
