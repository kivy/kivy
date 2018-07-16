import ast
import fnmatch
import re


class KVRule(object):

    __slots__ = ('bind_stores', 'callback', 'binds', 'delay', 'name', 'largs')

    def __init__(
            self, *binds, delay=None, name=None):
        self.binds = binds
        self.delay = delay
        self.name = name
        self.largs = ()
        self.callback = None
        self.bind_stores = ()

    def __enter__(self):
        raise TypeError(
            "Something went wrong and the KV code was not compiled. Did "
            "you forget to decorate the function with the KV compiler?")

    def __exit__(self, exc_type, exc_val, exc_tb):
        raise NotImplemented

    def unbind_rule(self):
        # we are slowly trimming leaves until all are unbound
        binds_stores = self.bind_stores

        for bind_store, leaf_indices in binds_stores:
            for leaf_index in leaf_indices:
                leaf = bind_store[leaf_index]
                if leaf is None:
                    # we're in the middle of binding and this should not have
                    # been called
                    raise Exception(
                        'Cannot unbind a rule before it was finished binding')

                leaf_tree_indices = leaf[5]
                assert leaf[4] == 1
                for bind_idx in leaf_tree_indices:
                    bind_item = bind_store[bind_idx]
                    if bind_item is None:
                        raise Exception(
                            'Cannot unbind a rule before it was finished '
                            'binding')

                    obj, attr, _, uid, count, _ = bind_item
                    if count == 1:
                        # last item bound, we're done with this one
                        obj.unbind_uid(attr, uid)
                        bind_store[bind_idx] = None
                    else:
                        bind_item[4] -= 1
                        assert bind_item[4] >= 1

        self.bind_stores = ()
        # it's ok to release the (possibly last) ref to the callback because at
        # worst it's scheduled in the clock, which has no problem dealing with
        # abandoned refs, or its scheduled with the canvas instructions that
        # holds a direct ref to it.
        self.callback = None


class KVParserRule(KVRule):

    __slots__ = ('callback_name', 'captures', 'src', 'with_var_name_ast')

    def __init__(self, **kwargs):
        super(KVParserRule, self).__init__(**kwargs)
        self.with_var_name_ast = None


class KVCtx(object):

    __slots__ = (
        'bind_stores_by_tree', 'rebind_functions',
        'named_rules', 'rules', 'transformer', 'kv_syntax')

    def __init__(self):
        self.rules = []
        self.named_rules = {}
        self.transformer = None

    def __enter__(self):
        raise TypeError(
            "Something went wrong and the KV code was not compiled. Did "
            "you forget to decorate the function with the KV compiler?")

    def __exit__(self, exc_type, exc_val, exc_tb):
        raise NotImplemented

    def set_kv_binding_ast_transformer(self, transformer, kv_syntax):
        if kv_syntax == 'minimal':
            transformer.whitelist = {
                'Name', 'Num', 'Bytes', 'Str', 'NameConstant', 'Subscript'}
        self.transformer = transformer

    def add_rule(self, rule, callback_name=None):
        if callback_name:
            rule.callback_name = callback_name

        self.rules.append(rule)
        if rule.name:
            self.named_rules[rule.name] = rule

    def parse_rules(self):
        for rule in self.rules:
            if not rule.binds:
                raise ValueError('binds must be specified')

            if isinstance(rule.binds, str):
                nodes = [ast.parse(rule.binds)]
            elif isinstance(rule.binds, ast.AST):
                nodes = [rule.binds]
            else:
                nodes = [ast.parse(bind) if isinstance(bind, str) else bind
                         for bind in rule.binds]
            self.transformer.update_tree(nodes, rule)

    def set_nodes_proxy(self, use_proxy, use_proxy_exclude=None):
        nodes_rules = self.transformer.nodes_by_rule
        if use_proxy is True:
            if use_proxy_exclude:
                if isinstance(use_proxy_exclude, str):
                    pat = re.compile(fnmatch.translate(use_proxy_exclude))
                else:
                    pat = re.compile(
                        '|'.join(map(fnmatch.translate, use_proxy_exclude)))
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
                    pat = re.compile(
                        '|'.join(map(fnmatch.translate, rebind_exclude)))
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
