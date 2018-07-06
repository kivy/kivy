from kivy.lang.compiler.src_gen import KVCompiler
from kivy.lang.compiler.kv_context import KVCtx


if __name__ == '__main__':
    from collections import defaultdict
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
