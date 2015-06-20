'''
Kivy language compiler
======================

.. author:: Mathieu Virbel <mat@kivy.org>, Matthew Einhorn <moiein2000@gmail.com>


Instantiation
===================

When a widget is created using the syntax `w = WidgetClass()`, the KV rules
associated with the class `WidgetClass` are applied to the instance before
it returns from its `__init__` method. The KV rules are applied in a specific
sequence of operations, some of which are batched. Consider the following KV
rules::

    <MyWidgetA@Widget>:
        width: 10
        prop: wid.myself
        height: self.width
        Button:
            id: wid
            myself: self
            MyWidgetC
            canvas:
                Color:
                    rgba: 1, 0, 1, 1
                Rectangle:
                    size: 10, 10
        MyWidgetB

    <MyWidgetB@Widget>:
        size_hint: None, None
        BoxLayout:
            MyWidgetC
        canvas:
            Line

    <MyWidgetC@Widget>:
        Label
        FloatLayout
            GridLayout


We can convert these rules to the following widget/graphics children tree

.. image:: images/kvrules1.png
    :align: right

Overall, when `w = MyWidgetA()` is executed and python calls its `__init__`
method, 4 steps occur:

#. __Initialization step__: For each KV rule that can be reached from the root
   `MyWidgetA` rule, all the widgets and graphics instructions are created.
   Also, all the _widget_ properties defined in the rules, e.g.
   `prop: prop_value` are initialized to those values.
#. __Binding step__: All the _graphics_ properties defined in the rules, e.g.
   `rgba: rgba_value` are initialized to those values. Followed by the creation
   of the bindings for every rule defined in KV, e.g. `prop: prop_value`, or
   `on_prop: do_func()`.


# For every widget or graphics instruction encountered in the rule
1. Walk through the widget tree generated from the kv rules associated with
   `the current widget` starting with `MyWidgetA` in a depth first manner.




Property Creation
-----------------

The first time a widget of any class type is created, we ensure that all the
properties set by the KV rule for that class exists - whether they are kivy or
python properties.

Consider the following KV rule::

    <RuleA@Label>:
        prop1: self.text
        prop2: 0.42

When the first `RuleA` is created, we check whether `prop1` and `prop2` exists
as attributes of the RuleA instance - whether as a proper kivy property or a
python property. If any don't exist, they are created dynamically as kivy
properties.

For such dynamically created properties, if the value of the rule
is a literal as described below, the type of the property created
is matched as close to the type of the value of the rule as possible
(e.g. a NumericProperty is created for 0.42) and the property is initialized
to that value. Otherwise, a `ObjectProperty` initialized to `None` is created.


Initialization
---------------

After the widgets and graphics instructions are created, and after we ensure
all properties set by the rules exist, the initialization step begins.

Initialization is split into three periods; literal initialization, non-literal
initialization, and grahical initilization.


Graphics Instructions
=====================

They are not instantly exec but are delayed.


Proxy refs
==========
direct refs are not stored

TODO:

#. Should args be initialized when the properties are executed so that they are
   available in that context? Can they be set to None, or do we actually have
   to set them to their real values? Which costs perfs.
'''

__all__ = []

__version__ = '0.1'

import datetime
from types import CodeType
from collections import OrderedDict, defaultdict
from kivy.lang import Parser, lang_str, Builder
from re import match, sub, split, compile as re_compile
from functools import partial
from os.path import abspath
import kivy

rule_handler = 0
'''The global count of the number of `__hn_prop` callback functions for rules
of the form `prop: value` that has been created. `n`, is the current value of
`rule_handler`.
'''
rule_on_handler = 0
'''The global count of the number of `__hn_on_prop` callback functions for
rules of the form `on_prop: do_x()` that has been created. `n`, is the current
value of `rule_on_handler`.
'''
rule_uid = 0
'''The global count of the number of rule application functions created so
far. I.e. each `__rn` function created for a KV root rule e.g. `<MyRule>:...`
increments this. `n`, is the current value of `rule_uid`.
'''

triquote_pat = r"(?<!\\)'''"
# Group that matches the string prefixes, e.g. rb"string"
typed_str = re_compile('.*?([rbuRBU]*)$')

header_imports = '''
import kivy.metrics as __Metrics
from kivy.factory import Factory
from kivy.lang import (
    ParserSelectorName as __ParserSelectorName, _handlers as __handlers,
    ProxyApp as __ProxyApp, delayed_call_fn as __delayed_call_fn,
    Builder as __Builder)
from kivy import require as __require
from functools import partial as __partial
'''

pyheader_imports = header_imports + \
    '''from kivy.event import EventDispatcher as __EventDispatcher, Observable as __Observable'''

cyheader_imports = header_imports + '''
from kivy._event cimport EventDispatcher as __EventDispatcher
from kivy._event cimport Observable as __Observable
from kivy.properties cimport Property
'''

header_gloabls = '''
app = __ProxyApp()
pt = __Metrics.pt
inch = __Metrics.inch
cm = __Metrics.cm
mm = __Metrics.mm
dp = __Metrics.dp
sp = __Metrics.sp
'''

pyheader_globals = header_gloabls + '''
__mc = [None, ] * {}
'''

cyheader_globals = header_gloabls + '''
cdef list __mc = [None, ] * {}
'''

rebind_callback_str = '''
def __rebind_callback(bound, i, instance, value):
    # bound is the list containing all the binds associated with a particular
    # root instance and its children nodes, e.g. `prop: root.obj`, bound
    # will contain all the binds that start with `root`. i is the bind index in
    # bound that triggered the rebind callback.
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
    parent = {{}}
    p = getattr(p, key)  # next parent
    if p is None or not isinstance(object, {0}):
        parent[i] = p, None, None, None
    else:
        parent[i] = p, p.proxy_ref, p.fast_bind, p.rebind_property

    dispatch = {{}}

    for k, node in enumerate(range(s, e)):
        # get the info stored for this bind
        node_s, node_e, pidx, p, key, buid, f, args = blist = bound[i]
        # node_s/e being None means it's a leaf with no children
        if buid:  # unbind parent's rebind
            try:
                p.unbind_uid(key, buid)
            except ReferenceError:
                pass

        p, pref, bind, rebind_prop = parent[pidx]
        # decide whether we can bind to this object
        if bind is not None and node_s is None:  # a leaf
            # replace the previous bind with the new object and bind
            blist[3] = pref  # new object ref
            blist[5] = bind(key, f, *args)  # bind leaf again
            dispatch[f] = args
            continue
        elif bind is not None and rebind_prop(key):  # a rebind node
            blist[3] = pref
            blist[5] = bind(key, f, *args)
        else:  # either None obj, or obj but no rebind and it's not a leaf
            blist[3] = blist[5] = None
            if node_s is None:
                continue

        # if the key is a leaf, don't save the key as a parent b/c it has no
        # children, hence the continue above so now, we are at rebind node
        # so we need to save this node for our children as their parent
        if node not in parent:
            if p is None:  # our parent is already None
                parent[node] = (None, None, None, None)
            else:
                p = getattr(p, key)  # next parent
                if p is None or not isinstance(object, {0}):
                    parent[node] = p, None, None, None, None
                else:
                    parent[node] = (
                        p, p.proxy_ref, p.fast_bind, p.rebind_property)

    for f, args in dispatch.items():
        f(*(args + (None, None)))
'''

return_args_str = '''
def __return_args(args):
    return args
'''


def break_multiline_code(code):
    '''Breaks a string containing (possibly multi-line) code into individual
    lines, while ensuring it's still legal python. E.g. strings that span
    multiple lines are broken into per-line quoted strings with the proper
    prefixes. For example::

        >>> s = '1 + self.width * 2'
        >>> break_multiline_code(s)
        ['1 + self.width * 2']
        >>> s = "self.text + 'whateves'"
        >>> break_multiline_code(s)
        ["self.text + 'whateves'"]
        >>> s = \'''self.text + rb\\'\\'\\'
        ... they ran a lot
        ... the next day they couldn't walk at all
        ... \\'\\'\\' + self.sleepy
        ... \'''
        >>> break_multiline_code(s)
        ["self.text + rb\'''\''' + (rb\'''\\n\'''", "rb\'''they ran a \
lot\\n\'''", "rb\'''the next day they couldn't walk at all\\n\'''", \
"rb\'''\''') + self.sleepy"]
    '''
    res = []
    last_line = ''
    vals = split(lang_str, code)

    for i, val in enumerate(vals):
        if not val:
            continue
        # splitlines doesn't add empty line if val ends with newline, so we
        # will have to check and start a new line if it does end with one
        lines = val.splitlines()

        # whole string/code is contained in current line
        if len(lines) == 1:
            last_line += lines[0]  # don't keep newline from `val`
            if val.endswith('\n') or val.endswith('\r'):
                res.append(last_line)
                last_line = ''
            continue

        # this is pure code part, just add it to result
        if not i % 2:
            res.append(last_line + lines[0])
            res.extend(lines[1:-1])
            last_line = lines[-1]
            if val.endswith('\n') or val.endswith('\r'):
                res.append(last_line)
                last_line = ''
            continue

        # for string, we split the string into a string per line
        if val.startswith('"""'):
            quote = '"""'
        elif val.startswith('"'):
            quote = '"'
        elif val.startswith("'''"):
            quote = "'''"
        else:
            assert val.startswith("'")
            quote = "'"
        # now find whether it has a type, e.g. r''
        tp = ''
        m = match(typed_str, last_line)
        if m is not None:
            tp = m.group(1)

        # for a multiline spanning string, keep the original newline types
        lines = val.splitlines(True)
        # add a parenthesis so it can be broken up
        res.append('{0}{2}{2} + ({1}{3}{2}'.
                   format(last_line, tp, quote, lines[0]))
        for line in lines[1:-1]:
            res.append(tp + quote + line + quote)
        last_line = tp + quote + lines[-1] + ')'
        # final string never ends with newline, so need to check

    if last_line:
        res.append(last_line)
    return res


def safe_comment(code, linenum):
    '''Takes any string representing code and returns a list of strings that
    when printed as one string per line will envelope the code as a single or
    multiline string.

    The resulting string also includes formatting indicating the source
    code line (linenum) from which the code originates. For example::

        >>> safe_comment('name = "55"', 7)
        ['\\'\\'\\'Line 7: name = "55" \\'\\'\\'']
        >>> safe_comment('val = 44', 7)
        ["\'''Line 7: val = 44 \'''"]
        >>> safe_comment('val = (1, 2,\\n3, 4)', 7)
        ["\'''Line 7: val = (1, 2,", "3, 4) \'''"]
        >>> safe_comment("val = (1, \'''fruits\\nand veggies\''')", 7)
        ["\'''Line 7: val = (1, \\\\\'''fruits", "and veggies\\\\\''') \'''"]
    '''
    lines = [sub(triquote_pat, r"\'''", l) for l in code.splitlines()]
    if not lines:
        return lines

    lines[0] = "'''Line {}: {}".format(linenum, lines[0])
    lines[-1] = lines[-1] + " '''"
    return lines


def make_tuple(objs):
    '''Create a string tuple from the string objects in objs. For example::

        >>> make_tuple([])
        '()'
        >>> make_tuple(['1', ])
        '(1, )'
        >>> make_tuple(['1', '3'])
        '(1, 3)'
    '''
    if not len(objs):
        return '()'
    elif len(objs) == 1:
        return '({}, )'.format(objs[0])
    else:
        return '({})'.format(', '.join(objs))


def push_empty(lines, max_empty=1):
    '''Adds an empty line to the `lines` list, if all the last `max_empty`
    items in `lines`, when stripped are not the empty string. For example::

        >>> lines = ['a', 'b']
        >>> push_empty(lines, max_empty=1)
        >>> lines
        ['a', 'b', '']
        >>> push_empty(lines, max_empty=1)
        >>> lines
        ['a', 'b', '']
        >>> push_empty(lines, max_empty=2)
        >>> lines
        ['a', 'b', '', '']
    '''
    if [l for l in lines[-max_empty:] if l.strip()]:
        lines.append('')


def find_maxline(line, rule):
    '''Finds the last line of the rule.
    '''
    line = max(line, rule.line)
    for child in rule.children:
        line = max(line, find_maxline(line, child))
    for prop in rule.properties.values():
        line = max(line, prop.line)
    if rule.canvas_root:
        line = max(line, find_maxline(line, rule.canvas_root))
    if rule.canvas_before:
        line = max(line, find_maxline(line, rule.canvas_before))
    if rule.canvas_after:
        line = max(line, find_maxline(line, rule.canvas_after))
    return line


def larger_than_one(options, n):
    '''Takes `options` and returns the first element of `options` if `n` is
    less than or equal to 1, other it returns the second element.
    '''
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
            return partial(self._get, name)
        raise AttributeError(name)

    def _get(self, selection, value, add=True):
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
    '''Returned by :class:`LazyString`, and when evaluated as a string, returns
    a value based on the usage in :class:`LazyString`.
    '''

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

    The instance also takes a `group` keyword argument, and if the value of
    `group` is in :attr:`hidden_groups`, then the instance evaluates to the
    empty string. This is useful by setting :attr:`hidden_groups` of the class,
    e.g. `LazyFmt.hidden_groups.add('doc')`, all the instances whose group
    is `'doc'`, will now evaluate to the empty string.
    '''

    hidden_groups = set()

    def __init__(self, text, *largs, **kwargs):
        self.group = kwargs.get('group')
        self.text = text
        self.largs = largs
        self.kwargs = kwargs

    def __str__(self):
        if self.group in LazyFmt.hidden_groups:
            return ''
        return self.text.format(*self.largs, **self.kwargs)

    def __repr__(self):
        return self.__str__()

DocFmt = partial(LazyFmt, group='doc')


class RuleContext(object):
    '''A :class:`RuleContext` represents the kv rules associated with a single
    (possibly child) object instantiated using kv. There's a rule associated
    with each object, including root, children, and graphics children objects.

    There are many properties of :class:`RuleContext` that can only be called
    depending if the instance is a widget type, or graphics type.

    See the class properties for the init parameters.

    The rule is that whenever a property or function returns a list of code
    strings, the shallowest code in the list is indented at indent of zero.
    It's the responsibility of the calling code to then re-indent the returned
    code to the appropriate level based on the required indent of the
    shallowest level.

    For example, if we return a `if` statement meant to be in a function,
    although in the final code the `if` will be at a indent of a single tab
    and the contents under the `if` will have two tabs, when returned here,
    because `if` is the shallowest level, `if` will not be indented, while its
    contents will be indented by one tab.
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
    uniquely for each rule (object) within the children objects of the root kv
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
    '''The number of spaces represented by a tab. Automatically set by
    :attr:`KVCompiler.tab`.
    '''

    compiler = None
    '''The :class:`KVCompiler` instance that created this :class:`RuleContext`
    instance.
    '''

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

        #. `root` for the root widget with no parent (even if it has a KV id),
        #. `xn` for objects with no `id` given in kv, or
        #. `xn_id` for objects with kv ids, where `id` is the KV id given.

        `x` above is either `g`, or `w` for graphics and widget objects,
        respectively. `n` above is the value of :attr:`count`.

        By mangeling the names in the compiled code, it is ensured that names
        given in kv will never clash with other parts of the compiled code,
        since nothing there is allowed to start with `w`, `g`, or root.
        '''
        if self.parent is None:
            return 'root'
        id_str = '_{}'.format(self.rule.id) if self.rule.id else ''
        if self.rule_type == 'widget':
            return 'w{}{}'.format(self.count, id_str)
        return 'g{}{}'.format(self.count, id_str)

    @property
    def self_name(self):
        '''If :attr:`rule_type` is `'widget'` it returns :attr:`name` of this
        rule, otherwise it returns the :attr:`name` of the widget in which
        this graphics instruction is child of, i.e. :attr:`parent`.
        '''
        return self.name if self.rule_type == 'widget' else self.parent.name

    @property
    def doc_name(self):
        '''Returns a representation for the docs of the name of the class of
        this rule. For example::

            <MyRule>:
                Widget:
                    Label:
                        prop: prop_value

        The `Label` rule would be returned as `MyRule -> Widget -> Label`.
        '''
        names = []
        obj = self
        while obj is not None:
            names.append(obj.rule.name)
            obj = obj.parent
        return ' -> '.join(names[::-1])

    @property
    def f_num(self):
        '''The number given to the compiled function generated for the root
        rule associated with this rule.

        This only makes sense when read for a :class:`RuleContext` that is a
        root rule, i.e. its :attr:`parent` is None. It is uniquely generated
        for all the compiled root rules.
        '''
        if self._root_f_num is None and self.parent is None:
            global rule_uid
            self._root_f_num = rule_uid
            rule_uid += 1
        return self._root_f_num

    @property
    def parent_add_child(self):
        '''Returns the code string used to add graphics to its parent's
        canvas (e.g. obj.canvas.add). This can only be called for
        :class:`RuleContext` representing graphical rules.

        Depending whether the instruction is a only child, a alias or the
        direct canvas add method is returned.
        '''
        assert self.parent is not None
        rule_type = self.rule_type
        assert rule_type != 'widget'  # it's added through cls(parent=child)
        if self.is_only_child:
            return '{}.{}.add'.format(
                self.parent.name, rule_type.replace('_root', '').replace('_', '.'))
        else:
            return '__add_{}_{}'.format(self.parent.name, rule_type)

    @property
    def creation_instructions(self):
        '''Returns the code string list used to create the object represented
        by this :attr:`RuleContext`, if it's not the root rule.

        It also creates the alias for adding graphics to this widget, if it's
        a widget, used by :attr:`parent_add_child` (e.g.
        `__add_obj_canvas_root = obj.canvas.add`). Widgets are added to their
        parents using the `parent` keyword.
        '''
        parent = self.parent
        fuse = self.compiler.factory_obj.use

        rule = self.rule
        rule_type = self.rule_type
        if rule_type == 'widget':
            ret = []
            if parent is not None:  # don't create if applying rule to root
                ret.append(DocFmt("'''Line {}: {}'''", rule.line, self.doc_name))
                batch = ', __builder_created=__bfuncs' if self.compiler.batch_bind else ''
                ret.append(LazyFmt(
                    '{} = {}(parent={}{})', self.name, fuse(rule.name),
                    parent.name, batch))
            if rule.canvas_root and len(rule.canvas_root.children) > 1:
                ret.append(
                    '__add_{0}_canvas_root = {0}.canvas.add'.format(self.name))
            if rule.canvas_before and len(rule.canvas_before.children) > 1:
                ret.append('__add_{0}_canvas_before = {0}.canvas.before.add'.
                           format(self.name))
            if rule.canvas_after and len(rule.canvas_after.children) > 1:
                ret.append('__add_{0}_canvas_after = {0}.canvas.after.add'.
                           format(self.name))
            return ret
        return [
            DocFmt("'''Line {}: {}'''", rule.line, self.doc_name),
            LazyFmt('{} = {}()', self.name, fuse(self.rule.name)),
            '{}({})'.format(self.parent_add_child, self.name)]

    @property
    def ids_map(self):
        '''Returns a dictionary mapping ids to the actual widget name given to
        the widget when created. E.g. `id: label` gets converted to e.g.
        `w2_label = Label()`, so the dict would map `w2_label` to `label`.

        Everything that is given an id (i.e. id: value) throughout this
        root rule context, as well as `self`, `app`, and `root` is a key in the dict.
        `self` always maps to :attr:`self_name`.
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
        '''Takes a KV rule as `rule_text` and for each key of the keys of
        :attr:`ids_map`, if the key is found in `rule_text` they are replaced
        by the corresponding value in :attr:`ids_map`.

        For example, for ::

            <MyRule>:
                Label:
                    id: label
                    text: str(self.size)

        `label.text = str(self.size)` will become e.g.
        `w2_label.text = str(w2_label.size)`.

        :returns:

            A 2-tuple; the first element is a string respresenting `rule_text`
            that has been fixed as described, and the second element is a
            dict whose keys are the keys of :attr:`ids_map` found in
            `rule_text`, and its values are the number of times they were
            found there.
        '''
        ids_map = self.ids_map
        used_ids = defaultdict(int)
        if self._ids_pat is None:
            self._ids_pat = pat = re_compile(
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
        '''Returns the code string list that checks whether any properties
        that are being set by a KV rule, e.g. `prop: value`, don't exist, and
        then creates these as kivy properties.

        For graphical children this returns an empty list, because they don't
        have kivy properties.
        '''
        if self.rule_type != 'widget':
            return []
        tab = self.tab
        self_name = self.name
        fix_rule_ids = self.fix_rule_ids
        dname = self.doc_name

        props = []
        for prop_name, prop in self.rule.properties.items():
            value = prop.value
            if type(prop.co_value) is CodeType:
                code = 'None'
            else:
                code, _ = fix_rule_ids(value)  # fix e.g. self naming

            comment = [
                DocFmt('{}', l) for l in
                safe_comment('{} @ {}: '.format(dname, prop_name) + value, prop.line)]
            props.append((prop_name, code, comment))

        ret = []
        # do we need to cache the create_property method?
        if len(props) > 1:
            ret.append(['__create_property_{0} = {0}.create_property'.format(self_name)])
            create_prop = '__create_property_{0}'.format(self_name)
        else:
            create_prop = '{0}.create_property'.format(self_name)

        for name, code, comment in props:
            code = '{}("{}", ({}))'.format(create_prop, name, code)
            code = ['{}{}'.format(tab, l) for l in break_multiline_code(code)]
            ret.append(
                comment +
                ['if not hasattr({}, "{}"):'.format(self_name, name)] + code)
        return ret

    @property
    def property_handlers(self):
        '''Returns a 5-tuple of `(funcs, bindings, inits, lit_init,
        delayed_init)` that contains the code for handling `prop: value` type
        KV rules associated with widget :attr:`name`. This is returned whether
        it's a graphical or widget instance attribute being set by the rule.

        `funcs`: is the function definitions and code of the `__h` functions
            bound and called to execute the KV rule and set the property.
        `bindings`: is a list of 7-tuples `(sname, prop_name, f, fargs,
            keys, delayed, comment)` use to create the bindings.
            `sname`: is :attr:`self_name`.
            `prop_name`: is the property name being set by the rule.
            `f`: is the function name in `funcs` associated with the rule.
            `fargs`: is the list of objects (e.g. widgets) that need to be
                passed to the function `f` upon a callback.
            `keys`: is a list of an attribute chain that the rule binds to.
                E.g. `prop: self.obj.name or self.cls.value`, will add two
                tuples to `bindings` whose respective `keys` are `['self',
                'obj', 'name']`, and `['self', 'cls', 'value']`.
            `delayed`: is None if a widget instance attribute is set, otherwise
                a graphical attribute is set and this is of the form
                `__delayed_xxx` and is the list passed to `__delayed_call_fn`
                for scheduling a graphical update.
            `comment`: is a list of strings containing the comments describing
                the KV code that generated this rule.
        `inits`: is the list of code that initializes non-literals rules.
        `lit_init`: is the list of code that initializes literal rules (e.g.
            `prop: self` or `prop: 2.5`).
        `delayed_init`: is the code that schedules the initilization of rules
            that set attributes of graphics children using `__delayed_call_fn`.
        '''
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
        dname = self.doc_name

        for prop_name, prop in self.rule.properties.items():
            keys = prop.watched_keys
            lnum = prop.line
            value = prop.value
            # used_ids is the names of known widgets (i.e. with __self__ attr)
            # in the fixed code
            code, used_ids = fix_ids(value)
            code = '{}.{} = {}'.format(sname, prop_name, code)
            code = break_multiline_code(code)
            comment = [
                DocFmt('{}', l) for l in
                safe_comment('{} @ {}: '.format(dname, prop_name) + value, lnum)]

            # if the rule doesn't bind anything (e.g. `prop: self`), or it's
            # not a CodeType - we consider it a literal
            if not keys or type(prop.co_value) is not CodeType:
                lit_init.append(comment + code)
                continue
            for key in keys:
                assert len(key) > 1  # only x.y or deeper can bind

            f = '__h{}_{}'.format(rule_handler, prop_name)  # function name
            # args to the callback. But first ensure e.g. self etc. is mapped
            # to the correct name, e.g. w4 (espeically for graphics instruct.)
            # fargs may include args that are not known (e.g. global names)
            fargs = sorted(set([(ids_map.get(k[0], k[0])) for k in keys] + [sname]))

            func = ['def {}({}):'.format(f, ', '.join(fargs + ['*args']))]
            func.extend([DocFmt('{}{}', tab, l) for l in comment])

            # do e.g. objname = objname.__self__ for better perf
            for arg, count in used_ids.items():
                if count < 1:
                    continue
                func.append('{0}{1} = {1}.__self__'.format(tab, arg))

            func.extend(['{}{}'.format(tab, line) for line in code])
            funcs.append(func)

            # if it's a graphics instruction we bind to delay function that
            # takes the args as args. See _delayed_start in lang.py.
            if self.rule_type == 'widget':
                inits.append(comment + code)
                delayed = None
            else:
                # if it's delayed, we only shcedule a call, but don't init
                delayed = '__delayed_{}'.format(f)  # list that stores args
                code = '{} = [{}{}, None]'.format(delayed, f, ', {}' * len(fargs))
                objs = [(proxy if arg in observables else
                         proxy_maybe).use(arg) for arg in fargs]
                delayed_init.append(comment + [
                    LazyFmt(code, *objs),
                    '__delayed_call_fn({}, None, None)'.format(delayed)
                ])

            # add all the (fixed) keys and args to which we need to bind
            bindings.extend([
                (sname, prop_name, f, fargs, [ids_map.get(k[0], k[0])] + k[1:],
                 delayed, comment)
                for k in keys])
            rule_handler += 1
        return funcs, bindings, inits, lit_init, delayed_init

    @property
    def property_on_handlers(self):
        '''Returns a 2-tuple of `(funcs, args)` that contains the code for
        handling `on_prop: do_x()` type KV rules associated with widget
        :attr:`name`.

        `funcs`: is the function definitions and code of the `__hx_on_prop`
            functions bound and called to execute the KV rule when the property
            changes.
        `args`: is a list of 6-tuples `(sname, ev_name, f, fargs, comment,
            code` use to create the bindings.
            `sname`: is :attr:`self_name`.
            `ev_name`: is the on_property or event name that triggers the rule.
            `f`: is the function name in `funcs` associated with the rule.
            `fargs`: is the list of objects (e.g. widgets) that need to be
                passed to the function `f` upon a callback.
            `comment`: is a list of strings containing the comments describing
                the KV code that generated this rule.
            `code`: is the inlined code of the rule used when all the rules are
                finished being applied in order to execute the rule if the prop
                or event was triggered during rule application.
        '''
        ids_map = self.ids_map
        tab = self.tab
        global rule_on_handler
        fix_rule_ids = self.fix_rule_ids
        funcs = []
        args = []
        sname = self.name
        dname = self.doc_name

        for rule in self.rule.handlers:
            keys = rule.watched_keys
            value = rule.value
            ev_name = rule.name
            # used_ids is the names of known widgets (i.e. with __self__ attr)
            # in the fixed code
            code, used_ids = fix_rule_ids(value)
            code = break_multiline_code(code)
            comment = [DocFmt('{}', l) for l in safe_comment(
                '{} @ {}: '.format(dname, ev_name) + value, rule.line)]

            keys = [(ids_map.get(k[0], k[0])) for k in (keys if keys else [])]
            f = '__h{}_{}'.format(rule_on_handler, ev_name)  # func name
            # args to the callback. But first ensure e.g. self etc. is mapped
            # to the correct name, e.g. w4 (espeically for graphics instruct.)
            fargs = sorted(set(used_ids.keys()).union(set(keys)))

            func_code = ['def {}({}):'.format(f, ', '.join(fargs + ['*args']))]
            func_code.extend([DocFmt('{}{}', tab, l) for l in comment])
            # do e.g. objname = objname.__self__ for better perf
            for arg, count in used_ids.items():
                if count < 1:
                    continue
                func_code.append('{0}{1} = {1}.__self__'.format(tab, arg))
            func_code.extend(['{}{}'.format(tab, line) for line in code])

            funcs.append(func_code)
            args.append((sname, ev_name, f, fargs, comment, code))
            rule_on_handler += 1
        return funcs, args


class KVCompiler(object):
    '''Class that takes parsed KV rules and generates python code from these
    rules.
    '''

    # compiler options
    tab = '    '
    '''The string to use whenever a tab is required. Defaults to 4 spaces.
    '''

    rebind = True
    '''Whether `rebind` as described in
    :class:`~kivy.properties.ObjectProperty` is assumed to always be False
    for all the objects enncountered in KV rules. If `False`, we can perform
    certain optimizations, but then no rebinding will be done.

    Defaults to True.
    '''

    base_types = ['EventDispatcher', 'Observable']
    '''The base class types used when checking whether a object found in a KV
    rule can be bound to, by checking whether it's an instance of any of these
    base types. Any class listed here must have `fast_bind` and related
    methods. By reducing the number of classes listed, performace can be
    improved.

    Defaults to `['EventDispatcher', 'Observable']`.
    '''

    event_dispatcher_type = False
    '''**Not implemented** cython option.
    When True, assumes only EventDispatcher and no Observable, and that the
    fast_bind methods has not been overwritten.
    '''

    cython = False
    '''**Not implemented** cython option.
    Whether to compile the code to cython.
    '''

    include_doc = True
    '''Whether doc strings will be included in the compiled code. Not
    including it will reduce the compiled code size.

    Defaults to True.
    '''

    batch_bind = True
    '''**Temporary experimental method**

    A temporary option that swicthes betweeen two fundemental ways of doing the
    executaion order of KV bindings.

    When `False`, bindings occur mostly like in the past, except for some
    optimizations.

    When `True`, bindings will batched across all the KV rules, even rules
    defined in other compiled files (if it was compiled with batch_bind=True).
    Consider the following KV rules::

        <RuleA@BoxLayout>:
            Label:
                my_pos: root.pos

        <RuleB@Button>:
            RuleA:
                markup: self.disabled and self.text
    '''

    # temporary, per rule variables

    rules = None

    ids = None

    root = None

    obj_names = None
    '''A set of the variable names of all the known objects; these are the
    names of the widget and graphical children that were created (whether they
    have an `id`, e.g. `root`, `w1`, etc.), as well as `app`.
    '''

    root_names = None
    '''All the root names that have been bound, includes e.g. import names.
    E.g. in `state: varname.state`, `varname` could be a created child or a
    imported global name, either way if `varname` is used when binding it's
    included here.
    '''

    # LazyString
    proxy = None

    proxy_maybe = None

    factory_obj = None

    fast_bind_alias = None

    # info about the rule

    has_bindings = False

    has_missing = False
    '''Whether this rule may have missing properties at all (i.e. at least one
    widget child has a rule like `prop: prop_value`). '''

    on_inits_map = None

    # stores compiled code

    missing_dec = []

    func_def = []

    factory_obj_code = []

    func_bind_def = []

    func_on_init_def = []

    missing_check = []

    missing_check_set = []

    creation = []

    missing = []

    handlers = []
    '''Stores the function handlers bound to `prop: value` type rules. '''

    on_handlers = []
    '''Stores the function handlers bound to `on_prop: value` type rules. '''

    prop_init = []

    prop_lit_init = []

    prop_delay_init = []

    proxies = []

    prop_init_return = []

    bindings = []

    on_init_creation = []

    on_init_return = []

    handlers_initial_count = []

    on_handlers_inits = []

    on_handlers_bind = []

    def walk_children(self, rule, parent=None, rule_type='widget'):
        '''Iterates through all the widgets and graphics instructions defined
        by the rule. It walks through the all the widgets, canvas before,
        canvas, and canvas after in that order and for each instance returns a
        3-tuple containing :class:`~kivy.lang.ParserRule`,
        the rule type with values similar to :attr:`RuleContext.rule_type`, and
        the parent :class:`~kivy.lang.ParserRule` of the current rule.

        The order walked for each :attr:`RuleContext.rule_type` is depth first,
        similar to the order they are declared.
        '''
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
        '''Starting from the root rule, it walks all the children rules with
        :method:`walk_children` and creates a :class:`RuleContext` instance for
        each rule.

        :returns:

            2-tuple (`children`, `ids`). `Children` is the list of all the
            created :class:`RuleContext`, and `ids` is a mapping from the id
            name given to the rule if it's a widget, to its
            :class:`RuleContext` instance.
        '''
        ids = {}
        children = []
        rule_ctxs = {}  # ParserRule -> RuleContext mapping
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
        '''Resets all the relavent class attributes and compiles and
        intitilizes all the code attrbutes with compiled code.

        :returns:

            2-tuple of `(fname, avoid_previous_rules)`, where fname is the
            rule's function name, and avoid_previous_rules is a boolean
            that applies to this rule.
        '''
        # clear stuff from previous runs
        self.has_bindings = self.has_missing = False
        self.prop_init_return = self.func_bind_def = \
            self.on_init_creation = self.func_on_init_def = \
            self.handlers_initial_count = self.on_handlers_inits = \
            self.on_handlers_bind = self.on_init_return = []
        inits_map = self.on_inits_map = {}
        tab = self.tab

        # get all the children rules in a linear order
        rules, ids = self.get_children(rule)
        self.rules = rules
        self.ids = ids
        # get the names of the objects to be created as well as root and app
        obj_names = self.obj_names = set([rule.name for rule in rules])
        obj_names.add('app')

        # clear the known root (`x` in `prop: x.y.z`) names
        self.root_names = root_names = set()
        self.root = root = rules[0]  # root rule
        fnum = root.f_num  # number of this root function
        fname = '__r{}'.format(fnum)  # and function name of the root function

        # create the potential alias types
        self.proxy = proxy = LazyString(
            dec=(None, '__ref_{0} = {0}.proxy_ref'),
            use=('{}.proxy_ref', '__ref_{}'))
        self.proxy_maybe = LazyString(
            dec=(None, '__ref_{0} = getattr({0}, "proxy_ref", {0})'),
            use=('getattr({0}, "proxy_ref", {0})', '__ref_{}'))
        self.factory_obj = factory_obj = LazyString(
            dec=(None, '__cls_{0} = Factory.{0}'),
            use=('Factory.{}', '__cls_{}'))
        self.fast_bind_alias = LazyString(
            dec=(None, '__bind_{0} = {0}.fast_bind'), use=('{}.fast_bind', '__bind_{}'))

        # init set that keeps track of classes we already instantiated before
        self.missing_dec = '__mc[{}] = set()'.format(root.f_num)
        # checks whether the root rule class hsa been instantiated before
        self.missing_check = 'if root.__class__ not in __mc[{}]:'.\
            format(root.f_num)
        # and add the class once it has been instantiated
        self.missing_check_set = '{}__mc[{}].add(root.__class__)'.\
            format(tab, root.f_num)

        # init it to decleration of proxies to the known EventDispatchers
        self.proxies = [proxy.dec(val, add=False) for val in sorted(obj_names)]

        # ordered set of the class names so we can alias multiused classes
        # these are e.g. Rectangle, Label and other classes that we instantiate
        objs = OrderedDict()
        for rule in rules[1:]:
            objs[rule.rule.name] = None
        self.factory_obj_code = [factory_obj.dec(r, add=False) for r in objs]

        self.creation = creation = []
        # create all children widgets and graphics
        for rule in rules:
            inst = rule.creation_instructions
            if inst:
                creation.append(inst)

        # check and ensure the missing properties are created
        self.missing = missing = []
        for rule in rules:
            inst = rule.missing_properties
            if inst:
                self.has_missing = True  # there's at least one property
                missing.append(inst)

        # handler function defs and code bodies
        self.handlers = handlers_code = []
        self.on_handlers = on_handlers_code = []
        # the bindings for the handlers
        handlers = []
        on_handlers = []
        # inits that init the prop values
        self.prop_init = init_code = []
        self.prop_lit_init = lit_init_code = []
        self.prop_delay_init = delay_init_code = []
        # for every rule, get the inits, handler functions, and bindings
        for rule in rules:
            # get the function defs and bindings for prop: val
            pcode, bindings, inits, linit, dinit = rule.property_handlers
            handlers_code.extend(pcode)
            handlers.extend(bindings)

            # get the literal, non-lit, and graphical init code
            init_code.extend(inits)
            lit_init_code.extend(linit)
            delay_init_code.extend(dinit)

            # get the function defs and bindings for on_prop: val
            pcode, bindings = rule.property_on_handlers
            on_handlers_code.extend(pcode)
            on_handlers.extend(bindings)

        # compile all the handler bindings
        self.bindings = self.compile_bindings(rules, handlers, on_handlers)
        self.generate_on_code(on_handlers)

        # the function definition that applies the rule
        self.func_def = code = [
            'def {}(root, __builder_created):'.format(fname)]

        # the names of all the widgets created
        widgets = [r.name for r in self.rules[1:] if r.rule_type == 'widget']
        wgts_str = make_tuple(widgets)
        if self.batch_bind and (widgets or self.has_bindings):
            code.append(
                '{}__bfuncs = [] if __builder_created is None else __builder_created'.
                format(tab))
            # the names of all the known objects, including imported ones
            names = sorted(set(list(root_names) + list(obj_names)))
            if inits_map:
                names += ['__on_init']
            # the bind function name
            bfunc = '__b{}'.format(fnum)

            # at the end of rule apllication do the bind and dispatch steps
            self.prop_init_return = [
                'if __builder_created is None:',
                '{}__bfuncs = [f() for f in __bfuncs]'.format(tab),
                '{}__bfuncs.append({}({}))'.format(tab, bfunc, ', '.join(names)),
                '{}__bfuncs = [f() for f in reversed(__bfuncs)]'.format(tab),
                '{}for __children in reversed(__bfuncs):'.format(tab),
                '{}for __child in __children:'.format(tab * 2),
                '{}__child.dispatch("on_kv_apply", root)'.format(tab * 3),
                'else:',
                '{}__bfuncs.append(__partial({}))'.format(tab, ', '.join([bfunc] + names))
            ]
            # pass all the objects to bind function
            self.func_bind_def = ['def {}({}):'.format(bfunc, ', '.join(names))]

            # dispatch function name
            dfunc = '__d{}'.format(fnum)
            # if there are no init and on_handlers to exec, then just
            # return the widgets that need to have on_kv_apply done one them
            if not self.on_handlers_inits and not self.prop_init:
                if widgets:
                    self.on_init_creation = [
                        'return __partial(__return_args, {})'.
                        format(wgts_str)]
                else:
                    self.on_init_creation = ['return tuple']
            else:
                # otherwise, create the dispatch function
                self.on_init_creation = (
                    'return __partial({})'.format(', '.join([dfunc] + names)))
                # and generate that func def
                self.func_on_init_def = [
                    'def {}({}):'.format(dfunc, ', '.join(names))]
                # and create that func return
                self.on_init_return = ['return {}'.format(wgts_str)]
        elif widgets:
            lines = self.on_init_return = []
            for obj in widgets:
                lines.append('{}.dispatch("on_kv_apply", root)'.format(obj))

        return fname, root.rule.avoid_previous_rules

    def format_code(self):
        '''Combines all the compiled code into a final list of strings, where
        each string is a single code line.
        '''
        ret = []
        tab = self.tab
        root = self.root.rule
        try:
            LazyFmt.hidden_groups.remove('doc')
        except KeyError:
            pass
        if not self.include_doc:
            LazyFmt.hidden_groups.add('doc')
        def flatten(groups, depth=0):
            '''Flatten the possible recursive list of lists of strings into a
            flat list of strings. Also adds tabs to the resulting code.
            Depth is the tab depth of the resulting code.
            '''
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

        # add the handler functions
        for handler in self.handlers + self.on_handlers:
            for line in handler:
                ret.extend(flatten(line))
            push_empty(ret)  # separate the handlers with one line
        if ret:  # after the handlers keep two blank lines
            push_empty(ret, 2)

        # document the rule
        ret.append('# {} L{}'.format(root.name, root.line))

        # add the missing property set() variable
        missing = self.missing
        if missing:
            ret.append(self.missing_dec)

        # add the rule function defintion
        func_def = flatten(self.func_def)
        ret.extend(func_def)
        if self.prop_init or self.prop_lit_init:
            ret.append('{}args = None, None'.format(tab))
        if len([l for l in func_def if l.strip()]) > 1:
            push_empty(ret)

        # the aliases for the children classes
        for lines in self.factory_obj_code:
            ret.extend(flatten(lines, depth=1))
        push_empty(ret)

        # now create the children
        for lines in self.creation:
            ret.extend(flatten(lines, depth=1))
            push_empty(ret)

        # add the missing check and missing creation
        if missing:
            ret.append(tab + self.missing_check)
            for i, inst in enumerate(missing):
                ret.extend(flatten(inst, depth=2))
                push_empty(ret)
            ret.append(tab + self.missing_check_set)
            push_empty(ret)

        # and then save the state of the on_handlers and init lits and non-lits
        for lines in (
                self.handlers_initial_count + self.prop_lit_init +
                self.prop_init):
            ret.extend(flatten(lines, depth=1))
            push_empty(ret)

        # add the on_kv_apply code if it exists
        ret.extend(flatten(self.prop_init_return, depth=1))
        push_empty(ret)
        # add the bind func def
        ret.extend(flatten(self.func_bind_def, depth=0))

        # add the proxy alias for storing in bound rules
        for lines in self.proxies:
            ret.extend(flatten(lines, depth=1))
        push_empty(ret)

        # schedule the graphics inits that were delayed
        for lines in self.prop_delay_init:
            ret.extend(flatten(lines, depth=1))
            push_empty(ret)

        # add the bindings
        for lines in self.bindings + self.on_handlers_bind:
            ret.extend(flatten(lines, depth=1))
            push_empty(ret)

        # add the return code that returns the dispatch callback
        ret.extend(flatten(self.on_init_creation, depth=1))
        push_empty(ret)
        # add that dispatch func if it exists
        ret.extend(flatten(self.func_on_init_def, depth=0))

        # now re-init the non-lits and dispatch the on_handlers
        init = self.prop_init if self.bindings else []

        if self.bindings and self.prop_init:
            for lines in ['args = None, None'] + self.prop_init:
                ret.extend(flatten(lines, depth=1))
                push_empty(ret)

        if self.on_handlers_inits:
            for lines in ['args = None,'] + self.on_handlers_inits:
                ret.extend(flatten(lines, depth=1))
                push_empty(ret)

        # now return the widgets that need to have on_kv_apply on them
        ret.extend(flatten(self.on_init_return, depth=1))

        # check whether there was any code at all in the func
        lines = [
            line for line in ret if line.strip() and
            not line.strip().startswith('#')]
        # if it's just a func def, add pass
        if len(lines) == 1:
            ret.insert(ret.index(lines[0]) + 1, '{}pass'.format(tab))
        return ret

    def walk_bindings(self, handlers):
        '''Walks in a sometimes ending circle.
        '''
        objs = defaultdict(list)
        for rule in handlers:
            root_watcher = rule[-3][0]
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
            for level, sname, name, f, fargs, watchers, delayed, comment in last:
                assert len(watchers) - level - 1 >= 1  # rem is at least on from this level
                # we're at end - 1 of watchers so it's just e.g. a prop name
                if len(watchers) - level - 1 == 1:
                    leaves.append((sname, name, watchers[-1], f, fargs, delayed, comment))
                else:
                    objs[watchers[level + 1]].append((level + 1, sname, name, f, fargs, watchers, delayed, comment))

            sorted_objs = sorted(objs.items(), key=lambda x: x[0])[::-1]
            bindings.extend([x[1] for x in sorted_objs])
            nodes = []
            for key, values in sorted_objs:
                # the paths start at next level and go down the tree. All paths
                # must be unique (rebind), but leaves are individually bound.
                # So #nodes is len unique paths excluding leaves + # leaves
                paths = [elem[-3][elem[0] + 1:-2] for elem in values]  # leaves
                unique_paths = set([tuple(elem) for elem in paths])
                N = sum(map(len, unique_paths)) + len(paths) + 1  # + itself
                nodes.append((key, N, len(paths)))

            yield leaves, nodes, level, watchers[:level + 1]

    def generate_on_code(self, on_handlers):
        '''Generates the initial count checking, bindings, and final rule
        evaluation based on these counts for all the on_prop rules.
        '''
        tab = self.tab
        tab2 = tab * 2
        obj_names = self.obj_names
        root_names = self.root_names
        proxy = self.proxy
        p_use = lambda x: proxy.use(x) if x in obj_names or level else x
        bind = self.fast_bind_alias

        prop_test = LazyString(
            dec=(None, '__get_prop_{0} = {0}.property'),
            use=('{}.property', '__get_prop_{}'))
        puse = prop_test.use
        pdec = prop_test.dec
        # a keys are widget objs names, values are dicts whose keys are the
        # event names of obj (i.e. on_event_name) and values are the goods
        objs = OrderedDict()
        mapping = self.on_inits_map
        inits = self.on_handlers_inits = []
        count = self.handlers_initial_count = []
        bind_code = self.on_handlers_bind = []

        # first sort the objects and events
        for sname, ev_name, f, fargs, comment, code in on_handlers:
            ev_name = ev_name[3:]
            if sname not in objs:
                objs[sname] = OrderedDict()
            obj = objs[sname]
            if ev_name not in obj:
                obj[ev_name] = []
            obj[ev_name].append((f, fargs, comment, code))

        # generate the instructions
        for obj, events in objs.items():
            count.append([pdec(obj, add=False)])
            if obj not in root_names:
                bind_code.append([bind.dec(obj, add=False)])
            for ev_name, items in events.items():
                i = mapping[(obj, ev_name)] = len(mapping)
                lines_count = []
                cappnd = lines_count.append
                lines_init = []
                iappnd = lines_init.append
                lines_bind = []
                bappnd = lines_bind.append

                # go through all the on_prop rules for property prop
                for f, fargs, comment, _ in items:
                    lines_count.extend(comment)  # add the doc comments
                    lines_init.extend(comment)
                    lines_bind.extend(comment)

                    # create the bindings that exec the on_xxx code
                    obj_bind = bind.use(obj)
                    proxies = map(p_use, fargs)
                    # check the on_event is actually a property
                    bappnd('__prop_init = __on_init[{}]'.format(i))
                    bappnd('if __prop_init is None:')
                    # it wasn't so bind to the event
                    line = '{}{}("on_{}", {}{})'.format(
                        tab, '{}', ev_name, f, ', {}' * len(fargs))
                    bappnd(LazyFmt(line, obj_bind, *proxies))

                    bappnd('else:')  # it was a property so bind to the prop
                    line = '{}{}("{}", {}{})'.format(
                        tab, '{}', ev_name, f, ', {}' * len(fargs))
                    bappnd(LazyFmt(line, obj_bind, *proxies))
                    # and save the current count for later
                    bappnd('{}__prop_init[2] = __prop_init[0].dispatch_count({})'.
                           format(tab, obj))

                # at init check if it's a prop and get the initial count
                cappnd(LazyFmt('__prop = {}("{}", quiet=True)', puse(obj), ev_name))
                cappnd('if __prop is not None:')
                cappnd('{}__on_init[{}] = [__prop, __prop.dispatch_count({}), None]'.format(tab, i, obj))

                # at dispatch, exec code if the property value changed earlier
                iappnd('if __on_init[{}] is not None:'.format(i))
                iappnd('{}__prop, s, e = __on_init[{}]'.format(tab, i))
                iappnd('{}if s != e and __prop.dispatch_count({}) == e:'.format(tab, obj))
                # add the code
                for _, _, _, code in items:
                    lines_init.extend([LazyFmt('{}{}', tab2, l) for l in code])

                count.append(lines_count)
                inits.append(lines_init)
                bind_code.append(lines_bind)

        # the list that will hold the on_xx dispatch count
        if mapping:
            count.insert(0, ['__on_init = [None, ] * {}'.format(len(mapping))])
        self.has_bindings = self.has_bindings or len(mapping)

    def append_bindings(
            self, do_bind, leaves, next_pos, unbind_idxs, curr_obj, bind_nodes,
            nodes, depth, bind_code, bind, start, p_use, cpos, pos,
            watchers, level, **kwargs):
        '''Emits the fast_bind code for the leaves and nodes. It binds to every
        leaf and node coming off from the current object at this level and
        saves the function and args for later rebinding. If not do_bind,
        it doesn't do the actual binding but just saves the args. This is
        needed when the parent is e.g. None but we need to save the args for
        later maybe rebinding.
        '''
        tab = self.tab
        not_delayed = set()
        for _, _, key, _, _, delayed, comment in leaves:
            if not delayed:
                not_delayed.add(key)
        if bind_nodes:
            for node, _, _ in nodes:
                not_delayed.add(node)

        # for every leaf, we need to save the target func and its args and bind
        # to that func if it's observable (i.e. do_bind=true)
        for sname, name, key, f, fargs, delayed, comment in leaves:
            assert fargs
            unbind_idxs[sname].append(next_pos)

            args = ''
            # when delayed, it's a graphics instruction so we delay callback
            if delayed:
                f = '__delayed_call_fn'
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
                '{}__bound[{}] = [None, None, {}, {}, "{}", {}, {}, {}]',
                tab * depth, next_pos, cpos, obj, key, code, f, save_args))
            next_pos += 1

        # cache checking of rebind for each prop when setting rebinding
        if bind_nodes and len(bind_nodes) > 1:
            bind_code.append(
                '{}__rebind_property = {}.rebind_property'.
                format(tab * depth, curr_obj))
            rebind_property = '__rebind_property'
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
                    '{}("{}", __rebind_callback, __bound, {})',
                    bind.use(curr_obj), node, next_pos)
                # now bind and save the args
                bind_code.append(LazyFmt(
                    '{}__bound[{}] = [{}, {}, {}, {}, "{}", {}, '
                    '__rebind_callback, (__bound, {})]',
                    tab * ldepth, next_pos, start[k], start[k] + N - 1, cpos,
                    p_use(curr_obj), node, code, next_pos))

                if level:  # see below
                    bind_code.append('{}else:'.format(tab * depth))

            # if it wasn't rebind_property(...) still save in case a obj in
            # the tree above changes and we need the args to rebind. But
            # that's only possible if we're below root level
            if level:
                bind_code.append(LazyFmt(
                    '{}__bound[{}] = [{}, {}, {}, None, "{}", None, '
                    '__rebind_callback, (__bound, {})]', tab * ldepth, next_pos,
                    start[k], start[k] + N - 1, cpos, node, next_pos))

            # now save the pos of the callback bound to this node
            pos[tuple(watchers) + (node, )] = next_pos
            next_pos += 1
        return next_pos

    def get_child_start_idxs(self, nodes, leaves, next_pos):
        # given a node, bound stores first all the direct children of the
        # node sequentially, then for each of its direct nodes all the
        # children of that node.
        # sizes is the number of nodes/leaves hanging off from each of the
        # direct nodes of the current node
        sizes = [node[1] - 1 for node in nodes]
        # start stores for each direct node from the current node, the idx
        # of that direct node's first child
        start = [sum(map(len, sizes[:k])) + len(nodes) + next_pos + len(leaves)
                 for k in range(len(nodes))]
        return start

    def compile_bindings(self, rules, handlers, on_handlers):
        tab = self.tab
        proxy, proxy_maybe = self.proxy, self.proxy_maybe
        ret = []
        rebind = self.rebind
        obj_names = self.obj_names
        root_names = self.root_names
        #has_proxy = set()  # contains all tree roots that have been given a proxy
        obj_name = lambda x: 'obj_' + '_'.join(x) if len(x) > 1 else root_name
        unbind_idxs = defaultdict(list)
        p_use = lambda x: proxy.use(x) if x in obj_names or level else x
        base_types = ['__' + b for b in self.base_types]
        if len(base_types) > 1:
            base_types = '({})'.format(', '.join(base_types))
        else:
            base_types = base_types[0]
        bind = self.fast_bind_alias

        # for every iter of the loop, we pick a node in topological depth first
        # order and we look at nodes and leaves that hang off. Leaves are binds
        # to final callbacks x_hn, nodes are binds to intermediats if rebind.
        # each object in bound is tuple of
        # (start, end, parent, obj, key (in its parent), uid, f, args)
        # watchers is the paths starting from root to the nodes and leaves
        # hanging from the node that the watchers path leads to (watchers[-1])
        for i, (leaves, nodes, level, watchers) in enumerate(
                self.walk_bindings(handlers)):
            assert nodes or leaves
            bind_code = []
            root_name = watchers[0]
            curr_obj = obj_name(watchers)
            bind_nodes = rebind and nodes
            reached_end = not nodes

            # a root level is the root of a new tree, e.g. label in label.obj.name
            # level is the distance to the child of the current node node from
            # the root (zero if we're the root)
            if not level:
                root_names.add(root_name)
                self.has_bindings = True
                pos = {}  # the index in bound to any node
                # if not rebind, only leaves are bound otherwise everything is
                # node[1] is the number of nodes hanging of from node,
                # node[2] is the number of all leaves reachable from node
                idx = 1 if rebind else 2
                # N is the total number of bindable nodes/leaves from root
                N = sum([n[idx] for n in nodes]) + len(leaves)
                # e.g. root_bound = bound = [None, ] * 70
                bind_code.append(
                    '__bound = [None, ] * {}'.format(N))
                next_pos = 0  # index in bound of current node binding
                #has_proxy.add(root_name)
                #if root_name not in obj_names:
                    # we found another root that is not an `id` or `app`
                    #self.proxies.append(proxy_maybe.dec(root_name, add=False))
            else:
                parent = obj_name(watchers[:-1])  # name of parent of this node

            # pos of the node that is the parent of the leaves/nodes in bound
            cpos = pos.get(tuple(watchers), None)
            start = self.get_child_start_idxs(nodes, leaves, next_pos)

            # given the current node, we need to bind all the leaves (and
            # nodes if rebind)
            depth = 0  # num tabs
            # did the current node have a parent that may be none? if we're at
            # level <= 1, e.g. 1 when the current node is y from x.y then the
            # parent x cannot be None since we created it, unless it's not an
            # `id` or `app`. If we're at zeroth level, there's no parent
            if level > 1 or level == 1 and root_name not in obj_names:
                # if we have just leaves and the parent is None then we don't
                # create an alias for this Node b/c it won't be used but if
                # there are nodes, create the alias = None for lower leaves
                if nodes:
                    bind_code.append(LazyFmt('if {} is None:', parent))
                    bind_code.append(LazyFmt('{}{} = None', tab, curr_obj))
                    bind_code.append('else:')
                else:
                    bind_code.append(LazyFmt('if {} is not None:', parent))
                depth = 1
            # now, if the parent could not be None or if it could and we're
            # under an `if` making sure the code is exec if it's not None

            # make alias for current node from the non-None parent, only needed
            # if we're not a root level node, which doesn't need an alias
            if level:
                bind_code.append(LazyFmt(
                    '{}{} = {}.{}', tab * depth, curr_obj, parent,
                    watchers[-1]))
            # we have an alias for the current node. But is its value None?
            # at root level, root could be None if it's not a recognized name
            # e.g. an imported variable name so add a check if it's None
            if level or curr_obj not in obj_names:
                # if no leaves, there must be some nodes, but if not rebind,
                # then we don't need anything with the nodes so skip following
                if leaves or bind_nodes:
                    bind_code.append(LazyFmt(
                        '{0}if {1} is not None and isinstance({1}, {2}):',
                        tab * depth, curr_obj, base_types))
                    depth += 1
                    if level:
                        bind_code.append(LazyFmt(
                            '{}{}', tab * depth, proxy.dec(curr_obj, add=False)))
            # alias bind = fast_bind for this node
            bind_code.append(
                LazyFmt('{}{}', tab * depth, bind.dec(curr_obj, add=False)))

            # if we're at root level and there are on_xxx events bind them
            ret.append(bind_code)

            lcls = locals().copy()  # now bind the leaves and nodes
            del lcls['self']
            old_next_pos = next_pos
            next_pos = self.append_bindings(True, **lcls)

            # if rebind, even if the parent or the node is None, if there was
            # a rebind = True in our parent tree, we need to save all the args
            # in case later we will be rebound to non-None object.
            if rebind and level:
                depth = 1
                next_pos = old_next_pos
                bind_code.append(
                    'if __bound[{}] is not None and __bound[{}] is None:'.
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
                        '__handlers[{}.uid].append((__bound, {}))'.
                        format(sname, idxs))
                unbind_idxs = defaultdict(list)
        return ret

    def compile_root(self, root):
        tab = self.tab
        if not root:
            return None, 'def get_root():\n{}pass'.format(tab)

        f_name, _ = self.compile_rule(root)
        compiled_rule = self.format_code()
        code = (
            'def get_root():\n'
            '{0}widget = Factory.get("{1}")()\n'
            '{0}{2}(widget, None)\n'
            '{0}return widget').format(tab, root.name, f_name)
        return compiled_rule, code

    def compile_directives(self, directives):
        includes = set()
        tab = self.tab
        ret = ['# directives']

        for directive in directives:
            cmd = directive[1].strip()
            if cmd[:5] == "kivy ":
                ret.append('__require("{}")'.format(cmd[5:].strip()))

            elif cmd[:7] == 'import ':
                package = cmd[7:].strip().split(' ')
                if len(package) != 2:
                    raise Exception('Bad import format "{}"'.format(cmd))
                alias, package = package
                pkgs = package.rsplit('.', 1)
                if len(pkgs) == 1:
                    ret.append('import {} as {}'.format(package, alias))
                else:
                    ret.extend([
                        'try:',
                        '{}import {} as {}'.format(tab, package, alias),
                        'except ImportError:',
                        '{}from {} import {} as {}'.format(tab, pkgs[0], pkgs[1], alias)
                    ])

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
                    ret.append('__Builder.unload_file({})'.format(ref))
                    ret.append('__Builder.load_file({})'.format(ref))
                else:
                    includes.add(ref)
                    ret.append('__Builder.load_file({})'.format(ref))
        return ret

    def compile_dynamic_classes(self, classes):
        ret = ['# register dynamic classes']
        for dname, dbases in classes.items():
            ret.append(
                'Factory.register("{}", baseclasses="{}", filename=__file__, '
                'warn=True)'.format(dname, dbases))
        return ret

    def generate_template(self, name, template):
        # template compilation is not supported at all, so rely on the current
        # interpreted language.
        minline = template.line
        maxline = find_maxline(minline, template)
        code = "\n".join(
            [c[1] for c in template.ctx.sourcecode[minline:maxline + 1]])
        return ["__Builder.load_string('''", code, "''')"]

    def compile(self, parser, file_hash, rule_opts={}, **kwargs):
        cython = kwargs.get('cython', KVCompiler.cython)
        for opts in rule_opts.values():
            if cython:
                break
            cython = opts.get('cython')

        defaults_opts = {
            'tab': KVCompiler.tab, 'rebind': KVCompiler.rebind,
            'base_types': KVCompiler.base_types,
            'event_dispatcher_type': KVCompiler.event_dispatcher_type,
            'cython': KVCompiler.cython,
            'include_doc': KVCompiler.include_doc,
            'batch_bind': KVCompiler.batch_bind
        }

        for keys in [kwargs.keys()] + [x.keys() for x in rule_opts.values()]:
            for key in keys:
                if key not in defaults_opts:
                    raise KeyError('Unrecognized option "{}"'.format(key))
        defaults_opts.update(kwargs)

        # make sure that the rebind callback uses all types in all rules
        # so pick the maximum provided base types from all options
        # use OrderedDict as ordered set.
        base_types = OrderedDict()
        for d in [defaults_opts] + rule_opts.values():
            for o_type in d.get('base_types', []):
                base_types[o_type] = None
        otype = make_tuple(['__' + b for b in base_types.keys()])

        ver = '__version__ = "{}"'.format(__version__)
        kver = '__kivy_version__ = "{}"'.format(kivy.__version__)
        source = '__source_file__ = r"{}"'.format(abspath(parser.filename))
        src_hash = '__source_hash__ = b"{}"'.format(file_hash)

        lines = [ver, kver, source, src_hash]
        if cython:
            lines += [cyheader_imports, cyheader_globals]
        else:
            lines += [pyheader_imports, pyheader_globals]
        lines += [rebind_callback_str.format(otype), '', return_args_str, '']

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
            push_empty(lines, 2)
            lines.extend(compiled_rule)
            push_empty(lines, 2)

        lines.extend(
            [''] + self.compile_dynamic_classes(parser.dynamic_classes) + [''])

        tab = defaults_opts['tab']
        lines.append('# registration (selector, rule, avoid_previous_rules)')
        lines.append('rules = (')
        for item in selectors_map.values():
            rule_name, avoid_previous_rules = item[:2]
            selectors = item[2:]
            for selector in selectors:
                lines.append('{}(__{}("{}"), {}, {}),'.format(
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
        lines[5] = lines[5].format(rule_uid)

        for name, cls, template in parser.templates:
            lines.extend(['', ''])
            lines.extend(self.generate_template(name, template))

        lines.insert(0, "# Compiled from {} at {}".format(
            abspath(parser.filename), datetime.datetime.now()))

        lines = [l for l in lines if l is not None]
        return lines, not cython


if __name__ == "__main__":
    import sys
    from kivy.lang import Builder
    fn = len(sys.argv) > 1 and sys.argv[1] or r'..\data\style.kv'
    Builder.compile_kv(fn)
