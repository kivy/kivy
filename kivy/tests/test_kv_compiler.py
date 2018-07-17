import re
import os
from os.path import exists, isfile
import inspect

from kivy.lang.compiler.kv_context import KVParserRule
from kivy.lang.compiler import KV_apply_manual, KV, KVCtx, KVRule
from kivy.lang.compiler.ast_parse import KVException, KVCompilerParserException
from kivy.lang.compiler.runtime import get_kvc_filename
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ObjectProperty, ListProperty, \
    DictProperty
from kivy.compat import PY2
from kivy.factory import Factory
from kivy.event import EventDispatcher
from kivy.lang import Builder

import unittest


skip_py2_decorator = unittest.skip('Does not support py2') if PY2 else \
    lambda x: x


def f_time(filename):
    return os.stat(filename).st_mtime


class TestBase(unittest.TestCase):

    def tearDown(self):
        import shutil
        p = os.path.join(os.path.dirname(__file__), '__kvcache__')
        if exists(p):
            shutil.rmtree(p)


class BaseWidget(Widget):

    value = NumericProperty(42)

    value2 = NumericProperty(7)

    value3 = NumericProperty(14)

    value_list = ListProperty([])

    value_dict = DictProperty({})


class SimpleWidget(BaseWidget):

    def simple_rule(self):
        with KVCtx():
            self.value @= self.width + 42

    def simple_rule2(self):
        with KVCtx():
            self.value @= self.width + 43

    def simple_rule3(self):
        with KVCtx():
            self.value @= self.width + 44

    def simple_rule4(self):
        with KVCtx():
            self.value @= self.width + 44


class SimpleWidget2(BaseWidget):

    def simple_rule4(self):
        with KVCtx():
            self.value @= self.width + 44


@skip_py2_decorator
class TestCompilationFilesAutoCompiler(TestBase):

    def tearDown(self):
        import shutil
        shutil.rmtree(os.path.join(
            os.path.dirname(__file__), '__kvcache__'))

    def test_func_vs_method(self):
        KV_f = KV()
        w = SimpleWidget()

        self.assertFalse(exists(get_kvc_filename(SimpleWidget.simple_rule)))
        self.assertFalse(exists(get_kvc_filename(w.simple_rule)))

        f_cls = KV_f(SimpleWidget.simple_rule)
        self.assertTrue(exists(get_kvc_filename(SimpleWidget.simple_rule)))
        t = f_time(get_kvc_filename(SimpleWidget.simple_rule))

        # file should not be recreated
        f = KV_f(w.simple_rule)
        self.assertTrue(exists(get_kvc_filename(w.simple_rule)))
        self.assertEqual(t, f_time(get_kvc_filename(w.simple_rule)))

    def test_single_compilation(self):
        KV_f = KV()
        w = SimpleWidget()
        w2 = SimpleWidget()

        self.assertFalse(exists(get_kvc_filename(w.simple_rule2)))
        f = KV_f(w.simple_rule2)
        self.assertTrue(exists(get_kvc_filename(w.simple_rule2)))
        t = f_time(get_kvc_filename(w.simple_rule2))

        f2 = KV_f(w.simple_rule2)
        self.assertIs(f, f2)
        self.assertEqual(t, f_time(get_kvc_filename(w.simple_rule2)))

        f2 = KV_f(w2.simple_rule2)
        self.assertEqual(f, f2)
        self.assertEqual(t, f_time(get_kvc_filename(w2.simple_rule2)))

    def test_func_uniqeness(self):
        KV_f = KV()

        self.assertFalse(exists(get_kvc_filename(SimpleWidget.simple_rule3)))
        f = KV_f(SimpleWidget.simple_rule3)
        self.assertTrue(exists(get_kvc_filename(SimpleWidget.simple_rule3)))

        self.assertFalse(exists(get_kvc_filename(SimpleWidget.simple_rule4)))
        f = KV_f(SimpleWidget.simple_rule4)
        self.assertTrue(exists(get_kvc_filename(SimpleWidget.simple_rule4)))

        self.assertFalse(exists(get_kvc_filename(SimpleWidget2.simple_rule4)))
        f = KV_f(SimpleWidget2.simple_rule4)
        self.assertTrue(exists(get_kvc_filename(SimpleWidget2.simple_rule4)))


rule_with_globals_duration = 198


class WidgetWithGlobals(BaseWidget):

    def rule_with_globals(self):
        with KVCtx():
            if 'rule_with_globals_duration1' in globals():
                val = globals()['rule_with_globals_duration1']
            else:
                val = rule_with_globals_duration

            self.value @= self.width + val


@skip_py2_decorator
class TestGlobalsAutoCompiler(TestBase):

    def test_global_capturing_and_modification(self):
        global rule_with_globals_duration
        KV_f = KV()
        f_static = KV_f(WidgetWithGlobals.rule_with_globals)

        w1 = WidgetWithGlobals()
        w2 = WidgetWithGlobals()
        w3 = WidgetWithGlobals()
        w4 = WidgetWithGlobals()

        f_static(w1)
        w1.width = 27
        self.assertEqual(w1.value, 27 + 198)
        w1.width = 33
        self.assertEqual(w1.value, 33 + 198)

        rule_with_globals_duration = 76

        self.assertEqual(w1.value, 33 + 198)
        w1.width = 55
        self.assertEqual(w1.value, 55 + 198)

        f_static(w2)
        w2.width = 27
        self.assertEqual(w2.value, 27 + 76)
        w2.width = 33
        self.assertEqual(w2.value, 33 + 76)

        rule_with_globals_duration = 125

        self.assertEqual(w2.value, 33 + 76)
        w2.width = 55
        self.assertEqual(w2.value, 55 + 76)

        globals()['rule_with_globals_duration1'] = 77

        f_static(w3)
        w3.width = 27
        self.assertEqual(w3.value, 27 + 77)
        w3.width = 33
        self.assertEqual(w3.value, 33 + 77)

        globals()['rule_with_globals_duration1'] = 79

        self.assertEqual(w3.value, 33 + 77)
        w3.width = 55
        self.assertEqual(w3.value, 55 + 77)

        del globals()['rule_with_globals_duration1']
        self.assertEqual(w3.value, 55 + 77)
        w3.width = 65
        self.assertEqual(w3.value, 65 + 77)

        f_static(w4)
        w4.width = 27
        self.assertEqual(w4.value, 27 + 125)
        w4.width = 33
        self.assertEqual(w4.value, 33 + 125)

        rule_with_globals_duration = 35

        self.assertEqual(w4.value, 33 + 125)
        w4.width = 98
        self.assertEqual(w4.value, 98 + 125)

    def test_function_name(self):
        KV_f = KV()
        f_static = KV_f(WidgetWithGlobals.rule_with_globals)

        self.assertEqual(
            f_static.__name__, WidgetWithGlobals.rule_with_globals.__name__)
        self.assertIn(
            WidgetWithGlobals.rule_with_globals.__qualname__,
            inspect.getfile(f_static))


class WidgetCapture(BaseWidget):

    widget = ObjectProperty(None)

    widget2 = ObjectProperty(None)

    widget3 = ObjectProperty(None)

    widget4 = ObjectProperty(None)

    def rule_with_capture_on_enter(self):
        self.widget = Widget()
        self.widget2 = Widget()
        self.widget3 = Widget()
        self.widget4 = Widget()
        self.widget.width = 10
        self.widget2.width = 20
        self.widget3.width = 30
        self.widget4.width = 40

        w = self.widget
        with KVCtx():
            w = self.widget2
            self.value @= w.width
            w = self.widget3
        w = self.widget4

    def rule_with_capture_on_exit(self):
        self.widget = Widget()
        self.widget2 = Widget()
        self.widget3 = Widget()
        self.widget4 = Widget()
        self.widget.width = 10
        self.widget2.width = 20
        self.widget3.width = 30
        self.widget4.width = 40

        w = self.widget
        with KVCtx():
            w = self.widget2
            self.value @= w.width
            w = self.widget3
        w = self.widget4

    def rule_with_capture_on_enter_not_exist(self):
        self.widget = Widget()

        with KVCtx():
            w = self.widget
            self.value @= w.width

    def rule_with_capture_on_exit_not_exist(self):
        self.widget = Widget()

        with KVCtx():
            w = self.widget
            self.value @= w.width
            del w


@skip_py2_decorator
class TestCaptureAutoCompiler(TestBase):

    def test_capture_on_enter(self):
        KV_f = KV(bind_on_enter=True)
        f_static = KV_f(WidgetCapture.rule_with_capture_on_enter)

        w = WidgetCapture()
        f_static(w)
        self.assertEqual(w.value, 20)
        w.widget2.width = 35
        self.assertEqual(w.value, 20)
        w.widget3.width = 44
        self.assertEqual(w.value, 20)
        w.widget4.width = 66
        self.assertEqual(w.value, 20)
        w.widget.width = 76
        self.assertEqual(w.value, 76)

    def test_capture_on_exit(self):
        KV_f = KV(bind_on_enter=False)
        f_static = KV_f(WidgetCapture.rule_with_capture_on_exit)

        w = WidgetCapture()
        f_static(w)
        self.assertEqual(w.value, 20)
        w.widget2.width = 35
        self.assertEqual(w.value, 20)
        w.widget4.width = 66
        self.assertEqual(w.value, 20)
        w.widget.width = 76
        self.assertEqual(w.value, 20)
        w.widget3.width = 44
        self.assertEqual(w.value, 44)

    def test_capture_on_enter_not_exist(self):
        KV_f = KV(bind_on_enter=True)
        f_static = KV_f(WidgetCapture.rule_with_capture_on_enter_not_exist)

        w = WidgetCapture()
        with self.assertRaises(UnboundLocalError):
            f_static(w)

    def test_capture_on_exit_not_exist(self):
        KV_f = KV(bind_on_enter=True)
        f_static = KV_f(WidgetCapture.rule_with_capture_on_exit_not_exist)

        w = WidgetCapture()
        with self.assertRaises(UnboundLocalError):
            f_static(w)

        # test x += y capture
        # capture x.y @= ... for x
        # read only x = x.y, should crash
        # read only no rules in nested ctx
        # recursive ctx


class CtxWidget(BaseWidget):
    def no_ctx(self):
        self.value = 55

    def no_bind_rule_without_ctx(self):
        self.value @= 55

    def bind_rule_without_ctx(self):
        self.value @= self.width

    def canvas_no_bind_rule_without_ctx(self):
        self.value ^= 55

    def bind_canvas_rule_without_ctx(self):
        self.value ^= self.width


@skip_py2_decorator
class TestCtxAutoCompiler(TestBase):

    def test_no_ctx_no_rule(self):
        KV_f = KV()

        w = CtxWidget()
        self.assertEqual(w.value, 42)
        KV_f(w.no_ctx)()
        self.assertEqual(w.value, 55)

    def test_no_ctx_with_rule(self):
        KV_f = KV()

        with self.assertRaises(KVCompilerParserException):
            KV_f(CtxWidget.no_bind_rule_without_ctx)
        with self.assertRaises(KVCompilerParserException):
            KV_f(CtxWidget.bind_rule_without_ctx)
        with self.assertRaises(KVCompilerParserException):
            KV_f(CtxWidget.canvas_no_bind_rule_without_ctx)
        with self.assertRaises(KVCompilerParserException):
            KV_f(CtxWidget.bind_canvas_rule_without_ctx)
