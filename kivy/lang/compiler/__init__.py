import textwrap
import itertools
import inspect
import re
import ast

from kivy.lang.compiler.src_gen import KVCompiler
from kivy.lang.compiler.ast_parse import ParseKVFunctionTransformer, ParseKVBindTransformer, generate_source, KVCompilerParserException
from kivy.lang.compiler.kv_context import KVCtx, KVRule
from kivy.lang.compiler.runtime import load_kvc_from_file, save_kvc_to_file

_space_match = re.compile('^ +$')


def KV(func, kv_syntax=None, proxy=False, rebind=True, compiler_cls=KVCompiler,
       transformer_cls=ParseKVFunctionTransformer, bind_on_enter=True):
    mod, f = load_kvc_from_file(func, func.__name__)  # no lambda
    if f is not None:
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
    for ctx_info in transformer.context_infos:
        ctx = ctx_info['ctx']
        ctx.parse_rules()
        # these must happen *before* anything else and after all rules
        ctx.set_nodes_proxy(proxy)
        ctx.set_nodes_rebind(rebind)

        ctx_name, funcs, binds = compiler.generate_bindings(ctx, None, True)
        ctx_info['assign_target_node'].id = ctx_name

        node = ctx_info['before_ctx' if bind_on_enter else 'after_ctx']
        node.src_lines = funcs + binds

    compiled = 'from kivy.lang.compiler.kv_context import KVCtx as __KVCtx, ' \
               'KVRule as __KVRule\n\n\n'
    compiled += generate_source(ast_nodes)

    save_kvc_to_file(func, compiled)
    mod, f = load_kvc_from_file(func, func.__name__)
    return f


def KV_apply_manual(
        ctx, compiler, func, local_vars, global_vars, proxy=False, rebind=True,
        kv_syntax=None):
    ctx_name = '__kv_ctx'
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

        parts = compiler.generate_bindings(ctx, ctx_name, False)
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
