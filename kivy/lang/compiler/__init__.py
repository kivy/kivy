import textwrap
import itertools
import inspect
import re
import ast

from kivy.lang.compiler.src_gen import KVCompiler
from kivy.lang.compiler.ast_parse import ParseKVFunctionTransformer, \
    ParseKVBindTransformer, generate_source, KVCompilerParserException, \
    ASTRuleCtxNodePlaceholder
from kivy.lang.compiler.kv_context import KVCtx, KVRule
from kivy.lang.compiler.runtime import load_kvc_from_file, save_kvc_to_file

_space_match = re.compile('^ +$')


class KVException(Exception):
    pass


def KV(func, kv_syntax=None, proxy=False, rebind=True, bind_on_enter=False,
       exec_rules_after_binding=False, compiler_cls=KVCompiler,
       transformer_cls=ParseKVFunctionTransformer):
    if func.__closure__:
        raise KVException(
            'The KV decorator cannot be used on a function that is a closure')
    mod, f = load_kvc_from_file(func, func.__name__)  # no lambda
    if f is not None:
        f._kv_src_func_globals = func.__globals__
        return f

    print('going the slow route')
    compiler = compiler_cls()
    inspect.getfile(func)
    src = textwrap.dedent(inspect.getsource(func))

    transformer = transformer_cls(kv_syntax=kv_syntax)
    tree = ast.parse(src)
    # remove the KV decorator
    func_def = tree.body[0]
    assert isinstance(func_def, ast.FunctionDef)
    if len(func_def.decorator_list) > 1:
        raise KVCompilerParserException(
            'KV functions can have only one decorator - the KV decorator')
    del func_def.decorator_list[:]
    ast_nodes = transformer.visit(tree)

    if not transformer.context_infos:
        save_kvc_to_file(
            func,
            'print("There was no KV context or rules, so this file will '
            'not be used and can be ignored - the original function has been '
            'returned instead. This statement should never be printed")')
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

    update_node = ASTRuleCtxNodePlaceholder()
    imports = ['from kivy.lang.compiler.kv_context import KVCtx as __KVCtx, '
               'KVRule as __KVRule']
    if compiler.used_canvas_rule:
        imports.append(
            'from kivy.lang.compiler.runtime import add_graphics_callback as '
            '__kv_add_graphics_callback')
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
    src_code = src_code + '\n'.join('    {}'.format(line) for line in deletion)
    src_code = re.sub('^ +$', '', src_code, flags=re.M)  # remove empty space
    src_code = re.sub('\n\n\n+', '\n\n', src_code)  # reduce newlines

    save_kvc_to_file(func, src_code)
    mod, f = load_kvc_from_file(func, func.__name__)
    f._kv_src_func_globals = func.__globals__
    return f


def KV_apply_manual(
        ctx, func, local_vars, global_vars, compiler_cls=KVCompiler,
        kv_syntax=None, proxy=False, rebind=True,
        exec_rules_after_binding=False):
    ctx_name = '__kv_ctx'
    compiler = compiler_cls()
    global_vars = global_vars.copy()
    global_vars.update(local_vars)
    global_vars[ctx_name] = ctx

    mod, f = load_kvc_from_file(func, '__kv_manual_wrapper', 'manual')

    if f is None:
        print('going the slow route')
        transformer = ParseKVBindTransformer()
        ctx.set_kv_binding_ast_transformer(transformer, kv_syntax)

        ctx.parse_rules()
        # these must happen *before* anything else and after all rules
        ctx.set_nodes_proxy(proxy)
        ctx.set_nodes_rebind(rebind)

        parts = compiler.generate_bindings(
            ctx, ctx_name, create_rules=False,
            exec_rules_after_binding=exec_rules_after_binding)
        lines = ('    {}'.format(line) if line else ''
                 for line in itertools.chain(*parts))
        globals_src = 'def update_globals(globals_vars):\n    globals_vars.' \
            'update(globals())\n    globals().update(globals_vars)\n\n'
        src = '{}def __kv_manual_wrapper():\n{}'.format(
            globals_src, '\n'.join(lines))

        save_kvc_to_file(func, src, 'manual')
        mod, f = load_kvc_from_file(func, '__kv_manual_wrapper', 'manual')

    mod.update_globals(global_vars)
    f()
