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

    def return_back(self, token):
        item = self.tokens[token]
        if item[2] == 1:  # last usage
            del self.tokens[token]
            self.pool[item[1]] = item[0]
            return 0
        else:
            item[2] -= 1
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

    def exec_bindings(self, ctx, local_vars, globals_vars):
        func_pool = self.rebind_func_pool
        bind_store_pool = self.binding_store_pool
        transformer = ctx.transformer

        for tree in transformer.nodes_by_tree:
            src_code = []
            func = func_pool.borrow(len(func_pool.get_used_items()))

            bind_store = bind_store_pool.borrow(func)
            bind_list_len = 0

            node_value_var = {}
            temp_pool = StringPool(prefix='__kv_temp_val')

            src_counts = defaultdict(int)
            for node in tree:
                if node.leaf_rule:
                    assert not node.src
                    src_counts[node.src] += 1

            for node in tree:
                if not node.depends:
                    assert not node.is_attribute
                    # we found a global or local variable, just add its name
                    node_value_var[node] = node.src
                else:
                    # add check if the last value(s) is not None
                    depends = [dep for dep in node.depends if dep.depends]
                    indent = 4
                    dep_name = ''
                    obj_attr = ''

                    if node.leaf_rule is None:
                        assert node.depends_on_me
                        var = temp_pool.borrow(node, len(node.depends_on_me))
                        if depends:
                            src_code.append('{}{} = None'.format(' ' * 4, var))

                    if node.is_attribute:
                        assert len(node.depends) == 1
                        dep_name = node_value_var[node.depends[0]]
                        obj_attr = node.ref_node.attr

                        src_code.append('{}if {}[{}] is not None:'.format(' ' * 4, bind_store, bind_list_len))
                        src_code.append('{}__kv_obj, __kv_attr, __kv_uid = {}[{}]'.format(' ' * 8, bind_store, bind_list_len))
                        src_code.append('{}if __kv_obj is not None and __kv_uid:'.format(' ' * 8))
                        src_code.append('{}__kv_obj.unbind_uid(__kv_attr, __kv_uid)'.format(' ' * 12))
                        src_code.append('{}{}[{}][0] = None'.format(' ' * 12, bind_store, bind_list_len))

                    if depends:
                        indent = 8
                        condition = []
                        for dep in depends:
                            name = node_value_var[dep]
                            condition.append('{} is not None'.format(name))
                        if node.is_attribute:
                            condition.append('{}[{}] is not None'.format(bind_store, bind_list_len))
                        condition = '{}if {}:'.format(' ' * 4, ' and '.join(condition))
                        src_code.append(condition)

                    if node.is_attribute:
                        bind = '{}.fbind("{}", {})'.format(dep_name, obj_attr, 'wait_for_it' if node.leaf_rule is None else 'already_waited_for_it')
                        src_code.append('{}{}[{}] = [{}, "{}", {}]'.format(' ' * indent, bind_store, bind_list_len, dep_name, obj_attr, bind))
                        bind_list_len += 1

                    if node.leaf_rule is None:
                        assignment = '{}{} = {}'.format(' ' * indent, var, generate_source(node).rstrip('\r\n'))
                        src_code.append(assignment)

                        node_value_var[node] = var
                        node.set_ref_node(ast.Name(id=var, ctx=ast.Load()))

                    for dep in node.depends:
                        if dep.depends:
                            temp_pool.return_back(dep)
                    src_code.append('')

            src_code.insert(0, 'def {}(*__largs):'.format(func))
            src_code.insert(0, '{} = [None, ] * {}'.format(bind_store, bind_list_len))
            src_code.append('')

            print('\n'.join(src_code))


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


class ASTNodeRef(ast.AST):

    ref_node = None

    src = ''
    '''
    Not set for final attribute nodes because we never evaluate the node. '''

    is_attribute = False

    depends_on_me = []

    depends = []

    count = 0

    leaf_rule = None
    # only attrs can be leaf

    my_tree = []

    def __init__(self, is_attribute):
        super(ASTNodeRef, self).__init__()
        self.is_attribute = is_attribute
        self.depends_on_me = []
        self.depends = []

    def set_ref_node(self, node):
        self._attributes = node._attributes
        self._fields = node._fields
        self.ref_node = node

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
            w.x = items[w.width + len(name) / 2 + w2.height + len(b"fruit") +
                   w2.height * count].width + count + items[w.width + len(name) / 2 + w2.height + len(b"fruit") +
                   w2.height * count].x + w.y
            print('updated w.x to ', w.x, "w's parent is", w.parent)
        ctx.add_rule(
            manage_x,
            'items[w.width + len(name) / 2 + w2.height + len(b"fruit") + '
            'w2.height * count].width + count + items[w.width + len(name) / 2 '
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
        ctx.add_rule(manage_w2_y, 'w2.parent.y + w2.height')

        compiler.exec_bindings(ctx, locals(), globals())

    build_kv()
