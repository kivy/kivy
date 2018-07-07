import ast
import fnmatch
import re
from kivy.lang.compiler.ast_parse import ParseKVBindTransformer


class KVCtx(object):

    bind_list = []

    callback = None

    transformer = None

    def __init__(self, kv_syntax=None, **kwargs):
        super(KVCtx, self).__init__(**kwargs)
        self.bind_list = []
        transformer = self.transformer = ParseKVBindTransformer()

        if kv_syntax is not None:
            if kv_syntax not in ('minimal', ):
                raise ValueError(
                    'kv_syntax can be either None or "minimal", not {}'.
                    format(kv_syntax))

        if kv_syntax == 'minimal':
            transformer.whitelist = {
                'Name', 'Num', 'Bytes', 'Str', 'NameConstant', 'Subscript'}

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

    def set_nodes_proxy(self, use_proxy, use_proxy_exclude=None):
        nodes_rules = self.transformer.nodes_by_rule
        if use_proxy is True:
            if use_proxy_exclude:
                if isinstance(use_proxy_exclude, str):
                    pat = re.compile(fnmatch.translate(use_proxy_exclude))
                else:
                    pat = re.compile('|'.join(map(fnmatch.translate, use_proxy_exclude)))
                match = re.match

                for nodes_rule in nodes_rules:
                    for node in nodes_rule:
                        node.proxy = any(
                            dep.is_attribute for dep in node.depends_on_me) \
                            and match(pat, node.src) is None
            else:
                for nodes_rule in nodes_rules:
                    for node in nodes_rule:
                        node.proxy = any(
                            dep.is_attribute for dep in node.depends_on_me)
        elif use_proxy is False:
            for nodes_rule in nodes_rules:
                for node in nodes_rule:
                    node.proxy = False
        elif isinstance(use_proxy, str):
            pat = re.compile(fnmatch.translate(use_proxy))
            match = re.match

            for nodes_rule in nodes_rules:
                for node in nodes_rule:
                    node.proxy = any(
                        dep.is_attribute for dep in node.depends_on_me) \
                        and match(pat, node.src) is not None
        else:
            pat = re.compile('|'.join(map(fnmatch.translate, use_proxy)))
            match = re.match

            for nodes_rule in nodes_rules:
                for node in nodes_rule:
                    node.proxy = any(
                        dep.is_attribute for dep in node.depends_on_me) \
                        and match(pat, node.src) is not None

    def set_nodes_rebind(self, rebind, rebind_exclude=None):
        nodes_rules = self.transformer.nodes_by_rule
        if rebind is True:
            if rebind_exclude:
                if isinstance(rebind_exclude, str):
                    pat = re.compile(fnmatch.translate(rebind_exclude))
                else:
                    pat = re.compile('|'.join(map(fnmatch.translate, rebind_exclude)))
                match = re.match

                for nodes_rule in nodes_rules:
                    for node in nodes_rule:
                        node.rebind = node.is_attribute and \
                            node.leaf_rule is None and \
                            match(pat, node.src) is None
            else:
                for nodes_rule in nodes_rules:
                    for node in nodes_rule:
                        node.rebind = node.is_attribute and \
                            node.leaf_rule is None
        elif rebind is False:
            for nodes_rule in nodes_rules:
                for node in nodes_rule:
                    node.rebind = False
        elif isinstance(rebind, str):
            pat = re.compile(fnmatch.translate(rebind))
            match = re.match

            for nodes_rule in nodes_rules:
                for node in nodes_rule:
                    node.rebind = node.is_attribute and \
                        node.leaf_rule is None and \
                        match(pat, node.src) is not None
        else:
            pat = re.compile('|'.join(map(fnmatch.translate, rebind)))
            match = re.match

            for nodes_rule in nodes_rules:
                for node in nodes_rule:
                    node.rebind = node.is_attribute and \
                        node.leaf_rule is None and \
                        match(pat, node.src) is not None
