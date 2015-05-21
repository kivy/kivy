'''
Kivy language compiler
======================

.. author:: Mathieu Virbel <mat@kivy.org>, Matthew Einhorn <moiein2000@gmail.com>

'''

__all__ = []

import datetime
from types import CodeType
from collections import OrderedDict, defaultdict
from kivy.lang import Parser, lang_str
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
from kivy.event import EventDispatcher, Observable
from kivy import require
'''

header_gloabls = '''
_mc = [None, ] * {}
_includes = []

app = ProxyApp()
pt = Metrics.pt
inch = Metrics.inch
cm = Metrics.cm
mm = Metrics.mm
dp = Metrics.dp
sp = Metrics.sp
'''

header_directives = '''
def _execute_directive(cmd):
    import sys
    # small version without error handling of directives
    # temporary, until the compiler analyse and do the work
    cmd = cmd.strip()
    if cmd[:4] == 'set ':
        name, value = cmd[4:].strip().split(' ', 1)
        globals()[name] = eval(value)
    elif cmd[:8] == 'include ':
        ref = cmd[8:].strip()
        force_load = False
        if ref[:6] == 'force ':
            ref = ref[6:].strip()
            force_load = True
        if ref[-3:] != '.kv':
            return
        if ref in _includes:
            if not force_load:
                return
            Builder.unload_file(ref)
            Builder.load_file(ref)
        else:
            _includes.append(ref)
            Builder.load_file(ref)
    elif cmd[:7] == 'import ':
        package = cmd[7:].strip()
        l = package.split(' ')
        if len(l) != 2:
            return
        alias, package = l
        try:
            if package not in sys.modules:
                try:
                    mod = __import__(package)
                except ImportError:
                    mod = __import__('.'.join(package.split('.')[:-1]))
                for part in package.split('.')[1:]:
                    mod = getattr(mod, part)
            else:
                mod = sys.modules[package]
            globals()[alias] = mod
        except ImportError:
            return


def update_intermediates(*l):
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
    rule. It is assigned by :class:`PyCompiler` according to the topological
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
    def f_name(self):
        '''The name of the compiled function generated for this root rule.
        The format is `_rn`, where `n` is :attr:`f_num`.

        Should only be called for a root rule, i.e. one whose :attr:`parent` is
        None.
        '''
        return '_r{}'.format(self.f_num)

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

        rule = self.rule
        rule_type = self.rule_type
        if rule_type == 'widget':
            ret = []
            if parent is not None:  # don't create if applying rule to root
                ret.append(
                    '{} = Factory.{}(parent={}, __builder_created=True)'.
                    format(self.name, self.rule.name, parent.name))
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
            '{} = Factory.{}()'.format(self.name, self.rule.name),
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
        assert self.rule_type == 'widget'
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
                inits.append([
                    LazyFmt(code, *objs),
                    'delayed_call_fn({}, None, None)'.format(delayed)])

            bindings.extend([
                (sname, name, f, fargs, [ids_map.get(k[0], k[0])] + k[1:],
                 delayed)
                for k in keys])
            rule_handler += 1
        return funcs, bindings, inits, lit_init

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


class PyCompiler(object):

    # compiler options
    tab = '    '

    rebind = True

    base_types = ['EventDispatcher', 'Observable']

    assume_dispatch_prop = False

    # temporary, per rule variables
    code = None

    rules = None

    ids = None

    root = None

    obj_names = None

    proxy = None

    proxy_maybe = None

    property_test = None

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
        tab = self.tab
        obj_names = self.obj_names = set([rule.name for rule in rules])
        obj_names.add('app')
        self.root = root = rules[0]
        self.proxy = proxy = LazyString(
            dec=(None, '{0}_ref = {0}.proxy_ref'),
            use=('{}.proxy_ref', '{}_ref'))
        self.proxy_maybe = LazyString(
            dec=(None, '{0}_ref = getattr({0}, "proxy_ref", {0})'),
            use=('getattr({0}, "proxy_ref", {0})', '{0}_ref'))
        self.property_test = prop_test = LazyString(
            dec=(None, '{0}_get_prop = {0}.property'),
            use=('{}.property', '{}_get_prop'))

        self.code = code = {
            'missing_dec': '_mc[{}] = set()'.format(root.f_num),
            'func_def': 'def {}(root):'.format(root.f_name),
            'missing_check': 'if root.__class__ not in _mc[{}]:'.format(root.f_num),
            'missing_check_set': '{}_mc[{}].add(root.__class__)'.format(tab, root.f_num),
            'creation': [],
            'missing': [],
            'handlers': [],
            'on_handlers': [],
            'prop_init': [],
            'prop_lit_init': [],
            'proxies': [proxy.dec(val, add=False) for val in sorted(obj_names)],
            'bindings': [],
            'dispath_prop_test': [prop_test.dec(val, add=False) for val in sorted(obj_names)],
            'dispatching': [],
            'avoid_previous_rules': '{}.avoid_previous_rules = {}'.format(root.f_name, root.rule.avoid_previous_rules)
            }

        creation = code['creation']
        for rule in rules:
            inst = rule.creation_instructions
            if inst:
                creation.append(inst)

        missing = code['missing']
        for rule in rules:
            if rule.rule_type != 'widget':
                continue
            inst = rule.missing_properties
            if inst:
                missing.append(inst)

        handlers_code = code['handlers']
        on_handlers_code = code['on_handlers']
        handlers = []
        on_handlers = []
        init_code = code['prop_init']
        lit_init_code = code['prop_lit_init']
        for rule in rules:
            pcode, bindings, inits, lit_init = rule.property_handlers
            handlers_code.extend(pcode)
            handlers.extend(bindings)
            init_code.append(inits)
            lit_init_code.append(lit_init)
            pcode, bindings = rule.property_on_handlers
            on_handlers_code.extend(pcode)
            on_handlers.extend(bindings)

        code['bindings'], dispatchers = self.compile_bindings(rules, handlers, on_handlers)

        dispatching = code['dispatching']
        for (root_obj, obj, key), (idx, bidx) in dispatchers.items():
            if obj not in obj_names:
                dcode = [
                    'try:',
                    '{0}if dispatch_objs[{1}] is not None and {2} == {2}_bound[{3}][3]:'.format(tab, idx, obj, bidx),
                    '{0}dispatch_objs[{1}][1].dispatch_stale({2}, dispatch_objs[{1}][2])'.format(tab * 2, idx, obj),
                    'except ReferenceError:',
                    '{}pass'.format(tab)
                ]
            else:
                dcode = [
                    'if dispatch_objs[{}] is not None:'.format(idx),
                    '{0}dispatch_objs[{1}][1].dispatch_stale({2}, dispatch_objs[{1}][2])'.format(tab, idx, obj)
                ]
            dispatching.append(dcode)
        for rule in rules[1:]:
            if rule.rule_type != 'widget':
                continue
            dispatching.append(['{}.dispatch("on_kv_apply", root)'.format(rule.name)])

        return code, root.f_name

    def format_code(self, code):
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

        for handler in code['handlers'] + code['on_handlers']:
            for line in handler:
                ret.extend(flatten(line))
            ret.append('')
        if ret:
            ret.append('')

        missing = code['missing']
        if missing:
            ret.append(code['missing_dec'])
        ret.append(code['func_def'])
        for create in code['creation']:
            ret.extend(flatten(create, depth=1))
            ret.append('')

        if missing:
            ret.append(tab + code['missing_check'])
            for i, inst in enumerate(missing):
                ret.extend(flatten(inst, depth=2))
                if i < len(missing) - 1:
                    ret.append('')
            ret.append(tab + code['missing_check_set'])
            ret.append('')

        for section, post_line in (
                (code['proxies'], 0), (code['prop_lit_init'], 1),
                (code['prop_init'], 1), (code['bindings'], 1),
                (code['dispath_prop_test'], 0), (code['dispatching'], 1)):
            if not section:
                continue
            for lines in section:
                values = flatten(lines, depth=1)
                ret.extend(values)
                if post_line and values:
                    ret.append('')
            if not post_line and ret[-1] != '':
                ret.append('')

        if [line for line in ret if line] == [code['func_def']]:
            ret.insert(1, '{}pass'.format(tab))
        ret.append(code['avoid_previous_rules'])
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
            if do_bind:
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
                    '{}("{}", update_intermediates, bound, {})',
                    bind.use(curr_obj), node, next_pos)
                # now bind and save the args
                bind_code.append(LazyFmt(
                    '{}bound[{}] = [{}, {}, {}, {}, "{}", {}, '
                    'update_intermediates, (bound, {})]',
                    tab * ldepth, next_pos, start[k], start[k] + N - 1, cpos,
                    p_use(curr_obj), node, code, next_pos))

                self.append_dispatcher(
                    watchers, curr_obj, node, dispatch_idxs, ldepth, bind_code,
                    next_pos)
                bind_code.append('{}else:'.format(tab * depth))

            # if it wasn't rebind_property(...) still save in case a obj in
            # the tree above changes and we need the args to rebind
            bind_code.append(LazyFmt(
                '{}bound[{}] = [{}, {}, {}, None, "{}", None, '
                'update_intermediates, (bound, {})]', tab * ldepth, next_pos,
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
                pos = {}
                # if not rebind, only leaves are bound otherwise everything is
                idx = 1 if rebind else 2
                N = sum([n[idx] for n in nodes]) + len(leaves)
                bind_code.append(
                    '{}_bound = bound = [None, ] * {}'.format(root_name, N))
                next_pos = 0
                if root_name not in obj_names:
                    self.code['proxies'].append(proxy_maybe.dec(root_name, add=False))

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
        return ret, dispatch_idxs

    def compile_root(self, root):
        tab = self.tab
        if not root:
            return None, 'def get_root():\n{}pass'.format(tab)

        code, f_name = self.compile_rule(root)
        compiled_rule = self.format_code(code)
        code = (
            'def get_root():\n'
            '{0}widget = Factory.get("{1}")()\n'
            '{0}{2}(widget)\n'
            '{0}return widget').format(tab, root.name, f_name)
        return compiled_rule, code

    def compile_directives(self, directives):
        ret = ['# directives']
        for directive in directives:
            d = directive[1]
            if d[:5] == "kivy ":
                ret.append('require("{}")'.format(d[5:].strip()))
            else:
                ret.append('_execute_directive("{}")'.format(d))
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

    def compile(self, parser):
        lines = [header_imports, header_gloabls, header_directives, '']
        lines.extend(self.compile_directives(parser.directives))

        selectors_map = OrderedDict()
        for key, rule in parser.rules:
            print key
            if rule in selectors_map:
                selectors_map[rule].append(key)
                continue
            code, f_name = self.compile_rule(rule)
            compiled_rule = self.format_code(code)
            selectors_map[rule] = [f_name, key]
            lines.append('\n')
            lines.extend(compiled_rule)

        lines.extend(
            [''] + self.compile_dynamic_classes(parser.dynamic_classes) + [''])

        lines.append('# registration')
        lines.append('badd = Builder.rules.append')
        for item in selectors_map.values():
            rule_name = item[0]
            selectors = item[1:]
            for selector in selectors:
                lines.append('badd(({}("{}"), {}))'.format(
                    selector.__class__.__name__, selector.key,
                    rule_name))

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
        return lines


class CyCompiler(PyCompiler):

    event_dispatcher_type = False
    '''When True, assumes no observable, no overwriting of fast_bind etc.
    '''


if __name__ == "__main__":
    import codecs
    import sys
    from os.path import splitext
    fn = len(sys.argv) > 1 and sys.argv[1] or r'..\data\style.kv'
    with codecs.open(fn) as fd:
        content = fd.read()
    parser = Parser(content=content, filename=fn)
    compiler = PyCompiler()
    lines = compiler.compile(parser)
    with codecs.open(splitext(fn)[0] + '.kvc', "w") as fd:
        fd.writelines(lines)
