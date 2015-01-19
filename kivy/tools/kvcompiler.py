"""
Kivy language compiler
======================

.. author:: Mathieu Virbel <mat@kivy.org>

This compiler require jinja2. The implementation is very messy but effective,
as the current benchmark goes from 31s to 19s.

What's supported:

- Rules
- Dynamic classes
- Root object
- Properties creation on the fly on the root element
- Canvas (root, before, after)
- Id (and ids)
- Directive "kivy"
- Handlers (on_)

What's not supported but passthrough:

- Templates
- Directives (all the others)

What's not supported:

- Properties creation on the fly on children
- Rebind
- Accessing of a object more than one . (self.parent.parent.myobj)
- Unloading
- Caching canvas updates during a clock cycle


"""

__all__ = []

import sys
import codecs
import datetime
from types import CodeType
from jinja2 import Template
import jinja2
from collections import OrderedDict
from kivy.lang import Parser

env = jinja2.Environment()

c_uid = 0
g_uid = 0
h_uid = 0
r_uid = 0


def squash_callbacks(link_properties, objs):
    '''Takes the property rules and the unique list of bound objects and
    returns a 3 deep list the bound rules.

    - First levels splits into objs.
    - Second level, for each obj split, further splits it into bound rules
    grouped by parents.

    The returned lists also filters out any empty sublists.

    The shape returned is:
    [
        [obj1,
            [
                [parent1,
                    [(who, parent, hname, symbols, bind),
                    (who, parent, hname, symbols, bind),
                    ...]
                ]
                [parent2, [...]]
                ...
            ]
        ],
        [obj2, [...]]
        ...
    ]
    '''
    ret = [[obj, [prop[:-1] + (bind, ) for prop in link_properties
                  for bind in prop[-1] if bind[:-1] == obj]] for obj in objs]
    for i, (obj, obj_binds) in enumerate(ret):
        parents = list(set([bind[1] for bind in obj_binds]))
        binds = [[parent, [bind for bind in obj_binds if bind[1] == parent]]
                 for parent in parents]
        ret[i] = obj, [(parent, parent_binds)
                       for (parent, parent_binds) in binds if parent_binds]
    ret = [(obj, obj_binds) for (obj, obj_binds) in ret if obj_binds]
    return sorted(ret, key=lambda x: '.'.join(x[0]))


def expand_symbols(symbols, who, parent, ref=True):
    '''Replaces the symbols with the correct names for properties.
    If ref, it also appends _ref to the names of those who are not `parent`.
    '''
    symbols = symbols[:]
    for i, sym in enumerate(symbols):
        if sym == 'self':
            symbols[i] = parent
        elif sym == 'gself':
            symbols[i] = who
        elif sym == 'root':
            symbols[i] = 'self'
    if ref:
        for i, sym in enumerate(symbols):
            if sym != parent:
                symbols[i] = '{}_ref'.format(sym)
    return symbols


def expand_symbols_handler(symbols, who, ref=True):
    '''Replaces the symbols with the correct names for handlers.
    If ref, it also appends _ref to the names of those who are not `who`.
    '''
    symbols = symbols[:]
    for i, sym in enumerate(symbols):
        if sym == 'self':
            symbols[i] = who
        elif sym == 'root':
            symbols[i] = 'self'
    if ref:
        for i, sym in enumerate(symbols):
            if sym != who:
                symbols[i] = '{}_ref'.format(sym)
    return symbols


def unique_symbols(props, handlers, ids):
    '''Returns the unique list of symbols accumulated from `props`, `handlers`,
    and `ids`.
    '''
    symbols = []
    for who, parent, _, _symbols, _ in props:
        symbols.extend(expand_symbols(_symbols, who, parent, ref=False))
    for who, _, _, _, _symbols in handlers:
        symbols.extend(expand_symbols_handler(_symbols, who, ref=False))
    symbols.extend(ids)
    return list(set(symbols))


def parent_handlers(handlers):
    '''Returns the names of the objects that have a on_parent rule so that we
    can execute them manually because add_widget happened before we bound the
    on_parent rule.
    Return the list in correct order because when executing, we always execute
    in reverse order.
    '''
    whos = [who for who, name, _, _, _ in handlers if name == 'on_parent']
    if len(whos) <= 1:
        return whos

    dedup = []
    for who in whos:
        if who not in dedup:
            dedup.append(who)
    return dedup


def cmp_idx(elems, idx, val):
    '''Returns the elems filtered so that the value ate index `idx` of each
    element is equal to `val`.
    '''
    return [x for x in elems if x[idx] == val]

env.filters['squash_callbacks'] = squash_callbacks
env.filters['expand_symbols'] = expand_symbols
env.filters['expand_symbols_handler'] = expand_symbols_handler
env.filters['unique_symbols'] = unique_symbols
env.filters['parent_handlers'] = parent_handlers
env.filters['cmp_idx'] = cmp_idx

header = """
import sys
from kivy.metrics import dp, sp
from kivy.factory import Factory
from functools import partial
from kivy.lang import (
    Builder, ParserSelectorId, ParserSelectorName, ParserSelectorClass,
    _handlers)
from kivy.event import EventDispatcher, Observable
from kivy import require
_mc = {}
_otype = (EventDispatcher, Observable)
_includes = []

def _execute_directive(cmd):
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
"""

tpl_directives = Template("""
# directives
{%- for directive in directives %}
{%- set d = directive[1] %}
{%- if d[:5] == "kivy " %}
{%- set d = d[5:]|trim %}
require("{{ d }}")
{%- else %}
_execute_directive('{{ directive[1] }}')
{%- endif %}
{%- endfor %}
""")

tpl_child = Template("""
    {{ name }} = Factory.{{ clsname }}(__no_builder=True)
    {{ parent }}.add_widget({{ name }})
    Builder.apply({{ name }})
    {%- for prop, value in literal_properties %}
    {{ name }}.{{ prop }} = {{ value }}
    {%- endfor %}
""")


tpl_canvas = Template("""
    {{ name }} = Factory.{{ clsname }}()
    {{ parent }}.{{ canvas }}.add({{ name }})
    {%- for prop, value in literal_properties %}
    {{ name }}.{{ prop }} = {{ value }}
    {%- endfor %}
""")


tpl_handler = Template("""
def {{ name }}(
    {%- for symbol in symbols -%}
    {%- if loop.index > 1 %}, {% endif -%}
    {{- symbol -}}
    {%- endfor -%}, *args):
    {{ wself }}.{{ prop }} = {{ value }}
""")


tpl_handler_on = Template("""
def on_{{ name }}(
    {%- for symbol in symbols -%}
    {%- if loop.index > 1 %}, {% endif -%}
    {{- symbol -}}
    {%- endfor -%}, *args):
{{ code }}
""")


tpl_dynamic_classes = Template("""
# register dynamic classes
{%- for dname, dbases in dynamic_classes %}
Factory.register("{{ dname }}", baseclasses="{{ dbases }}")
{%- endfor %}

""")

tpl_root = Template("""
# support for root object
{% if code %}
{{ code }}
{% endif -%}
def get_root():
    {%- if root %}
    widget = Factory.get("{{ root.name }}")()
    _r{{ uid }}(widget)
    return widget
    {% else %}
    pass
    {% endif %}
""")

tpl_template = Template("""
Builder.load_string('''
{{ code }}
''')
""")

tpl_apply = env.from_string("""
{%- for handler in properties %}
{{ handler }}
{% endfor %}

{%- for who, name, hname, hcode, symbols in handlers %}
{{ hcode }}
{% endfor %}

_mc[{{ name }}] = []
def _mc{{ name }}(self):
    if self.__class__ in _mc[{{ name }}]:
        return
    {% for key, value in missing -%}
    if not hasattr(self, "{{ key }}"):
        self.create_property("{{ key }}", {{ value }})
    {% endfor %}
    _mc[{{ name }}].append(self.__class__)

def _r{{ name }}(self):
    # {{ rule.ctx.filename }}:
    {{- rule.line }} {{ rule.ctx.sourcecode[rule.line][1] }}
    root = self
    {%- if children %}
    # create tree
    {%- for child in children %}
    {{- child }}
    {% endfor -%}
    {% endif %}

    # ensure all properties exists
    _mc{{ name }}(self)

    # id refs
    {%- for sym in link_properties|unique_symbols(handlers, ids) %}
    {{ sym }}_ref = {{ sym }}.proxy_ref
    {%- endfor %}

    {%- if literal_properties %}
    # set default properties
    {%- for prop, value in literal_properties %}
    self.{{ prop }} = {{ value }}
    {%- endfor %}
    {% endif %}

    {%- if link_properties %}
    # link properties
    {%- for obj, obj_binds in link_properties|squash_callbacks(objs) %}
    {%- set obj = obj|join('.') %}
    if isinstance({{ obj }}, _otype):
        {%- for parent, parent_binds in obj_binds %}
        {%- if parent_binds|length == 1 %}
        {%- for who, _, hname, symbols, bind in parent_binds %}
        _handlers[{{ parent }}.uid].append([({{ obj }}.proxy_ref, "
        {{- bind[-1] }}", {{ hname }}, {{ obj }}.fast_bind("
        {{- bind[-1] }}", {{ hname }}
        {%- for sym in symbols|expand_symbols(who, parent) %}, {{ sym }}
        {%- endfor -%}))])
        {%- endfor %}
        {%- else  %}
        fast_bind = {{ obj }}.fast_bind
        proxy_ref = {{ obj }}.proxy_ref
        bound = []
        append = bound.append
        {%- for who, _, hname, symbols, bind in parent_binds %}
        append((proxy_ref, "{{ bind[-1] }}", {{ hname }}, fast_bind("
        {{- bind[-1] }}", {{ hname }}
        {%- for sym in symbols|expand_symbols(who, parent) %}, {{ sym }}
        {%- endfor -%})))
        {%- endfor %}
        _handlers[{{ parent }}.uid].append(bound)
        {%- endif -%}
        {%- endfor %}
    {%- endfor %}
    {%- endif %}

    {%- for who, parent, hname, symbols, binds in link_properties|reverse %}
    {{ hname }}(
    {%- for sym in symbols|expand_symbols(who, parent, ref=False) %}
    {%- if loop.index > 1 %}, {% endif -%}{{ sym }}
    {%- endfor -%})
    {%- endfor %}

    {% if handlers %}
    # link handlers
    {%- for who, name, hname, hcode, symbols in handlers %}
    if {{ who }}.is_event_type("{{ name }}"):
        {{ who }}.fast_bind("{{ name }}", on_{{ hname }}
        {%- for sym in symbols|expand_symbols_handler(who) %}, {{ sym }}
        {%- endfor %})
    else:
        {{ who }}.fast_bind("{{ name[3:] }}", on_{{ hname }}
        {%- for sym in symbols|expand_symbols_handler(who) %}, {{ sym }}
        {%- endfor %})
    {%- endfor %}
    {%- for who in handlers|parent_handlers|reverse %}
    Factory.Widget.parent.dispatch({{ who }})
    {%- endfor %}
    {%- endif %}

_r{{ name }}.avoid_previous_rules = {{ avoid_previous_rules }}
""")


def generate_property(name, prop, rule, mode, symbols):
    global h_uid
    h_uid += 1
    handler_name = "h{}".format(h_uid)
    return handler_name, tpl_handler.render(
        name=handler_name,
        prop=prop,
        value=rule.value,
        wself="self" if mode == "widget" else "gself",
        symbols=symbols)


def generate_py_handler_on(name, rule, symbols):
    global h_uid
    h_uid += 1
    code = "\n".join(["    {}".format(line) for line in
                      rule.value.splitlines()])
    handler_name = "h{}".format(h_uid)
    return handler_name, tpl_handler_on.render(
        name=handler_name,
        code=code,
        symbols=symbols)


def generate_py_canvas(rule, parent, ids, canvas="canvas"):
    global g_uid
    g_uid += 1
    who = "g{}".format(g_uid)

    ctx = generate_py_rules(who, rule, who=who, mode="canvas", parent=parent,
            ids=ids)
    ctx["clsname"] = rule.name
    ctx["parent"] = parent
    ctx["canvas"] = canvas
    return ctx, tpl_canvas.render(**ctx)


def generate_py_child(rule, parent, ids):
    global c_uid
    if rule.id:
        who = rule.id
    else:
        c_uid += 1
        who = "c{}".format(c_uid)

    ctx = generate_py_rules(who, rule, who=who, ids=ids)
    ctx["clsname"] = rule.name
    ctx["parent"] = parent
    return ctx, tpl_child.render(**ctx)


def get_ids(rule, ids):
    if rule.id:
        ids.append(rule.id)
    for child in rule.children:
        get_ids(child, ids)


def generate_py_rules(key, rule, who="self", mode="widget", parent=None,
        ids=None):
    ctx = {
        "rule": rule,
        "name": key,
        "literal_properties": [],
        "canvas": [],
        "children": [],
        "properties": [],
        "link_properties": [],
        "handlers": [],
        "avoid_previous_rules": rule.avoid_previous_rules,
        "missing": [],
        "objs": []
    }

    # list all the id first
    if not ids:
        ids = []
        get_ids(rule, ids)
        ctx["ids"] = ids

    # set default properties if possible
    for name, prop in rule.properties.items():
        value = prop.co_value
        if type(value) is CodeType:
            value = None
        else:
            value = prop.value
        ctx["missing"].append((name, value))

    # set default properties if possible
    for name, prop in rule.properties.items():
        if type(prop.co_value) is CodeType and prop.watched_keys:
            continue
        ctx["literal_properties"].append((name, prop.value))

    # create canvas
    if rule.canvas_root:
        for child in rule.canvas_root.children:
            child_ctx, code = generate_py_canvas(child, who, ids)
            ctx["children"].append(code)
            ctx["children"].extend(child_ctx["children"])
            ctx["properties"] += child_ctx["properties"]
            ctx["link_properties"] += child_ctx["link_properties"]
            ctx["objs"] += child_ctx["objs"]
    if rule.canvas_before:
        for child in rule.canvas_before.children:
            child_ctx, code = generate_py_canvas(
                child, who, ids, canvas="canvas.before")
            ctx["children"].append(code)
            ctx["children"].extend(child_ctx["children"])
            ctx["properties"] += child_ctx["properties"]
            ctx["link_properties"] += child_ctx["link_properties"]
            ctx["objs"] += child_ctx["objs"]
    if rule.canvas_after:
        for child in rule.canvas_after.children:
            child_ctx, code = generate_py_canvas(
                child, who, ids, canvas="canvas.after")
            ctx["children"].append(code)
            ctx["children"].extend(child_ctx["children"])
            ctx["properties"] += child_ctx["properties"]
            ctx["link_properties"] += child_ctx["link_properties"]
            ctx["objs"] += child_ctx["objs"]

    # create children
    for child in rule.children:
        child_ctx, code = generate_py_child(child, who, ids)
        ctx["children"].append(code)
        ctx["children"].extend(child_ctx["children"])
        ctx["properties"] += child_ctx["properties"]
        ctx["link_properties"] += child_ctx["link_properties"]
        ctx["objs"] += child_ctx["objs"]
        ctx["handlers"] += child_ctx["handlers"]

    # properties
    objs = []
    symbols = ids + ["self", "root", "gself"]
    for name, prop in rule.properties.items():
        if not prop.watched_keys:
            continue
        hname, hcode = generate_property(key, name, prop, mode, symbols)
        ctx["properties"].append(hcode)
        binds = []
        for keys in prop.watched_keys:
            obj = list(keys[:-1])
            if obj[0] == "self":
                obj[0] = who if mode == "widget" else parent
            elif obj[0] == "root":
                obj[0] = "self"
            obj = tuple(obj)
            objs.append(obj)
            binds.append(obj + (keys[-1], ))
        ctx["link_properties"].append((
            who,
            who if mode == "widget" else parent,
            hname,
            symbols,
            binds))

    # handlers
    for rhdl in rule.handlers:
        symbols = ids + ["self", "root"]
        hname, hcode = generate_py_handler_on(rhdl.name, rhdl, symbols=symbols)
        objs.append(who)
        ctx["handlers"].append((who, rhdl.name, hname, hcode, symbols))

    ctx["objs"] = list(set(objs + ctx["objs"]))
    return ctx


def generate_dynamic_classes(dynamic_classes):
    return tpl_dynamic_classes.render(dynamic_classes=dynamic_classes.items())


def generate_directives(directives):
    return tpl_directives.render(directives=directives)


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


def generate_template(name, template):
    # template compilation is not supported at all, so rely on the current
    # interpreted language.
    minline = template.line
    maxline = _find_maxline(minline, template)
    code = "\n".join(
        [c[1] for c in template.ctx.sourcecode[minline:maxline + 1]])
    return tpl_template.render(code=code)


def generate_py_apply(ctx):
    return tpl_apply.render(**ctx)


def generate_root(root):
    global r_uid
    if root:
        r_uid += 1
        ctx = generate_py_rules(r_uid, root)
        code = generate_py_apply(ctx)
    else:
        code = None
    return tpl_root.render(root=root, code=code, uid=r_uid)


def generate_py(parser):
    global r_uid
    lines = [header]
    lines.append(generate_directives(parser.directives))

    selectors_map = OrderedDict()
    for key, rule in parser.rules:
        if rule in selectors_map:
            selectors_map[rule].append(key)
            continue

        r_uid += 1
        rule_name = "{}".format(r_uid)
        selectors_map[rule] = [rule_name, key]
        ctx = generate_py_rules(rule_name, rule)
        lines.append(generate_py_apply(ctx))

    lines.append(generate_dynamic_classes(parser.dynamic_classes))

    lines.append("# registration")
    lines.append("badd = Builder.rules.append")
    for item in selectors_map.values():
        rule_name = item[0]
        selectors = item[1:]
        for selector in selectors:
            lines.append("badd(({}(\"{}\"), _r{}))".format(
                selector.__class__.__name__, selector.key,
                rule_name))

    lines.append(generate_root(parser.root))

    for name, cls, template in parser.templates:
        lines.append(generate_template(name, template))

    lines.insert(0, "# Generated from {} at {}".format(
        parser.filename, datetime.datetime.now()))

    lines = [l + "\n" for l in lines if l]
    return lines


if __name__ == "__main__":
    fn = r'G:\Python\dev2\kivy\kivy\data\style.kv'
    with codecs.open(fn) as fd:
        content = fd.read()
    parser = Parser(content=content, filename=fn)
    pyfn = fn.replace(".kv", "_kv.py")
    lines = generate_py(parser)
    with codecs.open(pyfn, "w") as fd:
        fd.writelines(lines)
