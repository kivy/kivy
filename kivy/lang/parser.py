'''
Parser
======

Class used for the parsing of .kv files into rules.
'''
import os

import re
import sys
import traceback
import ast
import importlib
from re import sub, findall
from types import CodeType
from functools import partial
from collections import OrderedDict, defaultdict

import kivy.lang.builder  # imported as absolute to avoid circular import
from kivy.logger import Logger
from kivy.cache import Cache
from kivy import require
from kivy.resources import resource_find
from kivy.utils import rgba
import kivy.metrics as Metrics

__all__ = ('Parser', 'ParserException')


trace = Logger.trace
global_idmap = {}

# register cache for creating new classtype (template)
Cache.register('kv.lang')

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
                 'watched_keys', 'mode', 'count', 'ignore_prev')

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

    def precompile(self):
        name = self.name
        value = self.value

        # first, remove all the string from the value
        tmp = sub(lang_str, '', self.value)

        # detecting how to handle the value according to the key name
        mode = self.mode
        if self.mode is None:
            self.mode = mode = 'exec' if name[:3] == 'on_' else 'eval'
        if mode == 'eval':
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
                if isinstance(n, ast.Str):
                    # NOTE: required for python3.6
                    yield from cls.get_names_from_expression(n.s)
                else:
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
            if isinstance(node.value, ast.Name):
                yield f'{node.value.id}.{node.attr}'

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
                 'handlers', 'level', 'cache_marked', 'avoid_previous_rules')

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
            self._build_template()
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

    def _build_template(self):
        name = self.name
        exception = ParserException(
            self.ctx, self.line,
            'Deprecated Kivy lang template syntax used "{}". Templates will '
            'be removed in a future version'.format(name))
        if name not in ('[FileListEntry@FloatLayout+TreeViewNode]',
                        '[FileIconEntry@Widget]',
                        '[AccordionItemTitle@Label]'):
            Logger.warning(exception)

        if __debug__:
            trace('Builder: build template for %s' % name)
        if name[0] != '[' or name[-1] != ']':
            raise ParserException(self.ctx, self.line,
                                  'Invalid template (must be inside [])')
        item_content = name[1:-1]
        if '@' not in item_content:
            raise ParserException(self.ctx, self.line,
                                  'Invalid template name (missing @)')
        template_name, template_root_cls = item_content.split('@')
        self.ctx.templates.append((template_name, template_root_cls, self))

    def __repr__(self):
        return '<ParserRule name=%r>' % (self.name, )


class Parser(object):
    '''Create a Parser object to parse a Kivy language file or Kivy content.
    '''

    PROP_ALLOWED = ('canvas.before', 'canvas.after')
    CLASS_RANGE = list(range(ord('A'), ord('Z') + 1))
    PROP_RANGE = (
        list(range(ord('A'), ord('Z') + 1)) +
        list(range(ord('a'), ord('z') + 1)) +
        list(range(ord('0'), ord('9') + 1)) + [ord('_')])

    __slots__ = ('rules', 'templates', 'root', 'sourcecode',
                 'directives', 'filename', 'dynamic_classes')

    def __init__(self, **kwargs):
        super(Parser, self).__init__()
        self.rules = []
        self.templates = []
        self.root = None
        self.sourcecode = []
        self.directives = []
        self.dynamic_classes = {}
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
                except:
                    Logger.exception('')
                    raise ParserException(self, ln, 'Invalid directive syntax')
                try:
                    value = eval(value, global_idmap)
                except:
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

        # Precompile rules tree
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
