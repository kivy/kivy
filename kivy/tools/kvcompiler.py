'''
Kivy language compiler
======================

.. author:: Mathieu Virbel <mat@kivy.org>, Matthew Einhorn <moiein2000@gmail.com>

'''

__all__ = []

import datetime
from types import CodeType
from collections import OrderedDict, defaultdict
from kivy.lang import Parser, lang_str, Builder
from re import match, compile, sub, split
from functools import partial

rule_handler = 0
rule_on_handler = 0
rule_uid = 0

header_imports = '''
import kivy.metrics as Metrics
from kivy.factory import Factory
from kivy.lang import (
    Builder, ParserSelectorName, _handlers, ProxyApp, delayed_call_fn)
from kivy import require
from functools import partial
'''

pyheader_imports = header_imports + \
    '''from kivy.event import EventDispatcher, Observable'''

cyheader_imports = header_imports + '''
from kivy._event cimport EventDispatcher, Observable
from kivy.properties cimport Property
'''

header_gloabls = '''
app = ProxyApp()
pt = Metrics.pt
inch = Metrics.inch
cm = Metrics.cm
mm = Metrics.mm
dp = Metrics.dp
sp = Metrics.sp
'''

pyheader_globals = header_gloabls + '''
_mc = [None, ] * {}
'''

cyheader_globals = header_gloabls + '''
cdef list _mc = [None, ] * {}
'''

rebind_callback_str = '''
def rebind_callback(bound, i, instance, value):
    # bound[i] and p cannot be None b/c it dispatched
    s, e, pidx, p, key, _, _, _ = bound[i]
    # we need to rebind all children of root (p.key). First check if the value
    # actually changed - i.e. whether p.key is the same as `value`. p.key is
    # the parent of p.key.x and is stored as the parent of the first child of
    # p.key, so find the first child of p.key (p.key.x) and use its 1st child
    # `s` is the first direct child of p.key (s, e) are all the (indirect)
    # children
    try:
        if value == bound[s][3]:
            return
    except ReferenceError:
        pass
    # now, everything must have a non-None parent idx since p.key is the root
    # also, since p.key was rebind, every node below it will have bound[node]
    # not be None, even if it was not bound in case it would have rebind

    # now unbind all the children, and along the way set each parent value
    # to be the new parent in the p.key.x.y.z... tree. cache the values here.
    # keys are the index of the parent
    parent = {0}
    p = getattr(p, key)  # next parent
    if p is None or not isinstance(object, {1}):
        parent[i] = p, None, None, None, None
    else:
        parent[i] = p, p.proxy_ref, p.fast_bind, p.property, p.rebind_property

    dispatch = [None, ] * (e - s)
    for k, node in enumerate(range(s, e)):
        node_s, node_e, pidx, p, key, bid, f, args = blist = bound[i]
        # node_s/e being None means it's a leaf with no children
        if bid:  # unbind parent's rebind
            try:
                p.unbind_uid(key, bid)
            except ReferenceError:
                pass

        p, pref, bind, prop_get, rebind_prop = parent[pidx]
        # decide whether we can bind to this object
        if bind is not None and node_s is None:  # a leaf
            blist[3] = pref
            uid = blist[5] = bind(key, f, *args)
            if uid:  # it is a kivy prop
                prop = prop_get(key)
                dispatch[k] = (
                    node, p, prop.dispatch_stale, prop.dispatch_count(p))
            continue
        elif bind is not None and rebind_prop(key):  # a rebind node
            blist[3] = pref
            blist[5] = bind(key, f, *args)
            if uid:  # it is a kivy prop
                prop = prop_get(key)
                dispatch[k] = (
                    node, p, prop.dispatch_stale, prop.dispatch_count(p))
        else:  # either no obj, or obj but no rebind and it's not a leaf
            blist[3] = blist[5] = None
            if node_s is None:
                continue

        # if the key is a leaf, don't save the key as a parent b/c it has no
        # children, hence the continue above
        if node not in parent:
            if p is None:  # our parent is already None
                parent[node] = (None, None, None, None, None)
            else:
                p = getattr(p, key)  # next parent
                if p is None or not isinstance(object, (EventDispatcher, )):
                    parent[node] = p, None, None, None, None
                else:
                    parent[node] = (
                        p, p.proxy_ref, p.fast_bind, p.property,
                        p.rebind_property)

    for item in dispatch:
        if item is None:
            continue
        i, p, dispatch_stale, count = item

        try:
            if p == bound[i][3]:
                dispatch_stale(p, count)
        except ReferenceError:
            pass
'''


def argmax(iter):
    return sorted(enumerate(iter), key=lambda x: x[1])[-1][0]


def argmin(iter):
    return sorted(enumerate(iter), key=lambda x: x[1])[0][0]


def partition_tree_roots(adjacency):
    N = len(adjacency)
    assert N
    assert all([len(col) == N for col in adjacency])
    roots = []

    # partition into disjointed trees
    for c, col in enumerate(adjacency):
        if sum(col) == 0:
            roots.append(c)
    # if we didn't find any roots, pick the one with least incoming edges
    if not roots:
        roots.append(argmin(map(sum, adjacency)))


def make_tuple(objs):
    if not len(objs):
        return '()'
    elif len(objs) == 1:
        return '({}, )'.format(objs[0])
    else:
        return '({})'.format(', '.join(objs))


def push_empty(lines, max_empty=1):
    if [l for l in lines[-max_empty:] if l.strip()]:
        lines.append('')


def _find_maxline(line, rule):
    line = max(line, rule.line)
    for child in rule.children:
        line = max(line, _find_maxline(line, child))
    for prop in rule.properties.values():
        line = max(line, prop.line)
    if rule.canvas_root:
        line = max(line, _find_maxline(line, rule.canvas_root))
    if rule.canvas_before:
        line = max(line, _find_maxline(line, rule.canvas_before))
    if rule.canvas_after:
        line = max(line, _find_maxline(line, rule.canvas_after))
    return line


def larger_than_one(options, n):
    if n <= 1:
        return options[0]
    return options[1]


class LazyString(object):
    '''Takes key value pairs of names and options (where the options
    are each a list of possible values) as well as a
    function. One then calls the instance with instance.get(name, value)
    where name is one of the names, and value adds that value to a dictionary
    and it returns a :class:`LazyEval` instance representing this option and
    value.

    When `str` is called on the :class:`LazyEval` instance, the function
    determines which of the options in the options list is returned based on
    the number of times that value has been gotten and formats the string using
    the value.

    This is useful to pick a string from a list of possible strings based on
    how many times it has been used.

    :Parameters:

        `func`: callable that takes 2 parameters, the list of options, and a
        number. The number is the number of times get was called with
        `add=True` for a value (the function is called when stringifying a
        :class:`LazyEval` returned by :attr:`get`). It returns anything, but
        typically a value from the list of options based on the the number.

    ::

        >>> alias = LazyString(declare=(None, '{0}_alias = {0}.name'), use=('Hello ({}.name)', 'Hello ({}_alias)'))
        >>> jace = alias.declare('Jace', add=False)
        >>> jace

        >>> jace_inst1 = alias.use('Jace')
        >>> jace

        >>> jace_inst1
        Hello (Jace.name)
        >>> result = LazyFmt('The mango said "{}"', jace_inst1)
        >>> type(result)
        <class 'kivy.tools.kvcompiler.LazyFmt'>
        >>> result
        The mango said "Hello (Jace.name)"
        >>> jace_inst2 = alias.use('Jace')
        >>> jace
        Jace_alias = Jace.name
        >>> jace_inst1
        Hello (Jace_alias)
        >>> jace_inst2
        Hello (Jace_alias)
        >>> type(jace)
        <class 'kivy.tools.kvcompiler.LazyEval'>
        >>> result = LazyFmt('The tshirt said "{}"', jace_inst1)
        >>> type(result)
        <class 'kivy.tools.kvcompiler.LazyFmt'>
        >>> result
        The tshirt said "Hello (Jace_alias)"
    '''

    func = None

    selections = None

    values = None

    def __init__(self, func=larger_than_one, **kwargs):
        super(LazyString, self).__init__()
        self.func = func
        self.selections = kwargs
        self.values = defaultdict(int)

    def __getattr__(self, name):
        if name in self.selections:
            return partial(self.get, name)
        raise AttributeError(name)

    def get(self, selection, value, add=True):
        if selection not in self.selections:
            raise AttributeError(selection)
        if not isinstance(value, (list, tuple)):
            value = (value, )
        else:
            value = tuple(value)
        if add:
            self.values[value] += 1
        return LazyEval(self, selection, value)

    def eval(self, selection, value):
        text = self.func(self.selections[selection], self.values[value])
        if text is None:
            return None
        if isinstance(text, (tuple, list)):
            return [t.format(*value) for t in text]
        return text.format(*value) if text is not None else None


class LazyEval(object):

    lazy_str = None

    selection = None

    value = None

    def __init__(self, lazy_str, selection, value):
        super(LazyEval, self).__init__()
        self.lazy_str = lazy_str
        self.selection = selection
        self.value = value

    def __str__(self):
        val = self.lazy_str.eval(self.selection, self.value)
        return '' if val is None else val

    def __repr__(self):
        return self.__str__()


class LazyFmt(object):
    '''Performs `text.format(*largs, **kwargs)` lazily. It accepts a `text`
    string parameter as well as positional and keyword arguments and then
    performs the format when str is called on the object.::

        >>>> val = LazyFmt('Why are {} creating {}?', 'you', 'me')
        >>>> val
        Why are you creating me?
        >>>> str(val)
        'Why are you creating me?'
        >>> type(val)
        <class 'kivy.tools.kvcompiler.LazyFmt'>
    '''

    def __init__(self, text, *largs, **kwargs):
        self.text = text
        self.largs = largs
        self.kwargs = kwargs

    def __str__(self):
        return self.text.format(*self.largs, **self.kwargs)

    def __repr__(self):
        return self.__str__()


class RuleContext(object):
    '''A :class:`RuleContext` represents the kv rules associated with a single
    (possibly child) object instantiated using kv. There's a rule associated
    with each object, including root, children, and graphics children objects.

    There are many properties of :class:`RuleContext` that can only be called
    depending if the instance is a widget type, or graphics type.

    See the class properties for the init parameters.

    The rule is that whenever a property of function returns a list of code
    strings, the shallowest code is indented at indent of zero. It's the
    responsibility of the calling code to then re-indent the returned code
    to the appropriate level based on the required indent of the shallowest
    level.
    '''

    rule = None
    ''':class:`~kivy.lang.ParserRule` instance wrapped by this class.
    '''

    parent = None
    ''':class:`RuleContext` parent of this class.
    '''

    rule_type = None
    '''One of `widget`, `canvas_before`, `canvas_root`, or `canvas_after`
    representing the object (widget or graphics) that this kv rule applies to.
    '''

    count = 0
    '''The number associated with this object, see :attr:`name`. It is assigned
    uniquely for each rule (object) within the children objects of root kv
    rule. It is assigned by :class:`KVCompiler` according to the topological
    ordering.
    '''

    is_only_child = False
    '''Whether this object is the only :class:`rule_type` child of its parent.
    '''

    ids = None
    '''A dictionary of the kv ids given to the objects in kv, mapped to their
    associated :class:`RuleContext` instances.

    This dictionary is initially empty, and gets filled in as these objects are
    created, so a :class:`RuleContext` might be initialized with an ids dict
    that is still partially empty.
    '''

    tab = 0

    compiler = None

    _root_f_num = None  # cached value of :attr:`f_num`

    _ids_pat = None  # see fix_rule_ids, used to replace ids with :attr:`name`

    _ids_map = None  # cached value of :attr:`ids_map`

    def __init__(self, rule, parent, rule_type, count, ids, tab, compiler,
                 **kwargs):
        super(RuleContext, self).__init__(**kwargs)
        self.rule = rule
        self.parent = parent
        self.rule_type = rule_type
        self.ids = ids
        self.count = count
        self.tab = tab
        self.compiler = compiler
        if rule_type == 'widget':
            self.is_only_child = not parent or len(parent.rule.children) == 1
        else:
            self.is_only_child = (
                len(getattr(parent.rule, rule_type).children) == 1)

    @property
    def name(self):
        '''The compiled name given to the rule object. Its form is either:

        #. `root` for the root widget with no parent,
        #. `xn` for objects with no `id` given in kv, or
        #. `xn_id` for objects with kv ids.

        `x` above is either `g`, or `w` for graphics and widget objects,
        respectively. `n` above is the value of :attr:`count`.

        By mangeling the names in the compiled code, it is ensured that names
        given in kv will never clash with other parts of the compiled code.
        '''
        if self.parent is None:
            return 'root'
        id_str = '_{}'.format(self.rule.id) if self.rule.id else ''
        if self.rule_type == 'widget':
            return 'w{}{}'.format(self.count, id_str)
        return 'g{}{}'.format(self.count, id_str)

    @property
    def self_name(self):
        return self.name if self.rule_type == 'widget' else self.parent.name

    @property
    def f_num(self):
        '''The number given to the compiled function generated for this root
        rule. It is uniquely generated for all the compiled rules.

        Should only be called for a root rule, i.e. one whose :attr:`parent` is
        None.
        '''
        if self._root_f_num is None and self.parent is None:
            global rule_uid
            self._root_f_num = rule_uid
            rule_uid += 1
        return self._root_f_num

    @property
    def parent_add_child(self):
        '''
        '''
        assert self.parent is not None
        rule_type = self.rule_type
        assert rule_type != 'widget'  # it's added through cls(parent=child)
        if self.is_only_child:
            return '{}.{}.add'.format(
                self.parent.name, rule_type.replace('_root', '').replace('_', '.'))
        else:
            return '{}_{}_add'.format(self.parent.name, rule_type)

    @property
    def creation_instructions(self):
        parent = self.parent
        fuse = self.compiler.factory_obj.use

        rule = self.rule
        rule_type = self.rule_type
        if rule_type == 'widget':
            ret = []
            if parent is not None:  # don't create if applying rule to root
                ret.append(LazyFmt(
                    '{} = {}(parent={}, __builder_created=bfuncs)', self.name,
                    fuse(self.rule.name), parent.name))
            if rule.canvas_root and len(rule.canvas_root.children) > 1:
                ret.append(
                    '{0}_canvas_root_add = {0}.canvas.add'.format(self.name))
            if rule.canvas_before and len(rule.canvas_before.children) > 1:
                ret.append('{0}_canvas_before_add = {0}.canvas.before.add'.
                           format(self.name))
            if rule.canvas_after and len(rule.canvas_after.children) > 1:
                ret.append('{0}_canvas_after_add = {0}.canvas.after.add'.
                           format(self.name))
            return ret
        return [
            LazyFmt('{} = {}()', self.name, fuse(self.rule.name)),
            '{}({})'.format(self.parent_add_child, self.name)]

    @property
    def ids_map(self):
        '''Everything that is given an id (i.e. id: value), self, app, and
        root.
        '''
        if self._ids_map is None:
            self._ids_map = name_map = {k: v.name for k, v in self.ids.items()}
            name_map['self'] = self.self_name
            rule = self
            while rule.parent is not None:
                rule = rule.parent
            name_map['root'] = rule.name
            name_map['app'] = 'app'
        return self._ids_map

    def fix_rule_ids(self, rule_text):
        ids_map = self.ids_map
        used_ids = defaultdict(int)
        if self._ids_pat is None:
            self._ids_pat = pat = compile(
                '([^a-zA-Z_ 0-9\.]|(?:[^\. ] +)|^)({})([^a-zA-Z_0-9]|$)'.
                format('|'.join(self.ids_map.keys())))
        else:
            pat = self._ids_pat

        def f(x):
            used_ids[ids_map[x.group(2)]] += 1
            return (
                (x.group(1) if x.group(1) else '') + ids_map[x.group(2)] +
                (x.group(3) if x.group(3) else ''))

        vals = split(lang_str, rule_text)
        for i in range(0, len(vals), 2):
            if not vals[i]:
                continue
            vals[i] = pat.sub(f, vals[i])
        return ''.join(vals), used_ids

    @property
    def missing_properties(self):
        if self.rule_type != 'widget':
            return []
        tab = self.tab
        self_name = self.name
        fix_rule_ids = self.fix_rule_ids

        props = []
        for name, prop in self.rule.properties.items():
            value = prop.co_value
            if type(value) is CodeType:
                value = None
            else:
                value, _ = fix_rule_ids(prop.value)
            props.append((name, value))

        ret = []
        if len(props) > 1:
            ret.append('{0}_create_property = {0}.create_property'.format(self_name))
            create_prop = '{0}_create_property'.format(self_name)
        else:
            create_prop = '{0}.create_property'.format(self_name)
        for name, value in props:
            ret.append('if not hasattr({}, "{}"):'.format(self_name, name))
            ret.append('{}{}("{}", ({}))'.format(tab, create_prop, name, value))
        return ret

    @property
    def property_handlers(self):
        ids_map = self.ids_map
        tab = self.tab
        global rule_handler
        fix_ids = self.fix_rule_ids
        proxy = self.compiler.proxy
        proxy_maybe = self.compiler.proxy_maybe
        observables = self.compiler.obj_names
        funcs = []
        bindings = []
        sname = self.name
        inits = []
        lit_init = []
        delayed_init = []

        for name, prop in self.rule.properties.items():
            keys = prop.watched_keys
            # e.g. for `prop: self`
            if not keys or type(prop.co_value) is not CodeType:
                lit_init.append('{}.{} = {}'.format(sname, name, fix_ids(prop.value)[0]))
                continue
            for key in keys:
                assert len(key) > 1  # only x.y or deeper can bind

            f = '{}_h{}'.format(name, rule_handler)
            # everything given an id is mapped to fixed name, other things,
            # since no id they must
            fargs = sorted(set([(ids_map.get(k[0], k[0]))
                                for k in keys] + [sname]))
            code, used_ids = fix_ids(prop.value)
            code = '{}.{} = {}'.format(sname, name, code)

            func = ['def {}({}):'.format(f, ', '.join(fargs + ['*args']))]
            for arg, count in used_ids.items():
                if count <= 1:
                    continue
                func.append('{0}{1} = {1}.__self__'.format(tab, arg))
            func.append('{}{}'.format(tab, code))
            funcs.append(func)

            # if it's a graphics instruction we bind to delay function that
            # takes the args as args. See _delayed_start in lang.py.
            if self.rule_type == 'widget':
                inits.append([code])
                delayed = None
            else:
                delayed = 'delayed_{}'.format(f)
                code = '{} = [{}{}, None]'.format(delayed, f, ', {}' * len(fargs))
                objs = [(proxy if arg in observables else
                         proxy_maybe).use(arg) for arg in fargs]
                delayed_init.append([
                    LazyFmt(code, *objs),
                    'delayed_call_fn({}, None, None)'.format(delayed)])

            bindings.extend([
                (sname, name, f, fargs, [ids_map.get(k[0], k[0])] + k[1:],
                 delayed)
                for k in keys])
            rule_handler += 1
        return funcs, bindings, inits, lit_init, delayed_init

    @property
    def property_on_handlers(self):
        ids_map = self.ids_map
        tab = self.tab
        global rule_on_handler
        fix_rule_ids = self.fix_rule_ids
        funcs = []
        args = []
        sname = self.name

        for rule in self.rule.handlers:
            lines = []
            ids_count = defaultdict(int)
            # XXX is splitting+retab a problem if multiline string is allowed?
            for line in rule.value.splitlines():
                code, used_ids = fix_rule_ids(line)
                lines.append(code)
                for key, count in used_ids.items():
                    ids_count[key] += count

            keys = rule.watched_keys
            keys = [(ids_map.get(k[0], k[0])) for k in (keys if keys else [])]
            f = 'on_{}_h{}'.format(rule.name, rule_on_handler)
            fargs = sorted(set(ids_count.keys()).union(set(keys)))

            func_code = ['def {}({}):'.format(f, ', '.join(fargs + ['*args']))]
            for arg, count in ids_count.items():
                if count <= 1:
                    continue
                func_code.append('{0}{1} = {1}.__self__'.format(tab, arg))
            for line in lines:
                func_code.append('{}{}'.format(tab, line))

            funcs.append(func_code)
            args.append((sname, rule.name, f, fargs))
            rule_on_handler += 1
        return funcs, args


class KVCompiler(object):

    # compiler options
    tab = '    '

    rebind = True

    base_types = ['EventDispatcher', 'Observable']

    event_dispatcher_type = False
    '''When True, assumes no observable, no overwriting of fast_bind etc.
    '''

    cython = False

    # temporary, per rule variables

    rules = None

    ids = None

    root = None

    obj_names = None

    root_names = None
    '''All the root names that have been bound, includes e.g. import names.
    '''

    # LazyString
    proxy = None

    proxy_maybe = None

    property_test = None

    factory_obj = None

    # info about the rule

    has_bindings = False

    has_dispatching = False

    has_missing = False

    has_children = False

    # stores compiled code

    missing_dec = []

    func_def = []

    factory_obj_code = []

    func_bind_def = []

    func_dispatch_def = []

    missing_check = []

    missing_check_set = []

    creation = []

    missing = []

    handlers = []

    on_handlers = []

    prop_init = []

    prop_lit_init = []

    prop_delay_init = []

    proxies = []

    prop_init_return = []

    bindings = []

    dispatch_creation = []

    dispatching = []

    def walk_children(self, rule, parent=None, rule_type='widget'):
        walk = self.walk_children
        yield rule, rule_type, parent

        for child in rule.children:
            for val in walk(child, parent=rule):
                yield val
        if rule.canvas_before:
            for child in rule.canvas_before.children:
                for val in walk(child, rule_type='canvas_before', parent=rule):
                    yield val
        if rule.canvas_root:
            for child in rule.canvas_root.children:
                for val in walk(child, rule_type='canvas_root', parent=rule):
                    yield val
        if rule.canvas_after:
            for child in rule.canvas_after.children:
                for val in walk(child, rule_type='canvas_after', parent=rule):
                    yield val

    def get_children(self, root_rule):
        ids = {}
        children = []
        rule_ctxs = {}
        tab = self.tab

        for i, (rule, rule_type, parent) in enumerate(
                self.walk_children(root_rule)):
            ctx = rule_ctxs[rule] = RuleContext(
                rule=rule,
                parent=rule_ctxs[parent] if parent is not None else None,
                rule_type=rule_type, count=i, ids=ids, tab=tab, compiler=self)
            children.append(ctx)
            if rule.id:
                ids[rule.id] = ctx
        return children, ids

    def compile_rule(self, rule):
        rules, ids = self.get_children(rule)
        self.rules = rules
        self.ids = ids
        self.has_bindings = self.has_missing = self.has_dispatching = False
        self.prop_init_return = self.func_bind_def = \
            self.dispatch_creation = self.func_dispatch_def = []
        tab = self.tab
        obj_names = self.obj_names = set([rule.name for rule in rules])
        self.root_names = set()
        obj_names.add('app')
        self.root = root = rules[0]
        fnum = root.f_num
        fname = '_r{}'.format(fnum)
        self.proxy = proxy = LazyString(
            dec=(None, '{0}_ref = {0}.proxy_ref'),
            use=('{}.proxy_ref', '{}_ref'))
        self.proxy_maybe = LazyString(
            dec=(None, '{0}_ref = getattr({0}, "proxy_ref", {0})'),
            use=('getattr({0}, "proxy_ref", {0})', '{0}_ref'))
        self.property_test = prop_test = LazyString(
            dec=(None, '{0}_get_prop = {0}.property'),
            use=('{}.property', '{}_get_prop'))
        self.factory_obj = factory_obj = LazyString(
            dec=(None, 'cls_{0} = Factory.{0}'),
            use=('Factory.{}', 'cls_{}'))

        self.missing_dec = '_mc[{}] = set()'.format(root.f_num)
        self.missing_check = 'if root.__class__ not in _mc[{}]:'.\
            format(root.f_num)
        self.missing_check_set = '{}_mc[{}].add(root.__class__)'.\
            format(tab, root.f_num)
        self.proxies = [proxy.dec(val, add=False) for val in sorted(obj_names)]

        objs = OrderedDict()
        for rule in rules[1:]:
            objs[rule.rule.name] = None
        self.factory_obj_code = [factory_obj.dec(r, add=False) for r in objs]

        self.creation = creation = []
        self.has_children = len(rules) > 1
        for rule in rules:
            inst = rule.creation_instructions
            if inst:
                creation.append(inst)

        self.missing = missing = []
        for rule in rules:
            inst = rule.missing_properties
            if inst:
                self.has_missing = True
                missing.append(inst)

        self.handlers = handlers_code = []
        self.on_handlers = on_handlers_code = []
        handlers = []
        on_handlers = []
        self.prop_init = init_code = []
        self.prop_lit_init = lit_init_code = []
        self.prop_delay_init = delay_init_code = []
        for rule in rules:
            pcode, bindings, inits, linit, dinit = rule.property_handlers
            handlers_code.extend(pcode)
            handlers.extend(bindings)
            init_code.append(inits)
            lit_init_code.append(linit)
            delay_init_code.append(dinit)
            pcode, bindings = rule.property_on_handlers
            on_handlers_code.extend(pcode)
            on_handlers.extend(bindings)

        self.bindings, dispatchers = \
            self.compile_bindings(rules, handlers, on_handlers)
        self.rules_callbacks(dispatchers, fnum, fname)
        return fname, root.rule.avoid_previous_rules

    def rules_callbacks(self, dispatchers, fnum, fname):
        self.dispatching = dispatching = []
        obj_names = self.obj_names
        tab = self.tab
        root_names = list(self.root_names)

        self.func_def = code = ['def {}(root, builder_created):'.format(fname)]
        if not self.has_children and not self.has_bindings:
            return

        code.append(
            '{}bfuncs = [] if builder_created is None else builder_created'.
            format(tab))
        names = sorted(set(root_names + list(obj_names)))
        widgets = [r.name for r in self.rules[1:] if r.rule_type == 'widget']
        bfunc = '_b{}'.format(fnum)

        self.prop_init_return = [
            'if builder_created is None:',
            '{}bfuncs = [f() for f in bfuncs]'.format(tab),
            '{}bfuncs.append({}({}))'.format(tab, bfunc, ', '.join(names)),
            '{}bfuncs = [f() for f in reversed(bfuncs)]'.format(tab),
            '{}for children in reversed(bfuncs):'.format(tab),
            '{}for child in children:'.format(tab * 2),
            '{}child.dispatch("on_kv_apply", root)'.format(tab * 3),
            'else:',
            '{}bfuncs.append(partial({}))'.format(tab, ', '.join([bfunc] + names))
        ]
        self.func_bind_def = ['def {}({}):'.format(bfunc, ', '.join(names))]

        bound = ['{}_bound'.format(obj) for obj in root_names]
        dfunc = '_d{}'.format(fnum)
        if not self.has_dispatching:
            self.dispatch_creation = ['return tuple']
            return

        self.dispatch_creation = \
            'return partial({}, dispatch_objs, {})'.format(
                ', '.join([dfunc] + bound), make_tuple(widgets))

        self.func_dispatch_def = ['def {}({}):'.format(
            dfunc, ', '.join(bound + ['dispatch_objs', 'widgets']))
        ]

        for (root_obj, obj, key), (idx, bidx) in dispatchers.items():
            if obj not in obj_names:
                code = [
                    'if dispatch_objs[{}] is not None:'.format(idx),
                    '{}obj, prop, count = dispatch_objs[{}]'.format(tab, idx),
                    '{}try:'.format(tab),
                    '{}if obj == {}_bound[{}][3]:'.format(tab * 2, root_obj, bidx),
                    '{}prop.dispatch_stale(obj, count)'.format(tab * 3),
                    '{}except ReferenceError:'.format(tab),
                    '{}pass'.format(tab * 2)
                ]
            else:
                code = [
                    'if dispatch_objs[{}] is not None:'.format(idx),
                    '{}obj, prop, count = dispatch_objs[{}]'.format(tab, idx),
                    '{}prop.dispatch_stale(obj, count)'.format(tab)
                ]
            dispatching.append(code)
        dispatching.append(['return widgets'])

    def format_code(self):
        ret = []
        tab = self.tab
        def flatten(groups, depth=0):
            if isinstance(groups, (LazyFmt, LazyEval)):
                group = str(groups)
                return [tab * depth + group] if group.strip() else []
            elif isinstance(groups, (tuple, list)):
                result = []
                for group in groups:
                    result.extend(flatten(group, depth=depth))
                return result
            else:
                return [tab * depth + groups]

        for handler in self.handlers + self.on_handlers:
            for line in handler:
                ret.extend(flatten(line))
            push_empty(ret)
        if ret:
            push_empty(ret, 2)

        missing = self.missing
        if missing:
            ret.append(self.missing_dec)

        func_def = flatten(self.func_def)
        ret.extend(func_def)
        if len([l for l in func_def if l.strip()]) > 1:
            push_empty(ret)

        for lines in self.factory_obj_code:
            ret.extend(flatten(lines, depth=1))
        push_empty(ret)

        for lines in self.creation:
            ret.extend(flatten(lines, depth=1))
            push_empty(ret)

        if missing:
            ret.append(tab + self.missing_check)
            for i, inst in enumerate(missing):
                ret.extend(flatten(inst, depth=2))
                push_empty(ret)
            ret.append(tab + self.missing_check_set)
            push_empty(ret)

        for lines in self.prop_lit_init + self.prop_init:
            ret.extend(flatten(lines, depth=1))
            push_empty(ret)

        if self.prop_init_return:
            ret.extend(flatten(self.prop_init_return, depth=1))
            push_empty(ret)
            ret.extend(flatten(self.func_bind_def, depth=0))

            for lines in self.proxies:
                ret.extend(flatten(lines, depth=1))
            push_empty(ret)

            for lines in self.prop_delay_init:
                ret.extend(flatten(lines, depth=1))
                push_empty(ret)

            for lines in self.bindings:
                ret.extend(flatten(lines, depth=1))
                push_empty(ret)

            ret.extend(flatten(self.dispatch_creation, depth=1))
            push_empty(ret)
            ret.extend(flatten(self.func_dispatch_def, depth=0))

            for lines in self.dispatching:
                ret.extend(flatten(lines, depth=1))
                push_empty(ret)
        else:
            for lines in self.prop_delay_init:
                ret.extend(flatten(lines, depth=1))
                push_empty(ret)

        lines = [line for line in ret if line.strip()]
        if len(lines) == 1:
            ret.insert(ret.index(lines[0]) + 1, '{}pass'.format(tab))
        return ret

    def walk_bindings(self, handlers):
        objs = defaultdict(list)
        for rule in handlers:
            root_watcher = rule[-2][0]
            objs[root_watcher].append((0, ) + rule)
        # get the values of objs sorted by root_watcher keys in reverse
        bindings = [x[1] for x in sorted(objs.items(), key=lambda x: x[0])][::-1]

        # walk the nodes in the child binding tree
        while bindings:
            # take last node and replaces it with nodes of children at end
            last = bindings.pop()
            # we only put non-empty and level < len(watcher) - 1 on list
            # because other they are done
            assert last
            leaves = []
            objs = defaultdict(list)
            # all have the same level and for all the watchers[level] are the same
            for level, sname, name, f, fargs, watchers, delayed in last:
                assert len(watchers) - level - 1 >= 1  # rem is at least on from this level
                # we're at end - 1 of watchers so it's just e.g. a prop name
                if len(watchers) - level - 1 == 1:
                    leaves.append((sname, name, watchers[-1], f, fargs, delayed))
                else:
                    objs[watchers[level + 1]].append((level + 1, sname, name, f, fargs, watchers, delayed))

            sorted_objs = sorted(objs.items(), key=lambda x: x[0])[::-1]
            bindings.extend([x[1] for x in sorted_objs])
            nodes = []
            for key, values in sorted_objs:
                # the paths start at next level and go down the tree. All paths
                # must be unique (rebind), but leaves are individually bound.
                # So #nodes is len unique paths excluding leaves + # leaves
                paths = [elem[-2][elem[0] + 1:-1] for elem in values]  # leaves
                unique_paths = set([tuple(elem) for elem in paths])
                N = sum(map(len, unique_paths)) + len(paths) + 1  # + itself
                nodes.append((key, N, len(paths)))

            yield leaves, nodes, level, watchers[:level + 1]

    def append_dispatcher(
            self, watchers, curr_obj, key, dispatch_idxs, depth, bind_code,
            next_pos, check_prop=False):
        '''if check_prop we'll check if the prop exists, otherwise we'll assume
        it has been checked through trying to bind (fast_bind returns 0 if
        the prop has not beed found) and we'll check if the bound suceeded.
        '''
        tab = self.tab
        puse = self.property_test.use
        elem = watchers[0], curr_obj, key
        if elem not in dispatch_idxs:
            l = len(dispatch_idxs)
            dispatch_idxs[elem] = l, next_pos

            if not check_prop:
                bind_code.append(
                    LazyFmt('{}if bound[{}][5]:', tab * depth, next_pos))
                depth += 1

            quiet = ', quiet=True' if check_prop else ''
            bind_code.append(LazyFmt(
                '{}prop = {}("{}"{})', tab * depth, puse(curr_obj), key,
                quiet))

            if check_prop:
                bind_code.append(LazyFmt('{}if prop is not None:', tab * depth))
                depth += 1
            bind_code.append(LazyFmt(
                '{}dispatch_objs[{}] = [{}, prop, prop.dispatch_count({})]',
                tab * depth, l, curr_obj, curr_obj))

    def append_bindings(
            self, do_bind, leaves, next_pos, unbind_idxs, curr_obj, bind_nodes,
            nodes, depth, bind_code, bind, start, p_use, cpos, pos,
            watchers, dispatch_idxs, **kwargs):
        '''Emits the fast_bind code for the leaves and nodes. It binds to every
        leaf and node coming off from the current object at this level and
        saves the function and args for later rebinding. If not do_bind,
        it doesn't do the actual binding but just saves the args.
        '''
        ptest = self.property_test
        tab = self.tab
        not_delayed = set()
        for _, _, key, _, _, delayed in leaves:
            if not delayed:
                not_delayed.add(key)
        if bind_nodes:
            for node, _, _ in nodes:
                not_delayed.add(node)

        # for every leaf, we need to save the target func and its args and bind
        # to that func if it's observable (i.e. do_bind=true)
        for sname, name, key, f, fargs, delayed in leaves:
            assert fargs
            unbind_idxs[sname].append(next_pos)

            args = ''
            # when delayed, it's a graphics instruction so we delay callback
            if delayed:
                f = 'delayed_call_fn'
                save_args = '({}, )'.format(delayed)
                args = delayed
            elif len(fargs) == 1:
                save_args = LazyFmt('({}, )', p_use(fargs[0]))
                if do_bind:
                    args = p_use(fargs[0])
            else:
                save_args = LazyFmt('{}', map(p_use, fargs))
                if do_bind:
                    args = LazyFmt(
                        ', '.join(['{}', ] * len(fargs)), *map(p_use, fargs))

            # binding code (obj.fast_bind(...)), and proxy to object
            code = LazyFmt(
                '{}("{}", {}, {})', bind.use(curr_obj), key, f, args)
            if not do_bind:  # when not do_bind, just save args and don't
                obj = code = None
            else:
                obj = p_use(curr_obj)

            bind_code.append(LazyFmt(
                '{}bound[{}] = [None, None, {}, {}, "{}", {}, {}, {}]',
                tab * depth, next_pos, cpos, obj, key, code, f, save_args))
            if do_bind and name in not_delayed:
                self.append_dispatcher(
                    watchers, curr_obj, key, dispatch_idxs, depth, bind_code,
                    next_pos)
            next_pos += 1

        # cache checking of rebind for each prop when setting rebinding
        if bind_nodes and len(bind_nodes) > 1:
            bind_code.append(
                '{}rebind_property = {}.rebind_property'.
                format(tab * depth, curr_obj))
            rebind_property = 'rebind_property'
        else:
            rebind_property = '{}.rebind_property'.format(curr_obj)
        # when rebinding, it's all under an additonal `if rebind_prop` level
        ldepth = depth + 1 if do_bind else depth

        # now bind the update_intermediats all the intermediate nodes
        for k, (node, N, _) in enumerate(nodes if bind_nodes else []):
            assert N
            if do_bind:
                bind_code.append(       # if obj.rebind_property("prop_name"):
                    '{}if {}("{}"):'.
                    format(tab * depth, rebind_property, node))
                code = LazyFmt(  # the actual obj.fast_bind(node, ...)
                    '{}("{}", rebind_callback, bound, {})',
                    bind.use(curr_obj), node, next_pos)
                # now bind and save the args
                bind_code.append(LazyFmt(
                    '{}bound[{}] = [{}, {}, {}, {}, "{}", {}, '
                    'rebind_callback, (bound, {})]',
                    tab * ldepth, next_pos, start[k], start[k] + N - 1, cpos,
                    p_use(curr_obj), node, code, next_pos))

                if node in not_delayed:
                    self.append_dispatcher(
                        watchers, curr_obj, node, dispatch_idxs, ldepth,
                        bind_code, next_pos)
                bind_code.append('{}else:'.format(tab * depth))

            # if it wasn't rebind_property(...) still save in case a obj in
            # the tree above changes and we need the args to rebind
            bind_code.append(LazyFmt(
                '{}bound[{}] = [{}, {}, {}, None, "{}", None, '
                'rebind_callback, (bound, {})]', tab * ldepth, next_pos,
                start[k], start[k] + N - 1, cpos, node, next_pos))

            # now save the pos of the callback bound to this node
            pos[tuple(watchers) + (node, )] = next_pos
            next_pos += 1
        return next_pos

    def compile_bindings(self, rules, handlers, on_handlers):
        tab = self.tab
        proxy, proxy_maybe = self.proxy, self.proxy_maybe
        on_objs = defaultdict(list)
        ret = []
        rebind = self.rebind
        prop_test = self.property_test
        obj_names = self.obj_names
        root_names = self.root_names
        has_proxy = set()
        obj_name = lambda x: 'obj_' + '_'.join(x) if len(x) > 1 else root_name
        unbind_idxs = defaultdict(list)
        p_use = lambda x: (proxy if x in obj_names or level else proxy_maybe).use(x)
        if len(self.base_types) > 1:
            base_types = '({})'.format(', '.join(self.base_types))
        else:
            base_types = self.base_types[0]
        bind = LazyString(
            dec=(None, 'bind = {}.fast_bind'), use=('{}.fast_bind', 'bind'))
        dispatch_idxs = OrderedDict()

        # just sort the on_xx events by the objs they bind to (e.g. root, g1)
        for rule_name, prop_name, f, fargs in on_handlers:
            on_objs[rule_name].append((prop_name, f, fargs))

        # for every iter of the loop, we pick a node in topological depth first
        # order and we look at nodes and leaves that hang off. Leaves are bound
        # to final callbacks x_hn, nodes are bound to intermediats if rebind
        # each object in bound is tuple of
        # (start, end, parent, obj, key (in its parent), uid, f, args)
        for i, (leaves, nodes, level, watchers) in enumerate(
                self.walk_bindings(handlers)):
            assert nodes or leaves
            bind_code = []
            root_name = watchers[0]
            curr_obj = obj_name(watchers)
            bind_nodes = rebind and nodes
            reached_end = not nodes
            on_bindings = not level and on_objs[root_name]  # any on_xxx?

            if not level:
                root_names.add(root_name)
                self.has_bindings = True
                pos = {}
                # if not rebind, only leaves are bound otherwise everything is
                idx = 1 if rebind else 2
                N = sum([n[idx] for n in nodes]) + len(leaves)
                bind_code.append(
                    '{}_bound = bound = [None, ] * {}'.format(root_name, N))
                next_pos = 0
                if root_name not in obj_names:
                    self.proxies.append(proxy_maybe.dec(root_name, add=False))
                    has_proxy.add(root_name)

            cpos = pos.get(tuple(watchers), None)  # pos of parent in bound
            sizes = [node[1] - 1 for node in nodes]
            start = [sum(map(len, sizes[:k])) + len(nodes) + next_pos + len(leaves)
                     for k in range(len(nodes))]

            # get the next object a (if the parent wasn't already none)
            depth = 0
            # did we have a parent that may be none? Then check on it
            if level > 1 or level == 1 and watchers[0] not in obj_names:
                if nodes:
                    bind_code.append(LazyFmt('if {} is None:', obj_name(watchers[:-1])))
                    bind_code.append(LazyFmt('{}{} = None', tab, curr_obj))
                    bind_code.append('else:')
                else:
                    bind_code.append(LazyFmt('if {} is not None:', obj_name(watchers[:-1])))
                depth = 1

            if level:
                bind_code.append(LazyFmt(
                    '{}{} = {}.{}', tab * depth, curr_obj,
                    obj_name(watchers[:-1]), watchers[-1]))
            if level or curr_obj not in obj_names:
                bind_code.append(LazyFmt(
                    '{0}if {1} is not None and isinstance({1}, {2}):',
                    tab * depth, curr_obj, base_types))
                depth += 1
                if curr_obj not in has_proxy:
                    bind_code.append(LazyFmt(
                        '{}{}', tab * depth, proxy.dec(curr_obj, add=False)))
            bind_code.append(
                LazyFmt('{}{}', tab * depth, bind.dec(curr_obj, add=False)))
            bind_code.append(LazyFmt(
                '{}{}', tab * depth, prop_test.dec(curr_obj, add=False)))

            if on_bindings:  # on_xxx binds on obj.xxx, where obj is one of rules
                for prop_name, f, fargs in on_bindings:
                    code = '{}("{}", {}{})'.format(
                        '{}', prop_name, f, ', {}' * len(fargs))
                    bind_code.append(
                        LazyFmt(code, bind.use(curr_obj), *map(p_use, fargs)))
                    self.append_dispatcher(
                        watchers, curr_obj, prop_name, dispatch_idxs, 0,
                        bind_code, next_pos, check_prop=True)
                on_objs.pop(root_name)
            ret.append(bind_code)

            lcls = locals().copy()
            del lcls['self']
            old_next_pos = next_pos
            next_pos = self.append_bindings(True, **lcls)

            if rebind and level:
                depth = 1
                next_pos = old_next_pos
                bind_code.append(
                    'if bound[{}] is not None and bound[{}] is None:'.
                    format(cpos, next_pos))
                lcls = locals().copy()
                del lcls['self']
                next_pos = self.append_bindings(False, **lcls)

            if reached_end:
                for sname, idxs in unbind_idxs.items():
                    assert idxs
                    if len(idxs) == 1:
                        idxs = '({}, )'.format(idxs[0])
                    else:
                        idxs = str(tuple(sorted(set(idxs))))
                    bind_code.append(
                        '_handlers[{}.uid].append((bound, {}))'.
                        format(sname, idxs))
                unbind_idxs = defaultdict(list)

        # now finish the on_xxx not bound with props
        for rule_name, binds in on_objs.items():  # rule_name is always level 0
            if not binds:
                continue
            bind_code = []
            bind_code.append(bind.dec(rule_name, add=False))

            for prop_name, f, fargs in binds:
                code = '{}("{}", {}{})'.format(
                    '{}', prop_name, f, ', {}' * len(fargs))
                bind_code.append(
                    LazyFmt(code, bind.use(rule_name), *map(p_use, fargs)))
                self.append_dispatcher(
                        [rule_name], rule_name, prop_name, dispatch_idxs, 0,
                        bind_code, None, check_prop=True)
            ret.append(bind_code)

        if dispatch_idxs:
            ret.insert(0, 'dispatch_objs = [None, ] * {}'.format(len(dispatch_idxs)))
            self.has_dispatching = True
        return ret, dispatch_idxs

    def compile_root(self, root):
        tab = self.tab
        if not root:
            return None, 'def get_root():\n{}pass'.format(tab)

        f_name, _ = self.compile_rule(root)
        compiled_rule = self.format_code()
        code = (
            'def get_root():\n'
            '{0}widget = Factory.get("{1}")()\n'
            '{0}{2}(widget)\n'
            '{0}return widget').format(tab, root.name, f_name)
        return compiled_rule, code

    def compile_directives(self, directives):
        includes = set()
        ret = ['# directives']

        for directive in directives:
            cmd = directive[1].strip()
            if cmd[:5] == "kivy ":
                ret.append('require("{}")'.format(cmd[5:].strip()))

            elif cmd[:7] == 'import ':
                package = cmd[7:].strip().split(' ')
                if len(package) != 2:
                    raise Exception('Bad import format "{}"'.format(cmd))
                alias, package = package
                ret.append('import {} as {}'.format(package, alias))

            elif cmd[:4] == 'set ':
                name, value = cmd[4:].strip().split(' ', 1)
                ret.append('{} = {}'.format(name, value))

            elif cmd[:8] == 'include ':
                ref = cmd[8:].strip()
                force_load = False
                if ref[:6] == 'force ':
                    ref = ref[6:].strip()
                    force_load = True

                if ref[-3:] not in Builder.kv_ext:
                    raise Exception(
                        '"{}" is not a recognized kv file type'.format(ref))

                if ref in includes:
                    if not force_load:
                        continue
                    ret.append('Builder.unload_file({})'.format(ref))
                    ret.append('Builder.load_file({})'.format(ref))
                else:
                    includes.add(ref)
                    ret.append('Builder.load_file({})'.format(ref))
        return ret

    def compile_dynamic_classes(self, classes):
        ret = ['# register dynamic classes']
        for dname, dbases in classes.items():
            ret.append('Factory.register("{}", baseclasses="{}")'.
                       format(dname, dbases))
        return ret

    def generate_template(self, name, template):
        # template compilation is not supported at all, so rely on the current
        # interpreted language.
        minline = template.line
        maxline = _find_maxline(minline, template)
        code = "\n".join(
            [c[1] for c in template.ctx.sourcecode[minline:maxline + 1]])
        return ["Builder.load_string('''", code, "''')"]

    def compile(self, parser, rule_opts={}, **kwargs):
        cython = kwargs.get('cython', KVCompiler.cython)
        for opts in rule_opts.values():
            if cython:
                break
            cython = opts.get('cython')

        defaults_opts = {
            'tab': KVCompiler.tab, 'rebind': KVCompiler.rebind,
            'base_types': KVCompiler.base_types,
            'event_dispatcher_type': KVCompiler.event_dispatcher_type,
            'cython': KVCompiler.cython
        }

        for keys in [kwargs.keys()] + [x.keys() for x in rule_opts.values()]:
            for key in keys:
                if key not in defaults_opts:
                    raise KeyError('Unrecognized option "{}"'.format(key))
        defaults_opts.update(kwargs)

        # make sure that the rebind callback uses all types in all rules
        base_types = OrderedDict()
        for d in [defaults_opts] + rule_opts.values():
            for o_type in d.get('base_types', []):
                base_types[o_type] = None
        base_types = base_types.keys()
        if len(base_types) == 1:
            otype = '({}, )'.format(base_types[0])
        else:
            otype = str(tuple(base_types))

        if cython:
            lines = [cyheader_imports, cyheader_globals]
        else:
            lines = [pyheader_imports, pyheader_globals]
        lines += [rebind_callback_str.format('{}', otype), '']

        lines.extend(self.compile_directives(parser.directives))

        selectors_map = OrderedDict()
        for key, rule in parser.rules:
            if rule in selectors_map:
                selectors_map[rule].append(key)
                continue

            opts = defaults_opts.copy()
            opts.update(rule_opts.get(key, {}))
            for k, v in opts.items():
                setattr(self, k, v)

            f_name, avoid_previous_rules = self.compile_rule(rule)
            compiled_rule = self.format_code()
            selectors_map[rule] = [f_name, avoid_previous_rules, key]
            lines.append('\n')
            lines.extend(compiled_rule)

        lines.extend(
            [''] + self.compile_dynamic_classes(parser.dynamic_classes) + [''])

        tab = defaults_opts['tab']
        lines.append('# registration (selector, rule, avoid_previous_rules)')
        lines.append('rules = (')
        for item in selectors_map.values():
            rule_name, avoid_previous_rules = item[:2]
            selectors = item[2:]
            for selector in selectors:
                lines.append('{}({}("{}"), {}, {}),'.format(
                    tab, selector.__class__.__name__, selector.key,
                    rule_name, avoid_previous_rules))
        lines.append(')')

        opts = defaults_opts.copy()
        opts.update(rule_opts.get('Root', {}))
        for k, v in opts.items():
            setattr(self, k, v)
        rule_code, root_code = self.compile_root(parser.root)
        if rule_code:
            lines.extend(['' ''] + rule_code + ['', ''])
        else:
            lines.extend(['', ''])
        lines.append(root_code)
        lines[1] = lines[1].format(rule_uid)

        for name, cls, template in parser.templates:
            lines.extend(['', ''])
            lines.extend(self.generate_template(name, template))

        lines.insert(0, "# Generated from {} at {}".format(
            parser.filename, datetime.datetime.now()))

        lines = [l + "\n" for l in lines if l is not None]
        return lines, not cython


if __name__ == "__main__":
    import sys
    from kivy.lang import Builder
    fn = len(sys.argv) > 1 and sys.argv[1] or r'..\data\style.kv'
    Builder.compile_kv(fn)
