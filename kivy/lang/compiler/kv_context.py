import ast
from kivy.lang.compiler.ast_parse import ParseKVBindTransformer


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
