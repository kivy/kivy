'''
Builder
======

Class used for the registering and application of rules for specific widgets.
'''
import codecs
import sys
import types
from os import environ
from os.path import join
from copy import copy
from types import CodeType
from functools import partial

from kivy.factory import Factory
from kivy.lang.parser import Parser, ParserException, _handlers, global_idmap,\
    ParserRuleProperty
from kivy.logger import Logger
from kivy.utils import QueryDict
from kivy.cache import Cache
from kivy import kivy_data_dir
from kivy.compat import PY2, iteritems, iterkeys
from kivy.context import register_context
from kivy.resources import resource_find
from kivy._event import Observable, EventDispatcher

__all__ = ('Observable', 'Builder', 'BuilderBase', 'BuilderException')


trace = Logger.trace

# class types to check with isinstance
if PY2:
    _cls_type = (type, types.ClassType)
else:
    _cls_type = (type, )

# late import
Instruction = None

# delayed calls are canvas expression triggered during an loop. It is one
# directional linked list of args to call call_fn with. Each element is a list
# whos last element points to the next list of args to execute when
# Builder.sync is called.
_delayed_start = None


class BuilderException(ParserException):
    '''Exception raised when the Builder failed to apply a rule on a widget.
    '''
    pass


def get_proxy(widget):
    try:
        return widget.proxy_ref
    except AttributeError:
        return widget


def custom_callback(__kvlang__, idmap, *largs, **kwargs):
    idmap['args'] = largs
    exec(__kvlang__.co_value, idmap)


def call_fn(args, instance, v):
    element, key, value, rule, idmap = args
    if __debug__:
        trace('Lang: call_fn %s, key=%s, value=%r, %r' % (
            element, key, value, rule.value))
    rule.count += 1
    e_value = eval(value, idmap)
    if __debug__:
        trace('Lang: call_fn => value=%r' % (e_value, ))
    setattr(element, key, e_value)


def delayed_call_fn(args, instance, v):
    # it's already on the list
    if args[-1] is not None:
        return

    global _delayed_start
    if _delayed_start is None:
        _delayed_start = args
        args[-1] = StopIteration
    else:
        args[-1] = _delayed_start
        _delayed_start = args


def update_intermediates(base, keys, bound, s, fn, args, instance, value):
    ''' Function that is called when an intermediate property is updated
    and `rebind` of that property is True. In that case, we unbind
    all bound funcs that were bound to attrs of the old value of the
    property and rebind to the new value of the property.

    For example, if the rule is `self.a.b.c.d`, then when b is changed, we
    unbind from `b`, `c` and `d`, if they were bound before (they were not
    None and `rebind` of the respective properties was True) and we rebind
    to the new values of the attrs `b`, `c``, `d` that are not None and
    `rebind` is True.

    :Parameters:
        `base`
            A (proxied) ref to the base widget, `self` in the example
            above.
        `keys`
            A list of the name off the attrs of `base` being watched. In
            the example above it'd be `['a', 'b', 'c', 'd']`.
        `bound`
            A list 4-tuples, each tuple being (widget, attr, callback, uid)
            representing callback functions bound to the attributed `attr`
            of `widget`. `uid` is returned by `fbind` when binding.
            The callback may be None, in which case the attr
            was not bound, but is there to be able to walk the attr tree.
            E.g. in the example above, if `b` was not an eventdispatcher,
            `(_b_ref_, `c`, None)` would be added to the list so we can get
            to `c` and `d`, which may be eventdispatchers and their attrs.
        `s`
            The index in `keys` of the of the attr that needs to be
            updated. That is all the keys from `s` and further will be
            rebound, since the `s` key was changed. In bound, the
            corresponding index is `s - 1`. If `s` is None, we start from
            1 (first attr).
        `fn`
            The function to be called args, `args` on bound callback.
    '''
    # first remove all the old bound functions from `s` and down.
    for f, k, fun, uid in bound[s:]:
        if fun is None:
            continue
        try:
            f.unbind_uid(k, uid)
        except ReferenceError:
            pass
    del bound[s:]

    # find the first attr from which we need to start rebinding.
    f = getattr(*bound[-1][:2])
    if f is None:
        fn(args, None, None)
        return
    s += 1
    append = bound.append

    # bind all attrs, except last to update_intermediates
    for val in keys[s:-1]:
        # if we need to dynamically rebind, bindm otherwise just
        # add the attr to the list
        if isinstance(f, (EventDispatcher, Observable)):
            prop = f.property(val, True)
            if prop is not None and getattr(prop, 'rebind', False):
                # fbind should not dispatch, otherwise
                # update_intermediates might be called in the middle
                # here messing things up
                uid = f.fbind(
                    val, update_intermediates, base, keys, bound, s, fn, args)
                append([f.proxy_ref, val, update_intermediates, uid])
            else:
                append([f.proxy_ref, val, None, None])
        else:
            append([getattr(f, 'proxy_ref', f), val, None, None])

        f = getattr(f, val, None)
        if f is None:
            break
        s += 1

    # for the last attr we bind directly to the setting function,
    # because that attr sets the value of the rule.
    if isinstance(f, (EventDispatcher, Observable)):
        uid = f.fbind(keys[-1], fn, args)
        if uid:
            append([f.proxy_ref, keys[-1], fn, uid])
    # when we rebind we have to update the
    # rule with the most recent value, otherwise, the value might be wrong
    # and wouldn't be updated since we might not have tracked it before.
    # This only happens for a callback when rebind was True for the prop.
    fn(args, None, None)


def create_handler(iself, element, key, value, rule, idmap, delayed=False):
    idmap = copy(idmap)
    idmap.update(global_idmap)
    idmap['self'] = iself.proxy_ref
    bound_list = _handlers[iself.uid][key]
    handler_append = bound_list.append

    # we need a hash for when delayed, so we don't execute duplicate canvas
    # callbacks from the same handler during a sync op
    if delayed:
        fn = delayed_call_fn
        args = [element, key, value, rule, idmap, None]  # see _delayed_start
    else:
        fn = call_fn
        args = (element, key, value, rule, idmap)

    # bind every key.value
    if rule.watched_keys is not None:
        for keys in rule.watched_keys:
            base = idmap.get(keys[0])
            if base is None:
                continue
            f = base = getattr(base, 'proxy_ref', base)
            bound = []
            was_bound = False
            append = bound.append

            # bind all attrs, except last to update_intermediates
            k = 1
            for val in keys[1:-1]:
                # if we need to dynamically rebind, bindm otherwise
                # just add the attr to the list
                if isinstance(f, (EventDispatcher, Observable)):
                    prop = f.property(val, True)
                    if prop is not None and getattr(prop, 'rebind', False):
                        # fbind should not dispatch, otherwise
                        # update_intermediates might be called in the middle
                        # here messing things up
                        uid = f.fbind(
                            val, update_intermediates, base, keys, bound, k,
                            fn, args)
                        append([f.proxy_ref, val, update_intermediates, uid])
                        was_bound = True
                    else:
                        append([f.proxy_ref, val, None, None])
                elif not isinstance(f, _cls_type):
                    append([getattr(f, 'proxy_ref', f), val, None, None])
                else:
                    append([f, val, None, None])
                f = getattr(f, val, None)
                if f is None:
                    break
                k += 1

            # for the last attr we bind directly to the setting
            # function, because that attr sets the value of the rule.
            if isinstance(f, (EventDispatcher, Observable)):
                uid = f.fbind(keys[-1], fn, args)  # f is not None
                if uid:
                    append([f.proxy_ref, keys[-1], fn, uid])
                    was_bound = True
            if was_bound:
                handler_append(bound)

    try:
        return eval(value, idmap), bound_list
    except Exception as e:
        tb = sys.exc_info()[2]
        raise BuilderException(rule.ctx, rule.line,
                               '{}: {}'.format(e.__class__.__name__, e),
                               cause=tb)


class BuilderBase(object):
    '''The Builder is responsible for creating a :class:`Parser` for parsing a
    kv file, merging the results into its internal rules, templates, etc.

    By default, :class:`Builder` is a global Kivy instance used in widgets
    that you can use to load other kv files in addition to the default ones.
    '''

    _match_cache = {}
    _match_name_cache = {}

    def __init__(self):
        super(BuilderBase, self).__init__()
        self.files = []
        self.dynamic_classes = {}
        self.templates = {}
        self.rules = []
        self.rulectx = {}

    def load_file(self, filename, **kwargs):
        '''Insert a file into the language builder and return the root widget
        (if defined) of the kv file.

        :parameters:
            `rulesonly`: bool, defaults to False
                If True, the Builder will raise an exception if you have a root
                widget inside the definition.
        '''
        filename = resource_find(filename) or filename
        if __debug__:
            trace('Lang: load file %s' % filename)
        with open(filename, 'r') as fd:
            kwargs['filename'] = filename
            data = fd.read()

            # remove bom ?
            if PY2:
                if data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
                    raise ValueError('Unsupported UTF16 for kv files.')
                if data.startswith((codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE)):
                    raise ValueError('Unsupported UTF32 for kv files.')
                if data.startswith(codecs.BOM_UTF8):
                    data = data[len(codecs.BOM_UTF8):]

            return self.load_string(data, **kwargs)

    def unload_file(self, filename):
        '''Unload all rules associated with a previously imported file.

        .. versionadded:: 1.0.8

        .. warning::

            This will not remove rules or templates already applied/used on
            current widgets. It will only effect the next widgets creation or
            template invocation.
        '''
        # remove rules and templates
        filename = resource_find(filename) or filename
        self.rules = [x for x in self.rules if x[1].ctx.filename != filename]
        self._clear_matchcache()
        templates = {}
        for x, y in self.templates.items():
            if y[2] != filename:
                templates[x] = y
        self.templates = templates

        if filename in self.files:
            self.files.remove(filename)

        # unregister all the dynamic classes
        Factory.unregister_from_filename(filename)

    def load_string(self, string, **kwargs):
        '''Insert a string into the Language Builder and return the root widget
        (if defined) of the kv string.

        :Parameters:
            `rulesonly`: bool, defaults to False
                If True, the Builder will raise an exception if you have a root
                widget inside the definition.
            `filename`: str, defaults to None
                If specified, the filename used to index the kv rules.

        The filename parameter can be used to unload kv strings in the same way
        as you unload kv files. This can be achieved using pseudo file names
        e.g.::

            Build.load_string("""
                <MyRule>:
                    Label:
                        text="Hello"
            """, filename="myrule.kv")

        can be unloaded via::

            Build.unload_file("myrule.kv")

        '''

        kwargs.setdefault('rulesonly', False)
        self._current_filename = fn = kwargs.get('filename', None)

        # put a warning if a file is loaded multiple times
        if fn in self.files:
            Logger.warning(
                'Lang: The file {} is loaded multiples times, '
                'you might have unwanted behaviors.'.format(fn))

        try:
            # parse the string
            parser = Parser(content=string, filename=fn)

            # merge rules with our rules
            self.rules.extend(parser.rules)
            self._clear_matchcache()

            # add the template found by the parser into ours
            for name, cls, template in parser.templates:
                self.templates[name] = (cls, template, fn)
                Factory.register(name,
                                 cls=partial(self.template, name),
                                 is_template=True, warn=True)

            # register all the dynamic classes
            for name, baseclasses in iteritems(parser.dynamic_classes):
                Factory.register(name, baseclasses=baseclasses, filename=fn,
                                 warn=True)

            # create root object is exist
            if kwargs['rulesonly'] and parser.root:
                filename = kwargs.get('rulesonly', '<string>')
                raise Exception('The file <%s> contain also non-rules '
                                'directives' % filename)

            # save the loaded files only if there is a root without
            # template/dynamic classes
            if fn and (parser.templates or
                       parser.dynamic_classes or parser.rules):
                self.files.append(fn)

            if parser.root:
                widget = Factory.get(parser.root.name)(__no_builder=True)
                rule_children = []
                widget.apply_class_lang_rules(
                    root=widget, rule_children=rule_children)
                self._apply_rule(
                    widget, parser.root, parser.root,
                    rule_children=rule_children)

                for child in rule_children:
                    child.dispatch('on_kv_post', widget)
                widget.dispatch('on_kv_post', widget)
                return widget
        finally:
            self._current_filename = None

    def template(self, *args, **ctx):
        '''Create a specialized template using a specific context.

        .. versionadded:: 1.0.5

        With templates, you can construct custom widgets from a kv lang
        definition by giving them a context. Check :ref:`Template usage
        <template_usage>`.
        '''
        # Prevent naming clash with whatever the user might be putting into the
        # ctx as key.
        name = args[0]
        if name not in self.templates:
            raise Exception('Unknown <%s> template name' % name)
        baseclasses, rule, fn = self.templates[name]
        key = '%s|%s' % (name, baseclasses)
        cls = Cache.get('kv.lang', key)
        if cls is None:
            rootwidgets = []
            for basecls in baseclasses.split('+'):
                rootwidgets.append(Factory.get(basecls))
            cls = type(name, tuple(rootwidgets), {})
            Cache.append('kv.lang', key, cls)
        widget = cls()
        # in previous versions, ``ctx`` is passed as is as ``template_ctx``
        # preventing widgets in it from be collected by the GC. This was
        # especially relevant to AccordionItem's title_template.
        proxy_ctx = {k: get_proxy(v) for k, v in ctx.items()}
        self._apply_rule(widget, rule, rule, template_ctx=proxy_ctx)
        return widget

    def apply_rules(
            self, widget, rule_name, ignored_consts=set(), rule_children=None,
            dispatch_kv_post=False):
        '''Search all the rules that match the name `rule_name`
        and apply them to `widget`.

        .. versionadded:: 1.10.0

        :Parameters:

            `widget`: :class:`~kivy.uix.widget.Widget`
                The widget to whom the matching rules should be applied to.
            `ignored_consts`: set
                A set or list type whose elements are property names for which
                constant KV rules (i.e. those that don't create bindings) of
                that widget will not be applied. This allows e.g. skipping
                constant rules that overwrite a value initialized in python.
            `rule_children`: list
                If not ``None``, it should be a list that will be populated
                with all the widgets created by the kv rules being applied.

                .. versionchanged:: 1.11.0

            `dispatch_kv_post`: bool
                Normally the class `Widget` dispatches the `on_kv_post` event
                to widgets created during kv rule application.
                But if the rules are manually applied by calling :meth:`apply`,
                that may not happen, so if this is `True`, we will dispatch the
                `on_kv_post` event where needed after applying the rules to
                `widget` (we won't dispatch it for `widget` itself).

                Defaults to False.

                .. versionchanged:: 1.11.0
        '''
        rules = self.match_rule_name(rule_name)
        if __debug__:
            trace('Lang: Found %d rules for %s' % (len(rules), rule_name))
        if not rules:
            return

        if dispatch_kv_post:
            rule_children = rule_children if rule_children is not None else []
        for rule in rules:
            self._apply_rule(
                widget, rule, rule, ignored_consts=ignored_consts,
                rule_children=rule_children)
        if dispatch_kv_post:
            for w in rule_children:
                w.dispatch('on_kv_post', widget)

    def apply(self, widget, ignored_consts=set(), rule_children=None,
              dispatch_kv_post=False):
        '''Search all the rules that match the widget and apply them.

        :Parameters:

            `widget`: :class:`~kivy.uix.widget.Widget`
                The widget whose class rules should be applied to this widget.
            `ignored_consts`: set
                A set or list type whose elements are property names for which
                constant KV rules (i.e. those that don't create bindings) of
                that widget will not be applied. This allows e.g. skipping
                constant rules that overwrite a value initialized in python.
            `rule_children`: list
                If not ``None``, it should be a list that will be populated
                with all the widgets created by the kv rules being applied.

                .. versionchanged:: 1.11.0

            `dispatch_kv_post`: bool
                Normally the class `Widget` dispatches the `on_kv_post` event
                to widgets created during kv rule application.
                But if the rules are manually applied by calling :meth:`apply`,
                that may not happen, so if this is `True`, we will dispatch the
                `on_kv_post` event where needed after applying the rules to
                `widget` (we won't dispatch it for `widget` itself).

                Defaults to False.

                .. versionchanged:: 1.11.0
        '''
        rules = self.match(widget)
        if __debug__:
            trace('Lang: Found %d rules for %s' % (len(rules), widget))
        if not rules:
            return

        if dispatch_kv_post:
            rule_children = rule_children if rule_children is not None else []
        for rule in rules:
            self._apply_rule(
                widget, rule, rule, ignored_consts=ignored_consts,
                rule_children=rule_children)
        if dispatch_kv_post:
            for w in rule_children:
                w.dispatch('on_kv_post', widget)

    def _clear_matchcache(self):
        BuilderBase._match_cache = {}
        BuilderBase._match_name_cache = {}

    def _apply_rule(self, widget, rule, rootrule, template_ctx=None,
                    ignored_consts=set(), rule_children=None):
        # widget: the current instantiated widget
        # rule: the current rule
        # rootrule: the current root rule (for children of a rule)

        # will collect reference to all the id in children
        assert(rule not in self.rulectx)
        self.rulectx[rule] = rctx = {
            'ids': {'root': widget.proxy_ref},
            'set': [], 'hdl': []}

        # extract the context of the rootrule (not rule!)
        assert(rootrule in self.rulectx)
        rctx = self.rulectx[rootrule]

        # if a template context is passed, put it as "ctx"
        if template_ctx is not None:
            rctx['ids']['ctx'] = QueryDict(template_ctx)

        # if we got an id, put it in the root rule for a later global usage
        if rule.id:
            # use only the first word as `id` discard the rest.
            rule.id = rule.id.split('#', 1)[0].strip()
            rctx['ids'][rule.id] = widget.proxy_ref
            # set id name as a attribute for root widget so one can in python
            # code simply access root_widget.id_name
            _ids = dict(rctx['ids'])
            _root = _ids.pop('root')
            _new_ids = _root.ids
            for _key in iterkeys(_ids):
                if _ids[_key] == _root:
                    # skip on self
                    continue
                _new_ids[_key] = _ids[_key]
            _root.ids = _new_ids

        # first, ensure that the widget have all the properties used in
        # the rule if not, they will be created as ObjectProperty.
        rule.create_missing(widget)

        # build the widget canvas
        if rule.canvas_before:
            with widget.canvas.before:
                self._build_canvas(widget.canvas.before, widget,
                                   rule.canvas_before, rootrule)
        if rule.canvas_root:
            with widget.canvas:
                self._build_canvas(widget.canvas, widget,
                                   rule.canvas_root, rootrule)
        if rule.canvas_after:
            with widget.canvas.after:
                self._build_canvas(widget.canvas.after, widget,
                                   rule.canvas_after, rootrule)

        # create children tree
        Factory_get = Factory.get
        Factory_is_template = Factory.is_template
        for crule in rule.children:
            cname = crule.name

            if cname in ('canvas', 'canvas.before', 'canvas.after'):
                raise ParserException(
                    crule.ctx, crule.line,
                    'Canvas instructions added in kv must '
                    'be declared before child widgets.')

            # depending if the child rule is a template or not, we are not
            # having the same approach
            cls = Factory_get(cname)

            if Factory_is_template(cname):
                # we got a template, so extract all the properties and
                # handlers, and push them in a "ctx" dictionary.
                ctx = {}
                idmap = copy(global_idmap)
                idmap.update({'root': rctx['ids']['root']})
                if 'ctx' in rctx['ids']:
                    idmap.update({'ctx': rctx['ids']['ctx']})
                try:
                    for prule in crule.properties.values():
                        value = prule.co_value
                        if type(value) is CodeType:
                            value = eval(value, idmap)
                        ctx[prule.name] = value
                    for prule in crule.handlers:
                        value = eval(prule.value, idmap)
                        ctx[prule.name] = value
                except Exception as e:
                    tb = sys.exc_info()[2]
                    raise BuilderException(
                        prule.ctx, prule.line,
                        '{}: {}'.format(e.__class__.__name__, e), cause=tb)

                # create the template with an explicit ctx
                child = cls(**ctx)
                widget.add_widget(child)

                # reference it on our root rule context
                if crule.id:
                    rctx['ids'][crule.id] = child

            else:
                # we got a "normal" rule, construct it manually
                # we can't construct it without __no_builder=True, because the
                # previous implementation was doing the add_widget() before
                # apply(), and so, we could use "self.parent".
                child = cls(__no_builder=True)
                widget.add_widget(child)
                child.apply_class_lang_rules(
                    root=rctx['ids']['root'], rule_children=rule_children)
                self._apply_rule(
                    child, crule, rootrule, rule_children=rule_children)

                if rule_children is not None:
                    rule_children.append(child)

        # append the properties and handlers to our final resolution task
        if rule.properties:
            rctx['set'].append((widget.proxy_ref,
                                list(rule.properties.values())))
            for key, crule in rule.properties.items():
                # clear previously applied rules if asked
                if crule.ignore_prev:
                    Builder.unbind_property(widget, key)
        if rule.handlers:
            rctx['hdl'].append((widget.proxy_ref, rule.handlers))

        # if we are applying another rule that the root one, then it's done for
        # us!
        if rootrule is not rule:
            del self.rulectx[rule]
            return

        # normally, we can apply a list of properties with a proper context
        try:
            rule = None
            for widget_set, rules in reversed(rctx['set']):
                for rule in rules:
                    assert(isinstance(rule, ParserRuleProperty))
                    key = rule.name
                    value = rule.co_value
                    if type(value) is CodeType:
                        value, bound = create_handler(
                            widget_set, widget_set, key, value, rule,
                            rctx['ids'])
                        # if there's a rule
                        if (widget_set != widget or bound or
                                key not in ignored_consts):
                            setattr(widget_set, key, value)
                    else:
                        if (widget_set != widget or
                                key not in ignored_consts):
                            setattr(widget_set, key, value)

        except Exception as e:
            if rule is not None:
                tb = sys.exc_info()[2]
                raise BuilderException(rule.ctx, rule.line,
                                       '{}: {}'.format(e.__class__.__name__,
                                                       e), cause=tb)
            raise e

        # build handlers
        try:
            crule = None
            for widget_set, rules in rctx['hdl']:
                for crule in rules:
                    assert(isinstance(crule, ParserRuleProperty))
                    assert(crule.name.startswith('on_'))
                    key = crule.name
                    if not widget_set.is_event_type(key):
                        key = key[3:]
                    idmap = copy(global_idmap)
                    idmap.update(rctx['ids'])
                    idmap['self'] = widget_set.proxy_ref
                    if not widget_set.fbind(key, custom_callback, crule,
                                            idmap):
                        raise AttributeError(key)
                    # hack for on_parent
                    if crule.name == 'on_parent':
                        Factory.Widget.parent.dispatch(widget_set.__self__)
        except Exception as e:
            if crule is not None:
                tb = sys.exc_info()[2]
                raise BuilderException(
                    crule.ctx, crule.line,
                    '{}: {}'.format(e.__class__.__name__, e), cause=tb)
            raise e

        # rule finished, forget it
        del self.rulectx[rootrule]

    def match(self, widget):
        '''Return a list of :class:`ParserRule` objects matching the widget.
        '''
        cache = BuilderBase._match_cache
        k = (widget.__class__, tuple(widget.cls))
        if k in cache:
            return cache[k]
        rules = []
        for selector, rule in self.rules:
            if selector.match(widget):
                if rule.avoid_previous_rules:
                    del rules[:]
                rules.append(rule)
        cache[k] = rules
        return rules

    def match_rule_name(self, rule_name):
        '''Return a list of :class:`ParserRule` objects matching the widget.
        '''
        cache = BuilderBase._match_name_cache
        rule_name = str(rule_name)
        k = rule_name.lower()
        if k in cache:
            return cache[k]
        rules = []
        for selector, rule in self.rules:
            if selector.match_rule_name(rule_name):
                if rule.avoid_previous_rules:
                    del rules[:]
                rules.append(rule)
        cache[k] = rules
        return rules

    def sync(self):
        '''Execute all the waiting operations, such as the execution of all the
        expressions related to the canvas.

        .. versionadded:: 1.7.0
        '''
        global _delayed_start
        next_args = _delayed_start
        if next_args is None:
            return

        while next_args is not StopIteration:
            # is this try/except still needed? yes, in case widget died in this
            # frame after the call was scheduled
            try:
                call_fn(next_args[:-1], None, None)
            except ReferenceError:
                pass
            args = next_args
            next_args = args[-1]
            args[-1] = None
        _delayed_start = None

    def unbind_widget(self, uid):
        '''Unbind all the handlers created by the KV rules of the
        widget. The :attr:`kivy.uix.widget.Widget.uid` is passed here
        instead of the widget itself, because Builder is using it in the
        widget destructor.

        This effectively clears all the KV rules associated with this widget.
        For example:

        .. code-block:: python

            >>> w = Builder.load_string(\'''
            ... Widget:
            ...     height: self.width / 2. if self.disabled else self.width
            ...     x: self.y + 50
            ... \''')
            >>> w.size
            [100, 100]
            >>> w.pos
            [50, 0]
            >>> w.width = 500
            >>> w.size
            [500, 500]
            >>> Builder.unbind_widget(w.uid)
            >>> w.width = 222
            >>> w.y = 500
            >>> w.size
            [222, 500]
            >>> w.pos
            [50, 500]

        .. versionadded:: 1.7.2
        '''
        if uid not in _handlers:
            return
        for prop_callbacks in _handlers[uid].values():
            for callbacks in prop_callbacks:
                for f, k, fn, bound_uid in callbacks:
                    if fn is None:  # it's not a kivy prop.
                        continue
                    try:
                        f.unbind_uid(k, bound_uid)
                    except ReferenceError:
                        # proxy widget is already gone, that's cool :)
                        pass
        del _handlers[uid]

    def unbind_property(self, widget, name):
        '''Unbind the handlers created by all the rules of the widget that set
        the name.

        This effectively clears all the rules of widget that take the form::

            name: rule

        For example:

        .. code-block:: python

            >>> w = Builder.load_string(\'''
            ... Widget:
            ...     height: self.width / 2. if self.disabled else self.width
            ...     x: self.y + 50
            ... \''')
            >>> w.size
            [100, 100]
            >>> w.pos
            [50, 0]
            >>> w.width = 500
            >>> w.size
            [500, 500]
            >>> Builder.unbind_property(w, 'height')
            >>> w.width = 222
            >>> w.size
            [222, 500]
            >>> w.y = 500
            >>> w.pos
            [550, 500]

        .. versionadded:: 1.9.1
        '''
        uid = widget.uid
        if uid not in _handlers:
            return

        prop_handlers = _handlers[uid]
        if name not in prop_handlers:
            return

        for callbacks in prop_handlers[name]:
            for f, k, fn, bound_uid in callbacks:
                if fn is None:  # it's not a kivy prop.
                    continue
                try:
                    f.unbind_uid(k, bound_uid)
                except ReferenceError:
                    # proxy widget is already gone, that's cool :)
                    pass
        del prop_handlers[name]
        if not prop_handlers:
            del _handlers[uid]

    def _build_canvas(self, canvas, widget, rule, rootrule):
        global Instruction
        if Instruction is None:
            Instruction = Factory.get('Instruction')
        idmap = copy(self.rulectx[rootrule]['ids'])
        for crule in rule.children:
            name = crule.name
            if name == 'Clear':
                canvas.clear()
                continue
            instr = Factory.get(name)()
            if not isinstance(instr, Instruction):
                raise BuilderException(
                    crule.ctx, crule.line,
                    'You can add only graphics Instruction in canvas.')
            try:
                for prule in crule.properties.values():
                    key = prule.name
                    value = prule.co_value
                    if type(value) is CodeType:
                        value, _ = create_handler(
                            widget, instr.proxy_ref,
                            key, value, prule, idmap, True)
                    setattr(instr, key, value)
            except Exception as e:
                tb = sys.exc_info()[2]
                raise BuilderException(
                    prule.ctx, prule.line,
                    '{}: {}'.format(e.__class__.__name__, e), cause=tb)


#: Main instance of a :class:`BuilderBase`.
Builder = register_context('Builder', BuilderBase)
Builder.load_file(join(kivy_data_dir, 'style.kv'), rulesonly=True)

if 'KIVY_PROFILE_LANG' in environ:
    import atexit
    import cgi

    def match_rule(fn, index, rule):
        if rule.ctx.filename != fn:
            return
        for prop, prp in iteritems(rule.properties):
            if prp.line != index:
                continue
            yield prp
        for child in rule.children:
            for r in match_rule(fn, index, child):
                yield r
        if rule.canvas_root:
            for r in match_rule(fn, index, rule.canvas_root):
                yield r
        if rule.canvas_before:
            for r in match_rule(fn, index, rule.canvas_before):
                yield r
        if rule.canvas_after:
            for r in match_rule(fn, index, rule.canvas_after):
                yield r

    def dump_builder_stats():
        html = [
            '<!doctype html>'
            '<html><body>',
            '<style type="text/css">\n',
            'pre { margin: 0; }\n',
            '</style>']
        files = set([x[1].ctx.filename for x in Builder.rules])
        for fn in files:
            try:
                with open(fn) as f:
                    lines = f.readlines()
            except (IOError, TypeError) as e:
                continue
            html += ['<h2>', fn, '</h2>', '<table>']
            count = 0
            for index, line in enumerate(lines):
                line = line.rstrip()
                line = cgi.escape(line)
                matched_prp = []
                for psn, rule in Builder.rules:
                    matched_prp += list(match_rule(fn, index, rule))

                count = sum(set([x.count for x in matched_prp]))

                color = (255, 155, 155) if count else (255, 255, 255)
                html += ['<tr style="background-color: rgb{}">'.format(color),
                         '<td>', str(index + 1), '</td>',
                         '<td>', str(count), '</td>',
                         '<td><pre>', line, '</pre></td>',
                         '</tr>']
            html += ['</table>']
        html += ['</body></html>']
        with open('builder_stats.html', 'w') as fd:
            fd.write(''.join(html))

        print('Profiling written at builder_stats.html')

    atexit.register(dump_builder_stats)
