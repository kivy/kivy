'''
Parser
======

Class used for the parsing of .kv files into rules.
'''
import os

import io
import re
import sys
import keyword
import tokenize
import traceback
import ast
import importlib
from re import sub, findall
from types import CodeType
from functools import partial
from collections import OrderedDict, defaultdict

import kivy.lang.builder  # imported as absolute to avoid circular import
from kivy.logger import Logger
from kivy import require
from kivy.resources import resource_find
from kivy.utils import rgba
import kivy.metrics as Metrics

__all__ = ('Parser', 'ParserException', 'ParserControlRule',
           'ParserControlBranch')


trace = Logger.trace
global_idmap = {}

# all previously included files
__KV_INCLUDES__ = []

# precompile regexp expression
str_re = (
    "(?:'''.*?''')|"
    "(?:(?:(?<!')|''')'(?:[^']|\\\\')+?'(?:(?!')|'''))|"
    '(?:""".*?""")|'
    '(?:(?:(?<!")|""")"(?:[^"]|\\\\")+?"(?:(?!")|"""))'
)

lang_str = re.compile(f"({str_re})", re.DOTALL)
lang_fstr = re.compile(f"([fF](?:{str_re}))", re.DOTALL)

lang_key = re.compile('([a-zA-Z_]+)')
lang_keyvalue = re.compile(r'([a-zA-Z_][a-zA-Z0-9_.]*\.[a-zA-Z0-9_.]+)')
lang_tr = re.compile(r'(_\()')
lang_cls_split_pat = re.compile(', *')
lang_control = re.compile(r'(if|elif|else|for|slot|factory)\b')

# all the widget handlers, used to correctly unbind all the callbacks then the
# widget is deleted
_handlers = defaultdict(partial(defaultdict, list))


class ProxyApp(object):
    # proxy app object
    # taken from http://code.activestate.com/recipes/496741-object-proxying/

    __slots__ = ['_obj']

    def __init__(self):
        object.__init__(self)
        object.__setattr__(self, '_obj', None)

    def _ensure_app(self):
        app = object.__getattribute__(self, '_obj')
        if app is None:
            from kivy.app import App
            app = App.get_running_app()
            object.__setattr__(self, '_obj', app)
            # Clear cached application instance, when it stops
            app.bind(on_stop=lambda instance:
                     object.__setattr__(self, '_obj', None))
        return app

    def __getattribute__(self, name):
        object.__getattribute__(self, '_ensure_app')()
        return getattr(object.__getattribute__(self, '_obj'), name)

    def __delattr__(self, name):
        object.__getattribute__(self, '_ensure_app')()
        delattr(object.__getattribute__(self, '_obj'), name)

    def __setattr__(self, name, value):
        object.__getattribute__(self, '_ensure_app')()
        setattr(object.__getattribute__(self, '_obj'), name, value)

    def __bool__(self):
        object.__getattribute__(self, '_ensure_app')()
        return bool(object.__getattribute__(self, '_obj'))

    def __str__(self):
        object.__getattribute__(self, '_ensure_app')()
        return str(object.__getattribute__(self, '_obj'))

    def __repr__(self):
        object.__getattribute__(self, '_ensure_app')()
        return repr(object.__getattribute__(self, '_obj'))


global_idmap['app'] = ProxyApp()
global_idmap['pt'] = Metrics.pt
global_idmap['inch'] = Metrics.inch
global_idmap['cm'] = Metrics.cm
global_idmap['mm'] = Metrics.mm
global_idmap['dp'] = Metrics.dp
global_idmap['sp'] = Metrics.sp
global_idmap['rgba'] = rgba


class ParserException(Exception):
    '''Exception raised when something wrong happened in a kv file.
    '''

    def __init__(self, context, line, message, cause=None):
        self.filename = context.filename or '<inline>'
        self.line = line
        sourcecode = context.sourcecode
        sc_start = max(0, line - 2)
        sc_stop = min(len(sourcecode), line + 3)
        sc = ['...']
        for x in range(sc_start, sc_stop):
            if x == line:
                sc += ['>> %4d:%s' % (line + 1, sourcecode[line][1])]
            else:
                sc += ['   %4d:%s' % (x + 1, sourcecode[x][1])]
        sc += ['...']
        sc = '\n'.join(sc)

        message = 'Parser: File "%s", line %d:\n%s\n%s' % (
            self.filename, self.line + 1, sc, message)
        if cause:
            message += '\n' + ''.join(traceback.format_tb(cause))

        super(ParserException, self).__init__(message)


class ParserRuleProperty(object):
    '''Represent a property inside a rule.
    '''

    __slots__ = ('ctx', 'line', 'name', 'value', 'co_value',
                 'watched_keys', 'mode', 'count', 'ignore_prev',
                 'force_code')

    def __init__(self, ctx, line, name, value, ignore_prev=False):
        super(ParserRuleProperty, self).__init__()
        #: Associated parser
        self.ctx = ctx
        #: Line of the rule
        self.line = line
        #: Name of the property
        self.name = name
        #: Value of the property
        self.value = value
        #: Compiled value
        self.co_value = None
        #: Compilation mode
        self.mode = None
        #: Watched keys
        self.watched_keys = None
        #: Stats
        self.count = 0
        #: whether previous rules targeting name should be cleared
        self.ignore_prev = ignore_prev
        #: always compile to a code object, even for a constant expression
        #: (an iteration-local like `[]` must evaluate freshly per iteration)
        self.force_code = False

    def precompile(self):
        name = self.name
        value = self.value

        # first, remove all the string from the value
        tmp = sub(lang_str, '', self.value)

        # detecting how to handle the value according to the key name
        mode = self.mode
        if self.mode is None:
            self.mode = mode = 'exec' if name[:3] == 'on_' else 'eval'
        if mode == 'eval' and not self.force_code:
            # if we don't detect any string/key in it, we can eval and give the
            # result
            if re.search(lang_key, tmp) is None:
                value = '\n' * self.line + value
                self.co_value = eval(
                    compile(value, self.ctx.filename or '<string>', 'eval')
                )
                return

        # ok, we can compile.
        value = '\n' * self.line + value
        self.co_value = compile(value, self.ctx.filename or '<string>', mode)

        # for exec mode, we don't need to watch any keys.
        if mode == 'exec':
            return

        # now, detect obj.prop
        # find all the fstrings in the  value
        fstrings = lang_fstr.findall(value)
        wk = set()
        for s in fstrings:
            expression = ast.parse(s)
            wk |= set(self.get_names_from_expression(expression.body[0].value))

        # first, remove all the string from the value
        tmp = sub(lang_str, '', value)
        idx = tmp.find('#')
        if idx != -1:
            tmp = tmp[:idx]
        # detect key.value inside value, and split them
        wk |= set(findall(lang_keyvalue, tmp))
        if wk:
            self.watched_keys = [x.split('.') for x in wk]
        if findall(lang_tr, tmp):
            if self.watched_keys:
                self.watched_keys += [['_']]
            else:
                self.watched_keys = [['_']]

    @classmethod
    def get_names_from_expression(cls, node):
        """
        Look for all the symbols used in an ast node.
        """
        if isinstance(node, ast.Name):
            yield node.id

        if isinstance(node, (ast.JoinedStr, ast.BoolOp)):
            for n in node.values:
                yield from cls.get_names_from_expression(n.value)

        if isinstance(node, ast.BinOp):
            yield from cls.get_names_from_expression(node.right)
            yield from cls.get_names_from_expression(node.left)

        if isinstance(node, ast.IfExp):
            yield from cls.get_names_from_expression(node.test)
            yield from cls.get_names_from_expression(node.body)
            yield from cls.get_names_from_expression(node.orelse)

        if isinstance(node, ast.Subscript):
            yield from cls.get_names_from_expression(node.value)
            yield from cls.get_names_from_expression(node.slice)

        if isinstance(node, ast.Slice):
            yield from cls.get_names_from_expression(node.lower)
            yield from cls.get_names_from_expression(node.upper)
            yield from cls.get_names_from_expression(node.step)

        if isinstance(
            node,
            (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)
        ):
            for g in node.generators:
                yield from cls.get_names_from_expression(g.iter)

        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            for elt in node.elts:
                yield from cls.get_names_from_expression(elt)

        if isinstance(node, ast.Dict):
            for val in node.values:
                yield from cls.get_names_from_expression(val)

        if isinstance(node, ast.UnaryOp):
            yield from cls.get_names_from_expression(node.operand)

        if isinstance(node, ast.comprehension):
            yield from cls.get_names_from_expression(node.iter.value)

        if isinstance(node, ast.Attribute):
            # Build full dotted attribute path (e.g. "root.object.property")
            attribute_parts = []
            current_node = node
            while isinstance(current_node, ast.Attribute):
                attribute_parts.append(current_node.attr)
                current_node = current_node.value
            if isinstance(current_node, ast.Name):
                attribute_parts.append(current_node.id)
                full_attribute = ".".join(reversed(attribute_parts))
                yield full_attribute
            return

        if isinstance(node, ast.Call):
            yield from cls.get_names_from_expression(node.func)

            for arg in node.args:
                yield from cls.get_names_from_expression(arg)
            for keyword in node.keywords:
                yield from cls.get_names_from_expression(keyword.value)

    def __repr__(self):
        return '<ParserRuleProperty name=%r filename=%s:%d ' \
               'value=%r watched_keys=%r>' % (
                   self.name, self.ctx.filename, self.line + 1,
                   self.value, self.watched_keys)


class ParserRule(object):
    '''Represents a rule, in terms of the Kivy internal language.
    '''

    __slots__ = ('ctx', 'line', 'name', 'children', 'id', 'properties',
                 'canvas_before', 'canvas_root', 'canvas_after',
                 'handlers', 'level', 'cache_marked', 'avoid_previous_rules',
                 'has_controls', 'id_scope_key', 'id_scope_names', 'scope_id',
                 'slot_defs')

    def __init__(self, ctx, line, name, level):
        super(ParserRule, self).__init__()
        #: Level of the rule in the kv
        self.level = level
        #: Associated parser
        self.ctx = ctx
        #: Line of the rule
        self.line = line
        #: Name of the rule
        self.name = name
        #: List of children to create
        self.children = []
        #: Id given to the rule
        self.id = None
        #: Properties associated to the rule
        self.properties = OrderedDict()
        #: Canvas normal
        self.canvas_root = None
        #: Canvas before
        self.canvas_before = None
        #: Canvas after
        self.canvas_after = None
        #: Handlers associated to the rule
        self.handlers = []
        #: Properties cache list: mark which class have already been checked
        self.cache_marked = []
        #: Indicate if any previous rules should be avoided.
        self.avoid_previous_rules = False
        #: True if any direct child is a control statement (fast-path test)
        self.has_controls = False
        #: Key and names of the rule-level reactive-id scope (ids declared
        #: inside `if` branches and `slot` blocks of this rule)
        self.id_scope_key = None
        self.id_scope_names = []
        #: (scope_key, name) when this widget's id lives on a scope object
        self.scope_id = None
        #: Slot names this rule declares (definitions), in document order
        self.slot_defs = None

        if level == 0:
            self._detect_selectors()
        else:
            self._forbid_selectors()

    def precompile(self):
        for x in self.properties.values():
            x.precompile()
        for x in self.handlers:
            x.precompile()
        for x in self.children:
            x.precompile()
        if self.canvas_before:
            self.canvas_before.precompile()
        if self.canvas_root:
            self.canvas_root.precompile()
        if self.canvas_after:
            self.canvas_after.precompile()

    def create_missing(self, widget):
        # check first if the widget class already been processed by this rule
        cls = widget.__class__
        if cls in self.cache_marked:
            return
        self.cache_marked.append(cls)
        for name in self.properties:
            if hasattr(widget, name):
                continue
            value = self.properties[name].co_value
            if type(value) is CodeType:
                value = None
            widget.create_property(name, value, default_value=False)

    def _forbid_selectors(self):
        c = self.name[0]
        if c == '<' or c == '[':
            raise ParserException(
                self.ctx, self.line,
                'Selectors rules are allowed only at the first level')

    def _detect_selectors(self):
        c = self.name[0]
        if c == '<':
            self._build_rule()
        elif c == '[':
            raise ParserException(
                self.ctx, self.line,
                'Kivy lang templates ([Name@Base]:) were deprecated in 1.7.0 '
                'and have been removed. Use a dynamic class '
                '<Name@Base>: instead.')
        else:
            if self.ctx.root is not None:
                raise ParserException(
                    self.ctx, self.line,
                    'Only one root object is allowed by .kv')
            self.ctx.root = self

    def _build_rule(self):
        name = self.name
        if __debug__:
            trace('Builder: build rule for %s' % name)
        if name[0] != '<' or name[-1] != '>':
            raise ParserException(self.ctx, self.line,
                                  'Invalid rule (must be inside <>)')

        # if the very first name start with a -, avoid previous rules
        name = name[1:-1]
        if name[:1] == '-':
            self.avoid_previous_rules = True
            name = name[1:]

        for rule in re.split(lang_cls_split_pat, name):
            crule = None

            if not rule:
                raise ParserException(self.ctx, self.line,
                                      'Empty rule detected')

            if '@' in rule:
                # new class creation ?
                # ensure the name is correctly written
                rule, baseclasses = rule.split('@', 1)
                if not re.match(lang_key, rule):
                    raise ParserException(self.ctx, self.line,
                                          'Invalid dynamic class name')

                # save the name in the dynamic classes dict.
                self.ctx.dynamic_classes[rule] = baseclasses
                crule = ParserSelectorName(rule)

            else:
                # classical selectors.

                if rule[0] == '.':
                    crule = ParserSelectorClass(rule[1:])
                else:
                    crule = ParserSelectorName(rule)

            self.ctx.rules.append((crule, self))

    def __repr__(self):
        return '<ParserRule name=%r>' % (self.name, )


class ParserControlBranch(ParserRule):
    '''One branch of an ``if`` / ``elif`` / ``else`` chain: a full rule body
    (children, properties, handlers, canvas) plus the branch condition.
    '''

    __slots__ = ('cond_src',)

    def __init__(self, ctx, line, level, cond_src):
        super(ParserControlBranch, self).__init__(ctx, line, 'branch', level)
        #: Source of the condition; None for ``else``
        self.cond_src = cond_src


class ParserControlRule(ParserRule):
    '''A control statement (``if`` chain, ``for``, ``slot`` or ``factory``)
    at child position in a rule. The body is parsed with the ordinary rule
    machinery; :class:`Parser` finalizes it (chain merging, scope resolution,
    reference rewriting) before precompilation.
    '''

    __slots__ = ('kind', 'branches', 'selector_prop', 'iterator_prop',
                 'key_prop', 'class_prop', 'target_names', 'slot_name',
                 'locals', 'scope_key', 'scope_names', 'in_canvas',
                 'header_src')

    def __init__(self, ctx, line, kind, level):
        super(ParserControlRule, self).__init__(ctx, line, kind, level)
        #: 'if', 'for', 'slot' or 'factory' ('elif'/'else' only pre-merge)
        self.kind = kind
        #: raw condition source for if/elif headers (None for else)
        self.header_src = None
        #: if: list of :class:`ParserControlBranch`
        self.branches = []
        #: if: expression giving the index of the active branch (-1: none)
        self.selector_prop = None
        #: for: expression giving the list of loop-value tuples
        self.iterator_prop = None
        #: for: per-iteration key expression (evaluated during reconcile)
        self.key_prop = None
        #: factory: the class expression
        self.class_prop = None
        #: for: loop target names, in order
        self.target_names = []
        #: slot: the slot name ('' for the default slot)
        self.slot_name = ''
        #: for/slot: [(name, ParserRuleProperty)] scoped locals, in order
        self.locals = []
        #: for: name of the per-iteration scope in expressions
        self.scope_key = None
        #: for: every name living on the iteration scope (targets, locals,
        #: conditional locals, ids)
        self.scope_names = []
        #: True when the block generates graphics instructions
        self.in_canvas = False

    def precompile(self):
        super(ParserControlRule, self).precompile()
        for branch in self.branches:
            branch.precompile()
        for prop in (self.selector_prop, self.iterator_prop, self.key_prop,
                     self.class_prop):
            if prop is not None:
                prop.precompile()
        for _, prop in self.locals:
            prop.precompile()
        # keys rooted at a loop target are loop-local, not bindable
        if self.iterator_prop is not None and self.iterator_prop.watched_keys:
            targets = set(self.target_names)
            wk = [k for k in self.iterator_prop.watched_keys
                  if k[0] not in targets]
            self.iterator_prop.watched_keys = wk or None
        if self.key_prop is not None:
            # the key is evaluated per iteration during reconcile; it never
            # binds on its own
            self.key_prop.watched_keys = None


class _ScopeRewriter(ast.NodeTransformer):
    '''Rewrite ``name`` to ``<scope_key>.name`` for scoped names, respecting
    lambda and comprehension shadowing.
    '''

    def __init__(self, env):
        super(_ScopeRewriter, self).__init__()
        self.env = env
        self.shadow = []
        self.changed = False

    def _shadowed(self, name):
        return any(name in s for s in self.shadow)

    def visit_Name(self, node):
        if (isinstance(node.ctx, ast.Load) and node.id in self.env and
                not self._shadowed(node.id)):
            self.changed = True
            return ast.copy_location(ast.Attribute(
                value=ast.copy_location(
                    ast.Name(id=self.env[node.id], ctx=ast.Load()), node),
                attr=node.id, ctx=ast.Load()), node)
        return node

    def visit_Lambda(self, node):
        args = node.args
        # defaults evaluate in the enclosing scope
        args.defaults = [self.visit(d) for d in args.defaults]
        args.kw_defaults = [self.visit(d) if d is not None else None
                            for d in args.kw_defaults]
        names = {a.arg for a in args.args + args.posonlyargs + args.kwonlyargs}
        if args.vararg:
            names.add(args.vararg.arg)
        if args.kwarg:
            names.add(args.kwarg.arg)
        self.shadow.append(names)
        node.body = self.visit(node.body)
        self.shadow.pop()
        return node

    def _visit_comp(self, node):
        pushed = 0
        for gen in node.generators:
            gen.iter = self.visit(gen.iter)
            self.shadow.append({n.id for n in ast.walk(gen.target)
                                if isinstance(n, ast.Name)})
            pushed += 1
            gen.ifs = [self.visit(i) for i in gen.ifs]
        if isinstance(node, ast.DictComp):
            node.key = self.visit(node.key)
            node.value = self.visit(node.value)
        else:
            node.elt = self.visit(node.elt)
        del self.shadow[-pushed:]
        return node

    visit_ListComp = _visit_comp
    visit_SetComp = _visit_comp
    visit_DictComp = _visit_comp
    visit_GeneratorExp = _visit_comp


class Parser(object):
    '''Create a Parser object to parse a Kivy language file or Kivy content.
    '''

    PROP_ALLOWED = ('canvas.before', 'canvas.after')
    CLASS_RANGE = list(range(ord('A'), ord('Z') + 1))
    PROP_RANGE = (
        list(range(ord('A'), ord('Z') + 1)) +
        list(range(ord('a'), ord('z') + 1)) +
        list(range(ord('0'), ord('9') + 1)) + [ord('_')])

    __slots__ = ('rules', 'root', 'sourcecode',
                 'directives', 'filename', 'dynamic_classes', '_scope_count')

    def __init__(self, **kwargs):
        super(Parser, self).__init__()
        self.rules = []
        self.root = None
        self.sourcecode = []
        self.directives = []
        self.dynamic_classes = {}
        self._scope_count = 0
        self.filename = kwargs.get('filename', None)
        content = kwargs.get('content', None)
        if content is None:
            raise ValueError('No content passed')
        self.parse(content)

    def execute_directives(self):
        global __KV_INCLUDES__
        for ln, cmd in self.directives:
            cmd = cmd.strip()
            if __debug__:
                trace('Parser: got directive <%s>' % cmd)
            if cmd[:5] == 'kivy ':
                version = cmd[5:].strip()
                if len(version.split('.')) == 2:
                    version += '.0'
                require(version)
            elif cmd[:4] == 'set ':
                try:
                    name, value = cmd[4:].strip().split(' ', 1)
                except Exception:
                    Logger.exception('')
                    raise ParserException(self, ln, 'Invalid directive syntax')
                try:
                    value = eval(value, global_idmap)
                except Exception:
                    Logger.exception('')
                    raise ParserException(self, ln, 'Invalid value')
                global_idmap[name] = value
            elif cmd[:8] == 'include ':
                ref = cmd[8:].strip()
                force_load = False

                if ref[:6] == 'force ':
                    ref = ref[6:].strip()
                    force_load = True

                # if #:include [force] "path with quotes around"
                if ref[0] == ref[-1] and ref[0] in ('"', "'"):
                    c = ref[:3].count(ref[0])
                    ref = ref[c:-c] if c != 2 else ref

                if ref[-3:] != '.kv':
                    Logger.warning('Lang: {0} does not have a valid Kivy'
                                'Language extension (.kv)'.format(ref))
                    break
                if ref in __KV_INCLUDES__:
                    if not os.path.isfile(resource_find(ref) or ref):
                        raise ParserException(self, ln,
                                              'Invalid or unknown file: {0}'
                                              .format(ref))
                    if not force_load:
                        Logger.warning('Lang: {0} has already been included!'
                                    .format(ref))
                        continue
                    else:
                        Logger.debug('Lang: Reloading {0} '
                                     'because include was forced.'
                                     .format(ref))
                        kivy.lang.builder.Builder.unload_file(ref)
                        kivy.lang.builder.Builder.load_file(ref)
                        continue
                Logger.debug('Lang: Including file: {0}'.format(0))
                __KV_INCLUDES__.append(ref)
                kivy.lang.builder.Builder.load_file(ref)
            elif cmd[:7] == 'import ':
                package = cmd[7:].strip()
                z = package.split()
                if len(z) != 2:
                    raise ParserException(self, ln, 'Invalid import syntax')
                alias, package = z
                try:
                    if package not in sys.modules:
                        try:
                            mod = importlib.__import__(package)
                        except ImportError:
                            module_name = '.'.join(package.split('.')[:-1])
                            mod = importlib.__import__(module_name)
                        # resolve the whole thing
                        for part in package.split('.')[1:]:
                            mod = getattr(mod, part)
                    else:
                        mod = sys.modules[package]
                    global_idmap[alias] = mod
                except ImportError:
                    Logger.exception('')
                    raise ParserException(self, ln,
                                          'Unable to import package %r' %
                                          package)
            else:
                raise ParserException(self, ln, 'Unknown directive')

    def parse(self, content):
        '''Parse the contents of a Parser file and return a list
        of root objects.
        '''
        # Read and parse the lines of the file
        lines = content.splitlines()
        if not lines:
            return
        num_lines = len(lines)
        lines = list(zip(list(range(num_lines)), lines))
        self.sourcecode = lines[:]

        if __debug__:
            trace('Parser: parsing %d lines' % num_lines)

        # Strip all comments
        self.strip_comments(lines)

        # Execute directives
        self.execute_directives()

        # Get object from the first level
        objects, remaining_lines = self.parse_level(0, lines)

        # Finalize control statements (chain merging, scope resolution,
        # reference rewriting), then precompile the rules tree
        for rule in objects:
            self._finalize_controls(rule)
        for rule in objects:
            rule.precompile()

        # After parsing, there should be no remaining lines
        # or there's an error we did not catch earlier.
        if remaining_lines:
            ln, content = remaining_lines[0]
            raise ParserException(self, ln, 'Invalid data (not parsed)')

    def strip_comments(self, lines):
        '''Remove all comments from all lines in-place.
           Comments need to be on a single line and not at the end of a line.
           i.e. a comment line's first non-whitespace character must be a #.
        '''
        # extract directives
        for ln, line in lines[:]:
            stripped = line.strip()
            if stripped[:2] == '#:':
                self.directives.append((ln, stripped[2:]))
            if stripped[:1] == '#':
                lines.remove((ln, line))
            if not stripped:
                lines.remove((ln, line))

    def parse_level(self, level, lines, spaces=0):
        '''Parse the current level (level * spaces) indentation.
        '''
        indent = spaces * level if spaces > 0 else 0
        objects = []

        current_object = None
        current_property = None
        current_propobject = None
        i = 0
        while i < len(lines):
            line = lines[i]
            ln, content = line

            # Get the number of space
            tmp = content.lstrip(' \t')

            # Replace any tab with 4 spaces
            tmp = content[:len(content) - len(tmp)]
            tmp = tmp.replace('\t', '    ')

            # first indent designates the indentation
            if spaces == 0:
                spaces = len(tmp)

            count = len(tmp)

            if spaces > 0 and count % spaces != 0:
                raise ParserException(self, ln,
                                      'Invalid indentation, '
                                      'must be a multiple of '
                                      '%s spaces' % spaces)
            content = content.strip()
            rlevel = count // spaces if spaces > 0 else 0

            # Level finished
            if count < indent:
                return objects, lines[i - 1:]

            # Current level, create an object
            elif count == indent:
                if lang_control.match(content):
                    if count == 0:
                        raise ParserException(
                            self, ln, 'Control statements are not allowed at '
                            'the top level of a kv file')
                    current_object = self._parse_control_statement(
                        ln, content, rlevel)
                    current_property = None
                    objects.append(current_object)
                    i += 1
                    continue
                x = content.split(':', 1)
                if not x[0]:
                    raise ParserException(self, ln, 'Identifier missing')
                if (len(x) == 2 and len(x[1]) and
                        not x[1].lstrip().startswith('#')):
                    raise ParserException(self, ln,
                                          'Invalid data after declaration')
                name = x[0].rstrip()
                # if it's not a root rule, then we got some restriction
                # aka, a valid name, without point or everything else
                if count != 0:
                    if False in [ord(z) in Parser.PROP_RANGE for z in name]:
                        raise ParserException(self, ln, 'Invalid class name')

                current_object = ParserRule(self, ln, name, rlevel)
                current_property = None
                objects.append(current_object)

            # Next level, is it a property or an object ?
            elif count == indent + spaces:
                # a control statement is a child: recurse like a class child
                if lang_control.match(content):
                    _objects, _lines = self.parse_level(
                        level + 1, lines[i:], spaces)
                    if current_object is None:
                        raise ParserException(self, ln, 'Invalid indentation')
                    current_object.children = _objects
                    current_property = None
                    lines = _lines
                    i = 1
                    continue
                x = content.split(':', 1)
                if not x[0]:
                    raise ParserException(self, ln, 'Identifier missing')

                # It's a class, add to the current object as a children
                current_property = None
                name = x[0].rstrip()
                ignore_prev = name[0] == '-'
                if ignore_prev:
                    name = name[1:]

                if ord(name[0]) in Parser.CLASS_RANGE:
                    if ignore_prev:
                        raise ParserException(
                            self, ln, 'clear previous, `-`, not allowed here')
                    _objects, _lines = self.parse_level(
                        level + 1, lines[i:], spaces)
                    if current_object is None:
                        raise ParserException(self, ln, 'Invalid indentation')
                    current_object.children = _objects
                    lines = _lines
                    i = 0

                # It's a property
                else:
                    if name not in Parser.PROP_ALLOWED:
                        if not all(ord(z) in Parser.PROP_RANGE for z in name):
                            raise ParserException(self, ln,
                                                  'Invalid property name')
                    if len(x) == 1:
                        raise ParserException(self, ln, 'Syntax error')
                    value = x[1].strip()
                    if name == 'id':
                        if len(value) <= 0:
                            raise ParserException(self, ln, 'Empty id')
                        if value in ('self', 'root'):
                            raise ParserException(
                                self, ln,
                                'Invalid id, cannot be "self" or "root"')
                        current_object.id = value
                    elif len(value):
                        rule = ParserRuleProperty(
                            self, ln, name, value, ignore_prev)
                        if name[:3] == 'on_':
                            current_object.handlers.append(rule)
                        else:
                            ignore_prev = False
                            current_object.properties[name] = rule
                    else:
                        current_property = name
                        current_propobject = None

                    if ignore_prev:  # it wasn't consumed
                        raise ParserException(
                            self, ln, 'clear previous, `-`, not allowed here')

            # Two more levels?
            elif count == indent + 2 * spaces:
                if current_property in (
                        'canvas', 'canvas.after', 'canvas.before'):
                    _objects, _lines = self.parse_level(
                        level + 2, lines[i:], spaces)
                    rl = ParserRule(self, ln, current_property, rlevel)
                    rl.children = _objects
                    if current_property == 'canvas':
                        current_object.canvas_root = rl
                    elif current_property == 'canvas.before':
                        current_object.canvas_before = rl
                    else:
                        current_object.canvas_after = rl
                    current_property = None
                    lines = _lines
                    i = 0
                else:
                    if current_propobject is None:
                        current_propobject = ParserRuleProperty(
                            self, ln, current_property, content)
                        if not current_property:
                            raise ParserException(self, ln,
                                                  "Invalid indentation")
                        if current_property[:3] == 'on_':
                            current_object.handlers.append(current_propobject)
                        else:
                            current_object.properties[current_property] = \
                                current_propobject
                    else:
                        current_propobject.value += '\n' + content

            # Too much indentation, invalid
            else:
                raise ParserException(self, ln,
                                      'Invalid indentation (too many levels)')

            # Check the next line
            i += 1

        return objects, []

    #
    # Control statements: header parsing
    #

    def _parse_control_statement(self, ln, content, rlevel):
        kind = lang_control.match(content).group(1)
        head = self._split_control_header(ln, content)
        expr = head[len(kind):].strip()
        ctl = ParserControlRule(self, ln, kind, rlevel)

        if kind in ('if', 'elif'):
            if not expr:
                raise ParserException(
                    self, ln, '"%s" requires a condition expression' % kind)
            self._check_header_expr(ln, expr)
            ctl.header_src = expr
        elif kind == 'else':
            if expr:
                raise ParserException(self, ln, '"else" takes no expression')
            ctl.header_src = None
        elif kind == 'for':
            self._parse_for_header(ln, ctl, head)
        elif kind == 'slot':
            if expr and (not expr.isidentifier() or keyword.iskeyword(expr)):
                raise ParserException(
                    self, ln, 'invalid slot name %r' % expr)
            ctl.slot_name = expr
        else:  # factory
            if not expr:
                raise ParserException(
                    self, ln, '"factory" requires an expression giving the '
                    'widget class')
            self._check_header_expr(ln, expr)
            ctl.class_prop = ParserRuleProperty(
                self, ln, '__kv_factory_class', expr)
        return ctl

    def _split_control_header(self, ln, content):
        '''Return the header (text before the block colon), rejecting inline
        bodies. The colon is found at bracket depth 0, so colons inside
        strings, dicts, slices or parenthesized lambdas are skipped.
        '''
        depth = 0
        colon = None
        try:
            tokens = tokenize.generate_tokens(io.StringIO(content).readline)
            for tok in tokens:
                if tok.type != tokenize.OP:
                    continue
                if tok.string in '([{':
                    depth += 1
                elif tok.string in ')]}':
                    depth -= 1
                elif tok.string == ':' and depth == 0:
                    # keep the last depth-0 colon, so a bare lambda in the
                    # header keeps its own colon
                    colon = tok.start[1]
        except tokenize.TokenError:
            pass
        if colon is None:
            raise ParserException(
                self, ln, "expected ':' at the end of the control statement "
                'header')
        tail = content[colon + 1:].strip()
        if tail and not tail.startswith('#'):
            raise ParserException(
                self, ln, "unexpected content after ':' in a control "
                'statement (the body goes on the following lines)')
        return content[:colon].rstrip()

    def _check_header_expr(self, ln, expr):
        try:
            tree = ast.parse(expr, mode='eval')
        except SyntaxError as e:
            raise ParserException(
                self, ln, 'invalid expression in control statement header '
                '(%s)' % e)
        self._forbid_walrus(ln, tree)
        return tree

    def _forbid_walrus(self, ln, tree):
        if any(isinstance(n, ast.NamedExpr) for n in ast.walk(tree)):
            raise ParserException(
                self, ln, 'assignment expressions (":=") are not allowed in '
                'control statement headers')

    def _parse_for_header(self, ln, ctl, head):
        # `head` is the raw header ("for x, y in expr if cond"); parse it
        # through Python's comprehension grammar
        src = '[None %s]' % head
        try:
            tree = ast.parse(src, mode='eval')
        except SyntaxError as e:
            raise ParserException(
                self, ln, 'invalid "for" header (%s); the header takes a '
                'single "for ... in ..." clause with comprehension syntax'
                % e)
        self._forbid_walrus(ln, tree)
        generators = tree.body.generators
        if len(generators) != 1:
            raise ParserException(
                self, ln, 'a "for" header takes a '
                'single "for ... in ..." clause')
        gen = generators[0]
        if gen.is_async:
            raise ParserException(
                self, ln, '"async for" is not allowed in kv')

        names = []

        def collect(node):
            if isinstance(node, ast.Name):
                names.append(node.id)
            elif isinstance(node, ast.Starred):
                collect(node.value)
            elif isinstance(node, (ast.Tuple, ast.List)):
                for elt in node.elts:
                    collect(elt)
            else:
                raise ParserException(
                    self, ln, 'invalid loop target in "for" header')

        collect(gen.target)
        if len(set(names)) != len(names):
            raise ParserException(
                self, ln, 'duplicate loop target in "for" header')

        targets_src = ast.get_source_segment(src, gen.target)
        iter_src = ast.get_source_segment(src, gen.iter)
        filters = ''.join(
            ' if (%s)' % ast.get_source_segment(src, f) for f in gen.ifs)
        value = '[(%s,) for %s in (%s)%s]' % (
            ', '.join(names), targets_src, iter_src, filters)
        ctl.target_names = names
        ctl.iterator_prop = ParserRuleProperty(
            self, ln, '__kv_iterator', value)

    #
    # Control statements: finalization (chain merging, scope resolution,
    # reference rewriting). Runs after parse_level, before precompile.
    #

    def _new_scope_key(self):
        key = '__kvscope_%d' % self._scope_count
        self._scope_count += 1
        return key

    def _finalize_controls(self, rule):
        self._merge_control_chains(rule, False)
        # rule-level reactive-id scope: ids inside `if` branches and `slot`
        # blocks of this rule (an id under a `for` goes to the iteration
        # scope instead)
        found, statics = [], []
        self._collect_rule_ids(rule, found, statics)
        env = {}
        if found:
            names = [n for n, _ in found]
            for name in names:
                if name in statics:
                    raise ParserException(
                        self, rule.line, 'reactive id %r clashes with a '
                        'static id of the same rule' % name)
            rule.id_scope_key = self._new_scope_key()
            seen = set()
            rule.id_scope_names = [
                n for n in names if not (n in seen or seen.add(n))]
            for name, crule in found:
                crule.id = None
                crule.scope_id = (rule.id_scope_key, name)
            env = {n: rule.id_scope_key for n in rule.id_scope_names}
        self._walk_rule(rule, env, None)
        defs = []
        self._collect_slot_defs(rule, defs)
        rule.slot_defs = defs

    def _merge_control_chains(self, rule, in_canvas):
        self._merge_list(rule.children, in_canvas)
        for cv in (rule.canvas_before, rule.canvas_root, rule.canvas_after):
            if cv is not None:
                self._merge_list(cv.children, True)

    def _merge_list(self, children, in_canvas):
        out = []
        for child in children:
            if isinstance(child, ParserControlRule):
                child.in_canvas = in_canvas
                if child.kind in ('elif', 'else'):
                    prev = out[-1] if out else None
                    if (child.kind == 'else' and
                            isinstance(prev, ParserControlRule) and
                            prev.kind == 'for'):
                        raise ParserException(
                            self, child.line, '"else" after "for" is not '
                            'supported; use a paired "if not ..." block for '
                            'the empty state')
                    if (not isinstance(prev, ParserControlRule) or
                            prev.kind != 'if' or
                            prev.branches[-1].cond_src is None):
                        raise ParserException(
                            self, child.line, '"%s" must immediately follow '
                            'an "if" or "elif" block' % child.kind)
                    prev.branches.append(self._as_branch(child))
                    continue
                if child.kind == 'if':
                    child.branches = [self._as_branch(child)]
                    child.children = []
                    child.properties = OrderedDict()
                    child.handlers = []
                    child.canvas_root = None
                    child.canvas_before = None
                    child.canvas_after = None
                    child.id = None
            out.append(child)
        children[:] = out
        for child in out:
            if isinstance(child, ParserControlRule):
                for branch in child.branches:
                    self._merge_control_chains(branch, in_canvas)
                self._merge_list(child.children, in_canvas)
                for cv in (child.canvas_before, child.canvas_root,
                           child.canvas_after):
                    if cv is not None:
                        self._merge_list(cv.children, True)
                if child.kind == 'if':
                    child.selector_prop = self._build_selector(child)
            else:
                self._merge_control_chains(child, in_canvas)

    def _as_branch(self, ctl):
        branch = ParserControlBranch(
            self, ctl.line, ctl.level, ctl.header_src)
        branch.children = ctl.children
        branch.properties = ctl.properties
        branch.handlers = ctl.handlers
        branch.canvas_root = ctl.canvas_root
        branch.canvas_before = ctl.canvas_before
        branch.canvas_after = ctl.canvas_after
        branch.id = ctl.id
        return branch

    def _build_selector(self, ctl):
        conds = []
        else_index = -1
        for i, branch in enumerate(ctl.branches):
            if branch.cond_src is None:
                else_index = i
            else:
                conds.append('%d if (%s)' % (i, branch.cond_src))
        value = ' else '.join(conds) + ' else %d' % else_index
        return ParserRuleProperty(self, ctl.line, '__kv_selector', value)

    def _clean_id(self, value, crule):
        # same normalization as the builder: first word, comments dropped
        name = value.split('#', 1)[0].strip()
        if name == 'app':
            # a scoped id is rewritten wherever it is referenced, so unlike
            # a static id it would silently hijack the `app` proxy
            raise ParserException(
                self, crule.line,
                'Invalid id, cannot be "self", "root" or "app"')
        return name

    def _collect_rule_ids(self, rule, found, statics):
        '''Collect ids belonging to this rule's reactive-id scope: ids on
        widgets inside `if` branches and `slot` blocks, at any depth, stopping
        at `for` blocks (iteration scope) and rejecting ids in `factory`
        bodies. Also collects the rule's static ids for clash detection.
        '''
        for child in rule.children:
            if isinstance(child, ParserControlRule):
                if child.kind == 'if':
                    for branch in child.branches:
                        self._collect_scoped_ids(branch, found)
                elif child.kind == 'slot':
                    self._collect_scoped_ids(child, found)
                elif child.kind == 'factory':
                    self._forbid_ids(child)
                # 'for': its ids live on the iteration scope
            else:
                if child.id:
                    statics.append(self._clean_id(child.id, child))
                self._collect_rule_ids(child, found, statics)

    def _collect_scoped_ids(self, rule, found):
        for child in rule.children:
            if isinstance(child, ParserControlRule):
                if child.kind == 'if':
                    for branch in child.branches:
                        self._collect_scoped_ids(branch, found)
                elif child.kind == 'slot':
                    self._collect_scoped_ids(child, found)
                elif child.kind == 'factory':
                    self._forbid_ids(child)
            else:
                if child.id:
                    found.append((self._clean_id(child.id, child), child))
                self._collect_scoped_ids(child, found)

    def _forbid_ids(self, rule):
        for child in rule.children:
            if not isinstance(child, ParserControlRule) and child.id:
                raise ParserException(
                    self, child.line, '"id" is not allowed on widgets inside '
                    'a "factory" block')
            self._forbid_ids(child)

    def _collect_slot_defs(self, rule, defs):
        # slot names declared by this rule for its widget: direct blocks,
        # inside `if` branches and nested in slot bodies (forwarding) -- but
        # not across a child-widget boundary (those belong to the child)
        for child in rule.children:
            if isinstance(child, ParserControlRule):
                if child.kind == 'slot':
                    defs.append(child.slot_name)
                    self._collect_slot_defs(child, defs)
                elif child.kind == 'if':
                    for branch in child.branches:
                        self._collect_slot_defs(branch, defs)

    #
    # Control statements: validation, scopes and reference rewriting
    #

    def _walk_rule(self, rule, env, for_ctl):
        '''Validate and rewrite one rule body (a widget rule, an if branch, a
        factory body). `env` maps scoped names to their scope key; `for_ctl`
        is the enclosing `for` when this body is (part of) its direct block.
        '''
        for prop in rule.properties.values():
            self._rewrite_prop(prop, env)
        for prop in rule.handlers:
            self._rewrite_prop(prop, env)
        for cv in (rule.canvas_before, rule.canvas_root, rule.canvas_after):
            if cv is not None:
                self._walk_canvas(cv, env)
        rule.has_controls = any(
            isinstance(c, ParserControlRule) for c in rule.children)
        child_env = env
        if env and ('self' in env or 'args' in env):
            # a widget's own `self` (and a handler's `args`) win inside it
            child_env = {k: v for k, v in env.items()
                         if k not in ('self', 'args')}
        for child in rule.children:
            if isinstance(child, ParserControlRule):
                self._walk_control(child, env, for_ctl)
            else:
                self._walk_rule(child, child_env, None)

    def _walk_control(self, ctl, env, for_ctl):
        kind = ctl.kind
        if ctl.id:
            raise ParserException(
                self, ctl.line, '"id" is not allowed directly on a control '
                'statement')
        if kind == 'if':
            self._rewrite_prop(ctl.selector_prop, env)
            for branch in ctl.branches:
                self._walk_branch(branch, env, for_ctl)
        elif kind == 'for':
            self._walk_for(ctl, env)
        elif kind == 'slot':
            if for_ctl is not None:
                raise ParserException(
                    self, ctl.line, 'a slot cannot be defined inside a '
                    '"for" block')
            if ctl.handlers:
                raise ParserException(
                    self, ctl.handlers[0].line, 'event handlers are not '
                    'allowed in a "slot" block')
            if (ctl.canvas_root or ctl.canvas_before or ctl.canvas_after):
                raise ParserException(
                    self, ctl.line, 'canvas is not allowed in a "slot" '
                    'block')
            for name, prop in ctl.properties.items():
                if name == 'key':
                    raise ParserException(
                        self, prop.line, '"key:" is only allowed inside a '
                        '"for" block')
                self._rewrite_prop(prop, env)
                ctl.locals.append((name, prop))
            ctl.properties = OrderedDict()
            for child in ctl.children:
                if isinstance(child, ParserControlRule):
                    self._walk_control(child, env, None)
                else:
                    self._walk_rule(child, env, None)
        else:  # factory
            self._rewrite_prop(ctl.class_prop, env)
            if 'key' in ctl.properties:
                raise ParserException(
                    self, ctl.properties['key'].line, '"key:" is only '
                    'allowed inside a "for" block')
            # the body is an ordinary rule applied to the built instance
            self._walk_rule(ctl, env, None)

    def _walk_branch(self, branch, env, for_ctl):
        if branch.id:
            raise ParserException(
                self, branch.line, '"id" is not allowed directly on a '
                'control statement')
        if 'key' in branch.properties:
            raise ParserException(
                self, branch.properties['key'].line, '"key:" is only allowed '
                'inside a "for" block')
        if not (branch.children or branch.properties or branch.handlers or
                branch.canvas_root or branch.canvas_before or
                branch.canvas_after):
            raise ParserException(
                self, branch.line, 'an "if" block requires at least one '
                'child widget, property, handler or canvas')
        if for_ctl is not None:
            # nesting context semantics: the branch follows for-body rules
            if branch.handlers:
                raise ParserException(
                    self, branch.handlers[0].line, 'event handlers are not '
                    'allowed in a "for" block')
            if (branch.canvas_root or branch.canvas_before or
                    branch.canvas_after):
                raise ParserException(
                    self, branch.line, 'canvas is not allowed in a "for" '
                    'block')
        self._walk_rule(branch, env, for_ctl)

    def _walk_for(self, ctl, env):
        if ctl.handlers:
            raise ParserException(
                self, ctl.handlers[0].line, 'event handlers are not allowed '
                'in a "for" block (declare them on a child widget instead)')
        if ctl.canvas_root or ctl.canvas_before or ctl.canvas_after:
            raise ParserException(
                self, ctl.line, 'canvas is not allowed in a "for" block '
                '(declare it on a child widget instead)')
        if not ctl.children:
            raise ParserException(
                self, ctl.line, 'a "for" block requires at least one child '
                'widget')
        self._rewrite_prop(ctl.iterator_prop, env)

        # the iteration scope: loop targets, locals, conditional locals
        # (from nested ifs) and ids
        ctl.key_prop = ctl.properties.pop('key', None)
        ctl.locals = list(ctl.properties.items())
        ctl.properties = OrderedDict()
        cond_locals = []
        self._collect_cond_locals(ctl.children, cond_locals)
        ids = []
        self._collect_for_ids(ctl.children, ids)
        names = list(ctl.target_names)
        for name, _ in ctl.locals + cond_locals:
            if name not in names:
                names.append(name)
        id_names = []
        for name, crule in ids:
            if name in names:
                raise ParserException(
                    self, crule.line, 'id %r clashes with a loop target or '
                    'local of the same "for" block' % name)
            if name not in id_names:
                id_names.append(name)
        ctl.scope_key = key = self._new_scope_key()
        ctl.scope_names = names + id_names
        ctl.id_scope_names = id_names
        for name, crule in ids:
            crule.id = None
            crule.scope_id = (key, name)

        inner_env = dict(env)
        for name in ctl.scope_names:
            inner_env[name] = key
        for name, prop in ctl.locals:
            prop.force_code = True
            self._rewrite_prop(prop, inner_env)
        for child in ctl.children:
            if isinstance(child, ParserControlRule):
                self._walk_control(child, inner_env, ctl)
            else:
                stripped = {k: v for k, v in inner_env.items()
                            if k not in ('self', 'args')}
                self._walk_rule(child, stripped, None)

    def _collect_cond_locals(self, children, out):
        for child in children:
            if isinstance(child, ParserControlRule) and child.kind == 'if':
                for branch in child.branches:
                    for name, prop in branch.properties.items():
                        if name != 'key':
                            prop.force_code = True
                            out.append((name, prop))
                    self._collect_cond_locals(branch.children, out)

    def _collect_for_ids(self, children, out):
        for child in children:
            if isinstance(child, ParserControlRule):
                if child.kind == 'if':
                    for branch in child.branches:
                        self._collect_for_ids(branch.children, out)
                elif child.kind == 'factory':
                    self._forbid_ids(child)
                # nested 'for': its own scope; 'slot': forbidden in for
            else:
                if child.id:
                    out.append((self._clean_id(child.id, child), child))
                self._collect_for_ids(child.children, out)

    def _walk_canvas(self, canvas_rule, env):
        for child in canvas_rule.children:
            if isinstance(child, ParserControlRule):
                self._walk_canvas_control(child, env)
            else:
                for prop in child.properties.values():
                    self._rewrite_prop(prop, env)
                if any(isinstance(c, ParserControlRule)
                       for c in child.children):
                    raise ParserException(
                        self, child.line, 'a control statement is not '
                        'allowed under a graphics instruction')

    def _walk_canvas_control(self, ctl, env):
        kind = ctl.kind
        if kind in ('slot', 'factory'):
            raise ParserException(
                self, ctl.line, '"%s" cannot be declared inside canvas'
                % kind)
        if kind == 'if':
            self._rewrite_prop(ctl.selector_prop, env)
            for branch in ctl.branches:
                if branch.properties or branch.handlers:
                    prop = (list(branch.properties.values()) +
                            branch.handlers)[0]
                    raise ParserException(
                        self, prop.line, 'only graphics instructions are '
                        'allowed inside canvas control statements')
                self._walk_canvas(branch, env)
            return
        # for
        ctl.key_prop = ctl.properties.pop('key', None)
        if ctl.properties or ctl.handlers:
            prop = (list(ctl.properties.values()) + ctl.handlers)[0]
            raise ParserException(
                self, prop.line, 'only graphics instructions are allowed '
                'inside canvas control statements')
        if not ctl.children:
            raise ParserException(
                self, ctl.line, 'a "for" block requires at least one '
                'graphics instruction')
        self._rewrite_prop(ctl.iterator_prop, env)
        # loop targets are injected as plain names at build time
        inner_env = {k: v for k, v in env.items()
                     if k not in ctl.target_names}
        self._walk_canvas(ctl, inner_env)

    def _rewrite_prop(self, prop, env):
        if not env or prop is None:
            return
        mode = 'exec' if prop.name[:3] == 'on_' else 'eval'
        try:
            tree = ast.parse(prop.value, mode=mode)
        except SyntaxError:
            # let precompile report it with the proper kv context
            return
        rewriter = _ScopeRewriter(env)
        tree = rewriter.visit(tree)
        if rewriter.changed:
            ast.fix_missing_locations(tree)
            prop.value = ast.unparse(tree)


class ParserSelector(object):

    def __init__(self, key):
        self.key = key.lower()

    def match(self, widget):
        raise NotImplementedError

    def __repr__(self):
        return '<%s key=%s>' % (self.__class__.__name__, self.key)


class ParserSelectorClass(ParserSelector):

    def match(self, widget):
        return self.key in widget.cls


class ParserSelectorName(ParserSelector):

    parents = {}

    def get_bases(self, cls):
        for base in cls.__bases__:
            if base.__name__ == 'object':
                break
            yield base
            if base.__name__ == 'Widget':
                break
            for cbase in self.get_bases(base):
                yield cbase

    def match(self, widget):
        parents = ParserSelectorName.parents
        cls = widget.__class__
        if cls not in parents:
            classes = [x.__name__.lower() for x in
                       [cls] + list(self.get_bases(cls))]
            parents[cls] = classes
        return self.key in parents[cls]

    def match_rule_name(self, rule_name):
        return self.key == rule_name.lower()
