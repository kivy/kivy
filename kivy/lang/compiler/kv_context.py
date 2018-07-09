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

    bindings = []

    rebind_functions = []

    named_rules = {}

    rules = []

    transformer = None

    def __init__(self, kv_syntax=None, **kwargs):
        super(KVCtx, self).__init__(**kwargs)
        self.rules = []
        self.named_bindings = {}
        transformer = self.transformer = ParseKVBindTransformer()

        if kv_syntax is not None:
            if kv_syntax not in ('minimal', ):
                raise ValueError(
                    'kv_syntax can be either None or "minimal", not {}'.
                    format(kv_syntax))

        if kv_syntax == 'minimal':
            transformer.whitelist = {
                'Name', 'Num', 'Bytes', 'Str', 'NameConstant', 'Subscript'}

    def add_rule(self, rule, callback_name=None):
        if not callback_name:
            callback_name = '__kv_leaf_callback_{}'.format(len(self.rules))
        rule['callback_name'] = callback_name

        rule.setdefault('exec_rule', True)
        rule.setdefault('delay', None)

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
