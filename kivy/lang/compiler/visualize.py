from kivy.lang.compiler.ast_parse import ParseKVBindTransformer, BindSubGraph
from kivy.lang.compiler.kv_context import KVParserCtx, KVParserRule
from kivy.lang.compiler.utils import StringPool
import ast
try:
    from graphviz import Digraph
except ImportError:
    Digraph = None


class VisualizeBindTree(object):

    transformer = None

    ctx = None

    subgraphs = []

    def __init__(self):
        super(VisualizeBindTree, self).__init__()
        self.ctx = KVParserCtx()
        if Digraph is None:
            raise ValueError(
                'graphviz could not be imported. Please make sure it is '
                'installed and the binaries are on the PATH')

    def add_rule(self, *binds, name):
        self.ctx.add_rule(KVParserRule(*binds, name=name))

    def parse_rules(self, kv_syntax='minimal', proxy=False, rebind=True):
        self.transformer = transformer = ParseKVBindTransformer(kv_syntax)
        self.ctx.set_kv_binding_ast_transformer(transformer)
        self.ctx.parse_rules()
        self.ctx.set_nodes_proxy(proxy)
        self.ctx.set_nodes_rebind(rebind)

        self.subgraphs = BindSubGraph.get_ordered_subgraphs(transformer)
        BindSubGraph.populate_bind_store_size_indices_and_callback_names(
            self.subgraphs, True, self.ctx.rules, transformer,
            StringPool(prefix='RCB'), StringPool(prefix='LCB'))

    def repr_node(self, ref_node):
        node = ref_node.ref_node
        node_fields = zip(
            node._fields, (getattr(node, attr) for attr in node._fields))

        field_results = []
        if isinstance(node, ast.BinOp):
            field_results.append(node.op.__class__.__name__)
        elif isinstance(node, ast.unaryop):
            field_results.append(node.__class__.__name__)
        else:
            for field_name, field_value in node_fields:
                if isinstance(field_value, ast.AST):
                    continue

                elif isinstance(field_value, list):
                    assert False
                elif isinstance(field_value, str):
                    field_results.append('{}'.format(field_value))
                elif isinstance(field_value, (int, float)):
                    field_results.append(str(field_value))

                elif field_value is not None:
                    assert False
                    # field_results.append(str(field_value))
                else:
                    raise Exception

        if not field_results:
            desc = node.__class__.__name__
        else:
            desc = ','.join(field_results)

        assert ref_node.leaf_rule is not None or \
            ref_node.rebind == bool(ref_node.callback_names)

        cbs = ', '.join(ref_node.callback_names)
        proxy = ' *P' if ref_node.proxy else ''
        cbs = ' {{{}{}}}'.format(cbs, proxy) if (cbs + proxy) else ''

        name = ' {}'.format(ref_node.leaf_rule.name) if \
            ref_node.leaf_rule else ''

        s = '{} ({}){}{}'.format(desc, ref_node.count, cbs, name)
        return s

    def add_nodes_to_viz_graph(self, graph_viz, nodes, color=None):
        nodes = list(nodes)
        node_names = {}
        for node in nodes:
            node_names[node] = vis.repr_node(node)

        for node in nodes:
            if not node.depends:
                graph_viz.attr(
                    'node', shape='Mdiamond', color=color or 'chartreuse1',
                    style='filled')
                graph_viz.node(str(id(node)), label=node_names[node])
            else:
                if not node.depends_on_me:
                    graph_viz.attr(
                        'node', shape='doubleoctagon',
                        color=color or 'aquamarine', style='filled')
                else:
                    graph_viz.attr(
                        'node', shape='box', color=color or 'antiquewhite2',
                        style='filled')
                graph_viz.node(str(id(node)), label=node_names[node])

    def add_edges_to_viz_graph(self, graph_viz, nodes):
        for node in nodes:
            for parent in node.depends:
                graph_viz.edge(str(id(parent)), str(id(node)))

    def get_all_nodes(self):
        return list(
            node for rule in self.transformer.nodes_by_rule for node in rule)

    def split_subgraph_and_children_nodes(self, subgraph):
        subgraph_nodes = set()
        root_nodes = set(n for n in subgraph.nodes if n.rebind)
        for item in subgraph.get_subgraph_and_children_subgraphs():
            subgraph_nodes.update(
                n for n in item.nodes if not n.rebind and n.depends)
            subgraph_nodes.update(item.terminal_nodes)

        remaining_nodes = [
            n for n in self.get_all_nodes()
            if n not in subgraph_nodes and n not in root_nodes]

        return list(subgraph_nodes), list(root_nodes), \
            remaining_nodes

    def get_visualize_all_subgraphs_and_children(self, name):
        visuals = []
        nodes = self.get_all_nodes()
        for i, subgraph in enumerate(self.subgraphs):
            if not subgraph.n_rebind_deps:
                continue

            subgraph_nodes, root_nodes, remaining_nodes = \
                self.split_subgraph_and_children_nodes(subgraph)
            f = Digraph(name='{}_{}'.format(name, i))

            with f.subgraph(name='cluster_0') as c:
                self.add_nodes_to_viz_graph(c, subgraph_nodes)
            self.add_nodes_to_viz_graph(f, root_nodes, color='darkorange1')

            self.add_nodes_to_viz_graph(f, remaining_nodes)
            self.add_edges_to_viz_graph(f, nodes)

            visuals.append(f)

        return visuals

    def get_visualize_bind_graph(self, name):
        nodes = self.get_all_nodes()
        f = Digraph(name)

        self.add_nodes_to_viz_graph(f, nodes)
        self.add_edges_to_viz_graph(f, nodes)
        return f

    def get_visualize_all_unique_subgraphs(self, name):
        visuals = []
        nodes = self.get_all_nodes()
        for i, subgraph in enumerate(self.subgraphs):
            f = Digraph(name='{}_{}'.format(name, i))

            subgraph_all_nodes = set(subgraph.nodes)
            subgraph_all_nodes.update(subgraph.terminal_nodes)

            with f.subgraph(name='cluster_0') as c:
                self.add_nodes_to_viz_graph(
                    c, subgraph.terminal_nodes, color='violet')
                self.add_nodes_to_viz_graph(
                    c,
                    (n for n in subgraph.nodes if n.rebind or not n.depends),
                    color='darkorange1')
                self.add_nodes_to_viz_graph(
                    c,
                    (n for n in subgraph.nodes if not n.rebind and n.depends))

            self.add_nodes_to_viz_graph(
                f, (n for n in nodes if n not in subgraph_all_nodes))
            self.add_edges_to_viz_graph(f, nodes)

            visuals.append(f)

        return visuals


if __name__ == '__main__':
    vis = VisualizeBindTree()

    vis.add_rule('(self.x + self.y + 55).z + 29 + self.x', name='r1')
    vis.add_rule(
        'other.x[other.x + 86 + other.x.m.z].z + other.x.q', name='r2')
    vis.add_rule('(that.x + that.y).z', name='r3')
    vis.add_rule('(that.x + that.q).z', name='r4')

    vis.parse_rules(kv_syntax=None)

    vis.get_visualize_bind_graph('bind').view(cleanup=True)
    for item in vis.get_visualize_all_subgraphs_and_children('bind'):
        item.view(cleanup=True)
    for item in vis.get_visualize_all_unique_subgraphs('bind'):
        item.view(cleanup=True)
