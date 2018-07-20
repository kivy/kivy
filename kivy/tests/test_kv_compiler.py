# capture x.y @= ... for x
# read only x = x.y, should crash
# read only no rules in nested ctx
# rule within rule
# deep nested ctx
# rebind
# rule/ctx order
# objects that are None in rule
# bind mutliple of same object in rule

# TODO: add tests for async def, like do_def, once py2 support is dropped
# we must remove pycache b/c https://bugs.python.org/issue31772

import re
import time
import os
from os.path import exists, isfile
import inspect
import gc
import shutil

from kivy.lang.compiler.kv_context import KVParserRule
from kivy.lang.compiler import KV_apply_manual, KV, KVCtx, KVRule
from kivy.lang.compiler.ast_parse import KVException, KVCompilerParserException
from kivy.lang.compiler.runtime import get_kvc_filename, \
    process_graphics_callbacks
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ObjectProperty, ListProperty, \
    DictProperty
from kivy.tests.common import skip_py2_decorator

import unittest

delete_kvc_after_test = int(os.environ.get('KIVY_TEST_DELETE_KVC', 1))


def f_time(filename):
    return os.stat(filename).st_mtime


def remove_kvc(func, flags=''):
    fname = get_kvc_filename(func, flags=flags)
    if exists(fname):
        os.remove(fname)

    d = os.path.join(os.path.dirname(fname), '__pycache__')
    if exists(d):
        for f in os.listdir(d):
            file_path = os.path.join(d, f)
            if os.path.isfile(file_path):
                os.unlink(file_path)


class TestBase(unittest.TestCase):

    def tearDown(self):
        import shutil
        p = os.path.join(os.path.dirname(__file__), '__kvcache__')
        if delete_kvc_after_test and exists(p):
            shutil.rmtree(p)


class BaseWidget(Widget):

    value = NumericProperty(42)

    value2 = NumericProperty(7)

    value3 = NumericProperty(14)

    value_list = ListProperty([])

    value_dict = DictProperty({})

    widget = ObjectProperty(None)

    widget2 = ObjectProperty(None)

    widget3 = ObjectProperty(None)

    widget4 = ObjectProperty(None)


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

    def simple_rule5(self):
        with KVCtx():
            self.value @= self.width + 44


class SimpleWidget2(BaseWidget):

    def simple_rule4(self):
        with KVCtx():
            self.value @= self.width + 44


@skip_py2_decorator
class TestCompilationFilesAutoCompiler(TestBase):

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

    def test_compile_flags_compilation(self):
        KV_f = KV(proxy=False)
        self.assertFalse(exists(get_kvc_filename(SimpleWidget.simple_rule5)))
        f = KV_f(SimpleWidget.simple_rule5)
        self.assertTrue(exists(get_kvc_filename(SimpleWidget.simple_rule5)))
        t = f_time(get_kvc_filename(SimpleWidget.simple_rule5))

        f2 = KV_f(SimpleWidget.simple_rule5)
        self.assertIs(f, f2)
        self.assertEqual(
            t, f_time(get_kvc_filename(SimpleWidget.simple_rule5)))

        KV_f = KV(proxy=True)
        f3 = KV_f(SimpleWidget.simple_rule5)
        self.assertNotEqual(f3, f2)
        self.assertGreater(
            f_time(get_kvc_filename(SimpleWidget.simple_rule5)), t)

    def test_flags_compilation(self):
        # test manual vs auto compilation
        pass

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

    def enter_not_exist(self):
        self.widget = Widget()

        with KVCtx():
            w = self.widget
            self.value @= w.width

    def exit_not_exist(self):
        self.widget = Widget()

        with KVCtx():
            w = self.widget
            self.value @= w.width
            del w

    def enter_var_overwrite(self):
        w = Widget()
        with KVCtx():
            w = self.widget
            self.value @= w.width

    def enter_var_overwrite2(self):
        w = Widget()
        with KVCtx():
            self.value @= w.width
            w = self.widget

    def enter_var_overwrite3(self):
        w = Widget()
        with KVCtx():
            self.value @= w.width
        w = self.widget

    def enter_var_overwrite4(self):
        w = Widget()
        with KVCtx():
            w = self.widget
            q = w
            self.value @= q.width

    def enter_var_overwrite5(self):
        w = Widget()
        with KVCtx():
            w = self.widget
            with KVRule():
                q = w
                q = None or w
                self.value @= q.width

    def enter_var_overwrite_005(self):
        self.widget = w = Widget()
        with KVCtx():
            with KVRule():
                q = w
                q = None or w
                self.value @= q.width

    def enter_var_overwrite6(self):
        w = Widget()
        with KVCtx():
            q = 55
            self.value @= w.width + q

    def enter_var_overwrite7(self):
        self.widget = w = Widget()
        q = 55
        with KVCtx():
            q = 12
            self.value @= w.width + q

    def enter_var_overwrite8(self):
        self.widget = w = Widget()
        q = 55
        with KVCtx():
            with KVRule():
                q = 12
                self.value @= w.width + q

    def enter_var_overwrite9(self):
        self.widget = w = Widget()
        self.widget2 = w2 = Widget()
        q = 55
        with KVCtx():
            with KVRule(w2.width):
                w2 = Widget()
                self.value @= w.width + q

    def enter_var_overwrite_009(self):
        self.widget = w = Widget()
        w2 = Widget()
        q = 55
        with KVCtx():
            w2 = Widget()
            with KVRule(w2.width):
                w2 = Widget()
                self.value @= w.width + q

    def enter_var_overwrite_009_1(self):
        self.widget = w = Widget()
        w2 = Widget()
        q = 55
        with KVCtx():
            w2 = Widget()
            with KVRule(w2.width):
                w2 = Widget()
                x = w2
                self.value @= w.width + q

    def enter_var_overwrite_009_2(self):
        self.widget = w = Widget()
        w2 = Widget()
        q = 55
        with KVCtx():
            w2 = Widget()
            with KVRule(w2.width):
                x = w2
                self.value @= w.width + q

    def enter_var_overwrite10(self):
        self.widget = w = Widget()
        with KVCtx():
            with KVRule(w.width):
                self.widget2 = w = Widget()

    def enter_var_overwrite_010(self):
        self.widget = w = Widget()
        with KVCtx():
            with KVRule(w.width):
                self.widget3 = w
                self.widget2 = w = Widget()

    def enter_var_overwrite11(self):
        self.widget = w = Widget()
        q = 55
        with KVCtx():
            self.value @= w.width + q
            q = 27

    def enter_var_overwrite12(self):
        w = Widget()
        q = 55
        with KVCtx():
            q = 12
            with KVRule(w.width):
                q += 55

    def enter_var_overwrite13(self):
        w = Widget()
        q = 55
        with KVCtx():
            with KVRule(w.width):
                q += 55
                q = 12

    def enter_var_overwrite14(self):
        w = Widget()
        q = 55
        with KVCtx():
            with KVRule(w.width):
                q += 55
            q = 12

    def enter_var_overwrite15(self):
        self.widget = w = Widget()
        q = 55
        with KVCtx():
            with KVRule(w.width):
                q += 22
                self.value = q

    def enter_var_overwrite16(self):
        self.widget = Widget()
        self.widget2 = Widget()
        self.widget3 = Widget()
        q = 54
        e = 34
        r = 78
        with KVCtx():
            self.value @= self.widget.height + q
            with KVCtx():
                r = 90
                self.value @= self.widget2.height + e
            self.value @= self.widget3.height + r

    def enter_var_overwrite17(self):
        self.widget = Widget()
        self.widget2 = Widget()
        self.widget3 = Widget()
        q = 54
        e = 34
        r = 78
        with KVCtx():
            self.value @= self.widget.height + q
            r = 90
            with KVCtx():
                self.value @= self.widget2.height + e
            self.value @= self.widget3.height + r

    def enter_var_overwrite18(self):
        self.widget = Widget()
        self.widget2 = Widget()
        self.widget3 = Widget()
        self.widget.height = 98
        self.widget2.height = 65
        self.widget3.height = 12
        q = 54
        e = 34
        r = 78
        with KVCtx():
            self.value @= self.widget.height + q
            with KVCtx():
                self.value @= self.widget2.height + e
            e = 90
            self.value @= self.widget3.height + r

    def rule_with_capture_lambda(self):
        self.widget = Widget()

        with KVCtx():
            self.value @= self.widget.width + (lambda x: lambda y: 44)(12)(27)

    def rule_with_capture_list_comp(self):
        self.widget = Widget()

        with KVCtx():
            self.value @= self.widget.width + [
                [x for z in [1]][0] for x in range(10)
                for q in range(1) if True][3]

    def rule_with_capture_set_comp(self):
        self.widget = Widget()

        with KVCtx():
            self.value @= self.widget.width + list(
                {[x for z in [1]][0] * 0 for x in range(10)
                 for q in range(1) if True})[0]

    def rule_with_capture_gen_comp(self):
        self.widget = Widget()

        with KVCtx():
            self.value @= self.widget.width + list(
                [x for z in [1]][0] for x in range(10)
                for q in range(1) if True)[3]

    def rule_with_capture_dict_comp(self):
        self.widget = Widget()

        with KVCtx():
            self.value @= self.widget.width + {
                [x for z in [1]][0]: [x for z in [1]][0]
                for x in range(10) for q in range(1) if True}[3]

    def do_exception_handler(self):
        # comprehensions
        self.widget = Widget()
        with KVCtx():
            try:
                pass
            except Exception as e:
                pass
            self.width @= self.widget.width + len(str(e))


@skip_py2_decorator
class TestCaptureAutoCompiler(TestBase):

    def get_KV(self, bind_on_enter=True, **kwargs):
        KV_f_ro = KV(
            captures_are_readonly=True, bind_on_enter=bind_on_enter,
            **kwargs)
        KV_f = KV(
            captures_are_readonly=False, bind_on_enter=bind_on_enter,
            **kwargs)
        return KV_f_ro, KV_f

    def test_capture_on_enter(self):
        KV_f = KV(bind_on_enter=True, captures_are_readonly=False)
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
        KV_f = KV(bind_on_enter=False, captures_are_readonly=False)
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
        KV_f = KV(bind_on_enter=True, captures_are_readonly=False)
        f_static = KV_f(WidgetCapture.rule_with_capture_on_enter_not_exist)

        w = WidgetCapture()
        with self.assertRaises(UnboundLocalError):
            f_static(w)

    def test_capture_on_exit_not_exist(self):
        KV_f = KV(bind_on_enter=True, captures_are_readonly=False)
        f_static = KV_f(WidgetCapture.rule_with_capture_on_exit_not_exist)

        w = WidgetCapture()
        with self.assertRaises(UnboundLocalError):
            f_static(w)

    def test_enter_not_exists(self):
        KV_f_ro, KV_f = self.get_KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.enter_not_exist)

        remove_kvc(WidgetCapture.enter_not_exist)
        KV_f(WidgetCapture.enter_not_exist)

    def test_enter_overwrite_before_rule(self):
        KV_f_ro, KV_f = self.get_KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.enter_var_overwrite)

        remove_kvc(WidgetCapture.enter_var_overwrite)
        KV_f(WidgetCapture.enter_var_overwrite)

    def test_enter_overwrite_after_rule(self):
        KV_f_ro, KV_f = self.get_KV()
        KV_f_ro(WidgetCapture.enter_var_overwrite2)
        remove_kvc(WidgetCapture.enter_var_overwrite2)
        KV_f(WidgetCapture.enter_var_overwrite2)

    def test_enter_overwrite_after_ctx(self):
        KV_f_ro, KV_f = self.get_KV()
        KV_f_ro(WidgetCapture.enter_var_overwrite3)
        remove_kvc(WidgetCapture.enter_var_overwrite3)
        KV_f(WidgetCapture.enter_var_overwrite3)

    def test_enter_overwrite_before_rule_indirect(self):
        KV_f_ro, KV_f = self.get_KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.enter_var_overwrite4)
        remove_kvc(WidgetCapture.enter_var_overwrite4)
        f = KV_f(WidgetCapture.enter_var_overwrite4)
        w = WidgetCapture()
        with self.assertRaises(UnboundLocalError):
            f(w)

    def test_enter_overwrite_before_rule_indirect_explicit_rule(self):
        KV_f_ro, KV_f = self.get_KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.enter_var_overwrite5)
        remove_kvc(WidgetCapture.enter_var_overwrite5)
        f = KV_f(WidgetCapture.enter_var_overwrite5)
        w = WidgetCapture()
        with self.assertRaises(UnboundLocalError):
            f(w)

    def test_enter_indirect_explicit_rule(self):
        KV_f_ro, KV_f = self.get_KV()
        f = KV_f_ro(WidgetCapture.enter_var_overwrite_005)
        w = WidgetCapture()
        with self.assertRaises(UnboundLocalError):
            f(w)

        remove_kvc(WidgetCapture.enter_var_overwrite_005)
        f = KV_f(WidgetCapture.enter_var_overwrite_005)
        w = WidgetCapture()
        with self.assertRaises(UnboundLocalError):
            f(w)

    def test_enter_overwrite_in_ctx_not_defined(self):
        KV_f_ro, KV_f = self.get_KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.enter_var_overwrite6)
        remove_kvc(WidgetCapture.enter_var_overwrite6)
        f = KV_f(WidgetCapture.enter_var_overwrite6)
        w = WidgetCapture()
        with self.assertRaises(UnboundLocalError):
            f(w)

    def test_enter_overwrite_in_ctx_defined(self):
        KV_f_ro, KV_f = self.get_KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.enter_var_overwrite7)
        remove_kvc(WidgetCapture.enter_var_overwrite7)
        f = KV_f(WidgetCapture.enter_var_overwrite7)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget.width + 12)
        w.widget.width = 33
        self.assertEqual(w.value, w.widget.width + 55)

    def test_enter_overwrite_in_rule_explicit_rule_defined(self):
        KV_f_ro, KV_f = self.get_KV()
        f = KV_f_ro(WidgetCapture.enter_var_overwrite8)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget.width + 12)
        w.widget.width = 33
        self.assertEqual(w.value, w.widget.width + 12)

        remove_kvc(WidgetCapture.enter_var_overwrite8)
        f = KV_f(WidgetCapture.enter_var_overwrite8)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget.width + 12)
        w.widget.width = 33
        self.assertEqual(w.value, w.widget.width + 12)

    def test_enter_overwrite_in_rule_explicit_bind(self):
        KV_f_ro, KV_f = self.get_KV()
        f = KV_f_ro(WidgetCapture.enter_var_overwrite9)
        remove_kvc(WidgetCapture.enter_var_overwrite9)
        f = KV_f(WidgetCapture.enter_var_overwrite9)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget.width + 55)
        w.widget.width = 77
        self.assertEqual(w.value, w.widget.width + 55)

        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget.width + 55)
        w.widget.width = 77
        self.assertEqual(w.value, w.widget.width + 55)

    def test_enter_overwrite_before_rule_explicit_bind(self):
        KV_f_ro, KV_f = self.get_KV()
        f = KV_f_ro(WidgetCapture.enter_var_overwrite_009)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget.width + 55)
        w.widget.width = 77
        self.assertEqual(w.value, w.widget.width + 55)

        remove_kvc(WidgetCapture.enter_var_overwrite_009)
        f = KV_f(WidgetCapture.enter_var_overwrite_009)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget.width + 55)
        w.widget.width = 77
        self.assertEqual(w.value, w.widget.width + 55)

    def test_enter_overwrite_before_rule_explicit_bind_not_captured(self):
        KV_f_ro, KV_f = self.get_KV()
        f = KV_f_ro(WidgetCapture.enter_var_overwrite_009_1)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget.width + 55)
        w.widget.width = 77
        self.assertEqual(w.value, w.widget.width + 55)

    def test_enter_overwrite_before_rule_explicit_bind_captured(self):
        KV_f_ro, KV_f = self.get_KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.enter_var_overwrite_009_2)

    def test_enter_overwrite_in_rule_explicit_bind2(self):
        KV_f_ro, KV_f = self.get_KV()
        f = KV_f_ro(WidgetCapture.enter_var_overwrite10)
        w = WidgetCapture()
        f(w)
        self.assertIsNot(w.widget, w.widget2)
        w2 = w.widget2
        w.widget.width = 77
        self.assertIsNot(w.widget2, w2)

        remove_kvc(WidgetCapture.enter_var_overwrite10)
        f = KV_f(WidgetCapture.enter_var_overwrite10)
        w = WidgetCapture()
        f(w)
        self.assertIsNot(w.widget, w.widget2)
        w2 = w.widget2
        w.widget.width = 77
        self.assertIsNot(w.widget2, w2)

    def test_enter_overwrite_in_rule_explicit_bind_captured(self):
        KV_f_ro, KV_f = self.get_KV()
        f = KV_f_ro(WidgetCapture.enter_var_overwrite_010)
        w = WidgetCapture()
        f(w)
        self.assertIsNot(w.widget, w.widget2)
        self.assertIs(w.widget, w.widget3)
        w2 = w.widget2
        w.widget.width = 77
        self.assertIsNot(w.widget2, w2)

        remove_kvc(WidgetCapture.enter_var_overwrite_010)
        f = KV_f(WidgetCapture.enter_var_overwrite_010)
        w = WidgetCapture()
        f(w)
        self.assertIsNot(w.widget, w.widget2)
        self.assertIs(w.widget, w.widget3)
        w2 = w.widget2
        w.widget.width = 77
        self.assertIsNot(w.widget2, w2)

    def test_enter_overwrite_after_rule_captured(self):
        KV_f_ro, KV_f = self.get_KV()
        f = KV_f_ro(WidgetCapture.enter_var_overwrite11)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget.width + 55)
        w.widget.width = 27
        self.assertEqual(w.value, w.widget.width + 55)

        remove_kvc(WidgetCapture.enter_var_overwrite11)
        f = KV_f(WidgetCapture.enter_var_overwrite11)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget.width + 55)
        w.widget.width = 27
        self.assertEqual(w.value, w.widget.width + 55)

    def test_enter_aug_overwrite_before_rule_captured(self):
        KV_f_ro, KV_f = self.get_KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.enter_var_overwrite12)
        remove_kvc(WidgetCapture.enter_var_overwrite12)
        f = KV_f(WidgetCapture.enter_var_overwrite12)
        w = WidgetCapture()
        f(w)

    def test_enter_aug_overwrite_in_rule_captured(self):
        KV_f_ro, KV_f = self.get_KV()
        f = KV_f_ro(WidgetCapture.enter_var_overwrite13)
        w = WidgetCapture()
        f(w)
        remove_kvc(WidgetCapture.enter_var_overwrite13)
        f = KV_f(WidgetCapture.enter_var_overwrite13)
        w = WidgetCapture()
        f(w)

    def test_enter_aug_overwrite_after_rule_captured(self):
        KV_f_ro, KV_f = self.get_KV()
        f = KV_f_ro(WidgetCapture.enter_var_overwrite14)
        w = WidgetCapture()
        f(w)
        remove_kvc(WidgetCapture.enter_var_overwrite14)
        f = KV_f(WidgetCapture.enter_var_overwrite14)
        w = WidgetCapture()
        f(w)

    def test_enter_aug_overwrite_in_rule_read(self):
        KV_f_ro, KV_f = self.get_KV()
        f = KV_f_ro(WidgetCapture.enter_var_overwrite15)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, 55 + 22)
        w.widget.width = 43
        self.assertEqual(w.value, 55 + 22)

    def test_enter_nested_ctx_overwrite_in_nested(self):
        KV_f_ro, KV_f = self.get_KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.enter_var_overwrite16)
        remove_kvc(WidgetCapture.enter_var_overwrite16)
        f = KV_f(WidgetCapture.enter_var_overwrite16)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget3.height + 90)
        w.widget3.height = 33
        self.assertEqual(w.value, w.widget3.height + 78)

    def test_enter_nested_ctx_overwrite_before_nested(self):
        KV_f_ro, KV_f = self.get_KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.enter_var_overwrite17)
        remove_kvc(WidgetCapture.enter_var_overwrite17)
        f = KV_f(WidgetCapture.enter_var_overwrite17)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget3.height + 90)
        w.widget3.height = 33
        self.assertEqual(w.value, w.widget3.height + 78)

    def test_enter_nested_ctx_overwrite_after_nested(self):
        KV_f_ro, KV_f = self.get_KV()
        f = KV_f_ro(WidgetCapture.enter_var_overwrite18)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget3.height + 78)
        w.widget2.height = 33
        self.assertEqual(w.value, w.widget2.height + 34)

        remove_kvc(WidgetCapture.enter_var_overwrite18)
        f = KV_f(WidgetCapture.enter_var_overwrite18)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget3.height + 78)
        w.widget2.height = 33
        self.assertEqual(w.value, w.widget2.height + 34)

    def capture_inlined_code(self, func, num):
        KV_f_ro, KV_f = self.get_KV()
        f = KV_f_ro(func)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget.width + num)
        w.widget.width = 33
        self.assertEqual(w.value, w.widget.width + num)

        remove_kvc(func)
        f = KV_f(func)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget.width + num)
        w.widget.width = 33
        self.assertEqual(w.value, w.widget.width + num)

        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        remove_kvc(func)
        f = KV_f_ro(func)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget.width + num)
        w.widget.width = 33
        self.assertEqual(w.value, w.widget.width + num)

        remove_kvc(func)
        f = KV_f(func)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget.width + num)
        w.widget.width = 33
        self.assertEqual(w.value, w.widget.width + num)

    def test_captured_lambda(self):
        self.capture_inlined_code(
            WidgetCapture.rule_with_capture_lambda, 44)

    def test_captured_list_comp(self):
        self.capture_inlined_code(
            WidgetCapture.rule_with_capture_list_comp, 3)

    def test_captured_set_comp(self):
        self.capture_inlined_code(
            WidgetCapture.rule_with_capture_set_comp, 0)

    def test_captured_gen_comp(self):
        self.capture_inlined_code(
            WidgetCapture.rule_with_capture_gen_comp, 3)

    def test_captured_dict_comp(self):
        self.capture_inlined_code(
            WidgetCapture.rule_with_capture_dict_comp, 3)


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

    # mix rules types, test all rules without ctx etc, rule within rule


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

_temp_value = 45

class CodeNodesWidget(BaseWidget):

    def do_nonlocal(self):
        self.width = 55
        a = 12

        def inner():
            nonlocal a
            return 86
        return inner

    def do_nonlocal_ctx(self):
        self.width = 55
        a = 12

        def inner():
            nonlocal a
            return 86

        with KVCtx():
            pass
        return inner

    def do_global(self):
        self.width = 78
        global _temp_value

    def do_global_ctx(self):
        self.width = 78
        global _temp_value

        with KVCtx():
            pass

    def do_return(self, return_early):
        self.widget = Widget()
        self.value = 42
        if return_early:
            return
        with KVCtx():
            self.value @= self.widget.width

    def do_return2(self, return_early):
        self.widget = Widget()
        with KVCtx():
            if return_early:
                return
            self.value @= self.widget.width

    def do_return3(self, return_early):
        self.widget = Widget()
        with KVCtx():
            with KVCtx():
                if return_early:
                    return
            self.value @= self.widget.width

    def do_return4(self, return_early):
        self.widget = Widget()
        with KVCtx():
            self.value @= self.widget.width
            if return_early:
                return

    def do_return5(self, return_early):
        self.widget = Widget()
        with KVCtx():
            self.value @= self.widget.width
        if return_early:
            return

    def do_def(self):
        self.widget = Widget()
        def x():
            pass
        with KVCtx():
            self.width @= self.widget.width

    def do_def2(self):
        self.widget = Widget()
        with KVCtx():
            def x():
                pass
            self.width @= self.widget.width

    def do_def3(self):
        self.widget = Widget()
        with KVCtx():
            self.width @= self.widget.width
        def x():
            pass

    def do_def4(self):
        self.widget = Widget()
        with KVCtx():
            def x():
                pass
            with KVRule():
                self.width @= self.widget.width

    def do_def5(self):
        self.widget = Widget()
        with KVCtx():
            with KVRule():
                def x():
                    pass
                self.width @= self.widget.width

    def do_def6(self):
        self.widget = Widget()
        with KVCtx():
            with KVRule():
                self.width @= self.widget.width
            def x():
                pass

    def do_class(self):
        self.widget = Widget()
        class x(object):
            pass
        with KVCtx():
            self.width @= self.widget.width

    def do_class2(self):
        self.widget = Widget()
        with KVCtx():
            class x(object):
                pass
            self.width @= self.widget.width

    def do_class3(self):
        self.widget = Widget()
        with KVCtx():
            self.width @= self.widget.width
        class x(object):
            pass

    def do_class4(self):
        self.widget = Widget()
        with KVCtx():
            class x(object):
                pass
            with KVRule():
                self.width @= self.widget.width

    def do_class5(self):
        self.widget = Widget()
        with KVCtx():
            with KVRule():
                class x(object):
                    pass
                self.width @= self.widget.width

    def do_class6(self):
        self.widget = Widget()
        with KVCtx():
            with KVRule():
                self.width @= self.widget.width
            class x(object):
                pass

    def do_exception_handler(self):
        self.widget = Widget()
        with KVCtx():
            try:
                pass
            except KeyError as e:
                self.value @= self.widget.width

    def do_exception_handler1(self):
        self.widget = Widget()
        with KVCtx():
            try:
                pass
            except KeyError as e:
                pass
            self.value @= self.widget.width

    def do_exception_handler2(self):
        self.widget = Widget()
        with KVCtx():
            try:
                raise KeyError
            except KeyError as e:
                with KVCtx():
                    self.value @= self.widget.width

    def do_exception_handler3(self):
        self.widget = Widget()
        with KVCtx():
            try:
                raise KeyError
            except KeyError as e:
                with KVRule():
                    self.value @= self.widget.width

    def do_exception_handler4(self):
        self.widget = Widget()
        with KVCtx():
            try:
                pass
            except KeyError as e:
                pass
            except KeyError as e2:
                self.value @= self.widget.width

    def do_exception_handler5(self):
        self.widget = Widget()
        with KVCtx():
            try:
                raise KeyError
            except ValueError as e:
                pass
            except KeyError as e2:
                with KVCtx():
                    self.value @= self.widget.width

    def do_try(self):
        self.widget = Widget()
        with KVCtx():
            try:
                self.value @= self.widget.width
            except KeyError as e:
                pass

    def do_if(self):
        self.widget = Widget()
        with KVCtx():
            if True:
                self.value @= self.widget.width

    def do_if1(self):
        self.widget = Widget()
        with KVCtx():
            if True:
                q = 44
            self.value @= self.widget.width

    def do_if2(self):
        self.widget = Widget()
        with KVCtx():
            if True:
                with KVCtx():
                    self.value @= self.widget.width

    def do_if3(self):
        self.widget = Widget()
        with KVCtx():
            if True:
                with KVRule():
                    self.value @= self.widget.width

    def do_while(self):
        self.widget = Widget()
        with KVCtx():
            while True:
                self.value @= self.widget.width
                break

    def do_while1(self):
        self.widget = Widget()
        with KVCtx():
            while True:
                q = 44
                break
            self.value @= self.widget.width

    def do_while2(self, objs):
        self.widget = Widget()
        with KVCtx():
            i = 0
            while i < len(objs):
                with KVCtx():
                    self.value_list[i].value @= objs[i].width
                i += 1

    def do_while3(self):
        self.widget = Widget()
        with KVCtx():
            while True:
                with KVRule():
                    self.value @= self.widget.width
                break

    def do_for(self):
        self.widget = Widget()
        with KVCtx():
            for i in range(5):
                self.value @= self.widget.width

    def do_for1(self):
        self.widget = Widget()
        with KVCtx():
            for i in range(5):
                q = 44
            self.value @= self.widget.width

    def do_for2(self, objs):
        self.widget = Widget()
        with KVCtx():
            for i in range(5):
                with KVCtx():
                    self.value_list[i].value @= objs[i].width

    def do_for3(self):
        self.widget = Widget()
        with KVCtx():
            for i in range(5):
                with KVRule():
                    self.value @= self.widget.width


@skip_py2_decorator
class TestIllegalNodes(TestBase):

    def test_nonlocal(self):
        KV_f = KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f(CodeNodesWidget.do_nonlocal)

    def test_nonlocal_ctx(self):
        KV_f = KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f(CodeNodesWidget.do_nonlocal_ctx)

    def test_globall(self):
        KV_f = KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f(CodeNodesWidget.do_global)

    def test_global_ctx(self):
        KV_f = KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f(CodeNodesWidget.do_global_ctx)

    def test_return_before_ctx(self):
        KV_f = KV()
        f = KV_f(CodeNodesWidget.do_return)
        w = CodeNodesWidget()
        f(w, True)

        val = w.value
        self.assertEqual(val, 42)
        w.widget.width = 7445
        self.assertEqual(w.value, val)

    def test_return_before_rule(self):
        KV_f = KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f(CodeNodesWidget.do_return2)

    def test_return_before_rule_nested(self):
        KV_f = KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f(CodeNodesWidget.do_return3)

    def test_return_after_rule(self):
        KV_f = KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f(CodeNodesWidget.do_return4)

    def test_return_after_ctx(self):
        KV_f = KV()
        f = KV_f(CodeNodesWidget.do_return5)
        w = CodeNodesWidget()
        f(w, True)

        self.assertEqual(w.value, w.widget.width)
        w.widget.width = 132
        self.assertEqual(w.value, w.widget.width)

    def test_def_before_ctx(self):
        KV_f = KV()
        KV_f(CodeNodesWidget.do_def)

    def test_def_before_rule(self):
        KV_f = KV()
        KV_f(CodeNodesWidget.do_def2)

    def test_def_after_ctx(self):
        KV_f = KV()
        KV_f(CodeNodesWidget.do_def3)

    def test_def_before_explicit_rule(self):
        KV_f = KV()
        KV_f(CodeNodesWidget.do_def4)

    def test_def_in_explciit_rule(self):
        KV_f = KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f(CodeNodesWidget.do_def5)

    def test_def_after_explicit_rule(self):
        KV_f = KV()
        KV_f(CodeNodesWidget.do_def6)

    def test_class_before_ctx(self):
        KV_f = KV()
        KV_f(CodeNodesWidget.do_class)

    def test_class_before_rule(self):
        KV_f = KV()
        KV_f(CodeNodesWidget.do_class2)

    def test_class_after_ctx(self):
        KV_f = KV()
        KV_f(CodeNodesWidget.do_class3)

    def test_class_before_explicit_rule(self):
        KV_f = KV()
        KV_f(CodeNodesWidget.do_class4)

    def test_class_in_explciit_rule(self):
        KV_f = KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f(CodeNodesWidget.do_class5)

    def test_class_after_explicit_rule(self):
        KV_f = KV()
        KV_f(CodeNodesWidget.do_class6)

    def test_except_handler(self):
        KV_f = KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f(CodeNodesWidget.do_exception_handler)

    def test_after_except_handler(self):
        KV_f = KV()
        f = KV_f(CodeNodesWidget.do_exception_handler1)
        w = CodeNodesWidget()
        f(w)

        self.assertEqual(w.value, w.widget.width)
        w.widget.width = 155
        self.assertEqual(w.value, w.widget.width)

    def test_except_handler_wrap_ctx(self):
        KV_f = KV()
        f = KV_f(CodeNodesWidget.do_exception_handler2)
        w = CodeNodesWidget()
        f(w)

        self.assertEqual(w.value, w.widget.width)
        w.widget.width = 6345
        self.assertEqual(w.value, w.widget.width)

    def test_except_handler_explicit_rule(self):
        KV_f = KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f(CodeNodesWidget.do_exception_handler3)

    def test_except_handler_second(self):
        KV_f = KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f(CodeNodesWidget.do_exception_handler4)

    def test_except_handler_second_wrap_ctx(self):
        KV_f = KV()
        f = KV_f(CodeNodesWidget.do_exception_handler5)
        w = CodeNodesWidget()
        f(w)

        self.assertEqual(w.value, w.widget.width)
        w.widget.width = 158
        self.assertEqual(w.value, w.widget.width)

    def test_try(self):
        KV_f = KV()
        f = KV_f(CodeNodesWidget.do_try)
        w = CodeNodesWidget()
        f(w)

        self.assertEqual(w.value, w.widget.width)
        w.widget.width = 345
        self.assertEqual(w.value, w.widget.width)

    def test_if(self):
        KV_f = KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f(CodeNodesWidget.do_if)

    def test_after_if(self):
        KV_f = KV()
        f = KV_f(CodeNodesWidget.do_if1)
        w = CodeNodesWidget()
        f(w)

        self.assertEqual(w.value, w.widget.width)
        w.widget.width = 451
        self.assertEqual(w.value, w.widget.width)

    def test_if_wrap_ctx(self):
        KV_f = KV()
        f = KV_f(CodeNodesWidget.do_if2)
        w = CodeNodesWidget()
        f(w)

        self.assertEqual(w.value, w.widget.width)
        w.widget.width = 854
        self.assertEqual(w.value, w.widget.width)

    def test_if_explicit_rule(self):
        KV_f = KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f(CodeNodesWidget.do_if3)

    def test_while(self):
        KV_f = KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f(CodeNodesWidget.do_while)

    def test_after_while(self):
        KV_f = KV()
        f = KV_f(CodeNodesWidget.do_while1)
        w = CodeNodesWidget()
        f(w)

        self.assertEqual(w.value, w.widget.width)
        w.widget.width = 45
        self.assertEqual(w.value, w.widget.width)

    def test_while_wrap_ctx(self):
        KV_f = KV()
        f = KV_f(CodeNodesWidget.do_while2)
        w = CodeNodesWidget()
        sources = [CodeNodesWidget() for _ in range(5)]
        targets = w.value_list = [CodeNodesWidget() for _ in range(5)]
        f(w, sources)

        for target, source in zip(targets, sources):
            self.assertEqual(target.value, source.width)
            source.width = 95
            self.assertEqual(target.value, source.width)

    def test_while_explicit_rule(self):
        KV_f = KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f(CodeNodesWidget.do_while3)

    def test_for(self):
        KV_f = KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f(CodeNodesWidget.do_for)

    def test_after_for(self):
        KV_f = KV()
        f = KV_f(CodeNodesWidget.do_for1)
        w = CodeNodesWidget()
        f(w)

        self.assertEqual(w.value, w.widget.width)
        w.widget.width = 45
        self.assertEqual(w.value, w.widget.width)

    def test_for_wrap_ctx(self):
        KV_f = KV()
        f = KV_f(CodeNodesWidget.do_for2)
        w = CodeNodesWidget()
        sources = [CodeNodesWidget() for _ in range(5)]
        targets = w.value_list = [CodeNodesWidget() for _ in range(5)]
        f(w, sources)

        for target, source in zip(targets, sources):
            self.assertEqual(target.value, source.width)
            source.width = 95
            self.assertEqual(target.value, source.width)

    def test_for_explicit_rule(self):
        KV_f = KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f(CodeNodesWidget.do_for3)


@skip_py2_decorator
class TestClosure(TestBase):

    def test_closure(self):
        w = BaseWidget()

        def do_kv_closure():
            with KVCtx():
                w.value @= w.width

        KV_f = KV()
        with self.assertRaises(KVException):
            KV_f(do_kv_closure)

    def test_not_closure_but_local(self):
        def do_kv_not_closure(widget):
            with KVCtx():
                widget.value @= widget.width

        KV_f = KV()
        with self.assertRaises(KVException):
            KV_f(do_kv_not_closure)


class ProxyWidget(BaseWidget):

    kv_ctx = None

    def apply_kv(self, widget1, widget2):
        with KVCtx():
            self.value @= widget1.width + widget2.width

    def apply_kv2(self, widget1, widget2):
        with KVCtx():
            self.value @= widget1.width + widget2.width

    def apply_kv3(self, widget1, widget2):
        with KVCtx() as self.kv_ctx:
            self.value @= widget1.width + widget2.width

    def apply_kv4(self, widget1, widget2):
        with KVCtx() as self.kv_ctx:
            self.value @= widget1.width + widget2.width

    def apply_kv5(self):
        self.widget = Widget()
        self.widget2 = Widget()

        with KVCtx():
            self.value @= self.widget.width + self.widget2.width

    def apply_kv6(self):
        self.widget = Widget()
        self.widget2 = Widget()
        self.widget3 = Widget()

        with KVCtx():
            self.value @= \
                self.widget.width + self.widget2.width + self.widget3.width

    def apply_kv7(self):
        w = self.widget = BaseWidget()
        w.widget = Widget()
        self.widget2 = Widget()

        with KVCtx():
            self.value @= self.widget.widget.width + self.widget2.width

        return w, self.widget2, w.widget

    def apply_kv8(self):
        w = self.widget = BaseWidget()
        w.widget = Widget()
        self.widget2 = Widget()

        with KVCtx():
            self.value @= self.widget.widget.width + self.widget2.width

        return w, self.widget2, w.widget

    def apply_kv9(self, widget1, widget2):
        with KVCtx():
            self.value @= widget1.width + widget2.width

    def apply_kv10(self, widget1, widget2):
        with KVCtx():
            self.value @= widget1.width + widget2.width

    def apply_kv11(self, widget1, widget2):
        with KVCtx():
            self.value @= widget1.width + widget2.width


@skip_py2_decorator
class TestProxy(TestBase):

    def test_no_proxy(self):
        w1 = Widget()
        w2 = Widget()
        KV_f = KV(proxy=False)

        f = KV_f(ProxyWidget.apply_kv)
        w = ProxyWidget()
        f(w, w1, w2)
        gc.collect()
        self.assertEqual(w.value, w1.width + w2.width)
        w1.width = 564
        self.assertEqual(w.value, w1.width + w2.width)
        w2.width = 76
        self.assertEqual(w.value, w1.width + w2.width)

        ref = w.proxy_ref
        del w
        gc.collect()
        ref.size  # w1 and w2 keep it alive

        ref1 = w1.proxy_ref
        ref2 = w2.proxy_ref
        del w1
        gc.collect()
        ref1.size  # this will be kept alive by the rule bound to w2

        del w2
        gc.collect()
        with self.assertRaises(ReferenceError):
            ref1.size
        with self.assertRaises(ReferenceError):
            ref2.size
        with self.assertRaises(ReferenceError):
            ref.size

    def test_proxy_ref(self):
        w = Widget()
        ref = w.proxy_ref
        del w
        gc.collect()
        with self.assertRaises(ReferenceError):
            ref.size

    def test_all_proxy(self):
        w1 = Widget()
        w2 = Widget()
        KV_f = KV(proxy=True)

        f = KV_f(ProxyWidget.apply_kv2)
        w = ProxyWidget()
        f(w, w1, w2)
        gc.collect()
        # rules are dead now
        original_w = w1.width + w2.width
        self.assertEqual(w.value, original_w)
        w1.width = 564
        self.assertEqual(w.value, original_w)
        w2.width = 76
        self.assertEqual(w.value, original_w)

        ref = w.proxy_ref
        del w
        gc.collect()
        # w1 and w2 don't keep it alive anymore b/c proxy
        with self.assertRaises(ReferenceError):
            ref.size

        ref1 = w1.proxy_ref
        ref2 = w2.proxy_ref
        del w1
        gc.collect()
        # w2 holds a proxy to w1, so w1 is dead now
        with self.assertRaises(ReferenceError):
            ref1.size

        del w2
        gc.collect()
        with self.assertRaises(ReferenceError):
            ref2.size

    def test_all_proxy_save_ctx(self):
        w1 = Widget()
        w2 = Widget()
        KV_f = KV(proxy=True)

        f = KV_f(ProxyWidget.apply_kv3)
        w = ProxyWidget()
        f(w, w1, w2)
        gc.collect()

        ref = w.proxy_ref
        ref1 = w1.proxy_ref
        ref2 = w2.proxy_ref
        ctx = w.kv_ctx
        del w, w1, w2
        gc.collect()

        # ctx keeps rules alive
        self.assertEqual(ref.value, ref1.width + ref2.width)
        ref1.width = 564
        self.assertEqual(ref.value, ref1.width + ref2.width)
        ref2.width = 76
        self.assertEqual(ref.value, ref1.width + ref2.width)

        ref.size  # ctx keeps it alive
        ref1.size
        ref2.size

        ctx = None
        gc.collect()

        # now it's all dead
        with self.assertRaises(ReferenceError):
            ref1.size
        with self.assertRaises(ReferenceError):
            ref2.size
        with self.assertRaises(ReferenceError):
            ref.size

    def test_proxy_all_unbind(self):
        w1 = Widget()
        w2 = Widget()
        KV_f = KV(proxy=True)

        f = KV_f(ProxyWidget.apply_kv4)
        w = ProxyWidget()
        f(w, w1, w2)

        ctx = w.kv_ctx
        ref = w.proxy_ref
        del w, w1, w2
        gc.collect()
        ref.size

        # ctx keeps everything alive
        ctx.unbind_all_rules()
        ctx = None
        gc.collect()

        with self.assertRaises(ReferenceError):
            ref.size

    def test_partial_proxy(self):
        KV_f = KV(proxy='*widget')

        f = KV_f(ProxyWidget.apply_kv5)
        w = ProxyWidget()
        f(w)

        w1, w2 = w.widget, w.widget2
        ref = w.proxy_ref
        ref1 = w1.proxy_ref
        ref2 = w2.proxy_ref
        del w, w1
        gc.collect()

        original_w = ref1.width + w2.width
        self.assertEqual(ref.value, original_w)
        ref1.width = 564
        # the rules are kept alive by w2
        self.assertEqual(ref.value, ref1.width + w2.width)
        w2.width = 76
        self.assertEqual(ref.value, ref1.width + w2.width)

        # w2 keeps it alive
        ref.size
        ref1.size

        w1 = ref1.__self__  # bring it back

        del w2  # only w2 has to die for the rule to die
        gc.collect()
        gc.collect()
        with self.assertRaises(ReferenceError):
            ref2.size
        with self.assertRaises(ReferenceError):
            ref.size

        # should not cause issues because rule will get unbound when dispatcher
        # realizes the callback is dead
        w1.width = 657

    def test_partial_proxy_multi(self):
        KV_f = KV(proxy=['*widget', '*widget2'])

        f = KV_f(ProxyWidget.apply_kv6)
        w = ProxyWidget()
        f(w)

        w1, w2, w3 = w.widget, w.widget2, w.widget3
        ref = w.proxy_ref
        ref1 = w1.proxy_ref
        ref2 = w2.proxy_ref
        ref3 = w3.proxy_ref
        del w, w1, w2
        gc.collect()

        original_w = ref1.width + ref2.width + w3.width
        self.assertEqual(ref.value, original_w)
        ref1.width = 564
        # the rules are kept alive by w3
        self.assertEqual(ref.value, ref1.width + ref2.width + w3.width)
        ref2.width = 76
        self.assertEqual(ref.value, ref1.width + ref2.width + w3.width)
        w3.width = 67
        self.assertEqual(ref.value, ref1.width + ref2.width + w3.width)

        # w3 keeps it alive
        ref.size
        ref1.size
        ref2.size

        w1 = ref1.__self__
        w2 = ref2.__self__

        del w3  # only w3 has to die for the rule to die
        gc.collect()
        with self.assertRaises(ReferenceError):
            ref3.size
        with self.assertRaises(ReferenceError):
            ref.size

        # should not cause issues because rule will get unbound when dispatcher
        # realizes the callback is dead
        w1.width = 84
        w2.width = 2093

    def test_deep_proxy(self):
        KV_f = KV(proxy='*t.widget')

        f = KV_f(ProxyWidget.apply_kv7)
        w = ProxyWidget()
        w1, w2, ww1 = f(w)

        ref = w.proxy_ref
        ref1 = w1.proxy_ref
        ref_ww1 = ww1.proxy_ref
        ref2 = w2.proxy_ref
        del w, w1
        gc.collect()

        original_w = ww1.width + w2.width
        self.assertEqual(ref.value, original_w)
        ww1.width = 564
        # the rules are kept alive by w2
        self.assertEqual(ref.value, ww1.width + w2.width)
        w2.width = 76
        self.assertEqual(ref.value, ww1.width + w2.width)

        # w2 keeps it alive
        ref.size
        ref1.size

        # only w2 now has to die for the rule to die, even if ww1 is alive, it
        # should only bind with proxy
        del w2
        gc.collect()
        with self.assertRaises(ReferenceError):
            ref2.size
        with self.assertRaises(ReferenceError):
            ref.size
        with self.assertRaises(ReferenceError):
            ref1.size

        del ww1
        gc.collect()
        with self.assertRaises(ReferenceError):
            ref_ww1.size

    def test_deep_proxy2(self):
        # this time, w1 will keep it alive
        KV_f = KV(proxy='*t.widget')

        f = KV_f(ProxyWidget.apply_kv8)
        w = ProxyWidget()
        w1, w2, ww1 = f(w)

        ref = w.proxy_ref
        ref1 = w1.proxy_ref
        ref_ww1 = ww1.proxy_ref
        ref2 = w2.proxy_ref
        del w, w2
        gc.collect()

        original_w = ww1.width + ref2.width
        self.assertEqual(ref.value, original_w)
        ww1.width = 564
        # the rules are kept alive by w2
        self.assertEqual(ref.value, ww1.width + ref2.width)
        ref2.width = 76
        self.assertEqual(ref.value, ww1.width + ref2.width)

        # w1 keeps it alive
        ref.size
        ref2.size

        # only w1 now has to die for the rule to die, even if ww1 is alive, it
        # should only bind with proxy
        del w1
        gc.collect()
        with self.assertRaises(ReferenceError):
            ref1.size
        with self.assertRaises(ReferenceError):
            ref.size
        with self.assertRaises(ReferenceError):
            ref2.size

        del ww1
        gc.collect()
        with self.assertRaises(ReferenceError):
            ref_ww1.size

    def test_proxy_no_match(self):
        w1 = Widget()
        w2 = Widget()
        KV_f = KV(proxy=['widd', 'croker', '*idge'])

        f = KV_f(ProxyWidget.apply_kv9)
        w = ProxyWidget()
        f(w, w1, w2)
        gc.collect()
        self.assertEqual(w.value, w1.width + w2.width)
        w1.width = 564
        self.assertEqual(w.value, w1.width + w2.width)
        w2.width = 76
        self.assertEqual(w.value, w1.width + w2.width)

        ref = w.proxy_ref
        del w
        gc.collect()
        ref.size  # w1 and w2 keep it alive

        ref1 = w1.proxy_ref
        ref2 = w2.proxy_ref
        del w1
        gc.collect()
        ref1.size  # this will be kept alive by the rule bound to w2

        del w2
        gc.collect()
        with self.assertRaises(ReferenceError):
            ref1.size
        with self.assertRaises(ReferenceError):
            ref2.size
        with self.assertRaises(ReferenceError):
            ref.size

    def test_all_proxy_match(self):
        w1 = Widget()
        w2 = Widget()
        KV_f = KV(proxy='*idget*')

        f = KV_f(ProxyWidget.apply_kv10)
        w = ProxyWidget()
        f(w, w1, w2)
        gc.collect()
        # rules are dead now
        original_w = w1.width + w2.width
        self.assertEqual(w.value, original_w)
        w1.width = 564
        self.assertEqual(w.value, original_w)
        w2.width = 76
        self.assertEqual(w.value, original_w)

        ref = w.proxy_ref
        del w
        gc.collect()
        # w1 and w2 don't keep it alive anymore b/c proxy
        with self.assertRaises(ReferenceError):
            ref.size

        ref1 = w1.proxy_ref
        ref2 = w2.proxy_ref
        del w1
        gc.collect()
        # w2 holds a proxy to w1, so w1 is dead now
        with self.assertRaises(ReferenceError):
            ref1.size

        del w2
        gc.collect()
        with self.assertRaises(ReferenceError):
            ref2.size

    def test_all_proxy_match2(self):
        w1 = Widget()
        w2 = Widget()
        KV_f = KV(proxy=['widget1*', 'widget2*'])

        f = KV_f(ProxyWidget.apply_kv11)
        w = ProxyWidget()
        f(w, w1, w2)
        gc.collect()
        # rules are dead now
        original_w = w1.width + w2.width
        self.assertEqual(w.value, original_w)
        w1.width = 564
        self.assertEqual(w.value, original_w)
        w2.width = 76
        self.assertEqual(w.value, original_w)

        ref = w.proxy_ref
        del w
        gc.collect()
        # w1 and w2 don't keep it alive anymore b/c proxy
        with self.assertRaises(ReferenceError):
            ref.size

        ref1 = w1.proxy_ref
        ref2 = w2.proxy_ref
        del w1
        gc.collect()
        # w2 holds a proxy to w1, so w1 is dead now
        with self.assertRaises(ReferenceError):
            ref1.size

        del w2
        gc.collect()
        with self.assertRaises(ReferenceError):
            ref2.size


class CanvasWidget(BaseWidget):

    def canvas_rule(self):
        self.value = 42
        self.widget = Widget()
        with KVCtx():
            self.value ^= self.widget.width

    def canvas_rule2(self):
        self.value = 42
        self.widget = Widget()
        with KVCtx():
            with KVRule(self.widget.width, delay='canvas'):
                self.value = self.widget.width

    def canvas_rule3(self):
        self.value = 42
        self.widget = Widget()
        with KVCtx():
            with KVRule(delay='canvas'):
                self.value ^= self.widget.width

    def canvas_rule4(self):
        self.value = 42
        self.widget = Widget()
        with KVCtx():
            with KVRule(delay='canvas'):
                self.value @= self.widget.width

    def canvas_rule5(self):
        self.value = 42
        self.widget = Widget()
        with KVCtx():
            with KVRule(delay='canvas'):
                self.value ^= self.widget.width
            self.value2 ^= self.widget.height


@skip_py2_decorator
class TestCanvasScheduling(TestBase):

    def canvas_rule_base(self, f):
        KV_f = KV()
        f = KV_f(f)
        w = CanvasWidget()
        f(w)

        orig_val = w.widget.width
        self.assertEqual(w.value, orig_val)
        w.widget.width = 67
        self.assertEqual(w.value, orig_val)
        process_graphics_callbacks()
        self.assertEqual(w.value, w.widget.width)

        orig_val = w.widget.width
        w.widget.width = 67
        self.assertEqual(w.value, orig_val)
        w.widget.width = 98
        self.assertEqual(w.value, orig_val)
        w.widget.width = 234
        self.assertEqual(w.value, orig_val)
        process_graphics_callbacks()
        self.assertEqual(w.value, w.widget.width)

        return w

    def test_canvas_implicit_rule(self):
        self.canvas_rule_base(CanvasWidget.canvas_rule)

    def test_canvas_explicit_rule_bind_explicit(self):
        self.canvas_rule_base(CanvasWidget.canvas_rule2)

    def test_canvas_explicit_rule(self):
        self.canvas_rule_base(CanvasWidget.canvas_rule3)

    def test_canvas_explicit_rule_mix(self):
        KV_f = KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f(CanvasWidget.canvas_rule4)

    def test_canvas_multi(self):
        w = self.canvas_rule_base(CanvasWidget.canvas_rule5)

        # second rule
        orig_val = w.widget.height
        self.assertEqual(w.value2, orig_val)
        w.widget.height = 67
        self.assertEqual(w.value2, orig_val)
        process_graphics_callbacks()
        self.assertEqual(w.value2, w.widget.height)

        orig_val = w.widget.height
        w.widget.height = 67
        self.assertEqual(w.value2, orig_val)
        w.widget.height = 98
        self.assertEqual(w.value2, orig_val)
        w.widget.height = 234
        self.assertEqual(w.value2, orig_val)
        process_graphics_callbacks()
        self.assertEqual(w.value2, w.widget.height)


class ClockWidget(BaseWidget):

    ctx = None

    def clock_rule(self):
        self.value = 42
        self.widget = Widget()
        with KVCtx() as self.ctx:
            with KVRule(self.widget.width, delay=0):
                self.value = self.widget.width

    def clock_rule2(self):
        self.value = 42
        self.widget = Widget()
        with KVCtx() as self.ctx:
            with KVRule(delay=0):
                self.value @= self.widget.width

    def clock_rule3(self):
        self.value = 42
        self.widget = Widget()
        with KVCtx() as self.ctx:
            with KVRule(delay=0):
                self.value ^= self.widget.width

    def clock_rule4(self):
        self.value = 42
        self.widget = Widget()
        with KVCtx() as self.ctx:
            with KVRule(delay=0):
                self.value @= self.widget.width
            with KVRule(delay=0):
                self.value2 @= self.widget.height

    def clock_rule5(self):
        self.value = 42
        self.widget = Widget()
        with KVCtx():
            with KVRule(delay=0):
                self.value @= self.widget.width

    def clock_rule6(self):
        self.value = 42
        self.widget = Widget()
        with KVCtx() as self.ctx:
            with KVRule(delay=.3):
                self.value @= self.widget.width


@skip_py2_decorator
class TestClockScheduling(TestBase):

    def clock_rule_base(self, f, delay):
        from kivy.clock import Clock
        KV_f = KV()
        f = KV_f(f)
        w = ClockWidget()
        f(w)

        orig_val = w.widget.width
        self.assertEqual(w.value, orig_val)
        w.widget.width = 67
        self.assertEqual(w.value, orig_val)
        ts = time.clock()
        Clock.tick()
        while time.clock() - ts < delay + .1:
            Clock.tick()
        self.assertEqual(w.value, w.widget.width)

        orig_val = w.widget.width
        w.widget.width = 67
        self.assertEqual(w.value, orig_val)
        w.widget.width = 98
        self.assertEqual(w.value, orig_val)
        w.widget.width = 234
        self.assertEqual(w.value, orig_val)
        ts = time.clock()
        Clock.tick()
        while time.clock() - ts < delay + .1:
            Clock.tick()
        self.assertEqual(w.value, w.widget.width)

        return w

    def test_clock_explicit_rule_bind_explicit(self):
        self.clock_rule_base(ClockWidget.clock_rule, 0)

    def test_clock_explicit_rule(self):
        self.clock_rule_base(ClockWidget.clock_rule2, 0)

    def test_clock_explicit_rule_mix(self):
        KV_f = KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f(ClockWidget.clock_rule3)

    def test_clock_multi(self):
        from kivy.clock import Clock
        w = self.clock_rule_base(ClockWidget.clock_rule4, 0)

        # second rule
        orig_val = w.widget.height
        self.assertEqual(w.value2, orig_val)
        w.widget.height = 67
        self.assertEqual(w.value2, orig_val)
        Clock.tick()
        self.assertEqual(w.value2, w.widget.height)

        orig_val = w.widget.height
        w.widget.height = 67
        self.assertEqual(w.value2, orig_val)
        w.widget.height = 98
        self.assertEqual(w.value2, orig_val)
        w.widget.height = 234
        self.assertEqual(w.value2, orig_val)
        Clock.tick()
        self.assertEqual(w.value2, w.widget.height)

    def clock_rule_no_ctx(self):
        from kivy.clock import Clock
        KV_f = KV()
        f = KV_f(ClockWidget.clock_rule5)
        w = ClockWidget()
        f(w)

        orig_val = w.widget.width
        self.assertEqual(w.value, orig_val)
        w.widget.width = 67
        self.assertEqual(w.value, orig_val)
        Clock.tick()
        # clock event callback should die if no ref to the ctx is held
        self.assertEqual(w.value, orig_val)

    def test_clock_explicit_rule_non_zero(self):
        self.clock_rule_base(ClockWidget.clock_rule6, .3)


class LargsWidget(BaseWidget):

    rule = None

    def args_rule(self):
        self.widget = Widget()
        self.widget2 = Widget()

        with KVCtx():
            with KVRule() as self.rule:
                self.value @= self.widget.width + self.widget2.width

    def args_rule2(self):
        self.widget = Widget()
        self.widget2 = Widget()

        with KVCtx():
            with KVRule(delay='canvas') as self.rule:
                self.value ^= self.widget.width + self.widget2.width

    def args_rule3(self):
        self.widget = Widget()
        self.widget2 = Widget()

        with KVCtx():
            with KVRule(delay='canvas') as self.rule:
                self.value ^= self.widget.width + self.widget2.width

    def args_rule4(self):
        self.widget = Widget()
        self.widget2 = Widget()

        with KVCtx():
            with KVRule(delay=0) as self.rule:
                self.value @= self.widget.width + self.widget2.width

    def args_rule5(self):
        self.widget = Widget()
        self.widget2 = Widget()

        with KVCtx():
            with KVRule(delay=0) as self.rule:
                self.value @= self.widget.width + self.widget2.width


@skip_py2_decorator
class TestLargs(TestBase):

    def test_largs(self):
        KV_f = KV()
        f = KV_f(LargsWidget.args_rule)
        w = LargsWidget()
        f(w)

        self.assertEqual(w.value, w.widget.width + w.widget2.width)
        w.widget.width = 82
        self.assertEqual(w.value, w.widget.width + w.widget2.width)
        self.assertEqual(w.rule.largs[0], w.widget)
        self.assertEqual(w.rule.largs[1], 82)

        w.widget2.width = 98
        self.assertEqual(w.value, w.widget.width + w.widget2.width)
        self.assertEqual(w.rule.largs[0], w.widget2)
        self.assertEqual(w.rule.largs[1], 98)

    def test_largs_canvas(self):
        KV_f = KV()
        f = KV_f(LargsWidget.args_rule2)
        w = LargsWidget()
        f(w)
        process_graphics_callbacks()

        self.assertEqual(w.value, w.widget.width + w.widget2.width)
        w.widget.width = 82
        process_graphics_callbacks()
        self.assertEqual(w.value, w.widget.width + w.widget2.width)
        self.assertEqual(w.rule.largs[0], w.widget)
        self.assertEqual(w.rule.largs[1], 82)

        w.widget2.width = 98
        process_graphics_callbacks()
        self.assertEqual(w.value, w.widget.width + w.widget2.width)
        self.assertEqual(w.rule.largs[0], w.widget2)
        self.assertEqual(w.rule.largs[1], 98)

    def test_largs_canvas_pooled(self):
        KV_f = KV()
        f = KV_f(LargsWidget.args_rule3)
        w = LargsWidget()
        f(w)
        process_graphics_callbacks()

        orig_val = w.widget.width + w.widget2.width
        self.assertEqual(w.value, orig_val)
        w.widget.width = 82
        self.assertEqual(w.value, orig_val)

        w.widget2.width = 98
        process_graphics_callbacks()
        self.assertEqual(w.value, w.widget.width + w.widget2.width)
        self.assertEqual(w.rule.largs[0], w.widget)
        self.assertEqual(w.rule.largs[1], 82)

    def test_largs_clock(self):
        from kivy.clock import Clock
        KV_f = KV()
        f = KV_f(LargsWidget.args_rule4)
        w = LargsWidget()
        f(w)
        Clock.tick()

        self.assertEqual(w.value, w.widget.width + w.widget2.width)
        w.widget.width = 82
        Clock.tick()
        self.assertEqual(w.value, w.widget.width + w.widget2.width)
        self.assertEqual(len(w.rule.largs), 1)
        self.assertIsInstance(w.rule.largs[0], (int, float))

        w.widget2.width = 98
        Clock.tick()
        self.assertEqual(w.value, w.widget.width + w.widget2.width)
        self.assertEqual(len(w.rule.largs), 1)
        self.assertIsInstance(w.rule.largs[0], (int, float))

    def test_largs_clock_pooled(self):
        from kivy.clock import Clock
        KV_f = KV()
        f = KV_f(LargsWidget.args_rule5)
        w = LargsWidget()
        f(w)
        Clock.tick()

        orig_val = w.widget.width + w.widget2.width
        self.assertEqual(w.value, orig_val)
        w.widget.width = 82
        self.assertEqual(w.value, orig_val)

        w.widget2.width = 98
        Clock.tick()
        self.assertEqual(w.value, w.widget.width + w.widget2.width)
        self.assertEqual(len(w.rule.largs), 1)
        self.assertIsInstance(w.rule.largs[0], (int, float))


class NotCompiledWudget(BaseWidget):

    def apply_rule(self):
        with KVCtx():
            pass

    def apply_rule2(self):
        with KVRule():
            pass


@skip_py2_decorator
class TestNotCompiled(TestBase):

    def test_not_compiled_ctx(self):
        w = NotCompiledWudget()
        with self.assertRaises(TypeError):
            w.apply_rule()

    def test_not_compiled_rule(self):
        w = NotCompiledWudget()
        with self.assertRaises(TypeError):
            w.apply_rule2()

# unbinding
