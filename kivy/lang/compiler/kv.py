'''
KV Compilation
===============
'''

import textwrap
import inspect
import re
import ast
import copy
import inspect
from inspect import ismethod as _inspect_ismethod, \
    isfunction as _inspect_isfunction

from kivy.lang.compiler.src_gen import KVCompiler
from kivy.lang.compiler.ast_parse import ParseKVFunctionTransformer, \
    ParseKVBindTransformer, generate_source, KVCompilerParserException, \
    ASTStrPlaceholder, verify_readonly_nodes
from kivy.lang.compiler.runtime import load_kvc_from_file, save_kvc_to_file
from kivy.lang.compiler.ast_parse import KVException

__all__ = ('KV', 'KV_apply_manual', 'patch_inspect', 'unpatch_inspect')
# XXX: https://bugs.python.org/issue31772


def KV(kv_syntax='minimal', proxy=False, rebind=True, bind_on_enter=False,
       captures_are_readonly=True):
    '''
    Decorator factory function that returns a decorator that compiles a KV
    containing function. Typical usage::

        class MyWidget(Widget):
            @KV()  # notice that it MUST be called
            def apply_kv(self):
                with KVCtx():
                    self.x @= self.y + 256

    :param kv_syntax: The binding syntax to support. Default: `"minimal"`
        With `"minimal"`, it's similar to traditional KV, and binds rules e.g.
        `self.x @= self.widget.y` and `self.dict[self.name]`. When None, it
        binds to a expanded set of syntax, e.g.
        `(self.widget + self.widget2).width`.

        The `"minimal"` syntax is recommended for most situations and `None`
        should only be used in exceptional circumstance.
    :param proxy: glob pattern(s) describing the widgets that should not hold
        a direct reference to other widgets for garbage collection purposes.
        Defaults to `False`

        It is either `False` - when all widgets should hold direct references,
        or `True` - when no widgets should hold direct references, or
        a glob string describing the widget(s) that should not hold a
        reference, e.g. `"*widget"` will match `self.widget` and
        `self.my_widget`. Or it can be a list of glob strings and any that
        match will not hold a direct reference.

        This is to be used when binding widgets that have a very long life, and
        it's not desirable that the widget prevent other widgets from being
        garbage collected. This is mostly encountered when binding to the
        global App, which never dies.

        This is used for widgets that are being bound to, e.g. in the rule
        `self.x @= self.app.my_x`, `proxy` may be set to `"*app"`, to prevent
        the `self` widget from being kept alive by `app`. But is not needed
        e.g. when binding to widgets that are not independently kept alive.

        .. warning::

            If all binding widgets are using proxies, no one will keep the KV
            rules alive, and the rules will not be executed once garbage
            collection runs. You can save a reference to the KVCtx, and that
            will keep that context alive as long as the context is held.
    :param rebind: glob pattern(s) describing the intermediate widgets that
        should be rebound when they change. Defaults to `True`.

        It is either `True` - when all widgets should rebind,
        or `False` - when no widgets should rebind, or
        a glob string describing the widget(s) that should rebind, e.g.
        `"*widget"` will match `self.widget` and
        `self.my_widget` and both `widget` and `my_widget` will rebind. Or it
        can be a list of glob strings and any that match will rebind.

        This is used in rule e.g. `self.x @= self.widget.x`, if `self.widget`
        is rebound, then when `self.widget` changes, the rulee rebind to `x`
        belonging to the new widget stored in `self.widget`.
    :param bind_on_enter: Where KV binding should occur for the context.
        Defaults to False.

        For a rule such as::

            with KVCtx():
                ...

        binding can occur when the context is entered or exited. When
        `bind_on_enter` is `True`, it occurs upon entrance, when `False` it
        occurs upon exit. The default is `False`. Binding upon entrance is not
        recommended because it's unintuitive and doesn't follow the typical
        python programmatic flow.
    :param captures_are_readonly: Whether any variables that participate
        in a rule may be changed between rule execution and binding. Defaults
        to `True`.

        This parameter should not be changed to `False` except for debugging
        purposes or if you truly understand the internals of binding.
    :return: The compiled function associated with the original function,
        or the original function if there was nothing to compile.

    Once a function is decorated, calling KV again on it will not recompile
    the function, unless the source or the compile options changed. This means
    calling `KV()(f)` will not re-compile `f` (and it shouldn't need to).
    '''
    compile_flags = (
        kv_syntax, proxy, rebind, bind_on_enter, captures_are_readonly)

    def KV_decorate(func):
        if func.__closure__ or '<locals>' in func.__qualname__:
            raise KVException(
                'The KV decorator cannot be used on a function that is a '
                'closure or a local. It must be defined as a global function,'
                'such as a class method or global function in a module')
        # no lambda
        mod, f = load_kvc_from_file(func, compile_flags=compile_flags)
        if f is not None:
            if f == 'use_original':
                return func
            f._kv_src_func_globals = func.__globals__
            return f

        compiler = KVCompiler()
        inspect.getfile(func)
        src = textwrap.dedent(inspect.getsource(func))

        transformer = ParseKVFunctionTransformer(kv_syntax=kv_syntax)
        graph = ast.parse(src)
        # remove the KV decorator
        func_def = graph.body[0]
        assert isinstance(func_def, ast.FunctionDef)
        if len(func_def.decorator_list) > 1:
            raise KVCompilerParserException(
                'KV decorated functions can have only one decorator - a '
                'single KV decorator')
        del func_def.decorator_list[:]

        copied_graph = None
        if captures_are_readonly:
            copied_graph = copy.deepcopy(graph)
        ast_nodes = transformer.visit(graph)

        if not transformer.context_infos:
            save_kvc_to_file(
                func,
                '# There was no KV context or rules, the original function '
                'will be returned instead.\n{} = "use_original"\n'.
                format(func.__name__))
            return func

        func_def = graph.body[0]
        assert isinstance(func_def, ast.FunctionDef)
        func_body = func_def.body
        assert isinstance(func_body, list)

        for ctx_info in transformer.context_infos:
            ctx = ctx_info['ctx']
            ctx.parse_rules()
            # these must happen *before* anything else and after all rules
            ctx.set_nodes_proxy(proxy)
            ctx.set_nodes_rebind(rebind)

            ctx_name, funcs, rule_creation, rule_finalization, reinit = \
                compiler.generate_bindings(ctx, None, create_rules=True)
            ctx_info['assign_target_node'].id = ctx_name

            before_ctx_node = ctx_info['before_ctx']
            after_ctx_node = ctx_info['after_ctx']

            if bind_on_enter:
                before_ctx_node.src_lines = \
                    [''] + rule_creation + funcs + rule_finalization
            else:
                before_ctx_node.src_lines = [''] + rule_creation
                after_ctx_node.src_lines = funcs + rule_finalization
            after_ctx_node.src_lines += reinit

        creation, deletion = compiler.gen_temp_vars_creation_deletion()

        if captures_are_readonly:
            # needs to happen after all the rules are parsed
            verify_readonly_nodes(copied_graph, transformer, bind_on_enter)

        update_node = ASTStrPlaceholder()
        imports = [
            'from kivy.lang.compiler.kv_context import KVCtx as __KVCtx, '
            'KVRule as __KVRule']
        if compiler.used_canvas_rule:
            imports.append(
                'from kivy.lang.compiler.runtime import add_graphics_callback '
                'as __kv_add_graphics_callback')
        if compiler.used_clock_rule:
            imports.append('from kivy.clock import Clock as __kv_Clock')
        if compiler.used_weak_ref:
            imports.append(
                'from weakref import ref as __kv_ref')

        globals_update = [
            '__kv_mod_func = {}'.format(func.__name__),
            'globals().clear()',
            'globals().update(__kv_mod_func._kv_src_func_globals)',
            'globals()["{}"] = __kv_mod_func'.format(func.__name__),
            '']

        update_node.src_lines = imports + globals_update + creation
        func_body.insert(0, update_node)

        src_code = generate_source(ast_nodes) + '\n\n'
        src_code = src_code + '\n'.join(
            '    {}'.format(line) for line in deletion)
        src_code = re.sub('^ +$', '', src_code, flags=re.M)  # del empty space
        src_code = re.sub('\n\n\n+', '\n\n', src_code)  # reduce newlines

        save_kvc_to_file(func, src_code, compile_flags=compile_flags)
        mod, f = load_kvc_from_file(func, compile_flags=compile_flags)
        f._kv_src_func_globals = func.__globals__
        return f

    return KV_decorate


def KV_apply_manual(
        ctx, callback, local_vars, global_vars, kv_syntax='minimal',
        proxy=False, rebind=True):
    '''
    Similar to :func:`KV`, except that is is called manually to compile
    bindings. Similalrly to :func:`KV`, the bindings are compiled once, and are
    only recompiled if any of the compile options or source code file
    containing the callback is modified.

    This is meant to be used for debugging purposes, and may change in the
    future.

    Typical usage::

        class ManualKVWidget(Widget):

            def apply_kv(self):
                ctx = KVParserCtx()

                def manage_val(*largs):
                    self.x = self.y + 512
                manage_val()

                # will bind to `self.y`.
                rule = KVParserRule('self.y + 512')
                rule.callback = manage_val
                rule.callback_name = manage_val.__name__
                ctx.add_rule(rule)

                KV_apply_manual(ctx, self.apply_kv, locals(), globals())

    :param ctx: a `KVParserCtx` used for parsing the rules.
    :param callback: The callback to call when any of the bindings change.
    :param local_vars: `locals()` of the function where the bindings occur.
    :param global_vars: `globals()` of the function where the bindings occur.
    :param kv_syntax: See :func:`KV`.
    :param proxy: See :func:`KV`.
    :param rebind: See :func:`KV`.
    :return: None - it executes the compiled rule in the provided `locals()`,
        `globals()` environment.
    '''
    ctx_name = '__kv_ctx'
    compiler = KVCompiler()

    mod, f = load_kvc_from_file(callback, '__kv_manual_wrapper', 'manual')

    if f is None:
        transformer = ParseKVBindTransformer(kv_syntax)
        ctx.set_kv_binding_ast_transformer(transformer)

        ctx.parse_rules()
        # these must happen *before* anything else and after all rules
        ctx.set_nodes_proxy(proxy)
        ctx.set_nodes_rebind(rebind)

        _, funcs, rule_creation, rule_finalization, reinit = \
            compiler.generate_bindings(ctx, ctx_name, create_rules=False)

        creation, deletion = compiler.gen_temp_vars_creation_deletion()
        globals_update = [
            '__kv_mod_func = __kv_manual_wrapper',
            'globals().clear()',
            'globals().update(__kv_src_func_globals)',
            'globals()["__kv_manual_wrapper"] = __kv_mod_func',
            '']

        lines = globals_update + creation + rule_creation + funcs + \
            rule_finalization + reinit + deletion
        lines = ('    {}'.format(line) if line else '' for line in lines)
        src = 'def __kv_manual_wrapper(__kv_src_func_globals, {}):\n{}'.\
            format(ctx_name, '\n'.join(lines))

        save_kvc_to_file(callback, src, 'manual')
        mod, f = load_kvc_from_file(callback, '__kv_manual_wrapper', 'manual')

    global_vars = global_vars.copy()
    global_vars.update(local_vars)
    f(global_vars, ctx)


def patch_inspect():
    def ismethod_cython(object):
        if _inspect_ismethod(object):
            return True
        if object.__class__.__name__ == 'cython_function_or_method' and \
                hasattr(object, '__func__'):
            return True
        return False
    inspect.ismethod = ismethod_cython

    def isfunction_cython(object):
        if _inspect_isfunction(object):
            return True
        if object.__class__.__name__ == 'cython_function_or_method' and not \
                hasattr(object, '__func__'):
            return True
        return False
    inspect.isfunction = isfunction_cython


def unpatch_inspect():
    inspect.ismethod = _inspect_ismethod
    inspect.isfunction = _inspect_isfunction
