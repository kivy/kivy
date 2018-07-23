'''
KV Compiler Contexts and Rules
================================

Describes the classes that captures a KV binding rule as well as the context
that stores the rules.

Typical usage::

    class MyWidget(Widget):

        kv_ctx = None

        def __init__(self, **kwargs):
            super(MyWidget, self).__init__(**kwargs)
            self.apply_kv()

        @KV()
        def apply_rule(self):
            with KVCtx() as self.kv_ctx:
                self.width @= self.height + 10

                with KVRule(name='my_rule') as rule:
                    print('callback args is:', rule.largs)
                    self.x @= self.y + 25

Then::

    >>> widget = MyWidget()
    >>> widget.height = 43  # sets widget.width to 53
    >>> rule = widget.kv_ctx.named_rules['my_rule']
    >>> rule.unbind_rule()  # unbinds the rule
    >>> widget.kv_ctx.unbind_all_rules()  # unbinds all the rules

'''

import ast
import fnmatch
import re

__all__ = ('KVRule', 'KVCtx', 'KVParserRule', 'KVParserCtx')


class KVRule(object):
    '''
    Describes a KV rule.

    :param *binds: captures all positional arguments and add them to the bind
        list. E.g.::

            with KVRule():
                self.x @= self.y

        does the same things as::

            with KVRule(self.y):
                self.x = self.y

        and you can add as many positional args there as you like, and the rule
        will bind to all fo them. The args can be actual variable names, e.g.
        `self.y`, or as a string, e.g. `"self.y"` - they will do the same
        thing.
    :param delay: the rule type: can be None (default), `"canvas"`, or a
        number. Describes the rule type.
        * If `None`, it's a normal KV rule
        * If `"canvas"`, it's meant to be used with a canvas instruction and
          the rule will be scheduled to be executed with other graphics *after*
          the frame, rather than every time it is called.
        * If a number, a Clock trigger event will be created with the given
          delay and when the rule dispatches, the event will be triggered,
          rather than be executed immediately.

          .. warning:
              If setting the KV decorator proxy parameter to True and a clock
              rule is created, a reference must be held to the rule or context,
              otherwise the rule will be freed by the garbage collection.
    :param delay: name: a optional name for the rule. Defaults to `None`

    Class attributes:

    :var largs: The largs provided when the rule is dispatched.
    :var bind_stores: (internal): Maintains a reference to the lists that
        stores all the bindings created for the rule.
    :var callback: (internal): The callback function that is called by the rule
        whenever it is dispatched.
    :var _callback: (internal): If it's a clock or canvas rule, contains the
        underlying callback that actually executed the rule. In that case,
        `callback` contains the clock trigger or function that schedules the
        canvas update.
    '''

    __slots__ = ('bind_stores', 'callback', 'delay', 'name', 'largs',
                 '_callback')

    def __init__(self, *binds, delay=None, name=None):
        # we don't save any of the args here, because when a rule is created by
        # the manual compiler, it is the KVParserRule. For the auto compiler,
        # the user writes in the code KVRule, but the compiler intercepts it
        # and creates a KVParserRule instead when parsing and saves the args
        # there. Finally, the compiler emits the creation of a KVRule without
        # any args/kwargs and instead emits manual code that sets the
        # attributes of the KVRule based on the internal KVParserRule, rather
        # than passing it to the constructor.
        # Calss variables are not init here as a optimization
        self.largs = ()

    def __enter__(self):
        raise TypeError(
            "Something went wrong and the KV code was not compiled. Did "
            "you forget to decorate the function with the KV compiler? "
            "Make sure the KV rule class is KVRule because it cannot be "
            "inherited from as it's parsed syntactically at compile time.")

    def __exit__(self, exc_type, exc_val, exc_tb):
        raise NotImplemented

    def unbind_rule(self):
        '''Unbinds the rule, so that it will not be triggered by any of the
        properties that the rule is bound to.

        If the rule is already scheduled, e.g. with a canvas instruction or
        clock trigger, it may still execute (this may change in the future
        to immediately cancel that as well), but it won't be scheduled again.
        '''
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

                leaf_graph_indices = leaf[5]
                assert leaf[4] == 1
                for bind_idx in leaf_graph_indices:
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
    '''Created by the parser when it encounters a :class:`KVRule`.

    It is also used when manually compiling KV.
    '''

    __slots__ = ('callback_name', 'captures', 'src', 'with_var_name_ast',
                 '_callback_name', 'binds')

    def __init__(self, *binds, delay=None, name=None):
        super(KVParserRule, self).__init__()
        self.with_var_name_ast = None
        self._callback = None
        self.binds = binds
        self.delay = delay
        self.name = name
        self.bind_stores = ()
        self.callback = None


class KVCtx(object):
    '''
    Manages KV rules created under the context.

    Class attributes:

    :var rules: List of :class:`KVRule`
        Contains all the KV rules created under the context, ignoring rules
        created under a second context within this context. E.g.::

            with KVCtx() as my_ctx:
                self.x @= self.y
                with KVCtx() as my_ctx2:
                    self.y @= self.height + 10
                with KVRule(name='my_rule'):
                    self.width @= self.height

        then `my_ctx` will contain 2 rules, and my_ctx2 will contain 1 rule.
        The rules are ordered and numbered in the order they occur in the
        function.
    :var named_rules: dictionary with all the rules that are named.
        Similarly to `rules`, but contains the rules that have been given
        names. In the example above, `my_ctx.named_rules` contains one rule
        with name/key value `"my_rule"`.

    :var bind_stores_by_graph: (internal): Maintains a reference to the lists
        that stores all the bindings created for all the rules in the context.
    :var rebind_functions: (internal): Maintains a reference to all the
        callbacks used in all the context's rules.
    '''

    __slots__ = (
        'bind_stores_by_graph', 'rebind_functions', 'named_rules', 'rules')

    def __init__(self):
        self.rules = []
        self.named_rules = {}

    def __enter__(self):
        raise TypeError(
            "Something went wrong and the KV code was not compiled. Did "
            "you forget to decorate the function with the KV compiler? "
            "Make sure the KV context class is KVCtx because it cannot be "
            "inherited from as it's parsed syntactically at compile time.")

    def __exit__(self, exc_type, exc_val, exc_tb):
        raise NotImplemented

    def add_rule(self, rule):
        '''Adds the rule to the context.

        It is called automatically by the compiler and should only be called
        when manually compiling KV.
        '''
        self.rules.append(rule)
        if rule.name:
            self.named_rules[rule.name] = rule

    def unbind_all_rules(self):
        '''Calls :meth:`KVRule.unbind_rule` for all the rules in the context
        to unbind all the rules.
        '''
        for rule in self.rules:
            rule.unbind_rule()


class KVParserCtx(KVCtx):
    '''Created by the parser when it encounters a :class:`KVCtx`.

    It is also used when manually compiling KV.
    '''

    __slots__ = ('transformer', 'kv_syntax')

    def __init__(self):
        super(KVParserCtx, self).__init__()
        self.transformer = None

    def set_kv_binding_ast_transformer(self, transformer, kv_syntax):
        if kv_syntax == 'minimal':
            transformer.whitelist = {
                'Name', 'Num', 'Bytes', 'Str', 'NameConstant', 'Subscript'}
        self.transformer = transformer

    def parse_rules(self):
        for rule in self.rules:
            if not rule.binds:
                raise ValueError(
                    'To create a rule, some binding parameters must be '
                    'specified, or added in the rule using the x @= y syntax')

            if isinstance(rule.binds, str):
                nodes = [ast.parse(rule.binds)]
            elif isinstance(rule.binds, ast.AST):
                nodes = [rule.binds]
            else:
                nodes = [ast.parse(bind) if isinstance(bind, str) else bind
                         for bind in rule.binds]
            self.transformer.update_graph(nodes, rule)

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
