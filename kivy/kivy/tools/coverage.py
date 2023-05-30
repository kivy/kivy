"""Kivy coverage plugin
=======================

This provides a coverage plugin to measure code execution in kv files. To use,
create and add::

    [run]
    plugins =
        kivy.tools.coverage

to the ``.coveragerc`` file in the root of your project. Or::

    [coverage:run]
    plugins =
        kivy.tools.coverage

in ``setup.cfg``.

Then you can test your project with e.g. ``pip install coverage`` followed by
``coverage run --source=./ kivy_app.py`` and ``coverage report``.

Or to use with pytest, ``pip install pytest-cov`` followed by something like
``pytest --cov=./ .``

TODO: Expand kv statements measured.

Currently, it ignores rules such as Widget creation or graphics object
creation from being measured. Similarly for import statements.

KV code created as strings within a python file is also not measured. To
support the above, deeper changes will be required.
"""

import os
import coverage
from kivy.lang.parser import Parser


class CoverageKVParser(Parser):

    def execute_directives(self):
        # don't actually execute anything
        pass

    def get_coverage_lines(self):
        lines = set()
        for parser_prop in walk_parser(self):
            for line_num, line in enumerate(
                    parser_prop.value.splitlines(),
                    start=parser_prop.line + 1):
                if line.strip():
                    lines.add(line_num)

        return lines


def walk_parser_rules(parser_rule):
    yield parser_rule

    for child in parser_rule.children:
        for rule in walk_parser_rules(child):
            yield rule

    if parser_rule.canvas_before is not None:
        for rule in walk_parser_rules(parser_rule.canvas_before):
            yield rule
        yield parser_rule.canvas_before
    if parser_rule.canvas_root is not None:
        for rule in walk_parser_rules(parser_rule.canvas_root):
            yield rule
    if parser_rule.canvas_after is not None:
        for rule in walk_parser_rules(parser_rule.canvas_after):
            yield rule


def walk_parser_rules_properties(parser_rule):
    for rule in parser_rule.properties.values():
        yield rule
    for rule in parser_rule.handlers:
        yield rule


def walk_parser(parser):
    if parser.root is not None:
        for rule in walk_parser_rules(parser.root):
            for prop in walk_parser_rules_properties(rule):
                yield prop

    for _, cls_rule in parser.rules:
        for rule in walk_parser_rules(cls_rule):
            for prop in walk_parser_rules_properties(rule):
                yield prop


class KivyCoveragePlugin(coverage.plugin.CoveragePlugin):

    def file_tracer(self, filename):
        if filename.endswith('.kv'):
            return KivyFileTracer(filename=filename)
        return None

    def file_reporter(self, filename):
        return KivyFileReporter(filename=filename)

    def find_executable_files(self, src_dir):
        for (dirpath, dirnames, filenames) in os.walk(src_dir):
            for filename in filenames:
                if filename.endswith('.kv'):
                    yield os.path.join(dirpath, filename)


class KivyFileTracer(coverage.plugin.FileTracer):

    filename = ''

    def __init__(self, filename, **kwargs):
        super(KivyFileTracer, self).__init__(**kwargs)
        self.filename = filename

    def source_filename(self):
        return self.filename


class KivyFileReporter(coverage.plugin.FileReporter):

    def lines(self):
        with open(self.filename) as fh:
            source = fh.read()

        parser = CoverageKVParser(content=source, filename=self.filename)
        return parser.get_coverage_lines()


def coverage_init(reg, options):
    reg.add_file_tracer(KivyCoveragePlugin())
