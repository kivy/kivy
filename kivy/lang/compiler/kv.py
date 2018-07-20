# XXX: https://bugs.python.org/issue31772

import textwrap
import inspect
import re
import ast
import copy

from kivy.lang.compiler.src_gen import KVCompiler
from kivy.lang.compiler.ast_parse import ParseKVFunctionTransformer, \
    ParseKVBindTransformer, generate_source, KVCompilerParserException, \
    ASTRuleCtxNodePlaceholder, verify_readonly_nodes
from kivy.lang.compiler.runtime import load_kvc_from_file, save_kvc_to_file
from kivy.lang.compiler.ast_parse import KVException


def KV(kv_syntax='minimal', proxy=False, rebind=True, bind_on_enter=False,
       exec_rules_after_binding=False, captures_are_readonly=True):
    '''Once a function is decorated, calling KV again on it will ignore
    option changes, unless the source changed. This means calling KV()(f)
    multiple times with different flags will not re-compile f.'''
    compile_flags = (
        kv_syntax, proxy, rebind, bind_on_enter, exec_rules_after_binding,
        captures_are_readonly)

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
        tree = ast.parse(src)
        # remove the KV decorator
        func_def = tree.body[0]
        assert isinstance(func_def, ast.FunctionDef)
        if len(func_def.decorator_list) > 1:
            raise KVCompilerParserException(
                'KV decorated functions can have only one decorator - a '
                'single KV decorator')
        del func_def.decorator_list[:]

        copied_tree = None
        if captures_are_readonly:
            copied_tree = copy.deepcopy(tree)
        ast_nodes = transformer.visit(tree)

        if not transformer.context_infos:
            save_kvc_to_file(
                func,
                '# There was no KV context or rules, the original function '
                'will be returned instead.\n{} = "use_original"\n'.
                format(func.__name__))
            return func

        func_def = tree.body[0]
        assert isinstance(func_def, ast.FunctionDef)
        func_body = func_def.body
        assert isinstance(func_body, list)

        for ctx_info in transformer.context_infos:
            ctx = ctx_info['ctx']
            ctx.parse_rules()
            # these must happen *before* anything else and after all rules
            ctx.set_nodes_proxy(proxy)
            ctx.set_nodes_rebind(rebind)

            ctx_name, funcs, rule_creation, rule_finalization = \
                compiler.generate_bindings(
                    ctx, None, create_rules=True,
                    exec_rules_after_binding=exec_rules_after_binding)
            ctx_info['assign_target_node'].id = ctx_name

            before_ctx_node = ctx_info['before_ctx']
            after_ctx_node = ctx_info['after_ctx']

            if bind_on_enter:
                before_ctx_node.src_lines = \
                    [''] + rule_creation + funcs + rule_finalization
            else:
                before_ctx_node.src_lines = [''] + rule_creation
                after_ctx_node.src_lines = funcs + rule_finalization

        creation, deletion = compiler.gen_temp_vars_creation_deletion()

        if captures_are_readonly:
            # needs to happen after all the rules are parsed
            verify_readonly_nodes(copied_tree, transformer, bind_on_enter)

        update_node = ASTRuleCtxNodePlaceholder()
        imports = [
            'from kivy.lang.compiler.kv_context import KVCtx as __KVCtx, '
            'KVRule as __KVRule']
        if compiler.used_canvas_rule:
            imports.append(
                'from kivy.lang.compiler.runtime import add_graphics_callback '
                'as __kv_add_graphics_callback')
        if compiler.used_clock_rule:
            imports.append('from kivy.clock import Clock as __kv_Clock')

        globals_update = [
            '__kv_mod_func = {}'.format(func.__name__),
            'globals().clear()',
            'globals().update(__kv_mod_func._kv_src_func_globals)',
            'globals()["{}"] = __kv_mod_func'.format(func.__name__),
            '']

        update_node.src_lines = imports + globals_update + creation
        func_body.insert(0, update_node)

        src_code = generate_source(ast_nodes) + '\n'
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
        ctx, func, local_vars, global_vars, kv_syntax='minimal', proxy=False,
        rebind=True, exec_rules_after_binding=False):
    ctx_name = '__kv_ctx'
    compiler = KVCompiler()

    mod, f = load_kvc_from_file(func, '__kv_manual_wrapper', 'manual')

    if f is None:
        transformer = ParseKVBindTransformer()
        ctx.set_kv_binding_ast_transformer(transformer, kv_syntax)

        ctx.parse_rules()
        # these must happen *before* anything else and after all rules
        ctx.set_nodes_proxy(proxy)
        ctx.set_nodes_rebind(rebind)

        _, funcs, rule_creation, rule_finalization = \
            compiler.generate_bindings(
                ctx, ctx_name, create_rules=False,
                exec_rules_after_binding=exec_rules_after_binding)

        creation, deletion = compiler.gen_temp_vars_creation_deletion()
        globals_update = [
            '__kv_mod_func = __kv_manual_wrapper',
            'globals().clear()',
            'globals().update(__kv_src_func_globals)',
            'globals()["__kv_manual_wrapper"] = __kv_mod_func',
            '']

        lines = globals_update + creation + rule_creation + funcs + \
            rule_finalization + deletion
        lines = ('    {}'.format(line) if line else '' for line in lines)
        src = 'def __kv_manual_wrapper(__kv_src_func_globals, {}):\n{}'.\
            format(ctx_name, '\n'.join(lines))

        save_kvc_to_file(func, src, 'manual')
        mod, f = load_kvc_from_file(func, '__kv_manual_wrapper', 'manual')

    global_vars = global_vars.copy()
    global_vars.update(local_vars)
    f(global_vars, ctx)
