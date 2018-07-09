import textwrap
import itertools
import inspect

from kivy.lang.compiler.src_gen import KVCompiler
from kivy.lang.compiler.kv_context import KVCtx, KVRule
from kivy.lang.compiler.runtime import load_kvc_from_file, save_kvc_to_file


def KV(function):
    paprams = list(inspect.signature(function).parameters)
    if not paprams:
        raise ValueError('Function must accept a context parameter')
    return function


def KV_apply_manual(
        ctx, compiler, func, local_vars, global_vars, proxy=False, rebind=True):
    ctx_name = '__kv_ctx'
    global_vars = global_vars.copy()
    global_vars.update(local_vars)
    global_vars[ctx_name] = ctx
    mod, f = load_kvc_from_file(func, '__kv_manual_wrapper', 'manual')

    if f is None:
        print('going the slow route')
        ctx.parse_rules()
        # these must happen *before* anything else and after all rules
        ctx.set_nodes_proxy(proxy)
        ctx.set_nodes_rebind(rebind)

        parts = compiler.generate_bindings(ctx, ctx_name)
        globals_src = 'def update_globals(globals_vars):\n    globals_vars.' \
            'update(globals())\n    globals().update(globals_vars)\n\n'
        src = '{}def __kv_manual_wrapper():\n    {}'.format(
            globals_src, '\n    '.join(itertools.chain(*parts)))
        save_kvc_to_file(func, src, 'manual')
        mod, f = load_kvc_from_file(func, '__kv_manual_wrapper', 'manual')

    mod.update_globals(global_vars)
    f()
