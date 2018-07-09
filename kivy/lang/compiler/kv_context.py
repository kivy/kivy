import ast
import fnmatch
import re
from kivy.lang.compiler.ast_parse import ParseKVBindTransformer


class KVRule(object):

    rule_bindings = []

    callback = None

    callback_name = ''

    binds = []

    delay = None

    exec_rule = True

    name = None

    def __init__(
            self, callback=None, binds=[], delay=None, exec_rule=True,
            name=None, **kwargs):
        super(KVRule, self).__init__(**kwargs)
        self.callback = callback
        self.binds = binds
        self.delay = delay
        self.exec_rule = exec_rule
        self.name = name


class KVCtx(object):

    bind_stores_by_tree = []

    rebind_functions = []

    named_rules = {}

    rules = []

    transformer = None

    def __init__(self, kv_syntax=None, **kwargs):
        super(KVCtx, self).__init__(**kwargs)
        self.rules = []
        self.named_rules = {}
        transformer = self.transformer = ParseKVBindTransformer()

        if kv_syntax is not None:
            if kv_syntax not in ('minimal', ):
                raise ValueError(
                    'kv_syntax can be either None or "minimal", not {}'.
                    format(kv_syntax))

        if kv_syntax == 'minimal':
            transformer.whitelist = {
                'Name', 'Num', 'Bytes', 'Str', 'NameConstant', 'Subscript'}

    def unbind_rule(self, name=None, num=None):
        # we are slowly trimming leaves until all are unbound
        rule = self.rules[num] if name is None else self.named_rules[name]
        binds_stores = rule['bind_stores']

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

        rule['bind_stores'] = ()
        # it's ok to release the (possibly last) ref to the callback because at
        # worst it's scheduled in the clock, which has no problem dealing with
        # abandoned refs, or its scheduled with the canvas instructions that
        # holds a direct ref to it.
        rule['callback'] = None

    def add_rule(self, rule, callback_name=None):
        if not callback_name:
            callback_name = '__kv_leaf_callback_{}'.format(len(self.rules))
        rule['callback_name'] = callback_name

        rule.setdefault('exec_rule', True)
        rule.setdefault('delay', None)
        rule.setdefault('bind_stores', ())

        self.rules.append(rule)
        if rule['name']:
            self.named_rules[rule['name']] = rule

    def parse_rules(self):
        for rule in self.rules:
            if not rule['binds']:
                raise ValueError('binds must be specified')

            if isinstance(rule['binds'], str):
                nodes = [ast.parse(rule['binds'])]
            else:
                nodes = [ast.parse(bind) for bind in rule['binds']]
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
