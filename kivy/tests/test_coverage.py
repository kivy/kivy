import pytest
import os
try:
    import coverage
except ImportError:
    pytestmark = pytest.mark.skip("coverage not available")


kv_statement_lines = {4, 5, 6, 8, 9, 12, 15, 17}


def test_coverage_base():
    from kivy.lang.builder import Builder
    cov = coverage.Coverage(source=[os.path.dirname(__file__)])
    cov.start()

    fname = os.path.join(os.path.dirname(__file__), 'coverage_lang.kv')
    try:
        widget = Builder.load_file(fname)
    finally:
        cov.stop()

    Builder.unload_file(fname)
    _, statements, missing, _ = cov.analysis(fname)
    assert set(statements) == kv_statement_lines
    assert set(missing) == {4, 8, 9}


def test_coverage_multiline_on_event():
    from kivy.lang.builder import Builder
    cov = coverage.Coverage(source=[os.path.dirname(__file__)])
    cov.start()

    fname = os.path.join(os.path.dirname(__file__), 'coverage_lang.kv')
    try:
        widget = Builder.load_file(fname)
        widget.children[0].y = 65
    finally:
        cov.stop()

    Builder.unload_file(fname)
    _, statements, missing, _ = cov.analysis(fname)
    assert set(statements) == kv_statement_lines
    assert set(missing) == {4, }


def test_coverage_trigger_event():
    from kivy.lang.builder import Builder
    cov = coverage.Coverage(source=[os.path.dirname(__file__)])
    cov.start()

    fname = os.path.join(os.path.dirname(__file__), 'coverage_lang.kv')
    try:
        widget = Builder.load_file(fname)
        widget.children[0].x = 65
        widget.children[0].width = 97
    finally:
        cov.stop()

    Builder.unload_file(fname)
    _, statements, missing, _ = cov.analysis(fname)
    assert set(statements) == kv_statement_lines
    assert set(missing) == {8, 9}


def test_coverage_trigger_all():
    from kivy.lang.builder import Builder
    cov = coverage.Coverage(source=[os.path.dirname(__file__)])
    cov.start()

    fname = os.path.join(os.path.dirname(__file__), 'coverage_lang.kv')
    try:
        widget = Builder.load_file(fname)
        widget.children[0].x = 65
        widget.children[0].width = 97
        widget.children[0].y = 65
    finally:
        cov.stop()

    Builder.unload_file(fname)
    _, statements, missing, _ = cov.analysis(fname)
    assert set(statements) == kv_statement_lines
    assert set(missing) == set()
