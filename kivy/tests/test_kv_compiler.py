# TODO: add tests for async def, like do_def, once py2 support is dropped

import sys
import time
import os
from os.path import exists, isfile
import glob
import inspect
import gc
import subprocess
import ast
import shutil
import importlib

from kivy.compat import PY2
if not PY2:
    from kivy.lang.compiler.kv_context import KVParserRule, KVParserCtx
    from kivy.lang.compiler.kv import KV_apply_manual
    from kivy.lang.compiler.utils import StringPool
    from kivy.lang.compiler import KV, KVCtx, KVRule
    from kivy.lang.compiler.ast_parse import KVException, \
        KVCompilerParserException
    from kivy.lang.compiler.runtime import get_kvc_filename, \
        process_graphics_callbacks, clear_kvc_cache
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ObjectProperty, ListProperty, \
    DictProperty
from kivy.tests.common import skip_py2_decorator
from kivy.utils import platform
from kivy.compat import PY2

import unittest

delete_kvc_after_test = int(os.environ.get('KIVY_TEST_DELETE_KVC', 1))
# helpful during testing - if set to 0, it'll leave the kvc in the folder

skip_py2_non_win = unittest.skip('Does not support py2') \
    if PY2 or platform != 'win' else lambda x: x


def f_time(filename):
    return os.stat(filename).st_mtime


def remove_kvc(func, flags=''):
    fname = get_kvc_filename(func, flags=flags)
    if exists(fname):
        os.remove(fname)

    # we must remove pycache b/c https://bugs.python.org/issue31772
    d = os.path.join(os.path.dirname(fname), '__pycache__')
    if exists(d):
        for f in os.listdir(d):
            file_path = os.path.join(d, f)
            if os.path.isfile(file_path):
                os.unlink(file_path)


class TestStringPool(unittest.TestCase):

    def test_pool(self):
        pool = StringPool(prefix='var')

        self.assertEqual(set(pool.get_all_items()), set())
        self.assertEqual(set(pool.get_available_items()), set())
        self.assertEqual(pool.get_num_borrowed(), 0)

        obj1 = object()
        name1 = pool.borrow(obj1, 2)

        self.assertEqual(set(pool.get_all_items()), {name1})
        self.assertEqual(set(pool.get_available_items()), set())
        self.assertEqual(pool.get_num_borrowed(), 1)

        obj2 = object()
        name2 = pool.borrow(obj2, 1)
        self.assertNotEqual(name1, name2)

        self.assertEqual(set(pool.get_all_items()), {name1, name2})
        self.assertEqual(set(pool.get_available_items()), set())
        self.assertEqual(pool.get_num_borrowed(), 2)

        name3 = pool.borrow_persistent()
        self.assertNotEqual(name2, name3)

        self.assertEqual(set(pool.get_all_items()), {name1, name2, name3})
        self.assertEqual(set(pool.get_available_items()), set())
        self.assertEqual(pool.get_num_borrowed(), 3)

        self.assertEqual(pool.return_back(obj1), 1)

        self.assertEqual(set(pool.get_all_items()), {name1, name2, name3})
        self.assertEqual(set(pool.get_available_items()), set())
        self.assertEqual(pool.get_num_borrowed(), 3)

        self.assertEqual(pool.return_back(obj1), 0)

        self.assertEqual(set(pool.get_all_items()), {name1, name2, name3})
        self.assertEqual(set(pool.get_available_items()), {name1, })
        self.assertEqual(pool.get_num_borrowed(), 2)

        self.assertEqual(pool.return_back(obj2), 0)

        self.assertEqual(set(pool.get_all_items()), {name1, name2, name3})
        self.assertEqual(set(pool.get_available_items()), {name1, name2})
        self.assertEqual(pool.get_num_borrowed(), 1)

        name4 = pool.borrow(object())
        self.assertIn(name4, {name1, name2})

        self.assertEqual(set(pool.get_all_items()), {name1, name2, name3})
        self.assertEqual(
            set(pool.get_available_items()), {name1, name2} - {name4})
        self.assertEqual(pool.get_num_borrowed(), 2)

        name5 = pool.borrow(object())
        self.assertIn(name5, {name1, name2})
        self.assertNotEqual(name4, name5)

        self.assertEqual(set(pool.get_all_items()), {name1, name2, name3})
        self.assertEqual(set(pool.get_available_items()), set())
        self.assertEqual(pool.get_num_borrowed(), 3)


@skip_py2_decorator
class TestBase(unittest.TestCase):

    def setUp(self):
        super(TestBase, self).setUp()
        clear_kvc_cache()

    def tearDown(self):
        super(TestBase, self).tearDown()
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

    value_object = ObjectProperty(None)

    widget = ObjectProperty(None, allownone=True)

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

    count = 0

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

    def rule_with_capture_on_enter_not_exist(self):
        self.widget = Widget()

        with KVCtx():
            w = self.widget
            self.value @= w.width

    def enter_not_exist(self):
        self.widget = Widget()

        with KVCtx():
            w = self.widget
            self.value @= w.width

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
            with KVRule(w2.width):
                x = w2
                self.value @= w.width + q
            w2 = Widget()

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

    def enter_var_overwrite19(self):
        self.widget = w = Widget()
        with KVCtx():
            with KVRule(self.width):
                w.width += self.width

    def enter_var_overwrite20(self):
        w = Widget()
        with KVCtx():
            w @= w.width

    def enter_var_overwrite21(self):
        w = Widget()
        with KVCtx():
            with KVRule():
                w @= w.width

    def enter_var_overwrite22(self):
        self.widget = w = Widget()
        with KVCtx():
            with KVRule():
                self.width @= self.widget.width
                w = w.width

    def enter_var_overwrite23(self):
        self.widget = w = Widget()
        with KVCtx():
            with KVCtx():
                with KVCtx():
                    w = w.width

    def enter_callback_at_end(self):
        with KVCtx():
            with KVRule():
                self.count += 1
                self.width @= self.height

    def enter_del_in_rule(self):
        x = 22
        with KVCtx():
            with KVRule():
                self.width @= self.height
                del x

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

    def rule_with_capture_on_exit_not_exist(self):
        self.widget = Widget()

        with KVCtx():
            w = self.widget
            self.value @= w.width
            del w

    def exit_not_exist(self):
        self.widget = Widget()

        with KVCtx():
            w = self.widget
            self.value @= w.width
            del w

    def exit_var_overwrite(self):
        w = Widget()
        with KVCtx():
            w = self.widget
            self.value @= w.width

    def exit_var_overwrite2(self):
        w = Widget()
        with KVCtx():
            self.value @= w.width
            w = self.widget

    def exit_var_overwrite3(self):
        w = Widget()
        with KVCtx():
            self.value @= w.width
        w = self.widget

    def exit_var_overwrite4(self):
        w = Widget()
        with KVCtx():
            q = w
            self.value @= q.width
            w = self.widget

    def exit_var_overwrite5(self):
        w = Widget()
        with KVCtx():
            with KVRule():
                q = w
                q = None or w
                self.value @= q.width
            w = self.widget

    def exit_var_overwrite_005(self):
        self.widget = w = Widget()
        with KVCtx():
            with KVRule():
                q = w
                q = None or w
                self.value @= q.width
            del q

    def exit_var_overwrite6(self):
        w = Widget()
        with KVCtx():
            q = 55
            self.value @= w.width + q
            q = 56

    def exit_var_overwrite7(self):
        self.widget = w = Widget()
        q = 55
        with KVCtx():
            q = 12
            self.value @= w.width + q
            q = 56

    def exit_var_overwrite8(self):
        self.widget = w = Widget()
        q = 55
        with KVCtx():
            with KVRule():
                self.value @= w.width + q
                q = 12

    def exit_var_overwrite_008(self):
        self.widget = w = Widget()
        q = 55
        with KVCtx():
            with KVRule():
                q = 12
                self.value @= w.width + q

    def exit_var_overwrite_009_pre_ctx(self):
        self.widget = w = Widget()
        self.widget2 = w2 = Widget()
        q = 55
        w2 = Widget()
        with KVCtx():
            with KVRule(w2.width):
                self.count += 1
                self.value @= w.width + q

    def exit_var_overwrite_009_pre_rule(self):
        self.widget = w = Widget()
        self.widget2 = w2 = Widget()
        q = 55
        with KVCtx():
            w2 = Widget()
            with KVRule(w2.width):
                self.count += 1
                self.value @= w.width + q

    def exit_var_overwrite_009_in_rule(self):
        self.widget = w = Widget()
        self.widget2 = w2 = Widget()
        q = 55
        with KVCtx():
            with KVRule(w2.width):
                self.count += 1
                w2 = Widget()
                self.value @= w.width + q

    def exit_var_overwrite9(self):
        self.widget = w = Widget()
        self.widget2 = w2 = Widget()
        q = 55
        with KVCtx():
            with KVRule(w2.width):
                self.count += 1
                self.value @= w.width + q
                w2 = Widget()

    def exit_var_overwrite_009(self):
        self.widget = w = Widget()
        self.widget2 = w2 = Widget()
        q = 55
        with KVCtx():
            with KVRule(w2.width):
                self.count += 1
                self.value @= w.width + q
            w2 = Widget()

    def exit_var_overwrite_009_1(self):
        self.widget = w = Widget()
        self.widget2 = w2 = Widget()
        q = 55
        with KVCtx():
            with KVRule(w2.width):
                w2 = Widget()
                x = w2
                self.value @= w.width + q
            w2 = Widget()

    def exit_var_overwrite_009_2(self):
        self.widget = w = Widget()
        self.widget2 = w2 = Widget()
        q = 55
        with KVCtx():
            with KVRule(w2.width):
                x = w2
                self.value @= w.width + q
            w2 = Widget()

    def exit_var_overwrite10(self):
        self.widget = w = Widget()
        with KVCtx():
            with KVRule(w.width):
                self.widget2 = w = Widget()

    def exit_var_overwrite_010(self):
        self.widget = w = Widget()
        with KVCtx():
            with KVRule(w.width):
                self.widget3 = w
                self.widget2 = w = Widget()

    def exit_var_overwrite11(self):
        self.widget = w = Widget()
        q = 55
        with KVCtx():
            self.value @= w.width + q
            q = 27

    def exit_var_overwrite12(self):
        w = Widget()
        q = 55
        with KVCtx():
            with KVRule(w.width):
                q += 55

    def exit_var_overwrite13(self):
        w = Widget()
        q = 55
        with KVCtx():
            q += 55
            with KVRule(w.width):
                x = q

    def exit_var_overwrite15(self):
        self.widget = w = Widget()
        q = 55
        with KVCtx():
            q += 22
            with KVRule(w.width):
                self.value = q

    def exit_var_overwrite16(self):
        self.widget = Widget()
        self.widget2 = Widget()
        self.widget3 = Widget()
        q = 54
        e = 34
        r = 78
        with KVCtx():
            self.value @= self.widget.height + q
            with KVCtx():
                q = 90
                self.value @= self.widget2.height + e
            self.value @= self.widget3.height + r + q

    def exit_var_overwrite17(self):
        self.widget = Widget()
        self.widget2 = Widget()
        self.widget3 = Widget()
        q = 54
        e = 34
        r = 78
        with KVCtx():
            self.value @= self.widget.height + q
            q = 90
            with KVCtx():
                self.value @= self.widget2.height + e
            self.value @= self.widget3.height + r + q

    def exit_var_overwrite18(self):
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
            q = 90
            self.value @= self.widget.height + q
            e = 97
            with KVCtx():
                self.value @= self.widget2.height + e
            self.value @= self.widget3.height + r + q

    def exit_var_overwrite19(self):
        self.widget = Widget()
        self.widget2 = Widget()
        self.widget3 = Widget()
        q = 54
        e = 34
        r = 78
        with KVCtx():
            self.value @= self.widget.height + q
            self.value @= self.widget3.height + r + q
            with KVCtx():
                self.value @= self.widget2.height + e + q
                q = 90

    def exit_var_overwrite20(self):
        self.widget = w = Widget()
        with KVCtx():
            with KVRule(self.width):
                w.width += self.width

    def exit_var_overwrite21(self):
        w = Widget()
        with KVCtx():
            w @= w.width

    def exit_var_overwrite22(self):
        w = Widget()
        with KVCtx():
            with KVRule():
                w @= w.width

    def exit_var_overwrite23(self):
        self.widget = w = Widget()
        with KVCtx():
            with KVRule():
                self.width @= self.widget.width
                w = w.width

    def exit_var_overwrite24(self):
        self.widget = w = Widget()
        with KVCtx():
            with KVCtx():
                with KVCtx():
                    w = w.width

    def exit_callback_at_end(self):
        with KVCtx():
            with KVRule():
                self.count += 1
                self.width @= self.height

    def exit_del_in_rule(self):
        x = 22
        with KVCtx():
            with KVRule():
                self.width @= self.height
                del x

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

    def test_capture_on_enter_not_exist(self):
        KV_f = KV(bind_on_enter=True, captures_are_readonly=False)
        f_static = KV_f(WidgetCapture.rule_with_capture_on_enter_not_exist)

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
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.enter_var_overwrite_005)

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
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.enter_var_overwrite8)

        remove_kvc(WidgetCapture.enter_var_overwrite8)
        f = KV_f(WidgetCapture.enter_var_overwrite8)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget.width + 12)
        w.widget.width = 33
        self.assertEqual(w.value, w.widget.width + 12)

    def test_enter_overwrite_in_rule_explicit_bind(self):
        KV_f_ro, KV_f = self.get_KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.enter_var_overwrite9)

        remove_kvc(WidgetCapture.enter_var_overwrite9)
        f = KV_f(WidgetCapture.enter_var_overwrite9)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget.width + 55)
        w.widget.width = 77
        self.assertEqual(w.value, w.widget.width + 55)

    def test_enter_overwrite_before_rule_explicit_bind(self):
        KV_f_ro, KV_f = self.get_KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.enter_var_overwrite_009)

        remove_kvc(WidgetCapture.enter_var_overwrite_009)
        f = KV_f(WidgetCapture.enter_var_overwrite_009)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget.width + 55)
        w.widget.width = 77
        self.assertEqual(w.value, w.widget.width + 55)

    def test_enter_overwrite_before_rule_explicit_bind_not_captured(self):
        KV_f_ro, KV_f = self.get_KV()
        KV_f_ro(WidgetCapture.enter_var_overwrite_009_1)

        remove_kvc(WidgetCapture.enter_var_overwrite_009_1)
        f = KV_f(WidgetCapture.enter_var_overwrite_009_1)
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
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.enter_var_overwrite10)

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
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.enter_var_overwrite_010)

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
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.enter_var_overwrite13)
        remove_kvc(WidgetCapture.enter_var_overwrite13)
        f = KV_f(WidgetCapture.enter_var_overwrite13)
        w = WidgetCapture()
        f(w)

    def test_enter_aug_overwrite_after_rule_captured(self):
        KV_f_ro, KV_f = self.get_KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.enter_var_overwrite14)
        remove_kvc(WidgetCapture.enter_var_overwrite14)
        f = KV_f(WidgetCapture.enter_var_overwrite14)
        w = WidgetCapture()
        f(w)

    def test_enter_aug_overwrite_in_rule_read(self):
        KV_f_ro, KV_f = self.get_KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.enter_var_overwrite15)

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

    def test_enter_aug(self):
        KV_f_ro, KV_f = self.get_KV()
        f = KV_f_ro(WidgetCapture.enter_var_overwrite19)
        w = WidgetCapture()
        f(w)
        width = w.widget.width
        widget = w.widget
        w.widget = None
        w.width = 124
        self.assertEqual(widget.width, 124 + width)

        remove_kvc(WidgetCapture.enter_var_overwrite19)
        f = KV_f(WidgetCapture.enter_var_overwrite19)
        w = WidgetCapture()
        f(w)
        width = w.widget.width
        widget = w.widget
        w.widget = None
        w.width = 124
        self.assertEqual(widget.width, 124 + width)

    def test_enter_overwrite_var(self):
        KV_f_ro, KV_f = self.get_KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.enter_var_overwrite20)

        remove_kvc(WidgetCapture.enter_var_overwrite20)
        f = KV_f(WidgetCapture.enter_var_overwrite20)

    def test_enter_overwrite_var_explicit(self):
        KV_f_ro, KV_f = self.get_KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.enter_var_overwrite21)

        remove_kvc(WidgetCapture.enter_var_overwrite21)
        f = KV_f(WidgetCapture.enter_var_overwrite21)

    def test_enter_overwrite_var_assign(self):
        KV_f_ro, KV_f = self.get_KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.enter_var_overwrite22)

        remove_kvc(WidgetCapture.enter_var_overwrite22)
        f = KV_f(WidgetCapture.enter_var_overwrite22)

    def test_enter_overwrite_var_assign_no_rule(self):
        KV_f_ro, KV_f = self.get_KV()
        KV_f_ro(WidgetCapture.enter_var_overwrite23)

        remove_kvc(WidgetCapture.enter_var_overwrite23)
        f = KV_f(WidgetCapture.enter_var_overwrite23)

    def test_enter_callbacks_at_end(self):
        KV_f = KV(bind_on_enter=True, exec_rules_after_binding=False)
        f = KV_f(WidgetCapture.enter_callback_at_end)
        w = WidgetCapture()
        f(w)

        self.assertEqual(w.count, 1)
        self.assertEqual(w.width, w.height)
        w.height = 237
        self.assertEqual(w.count, 2)
        self.assertEqual(w.width, w.height)

        remove_kvc(WidgetCapture.enter_callback_at_end)

        KV_f = KV(bind_on_enter=True, exec_rules_after_binding=True)
        f = KV_f(WidgetCapture.enter_callback_at_end)
        w = WidgetCapture()
        f(w)

        self.assertEqual(w.count, 2)
        self.assertEqual(w.width, w.height)
        w.height = 237
        self.assertEqual(w.count, 3)
        self.assertEqual(w.width, w.height)

    def test_enter_del_in_rule(self):
        KV_f_ro, KV_f = self.get_KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.enter_del_in_rule)

        remove_kvc(WidgetCapture.enter_del_in_rule)
        with self.assertRaises(KVCompilerParserException):
            KV_f(WidgetCapture.enter_del_in_rule)

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

    def test_capture_on_exit_not_exist(self):
        KV_f = KV(bind_on_enter=True, captures_are_readonly=False)
        f_static = KV_f(WidgetCapture.rule_with_capture_on_exit_not_exist)

        w = WidgetCapture()
        with self.assertRaises(UnboundLocalError):
            f_static(w)

    def test_exit_not_exists(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.exit_not_exist)

        remove_kvc(WidgetCapture.exit_not_exist)
        KV_f(WidgetCapture.exit_not_exist)

    def test_exit_overwrite_before_rule(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)

        KV_f_ro(WidgetCapture.exit_var_overwrite)
        remove_kvc(WidgetCapture.exit_var_overwrite)
        KV_f(WidgetCapture.exit_var_overwrite)

    def test_exit_overwrite_after_rule(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.exit_var_overwrite2)
        remove_kvc(WidgetCapture.exit_var_overwrite2)
        KV_f(WidgetCapture.exit_var_overwrite2)

    def test_exit_overwrite_after_ctx(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        KV_f_ro(WidgetCapture.exit_var_overwrite3)
        remove_kvc(WidgetCapture.exit_var_overwrite3)
        KV_f(WidgetCapture.exit_var_overwrite3)

    def test_exit_overwrite_after_rule_indirect(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        f = KV_f_ro(WidgetCapture.exit_var_overwrite4)
        w = WidgetCapture()
        f(w)

        remove_kvc(WidgetCapture.exit_var_overwrite4)
        f = KV_f(WidgetCapture.exit_var_overwrite4)
        w = WidgetCapture()
        f(w)

    def test_exit_overwrite_after_rule_indirect_explicit_rule(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.exit_var_overwrite5)
        remove_kvc(WidgetCapture.exit_var_overwrite5)
        f = KV_f(WidgetCapture.exit_var_overwrite5)
        w = WidgetCapture()
        f(w)

    def test_exit_indirect_explicit_rule(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.exit_var_overwrite_005)

        remove_kvc(WidgetCapture.exit_var_overwrite_005)
        f = KV_f(WidgetCapture.exit_var_overwrite_005)
        w = WidgetCapture()
        with self.assertRaises(UnboundLocalError):
            f(w)

    def test_exit_overwrite_in_ctx_not_defined(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.exit_var_overwrite6)
        remove_kvc(WidgetCapture.exit_var_overwrite6)
        f = KV_f(WidgetCapture.exit_var_overwrite6)
        w = WidgetCapture()
        f(w)

    def test_exit_overwrite_in_ctx_defined(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.exit_var_overwrite7)
        remove_kvc(WidgetCapture.exit_var_overwrite7)
        f = KV_f(WidgetCapture.exit_var_overwrite7)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget.width + 12)
        w.widget.width = 965
        self.assertEqual(w.value, w.widget.width + 56)

    def test_exit_overwrite_in_rule_explicit_rule_defined(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.exit_var_overwrite8)

        remove_kvc(WidgetCapture.exit_var_overwrite8)
        f = KV_f(WidgetCapture.exit_var_overwrite8)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget.width + 55)
        w.widget.width = 33
        self.assertEqual(w.value, w.widget.width + 12)

    def test_exit_overwrite_in_rule_explicit_rule_defined_before(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        f = KV_f_ro(WidgetCapture.exit_var_overwrite_008)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget.width + 12)
        w.widget.width = 33
        self.assertEqual(w.value, w.widget.width + 12)

        remove_kvc(WidgetCapture.exit_var_overwrite_008)
        f = KV_f(WidgetCapture.exit_var_overwrite_008)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget.width + 12)
        w.widget.width = 33
        self.assertEqual(w.value, w.widget.width + 12)

    def test_exit_overwrite_in_rule_explicit_bind_pre_ctx(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        f = KV_f_ro(WidgetCapture.exit_var_overwrite_009_pre_ctx)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget.width + 55)
        w.widget.width = 77
        self.assertEqual(w.value, w.widget.width + 55)

        count = w.count
        w.widget2.width = 436
        self.assertEqual(w.count, count)

        remove_kvc(WidgetCapture.exit_var_overwrite_009_pre_ctx)
        f = KV_f(WidgetCapture.exit_var_overwrite_009_pre_ctx)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget.width + 55)
        w.widget.width = 77
        self.assertEqual(w.value, w.widget.width + 55)

    def test_exit_overwrite_in_rule_explicit_bind_pre_rule(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        f = KV_f_ro(WidgetCapture.exit_var_overwrite_009_pre_rule)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget.width + 55)
        w.widget.width = 77
        self.assertEqual(w.value, w.widget.width + 55)

        count = w.count
        w.widget2.width = 436
        self.assertEqual(w.count, count)

        remove_kvc(WidgetCapture.exit_var_overwrite_009_pre_rule)
        f = KV_f(WidgetCapture.exit_var_overwrite_009_pre_rule)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget.width + 55)
        w.widget.width = 77
        self.assertEqual(w.value, w.widget.width + 55)

    def test_exit_overwrite_in_rule_explicit_bind_in_rule(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.exit_var_overwrite_009_in_rule)

        remove_kvc(WidgetCapture.exit_var_overwrite_009_in_rule)
        f = KV_f(WidgetCapture.exit_var_overwrite_009_in_rule)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget.width + 55)
        w.widget.width = 77
        self.assertEqual(w.value, w.widget.width + 55)

        count = w.count
        w.widget2.width = 436
        self.assertEqual(w.count, count)

    def test_exit_overwrite_in_rule_explicit_bind(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.exit_var_overwrite9)

        remove_kvc(WidgetCapture.exit_var_overwrite9)
        f = KV_f(WidgetCapture.exit_var_overwrite9)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget.width + 55)
        w.widget.width = 77
        self.assertEqual(w.value, w.widget.width + 55)

        count = w.count
        w.widget2.width = 436
        self.assertEqual(w.count, count)

    def test_exit_overwrite_after_rule_explicit_bind(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.exit_var_overwrite_009)

        remove_kvc(WidgetCapture.exit_var_overwrite_009)
        f = KV_f(WidgetCapture.exit_var_overwrite_009)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget.width + 55)
        w.widget.width = 77
        self.assertEqual(w.value, w.widget.width + 55)

        count = w.count
        w.widget2.width = 436
        self.assertEqual(w.count, count)

    def test_exit_overwrite_before_rule_explicit_bind_not_captured(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.exit_var_overwrite_009_1)

        remove_kvc(WidgetCapture.exit_var_overwrite_009_1)
        f = KV_f(WidgetCapture.exit_var_overwrite_009_1)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget.width + 55)
        w.widget.width = 77
        self.assertEqual(w.value, w.widget.width + 55)

        count = w.count
        w.widget2.width = 436
        self.assertEqual(w.count, count)

    def test_exit_overwrite_before_rule_explicit_bind_captured(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.exit_var_overwrite_009_2)

    def test_exit_overwrite_in_rule_explicit_bind2(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.exit_var_overwrite10)

        remove_kvc(WidgetCapture.exit_var_overwrite10)
        f = KV_f(WidgetCapture.exit_var_overwrite10)
        w = WidgetCapture()
        f(w)
        self.assertIsNot(w.widget, w.widget2)
        w2 = w.widget2
        w.widget.width = 77
        self.assertIs(w.widget2, w2)
        w.widget2.width = 54
        self.assertIsNot(w.widget2, w2)

    def test_exit_overwrite_in_rule_explicit_bind_captured(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.exit_var_overwrite_010)

        remove_kvc(WidgetCapture.exit_var_overwrite_010)
        f = KV_f(WidgetCapture.exit_var_overwrite_010)
        w = WidgetCapture()
        f(w)
        self.assertIsNot(w.widget, w.widget2)
        w2 = w.widget2
        w.widget.width = 77
        self.assertIs(w.widget2, w2)
        w.widget2.width = 54
        self.assertIsNot(w.widget2, w2)

    def test_exit_overwrite_after_rule_captured(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.exit_var_overwrite11)

        remove_kvc(WidgetCapture.exit_var_overwrite11)
        f = KV_f(WidgetCapture.exit_var_overwrite11)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget.width + 55)
        w.widget.width = 27
        self.assertEqual(w.value, w.widget.width + 27)

    def test_exit_aug_overwrite_before_rule_captured(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.exit_var_overwrite12)
        remove_kvc(WidgetCapture.exit_var_overwrite12)
        f = KV_f(WidgetCapture.exit_var_overwrite12)
        w = WidgetCapture()
        f(w)

    def test_exit_aug_overwrite_in_rule_captured(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        f = KV_f_ro(WidgetCapture.exit_var_overwrite13)
        w = WidgetCapture()
        f(w)
        remove_kvc(WidgetCapture.exit_var_overwrite13)
        f = KV_f(WidgetCapture.exit_var_overwrite13)
        w = WidgetCapture()
        f(w)

    def test_exit_aug_overwrite_in_rule_read(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        f = KV_f_ro(WidgetCapture.exit_var_overwrite15)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, 55 + 22)
        w.widget.width = 43
        self.assertEqual(w.value, 55 + 22)

    def test_exit_nested_ctx_overwrite_in_nested(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.exit_var_overwrite16)
        remove_kvc(WidgetCapture.exit_var_overwrite16)
        f = KV_f(WidgetCapture.exit_var_overwrite16)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget3.height + 78 + 90)
        w.widget3.height = 26
        self.assertEqual(w.value, 26 + 78 + 90)

    def test_exit_nested_ctx_overwrite_before_nested(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.exit_var_overwrite17)
        remove_kvc(WidgetCapture.exit_var_overwrite17)
        f = KV_f(WidgetCapture.exit_var_overwrite17)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget3.height + 78 + 90)
        w.widget3.height = 458
        self.assertEqual(w.value, 458 + 78 + 90)

    def test_exit_nested_ctx_overwrite_after_nested(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        f = KV_f_ro(WidgetCapture.exit_var_overwrite18)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget3.height + 78 + 90)
        w.widget2.height = 923
        self.assertEqual(w.value, 923 + 97)

        remove_kvc(WidgetCapture.exit_var_overwrite18)
        f = KV_f(WidgetCapture.exit_var_overwrite18)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget3.height + 78 + 90)
        w.widget2.height = 923
        self.assertEqual(w.value, 923 + 97)

    def test_exit_nested_ctx_overwrite_after_final_nested(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.exit_var_overwrite19)

        remove_kvc(WidgetCapture.exit_var_overwrite19)
        f = KV_f(WidgetCapture.exit_var_overwrite19)
        w = WidgetCapture()
        f(w)
        self.assertEqual(w.value, w.widget2.height + 54 + 34)
        w.widget2.height = 692
        self.assertEqual(w.value, 692 + 34 + 90)

    def test_exit_aug(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        f = KV_f_ro(WidgetCapture.exit_var_overwrite20)
        w = WidgetCapture()
        f(w)
        width = w.widget.width
        widget = w.widget
        w.widget = None
        w.width = 124
        self.assertEqual(widget.width, 124 + width)

        remove_kvc(WidgetCapture.exit_var_overwrite20)
        f = KV_f(WidgetCapture.exit_var_overwrite20)
        w = WidgetCapture()
        f(w)
        width = w.widget.width
        widget = w.widget
        w.widget = None
        w.width = 124
        self.assertEqual(widget.width, 124 + width)

    def test_exit_overwrite_var(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.exit_var_overwrite21)

        remove_kvc(WidgetCapture.exit_var_overwrite21)
        f = KV_f(WidgetCapture.exit_var_overwrite21)

    def test_exit_overwrite_var_explicit(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.exit_var_overwrite22)

        remove_kvc(WidgetCapture.exit_var_overwrite22)
        f = KV_f(WidgetCapture.exit_var_overwrite22)

    def test_exit_overwrite_var_assign(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.exit_var_overwrite23)

        remove_kvc(WidgetCapture.exit_var_overwrite23)
        f = KV_f(WidgetCapture.exit_var_overwrite23)

    def test_exit_overwrite_var_assign_no_rule(self):
        KV_f_ro, KV_f = self.get_KV(bind_on_enter=False)
        KV_f_ro(WidgetCapture.exit_var_overwrite24)

        remove_kvc(WidgetCapture.exit_var_overwrite24)
        f = KV_f(WidgetCapture.exit_var_overwrite24)

    def test_exit_callbacks_at_end(self):
        KV_f = KV(bind_on_enter=False, exec_rules_after_binding=False)
        f = KV_f(WidgetCapture.exit_callback_at_end)
        w = WidgetCapture()
        f(w)

        self.assertEqual(w.count, 1)
        self.assertEqual(w.width, w.height)
        w.height = 237
        self.assertEqual(w.count, 2)
        self.assertEqual(w.width, w.height)

        remove_kvc(WidgetCapture.exit_callback_at_end)

        KV_f = KV(bind_on_enter=False, exec_rules_after_binding=True)
        f = KV_f(WidgetCapture.exit_callback_at_end)
        w = WidgetCapture()
        f(w)

        self.assertEqual(w.count, 2)
        self.assertEqual(w.width, w.height)
        w.height = 237
        self.assertEqual(w.count, 3)
        self.assertEqual(w.width, w.height)

    def test_exit_del_in_rule(self):
        KV_f_ro, KV_f = self.get_KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f_ro(WidgetCapture.exit_del_in_rule)

        remove_kvc(WidgetCapture.exit_del_in_rule)
        with self.assertRaises(KVCompilerParserException):
            KV_f(WidgetCapture.exit_del_in_rule)

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

    ctx = None

    def no_ctx(self):
        self.value = 55

    def ctx_no_rule(self):
        with KVCtx():
            pass

    def ctx_no_rule2(self):
        with KVCtx():
            self.value = self.width

    def no_bind_rule_without_ctx(self):
        self.value @= 55

    def bind_rule_without_ctx(self):
        self.value @= self.width

    def no_bind_rule_without_ctx_explicit(self):
        with KVRule():
            self.value = 55

    def bind_rule_without_ctx_explicit(self):
        with KVRule():
            self.value = self.width

    def canvas_no_bind_rule_without_ctx(self):
        self.value ^= 55

    def bind_canvas_rule_without_ctx(self):
        self.value ^= self.width

    def canvas_no_bind_rule_without_ctx_explicit(self):
        with KVRule(delay='canvas'):
            self.value = 55

    def bind_canvas_rule_without_ctx_explicit(self):
        with KVRule(delay='canvas'):
            self.value = self.width

    def clock_no_bind_rule_without_ctx_explicit(self):
        with KVRule(delay='canvas'):
            self.value = 55

    def bind_clock_rule_without_ctx_explicit(self):
        with KVRule(delay='canvas'):
            self.value = self.width

    def apply_kv_test(self):
        with KVCtx():
            with KVRule():
                self.value = self.width
                with KVRule():
                    self.value2 = self.height

    def apply_kv_test2(self):
        with KVCtx():
            with KVRule(delay='canvas'):
                self.value = self.width
                with KVRule(delay='canvas'):
                    self.value2 = self.height

    def apply_kv_test3(self):
        with KVCtx():
            with KVRule(delay=0):
                self.value = self.width
                with KVRule(delay=0):
                    self.value2 = self.height

    def apply_kv_test4(self):
        with KVCtx():
            with KVRule():
                self.value = self.width
                with KVRule(delay=0):
                    self.value2 = self.height

    def apply_kv_test5(self):
        with KVCtx():
            with KVRule(delay=0):
                self.value = self.width
                with KVRule():
                    self.value2 = self.height

    def apply_kv_test6(self):
        with KVCtx():
            with KVRule(delay=0):
                self.value = self.width
                with KVRule(delay='canvas'):
                    self.value2 = self.height

    def apply_kv_test7(self):
        with KVCtx():
            with KVRule(delay='canvas'):
                self.value = self.width
                with KVRule(delay=0):
                    self.value2 = self.height

    def apply_kv_test8(self):
        with KVCtx():
            with KVRule():
                self.value = self.width
                with KVRule(delay='canvas'):
                    self.value2 = self.height

    def apply_kv_test9(self):
        with KVCtx():
            with KVRule(delay='canvas'):
                self.value = self.width
                with KVRule(delay=None):
                    self.value2 = self.height

    def apply_kv_test10(self):
        import kivy.lang.compiler
        with kivy.lang.compiler.KVCtx():
            with kivy.lang.compiler.KVRule():
                self.value @= self.width

    def apply_kv_test11(self):
        self.value3 = 0
        self.value = 1
        self.value2 = 2
        with KVCtx():
            self.value @= self.height
            with KVCtx():
                self.value @= self.width
                with KVCtx() as self.ctx:
                    self.value @= self.x
                    with KVCtx():
                        self.value @= self.y
                        with KVCtx():
                            self.value @= self.value2
                self.value3 @= self.value


@skip_py2_decorator
class TestCtxAutoCompiler(TestBase):

    def test_no_ctx_no_rule(self):
        KV_f = KV()

        w = CtxWidget()
        self.assertEqual(w.value, 42)
        KV_f(w.no_ctx)()
        self.assertEqual(w.value, 55)

    def test_ctx_no_rule(self):
        KV_f = KV()
        f = KV_f(CtxWidget.ctx_no_rule)

        w = CtxWidget()
        f(w)

    def test_ctx_no_rule_stmt(self):
        KV_f = KV()
        f = KV_f(CtxWidget.ctx_no_rule2)

        w = CtxWidget()
        f(w)

    def test_no_ctx_with_rule(self):
        KV_f = KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f(CtxWidget.no_bind_rule_without_ctx)
        with self.assertRaises(KVCompilerParserException):
            KV_f(CtxWidget.bind_rule_without_ctx)
        with self.assertRaises(KVCompilerParserException):
            KV_f(CtxWidget.no_bind_rule_without_ctx_explicit)
        with self.assertRaises(KVCompilerParserException):
            KV_f(CtxWidget.bind_rule_without_ctx_explicit)

    def test_no_ctx_with_rule_canvas(self):
        KV_f = KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f(CtxWidget.canvas_no_bind_rule_without_ctx)
        with self.assertRaises(KVCompilerParserException):
            KV_f(CtxWidget.bind_canvas_rule_without_ctx)
        with self.assertRaises(KVCompilerParserException):
            KV_f(CtxWidget.canvas_no_bind_rule_without_ctx_explicit)
        with self.assertRaises(KVCompilerParserException):
            KV_f(CtxWidget.bind_canvas_rule_without_ctx_explicit)

    def test_no_ctx_with_rule_clock(self):
        KV_f = KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f(CtxWidget.clock_no_bind_rule_without_ctx_explicit)
        with self.assertRaises(KVCompilerParserException):
            KV_f(CtxWidget.bind_clock_rule_without_ctx_explicit)

    def test_nested_rule(self):
        KV_f = KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f(CtxWidget.apply_kv_test)

    def test_nested_rule_canvas(self):
        KV_f = KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f(CtxWidget.apply_kv_test2)

    def test_nested_rule_clock(self):
        KV_f = KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f(CtxWidget.apply_kv_test3)

    def test_nested_rule_mix(self):
        KV_f = KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f(CtxWidget.apply_kv_test4)
        with self.assertRaises(KVCompilerParserException):
            KV_f(CtxWidget.apply_kv_test5)
        with self.assertRaises(KVCompilerParserException):
            KV_f(CtxWidget.apply_kv_test6)
        with self.assertRaises(KVCompilerParserException):
            KV_f(CtxWidget.apply_kv_test7)
        with self.assertRaises(KVCompilerParserException):
            KV_f(CtxWidget.apply_kv_test8)
        with self.assertRaises(KVCompilerParserException):
            KV_f(CtxWidget.apply_kv_test9)

    def test_dotted_rule_ctx_name(self):
        KV_f = KV()
        f = KV_f(CtxWidget.apply_kv_test10)
        w = CtxWidget()
        f(w)

        self.assertEqual(w.value, w.width)
        w.width = 56
        self.assertEqual(w.value, 56)

    def test_deeply_nested_ctx(self):
        KV_f = KV()
        f = KV_f(CtxWidget.apply_kv_test11)
        w = CtxWidget()
        f(w)

        self.assertEqual(w.value, 2)
        self.assertEqual(w.value2, 2)
        self.assertEqual(w.value3, 2)

        w.height = 12
        self.assertEqual(w.value, 12)
        self.assertEqual(w.value3, 12)

        w.width = 45
        self.assertEqual(w.value, 45)
        self.assertEqual(w.value3, 45)

        w.x = 78
        self.assertEqual(w.value, 78)
        self.assertEqual(w.value3, 78)

        w.y = 34
        self.assertEqual(w.value, 34)
        self.assertEqual(w.value3, 34)

        w.value2 = 87
        self.assertEqual(w.value, 87)
        self.assertEqual(w.value3, 87)

        w.value = 63
        self.assertEqual(w.value3, 63)

        w.ctx.unbind_all_rules()

        w.height = 65
        self.assertEqual(w.value, 65)
        self.assertEqual(w.value3, 65)

        w.width = 49
        self.assertEqual(w.value, 49)
        self.assertEqual(w.value3, 49)

        w.x = 45
        self.assertEqual(w.value, 49)
        self.assertEqual(w.value3, 49)

        w.y = 93
        self.assertEqual(w.value, 93)
        self.assertEqual(w.value3, 93)

        w.value2 = 238
        self.assertEqual(w.value, 238)
        self.assertEqual(w.value3, 238)

        w.value = 5368
        self.assertEqual(w.value3, 5368)


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

    def apply_kv_test(self, widget1, widget2):
        with KVCtx():
            self.value @= widget1.width + widget2.width

    def apply_kv_test2(self, widget1, widget2):
        with KVCtx():
            self.value @= widget1.width + widget2.width

    def apply_kv_test3(self, widget1, widget2):
        with KVCtx() as self.kv_ctx:
            self.value @= widget1.width + widget2.width

    def apply_kv_test4(self, widget1, widget2):
        with KVCtx() as self.kv_ctx:
            self.value @= widget1.width + widget2.width

    def apply_kv_test5(self):
        self.widget = Widget()
        self.widget2 = Widget()

        with KVCtx():
            self.value @= self.widget.width + self.widget2.width

    def apply_kv_test6(self):
        self.widget = Widget()
        self.widget2 = Widget()
        self.widget3 = Widget()

        with KVCtx():
            self.value @= \
                self.widget.width + self.widget2.width + self.widget3.width

    def apply_kv_test7(self):
        w = self.widget = BaseWidget()
        w.widget = Widget()
        self.widget2 = Widget()

        with KVCtx():
            self.value @= self.widget.widget.width + self.widget2.width

        return w, self.widget2, w.widget

    def apply_kv_test8(self):
        w = self.widget = BaseWidget()
        w.widget = Widget()
        self.widget2 = Widget()

        with KVCtx():
            self.value @= self.widget.widget.width + self.widget2.width

        return w, self.widget2, w.widget

    def apply_kv_test9(self, widget1, widget2):
        with KVCtx():
            self.value @= widget1.width + widget2.width

    def apply_kv_test10(self, widget1, widget2):
        with KVCtx():
            self.value @= widget1.width + widget2.width

    def apply_kv_test11(self, widget1, widget2):
        with KVCtx():
            self.value @= widget1.width + widget2.width


@skip_py2_decorator
class TestProxy(TestBase):

    def test_no_proxy(self):
        w1 = Widget()
        w2 = Widget()
        KV_f = KV(proxy=False)

        f = KV_f(ProxyWidget.apply_kv_test)
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

        f = KV_f(ProxyWidget.apply_kv_test2)
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

        f = KV_f(ProxyWidget.apply_kv_test3)
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

        f = KV_f(ProxyWidget.apply_kv_test4)
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

        f = KV_f(ProxyWidget.apply_kv_test5)
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

        f = KV_f(ProxyWidget.apply_kv_test6)
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

        f = KV_f(ProxyWidget.apply_kv_test7)
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

        f = KV_f(ProxyWidget.apply_kv_test8)
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

        f = KV_f(ProxyWidget.apply_kv_test9)
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

        f = KV_f(ProxyWidget.apply_kv_test10)
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

        f = KV_f(ProxyWidget.apply_kv_test11)
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

    def canvas_rule6(self):
        self.value = 42
        self.widget = Widget()
        with KVCtx():
            with KVRule(delay=None):
                self.value ^= self.widget.width


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

    def test_canvas_explicit_rule_mix_flipped(self):
        KV_f = KV()
        with self.assertRaises(KVCompilerParserException):
            KV_f(CanvasWidget.canvas_rule6)

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


class SyntaxUnbindingCtxRulePropsWidget(BaseWidget):

    ctx = None

    ctx2 = None

    ctx3 = None

    count = 0

    def unbind_rule(self):
        self.widget = Widget()
        with KVCtx() as self.ctx:
            self.value @= self.widget.width

    def unbind_rule2(self):
        self.widget = Widget()
        with KVCtx() as self.ctx:
            with KVRule(self.widget.width):
                self.value = self.widget.width

    def unbind_rule3(self):
        self.widget = Widget()
        self.widget2 = Widget()
        self.widget3 = Widget()

        with KVCtx() as self.ctx:
            with KVRule(self.widget.width, name='first'):
                self.value @= self.widget.width

            with KVCtx() as self.ctx3:
                with KVRule(self.widget3.width, name='third'):
                    self.value3 @= self.widget3.width
                self.value3 @= self.widget3.height

            self.value @= self.widget.height

        with KVCtx() as self.ctx2:
            self.value2 @= self.widget2.height
            with KVRule(self.widget2.width, name='second'):
                self.value2 @= self.widget2.width

    def unbind_rule4(self):
        self.widget = Widget()
        with KVCtx() as self.ctx:
            self.value @= self.widget.width
            self.value2 @= self.widget.width

    def unbind_rule5(self):
        self.widget = Widget()
        with KVCtx() as self.ctx:
            with KVRule(self.widget.width):
                self.count += 1
                self.value @= \
                    self.widget.width + self.widget.width + self.widget.width

    def unbind_rule6(self):
        self.value2 = 0
        self.widget = Widget()
        self.widget2 = Widget()
        widget = self.widget3 = Widget()

        with KVCtx() as self.ctx:
            with KVRule():
                self.count += 1
                self.value @= (
                    self.widget if self.value2 else self.widget2).width + \
                    widget.height
            self.value3 @= self.widget.width

    def dict_rule7(self):
        self.value_dict = {0: 44, 1: 23}
        self.value2 = 0

        with KVCtx() as self.ctx:
            with KVRule():
                self.count += 1
                self.value @= self.value_dict[self.value2] + 76

    def dict_rule8(self):
        self.value_dict = {0: 44, 1: 23, 2: 87}
        self.value2 = 0
        self.value3 = 0

        with KVCtx() as self.ctx:
            with KVRule():
                self.count += 1
                self.value @= \
                    self.value_dict[self.value2 + self.value3] + self.value3

    def dict_rule9(self):
        self.widget = Widget()
        self.widget2 = Widget()
        self.value_dict = {0: self.widget, 1: self.widget2}
        self.value2 = 0

        with KVCtx() as self.ctx:
            with KVRule():
                self.count += 1
                self.value @= self.value_dict[self.value2].width + self.value3

    def apply_kv_test(self):
        self.widget = Widget()
        with KVCtx() as self.ctx:
            self.value @= self.widget.width

    def apply_kv_test2(self):
        self.widget = Widget()
        with KVCtx() as self.ctx:
            with KVRule(delay=None):
                self.value @= self.widget.width

    def apply_kv_test3(self):
        self.widget = Widget()
        with KVCtx() as self.ctx:
            self.value ^= self.widget.width

    def apply_kv_test4(self):
        self.widget = Widget()
        with KVCtx() as self.ctx:
            with KVRule(delay='canvas'):
                self.value ^= self.widget.width

    def apply_kv_test5(self):
        self.widget = Widget()
        with KVCtx() as self.ctx:
            with KVRule(delay=0):
                self.value @= self.widget.width


@skip_py2_decorator
class TestSyntaxUnbindingCtxRulePropsWidget(TestBase):

    def test_unbind_rule(self):
        KV_f = KV()
        f = KV_f(SyntaxUnbindingCtxRulePropsWidget.unbind_rule)
        w = SyntaxUnbindingCtxRulePropsWidget()
        f(w)

        self.assertEqual(len(w.ctx.bind_store), 2)
        self.assertEqual(len(w.ctx.rules[0].bind_store_leaf_indices), 1)
        self.assertIsNotNone(w.ctx.rules[0].bind_store)
        for item in w.ctx.bind_store:
            self.assertIsNotNone(item)

        self.assertEqual(w.value, w.widget.width)
        w.widget.width = 453
        self.assertEqual(w.value, 453)

        w.ctx.unbind_all_rules()
        w.widget.width = 756
        self.assertEqual(w.value, 453)

        for item in w.ctx.bind_store:
            self.assertIsNone(item)

    def test_unbind_rule_explicit(self):
        KV_f = KV()
        f = KV_f(SyntaxUnbindingCtxRulePropsWidget.unbind_rule2)
        w = SyntaxUnbindingCtxRulePropsWidget()
        f(w)

        self.assertEqual(len(w.ctx.bind_store), 2)
        self.assertEqual(len(w.ctx.rules[0].bind_store_leaf_indices), 1)
        self.assertIsNotNone(w.ctx.rules[0].bind_store)
        for item in w.ctx.bind_store:
            self.assertIsNotNone(item)

        self.assertEqual(w.value, w.widget.width)
        w.widget.width = 453
        self.assertEqual(w.value, 453)

        w.ctx.unbind_all_rules()
        w.widget.width = 756
        self.assertEqual(w.value, 453)

        for item in w.ctx.bind_store:
            self.assertIsNone(item)

    def test_unbind_rule_multi(self):
        from random import randint
        KV_f = KV()
        f = KV_f(SyntaxUnbindingCtxRulePropsWidget.unbind_rule3)
        w = SyntaxUnbindingCtxRulePropsWidget()
        f(w)

        self.assertEqual(len(w.ctx.bind_store), 3)
        self.assertIs(w.ctx.bind_store, w.ctx.rules[0].bind_store)
        self.assertIs(w.ctx.bind_store, w.ctx.rules[1].bind_store)
        self.assertEqual(len(w.ctx.rules[0].bind_store_leaf_indices), 1)
        self.assertEqual(len(w.ctx.rules[1].bind_store_leaf_indices), 1)

        self.assertEqual(len(w.ctx2.bind_store), 3)
        self.assertIs(w.ctx2.bind_store, w.ctx2.rules[0].bind_store)
        self.assertIs(w.ctx2.bind_store, w.ctx2.rules[1].bind_store)
        self.assertEqual(len(w.ctx2.rules[0].bind_store_leaf_indices), 1)
        self.assertEqual(len(w.ctx2.rules[1].bind_store_leaf_indices), 1)

        self.assertEqual(len(w.ctx3.bind_store), 3)
        self.assertIs(w.ctx3.bind_store, w.ctx3.rules[0].bind_store)
        self.assertIs(w.ctx3.bind_store, w.ctx3.rules[1].bind_store)
        self.assertEqual(len(w.ctx3.rules[0].bind_store_leaf_indices), 1)
        self.assertEqual(len(w.ctx3.rules[1].bind_store_leaf_indices), 1)

        for item in w.ctx.bind_store:
            self.assertIsNotNone(item)
        for item in w.ctx2.bind_store:
            self.assertIsNotNone(item)
        for item in w.ctx3.bind_store:
            self.assertIsNotNone(item)

        self.assertEqual(w.value, w.widget.height)
        self.assertEqual(w.value2, w.widget2.width)
        self.assertEqual(w.value3, w.widget3.height)

        def check_1_1(bound=True):
            orig = w.value
            w.widget.width = randint(0, 100000)
            if bound:
                self.assertEqual(w.value, w.widget.width)
            else:
                self.assertEqual(w.value, orig)

        def check_1_2(bound=True):
            orig = w.value
            w.widget.height = randint(0, 100000)
            if bound:
                self.assertEqual(w.value, w.widget.height)
            else:
                self.assertEqual(w.value, orig)

        def check_2_1(bound=True):
            orig = w.value2
            w.widget2.height = randint(0, 100000)
            if bound:
                self.assertEqual(w.value2, w.widget2.height)
            else:
                self.assertEqual(w.value2, orig)

        def check_2_2(bound=True):
            orig = w.value2
            w.widget2.width = randint(0, 100000)
            if bound:
                self.assertEqual(w.value2, w.widget2.width)
            else:
                self.assertEqual(w.value2, orig)

        def check_3_1(bound=True):
            orig = w.value3
            w.widget3.width = randint(0, 100000)
            if bound:
                self.assertEqual(w.value3, w.widget3.width)
            else:
                self.assertEqual(w.value3, orig)

        def check_3_2(bound=True):
            orig = w.value3
            w.widget3.height = randint(0, 100000)
            if bound:
                self.assertEqual(w.value3, w.widget3.height)
            else:
                self.assertEqual(w.value3, orig)

        self.assertIs(w.ctx.named_rules['first'], w.ctx.rules[0])
        self.assertIs(w.ctx2.named_rules['second'], w.ctx2.rules[1])
        self.assertIs(w.ctx3.named_rules['third'], w.ctx3.rules[0])

        self.assertEqual(len(w.ctx.rules), 2)
        self.assertEqual(len(w.ctx2.rules), 2)
        self.assertEqual(len(w.ctx3.rules), 2)

        check_1_1()
        check_1_2()
        check_2_1()
        check_2_2()
        check_3_1()
        check_3_2()

        w.ctx.named_rules['first'].unbind_rule()
        check_1_1(bound=False)
        check_1_2()
        check_2_1()
        check_2_2()
        check_3_1()
        check_3_2()
        w.ctx.named_rules['first'].unbind_rule()  # check no error

        w.ctx3.rules[1].unbind_rule()
        check_1_1(bound=False)
        check_1_2()
        check_2_1()
        check_2_2()
        check_3_1()
        check_3_2(bound=False)
        w.ctx3.rules[1].unbind_rule()  # check no error

        w.ctx2.named_rules['second'].unbind_rule()
        check_1_1(bound=False)
        check_1_2()
        check_2_1()
        check_2_2(bound=False)
        check_3_1()
        check_3_2(bound=False)
        w.ctx2.named_rules['second'].unbind_rule()  # check no error

        w.ctx3.named_rules['third'].unbind_rule()
        check_1_1(bound=False)
        check_1_2()
        check_2_1()
        check_2_2(bound=False)
        check_3_1(bound=False)
        check_3_2(bound=False)
        w.ctx3.named_rules['third'].unbind_rule()  # check no error

        w.ctx2.rules[0].unbind_rule()
        check_1_1(bound=False)
        check_1_2()
        check_2_1(bound=False)
        check_2_2(bound=False)
        check_3_1(bound=False)
        check_3_2(bound=False)
        w.ctx2.rules[0].unbind_rule()  # check no error

        w.ctx.rules[1].unbind_rule()
        check_1_1(bound=False)
        check_1_2(bound=False)
        check_2_1(bound=False)
        check_2_2(bound=False)
        check_3_1(bound=False)
        check_3_2(bound=False)
        w.ctx.rules[1].unbind_rule()  # check no error

        self.assertEqual(len(w.ctx.bind_store), 3)
        self.assertIsNone(w.ctx.rules[0].bind_store)
        self.assertIsNone(w.ctx.rules[1].bind_store)
        self.assertEqual(len(w.ctx.rules[0].bind_store_leaf_indices), 0)
        self.assertEqual(len(w.ctx.rules[1].bind_store_leaf_indices), 0)

        self.assertEqual(len(w.ctx2.bind_store), 3)
        self.assertIsNone(w.ctx2.rules[0].bind_store)
        self.assertIsNone(w.ctx2.rules[1].bind_store)
        self.assertEqual(len(w.ctx2.rules[0].bind_store_leaf_indices), 0)
        self.assertEqual(len(w.ctx2.rules[1].bind_store_leaf_indices), 0)

        self.assertEqual(len(w.ctx3.bind_store), 3)
        self.assertIsNone(w.ctx3.rules[0].bind_store)
        self.assertIsNone(w.ctx3.rules[1].bind_store)
        self.assertEqual(len(w.ctx3.rules[0].bind_store_leaf_indices), 0)
        self.assertEqual(len(w.ctx3.rules[1].bind_store_leaf_indices), 0)

        for item in w.ctx.bind_store:
            self.assertIsNone(item)
        for item in w.ctx2.bind_store:
            self.assertIsNone(item)
        for item in w.ctx3.bind_store:
            self.assertIsNone(item)

        w.ctx.unbind_all_rules()
        check_1_1(bound=False)
        check_1_2(bound=False)
        check_2_1(bound=False)
        check_2_2(bound=False)
        check_3_1(bound=False)
        check_3_2(bound=False)

    def test_unbind_rebind(self):
        KV_f = KV(rebind=True)
        f = KV_f(SyntaxUnbindingCtxRulePropsWidget.unbind_rule4)
        w = SyntaxUnbindingCtxRulePropsWidget()
        f(w)

        self.assertEqual(len(w.ctx.bind_store), 3)
        self.assertEqual(len(w.ctx.rules[0].bind_store_leaf_indices), 1)
        self.assertIs(w.ctx.rules[0].bind_store, w.ctx.bind_store)
        self.assertEqual(len(w.ctx.rules[1].bind_store_leaf_indices), 1)
        self.assertIs(w.ctx.rules[1].bind_store, w.ctx.bind_store)
        for item in w.ctx.bind_store:
            self.assertIsNotNone(item)

        self.assertEqual(w.value, w.widget.width)
        self.assertEqual(w.value2, w.widget.width)

        w.widget.width = 56
        self.assertEqual(w.value, 56)
        self.assertEqual(w.value2, 56)

        w.ctx.rules[0].unbind_rule()
        w.widget.width = 43
        self.assertEqual(w.value, 56)
        self.assertEqual(w.value2, 43)

        w.widget = Widget()
        self.assertEqual(w.value, 56)
        self.assertEqual(w.value2, w.widget.width)

        w.widget.width = 5123
        self.assertEqual(w.value, 56)
        self.assertEqual(w.value2, 5123)

        w.ctx.rules[1].unbind_rule()
        w.widget.width = 155
        self.assertEqual(w.value, 56)
        self.assertEqual(w.value2, 5123)

        for item in w.ctx.bind_store:
            self.assertIsNone(item)

    def test_unbind_rule_explicit_multiple_of_same(self):
        KV_f = KV()
        f = KV_f(SyntaxUnbindingCtxRulePropsWidget.unbind_rule5)
        w = SyntaxUnbindingCtxRulePropsWidget()
        f(w)

        self.assertEqual(len(w.ctx.bind_store), 2)
        self.assertEqual(len(w.ctx.rules[0].bind_store_leaf_indices), 1)
        self.assertIs(w.ctx.rules[0].bind_store, w.ctx.bind_store)
        for item in w.ctx.bind_store:
            self.assertIsNotNone(item)

        self.assertEqual(w.value, 3 * w.widget.width)
        count = w.count
        w.widget.width = 851
        self.assertEqual(w.value, 3 * 851)
        self.assertEqual(count + 1, w.count)

        w.widget.width = 65
        self.assertEqual(w.value, 3 * 65)
        self.assertEqual(count + 2, w.count)

        w.ctx.unbind_all_rules()
        w.widget.width = 59
        self.assertEqual(w.value, 3 * 65)

        for item in w.ctx.bind_store:
            self.assertIsNone(item)

    def test_unbind_rule_full_syntax(self):
        KV_f = KV(kv_syntax=None, rebind=True)
        f = KV_f(SyntaxUnbindingCtxRulePropsWidget.unbind_rule6)
        w = SyntaxUnbindingCtxRulePropsWidget()
        f(w)

        self.assertEqual(len(w.ctx.bind_store), 7)
        self.assertIs(w.ctx.bind_store, w.ctx.rules[0].bind_store)
        self.assertIs(w.ctx.bind_store, w.ctx.rules[1].bind_store)
        self.assertEqual(len(w.ctx.rules[0].bind_store_leaf_indices), 2)
        self.assertEqual(len(w.ctx.rules[1].bind_store_leaf_indices), 1)
        for item in w.ctx.bind_store:
            self.assertIsNotNone(item)

        orig = w.widget2.width + w.widget3.height
        self.assertEqual(w.value, orig)
        w.widget.width = 433
        self.assertEqual(w.value, orig)
        self.assertEqual(w.value3, w.widget.width)
        w.widget2.width = 786
        self.assertEqual(w.value, w.widget2.width + w.widget3.height)
        w.widget3.height = 987
        self.assertEqual(w.value, w.widget2.width + w.widget3.height)
        self.assertEqual(w.value3, w.widget.width)

        w.value2 = 1

        orig = w.widget.width + w.widget3.height
        self.assertEqual(w.value, orig)
        w.widget2.width = 34
        self.assertEqual(w.value, orig)
        w.widget.width = 67
        self.assertEqual(w.value3, w.widget.width)
        self.assertEqual(w.value, w.widget.width + w.widget3.height)
        w.widget3.height = 123
        self.assertEqual(w.value, w.widget.width + w.widget3.height)
        self.assertEqual(w.value3, w.widget.width)

        w.widget2 = Widget()

        orig = w.widget.width + w.widget3.height
        self.assertEqual(w.value, orig)
        w.widget2.width = 3298
        self.assertEqual(w.value, orig)
        w.widget.width = 1896
        self.assertEqual(w.value3, w.widget.width)
        self.assertEqual(w.value, w.widget.width + w.widget3.height)
        w.widget3.height = 872
        self.assertEqual(w.value, w.widget.width + w.widget3.height)
        self.assertEqual(w.value3, w.widget.width)

        w.widget = Widget()

        orig = w.widget.width + w.widget3.height
        self.assertEqual(w.value, orig)
        w.widget2.width = 4567
        self.assertEqual(w.value, orig)
        w.widget.width = 345
        self.assertEqual(w.value3, w.widget.width)
        self.assertEqual(w.value, w.widget.width + w.widget3.height)
        w.widget3.height = 987
        self.assertEqual(w.value, w.widget.width + w.widget3.height)
        self.assertEqual(w.value3, w.widget.width)

        orig2 = w.value3
        orig = w.widget.width + w.widget3.height
        w.ctx.rules[1].unbind_rule()

        self.assertEqual(w.value, orig)
        w.widget2.width = 6734
        self.assertEqual(w.value, orig)
        self.assertEqual(w.value3, orig2)
        w.widget.width = 347
        self.assertEqual(w.value3, orig2)
        self.assertEqual(w.value, w.widget.width + w.widget3.height)
        w.widget3.height = 987
        self.assertEqual(w.value, w.widget.width + w.widget3.height)
        self.assertEqual(w.value3, orig2)

        orig2 = w.value3
        orig = w.widget.width + w.widget3.height
        w.ctx.rules[0].unbind_rule()

        self.assertEqual(w.value, orig)
        w.widget2.width = 6734
        self.assertEqual(w.value, orig)
        self.assertEqual(w.value3, orig2)
        w.widget.width = 347
        self.assertEqual(w.value3, orig2)
        self.assertEqual(w.value, orig)
        w.widget3.height = 987
        self.assertEqual(w.value, orig)
        self.assertEqual(w.value3, orig2)

    def test_unbind_rule_full_syntax_flipped(self):
        KV_f = KV(kv_syntax=None, rebind=True)
        f = KV_f(SyntaxUnbindingCtxRulePropsWidget.unbind_rule6)
        w = SyntaxUnbindingCtxRulePropsWidget()
        f(w)

        orig = w.widget2.width + w.widget3.height
        self.assertEqual(w.value, orig)
        w.widget.width = 867
        self.assertEqual(w.value, orig)
        self.assertEqual(w.value3, w.widget.width)
        w.widget2.width = 234
        self.assertEqual(w.value, w.widget2.width + w.widget3.height)
        w.widget3.height = 437
        self.assertEqual(w.value, w.widget2.width + w.widget3.height)
        self.assertEqual(w.value3, w.widget.width)

        orig2 = w.value3
        orig = w.widget2.width + w.widget3.height
        self.assertEqual(w.value, orig)
        self.assertEqual(w.value3, orig2)
        w.ctx.rules[0].unbind_rule()

        self.assertEqual(w.value, orig)
        w.widget2.width = 357
        self.assertEqual(w.value, orig)
        self.assertEqual(w.value3, orig2)
        w.widget.width = 457
        self.assertEqual(w.value3, w.widget.width)
        self.assertEqual(w.value, orig)
        w.widget3.height = 349
        self.assertEqual(w.value, orig)
        self.assertEqual(w.value3, w.widget.width)

        orig2 = w.value3
        w.ctx.rules[1].unbind_rule()

        self.assertEqual(w.value, orig)
        w.widget2.width = 67342
        self.assertEqual(w.value, orig)
        self.assertEqual(w.value3, orig2)
        w.widget.width = 8346
        self.assertEqual(w.value3, orig2)
        self.assertEqual(w.value, orig)
        w.widget3.height = 9546
        self.assertEqual(w.value, orig)
        self.assertEqual(w.value3, orig2)

    def test_syntax_rule_dict(self):
        KV_f = KV(kv_syntax='minimal', rebind=True)
        f = KV_f(SyntaxUnbindingCtxRulePropsWidget.dict_rule7)
        w = SyntaxUnbindingCtxRulePropsWidget()
        f(w)

        count = w.count
        self.assertEqual(w.value, 44 + 76)
        w.value_dict[0] = 89
        self.assertEqual(w.value, 89 + 76)
        self.assertEqual(w.count, count + 1)

        w.value_dict[1] = 26
        self.assertEqual(w.value, 89 + 76)
        self.assertEqual(w.count, count + 2)

        w.value2 = 1
        self.assertEqual(w.value, 26 + 76)
        self.assertEqual(w.count, count + 3)

    def test_syntax_rule_dict_multi(self):
        KV_f = KV(kv_syntax='minimal', rebind=True)
        f = KV_f(SyntaxUnbindingCtxRulePropsWidget.dict_rule8)
        w = SyntaxUnbindingCtxRulePropsWidget()
        f(w)

        count = w.count
        self.assertEqual(w.value, 44 + 0)
        w.value_dict[0] = 89
        self.assertEqual(w.value, 89 + 0)
        self.assertEqual(w.count, count + 1)

        w.value_dict[1] = 26
        self.assertEqual(w.value, 89 + 0)
        self.assertEqual(w.count, count + 2)

        w.value2 = 1
        self.assertEqual(w.value, 26 + 0)
        self.assertEqual(w.count, count + 3)

        w.value3 = 1
        self.assertEqual(w.value, 87 + 1)
        self.assertEqual(w.count, count + 4)

        w.value2 = 0
        self.assertEqual(w.value, 26 + 1)
        self.assertEqual(w.count, count + 5)

        w.ctx.unbind_all_rules()
        w.value2 = 1
        w.value3 = 0
        w.value_dict[0] = 654
        self.assertEqual(w.value, 26 + 1)
        self.assertEqual(w.count, count + 5)

    def test_syntax_rule_dict_rebind(self):
        KV_f = KV(kv_syntax='minimal', rebind=True)
        f = KV_f(SyntaxUnbindingCtxRulePropsWidget.dict_rule9)
        w = SyntaxUnbindingCtxRulePropsWidget()
        f(w)

        self.assertEqual(w.value, w.widget.width + w.value3)
        w.widget.width = 354
        self.assertEqual(w.value, w.widget.width + w.value3)
        orig = w.widget.width + w.value3
        w.widget2.width = 43
        self.assertEqual(w.value, orig)

        w.value2 = 1
        self.assertEqual(w.value, w.widget2.width + w.value3)
        w.widget2.width = 45
        self.assertEqual(w.value, w.widget2.width + w.value3)
        orig = w.widget2.width + w.value3
        w.widget.width = 585
        self.assertEqual(w.value, orig)

        w.value3 = 435
        self.assertEqual(w.value, w.widget2.width + w.value3)

    def test_callback_rule(self):
        KV_f = KV()
        f = KV_f(SyntaxUnbindingCtxRulePropsWidget.apply_kv_test)
        w = SyntaxUnbindingCtxRulePropsWidget()
        f(w)

        self.assertIsNotNone(w.ctx.rules[0].callback)
        self.assertIsNone(w.ctx.rules[0]._callback)
        self.assertEqual(w.ctx.rules[0].delay, None)

    def test_callback_rule_explicit(self):
        KV_f = KV()
        f = KV_f(SyntaxUnbindingCtxRulePropsWidget.apply_kv_test2)
        w = SyntaxUnbindingCtxRulePropsWidget()
        f(w)

        self.assertIsNotNone(w.ctx.rules[0].callback)
        self.assertIsNone(w.ctx.rules[0]._callback)
        self.assertEqual(w.ctx.rules[0].delay, None)

    def test_callback_rule_canvas(self):
        KV_f = KV()
        f = KV_f(SyntaxUnbindingCtxRulePropsWidget.apply_kv_test3)
        w = SyntaxUnbindingCtxRulePropsWidget()
        f(w)

        self.assertIsNotNone(w.ctx.rules[0].callback)
        self.assertIsNotNone(w.ctx.rules[0]._callback)
        self.assertEqual(w.ctx.rules[0].delay, 'canvas')

    def test_callback_rule_explicit_canvas(self):
        KV_f = KV()
        f = KV_f(SyntaxUnbindingCtxRulePropsWidget.apply_kv_test4)
        w = SyntaxUnbindingCtxRulePropsWidget()
        f(w)

        self.assertIsNotNone(w.ctx.rules[0].callback)
        self.assertIsNotNone(w.ctx.rules[0]._callback)
        self.assertEqual(w.ctx.rules[0].delay, 'canvas')

    def test_callback_rule_explicit_clock(self):
        KV_f = KV()
        f = KV_f(SyntaxUnbindingCtxRulePropsWidget.apply_kv_test5)
        w = SyntaxUnbindingCtxRulePropsWidget()
        f(w)

        self.assertIsNotNone(w.ctx.rules[0].callback)
        self.assertIsNotNone(w.ctx.rules[0]._callback)
        self.assertEqual(w.ctx.rules[0].delay, 0)


class EventBindWidget(BaseWidget):

    ctx = None

    def on_touch_down(self, touch):
        pass

    def apply_kv_test(self):
        with KVCtx() as self.ctx:
            with KVRule(self.on_touch_down) as my_rule:
                self.value_object = my_rule.largs

    def apply_kv_test2(self):
        self.value2 = 0
        with KVCtx() as self.ctx:
            with KVRule(self.on_touch_down, self.value2) as my_rule:
                self.value @= self.value2


@skip_py2_decorator
class TestEventBind(TestBase):

    def test_event(self):
        KV_f = KV()
        f = KV_f(EventBindWidget.apply_kv_test)
        w = EventBindWidget()
        f(w)

        self.assertEqual(w.value_object, ())
        w.dispatch('on_touch_down', "here's johnny")
        self.assertEqual(w.value_object, (w, "here's johnny"))
        w.dispatch('on_touch_down', "blah")
        self.assertEqual(w.value_object, (w, "blah"))

        w.ctx.unbind_all_rules()
        w.dispatch('on_touch_down', "friday!!!")
        self.assertEqual(w.value_object, (w, "blah"))

    def test_event_multi(self):
        KV_f = KV()
        f = KV_f(EventBindWidget.apply_kv_test2)
        w = EventBindWidget()
        f(w)

        self.assertEqual(w.value, 0)

        w.dispatch('on_touch_down', "here's johnny")
        self.assertEqual(w.ctx.rules[0].largs, (w, "here's johnny"))
        w.dispatch('on_touch_down', "blah")
        self.assertEqual(w.ctx.rules[0].largs, (w, "blah"))
        w.value2 = 76
        self.assertEqual(w.ctx.rules[0].largs, (w, 76))

        w.ctx.unbind_all_rules()
        w.dispatch('on_touch_down', "friday!!!")
        self.assertEqual(w.ctx.rules[0].largs, (w, 76))
        w.value2 = 56
        self.assertEqual(w.ctx.rules[0].largs, (w, 76))


class RebindWidget(BaseWidget):

    def apply_kv_test(self):
        self.widget = Widget()
        self.widget2 = Widget()

        with KVCtx():
            self.value @= self.widget.width + self.widget2.width

    def apply_kv_test2(self):
        self.widget = Widget()
        self.widget2 = Widget()

        with KVCtx():
            self.value @= self.widget.width + self.widget2.width

    def apply_kv_test3(self):
        self.widget = Widget()
        self.widget2 = Widget()

        with KVCtx():
            self.value @= self.widget.width + self.widget2.width

    def apply_kv_test4(self):
        self.widget = Widget()
        self.widget2 = Widget()

        with KVCtx():
            self.value @= self.widget.width + self.widget2.width

    def apply_kv_test5(self):
        self.widget = Widget()
        self.widget2 = Widget()

        with KVCtx():
            self.value @= self.widget.width + self.widget2.width

    def apply_kv_test6(self):
        self.widget = Widget()
        self.widget2 = Widget()

        with KVCtx():
            self.value @= self.widget.width + self.widget2.width


@skip_py2_decorator
class TestRebind(TestBase):

    def test_rebind(self):
        KV_f = KV(rebind=False)
        f = KV_f(RebindWidget.apply_kv_test)
        w = RebindWidget()
        f(w)

        self.assertEqual(w.value, w.widget.width + w.widget2.width)
        w.widget.width = 54
        self.assertEqual(w.value, w.widget.width + w.widget2.width)
        w.widget2.width = 856
        self.assertEqual(w.value, w.widget.width + w.widget2.width)

        orig_widget = w.widget
        orig_widget2 = w.widget2
        w.widget = Widget()
        w.widget2 = Widget()
        self.assertEqual(w.value, orig_widget.width + orig_widget2.width)
        w.widget.width = 67
        self.assertEqual(w.value, orig_widget.width + orig_widget2.width)
        w.widget2.width = 568
        self.assertEqual(w.value, orig_widget.width + orig_widget2.width)
        orig_widget.width = 5637
        self.assertEqual(w.value, w.widget.width + w.widget2.width)
        orig_widget2.width = 6854
        self.assertEqual(w.value, w.widget.width + w.widget2.width)

    def test_rebind_true(self):
        KV_f = KV(rebind=True)
        f = KV_f(RebindWidget.apply_kv_test2)
        w = RebindWidget()
        f(w)

        self.assertEqual(w.value, w.widget.width + w.widget2.width)
        w.widget.width = 41
        self.assertEqual(w.value, w.widget.width + w.widget2.width)
        w.widget2.width = 872
        self.assertEqual(w.value, w.widget.width + w.widget2.width)

        orig_widget = w.widget
        orig_widget2 = w.widget2
        w.widget = Widget()
        w.widget2 = Widget()
        self.assertEqual(w.value, w.widget.width + w.widget2.width)
        w.widget.width = 782
        self.assertEqual(w.value, w.widget.width + w.widget2.width)
        w.widget2.width = 2748
        self.assertEqual(w.value, w.widget.width + w.widget2.width)
        orig_widget.width = 456
        self.assertEqual(w.value, w.widget.width + w.widget2.width)
        orig_widget2.width = 78
        self.assertEqual(w.value, w.widget.width + w.widget2.width)

    def rebind_partial_base(self, f, params):
        KV_f = KV(rebind=params)
        f = KV_f(f)
        w = RebindWidget()
        f(w)

        self.assertEqual(w.value, w.widget.width + w.widget2.width)
        w.widget.width = 786
        self.assertEqual(w.value, w.widget.width + w.widget2.width)
        w.widget2.width = 468
        self.assertEqual(w.value, w.widget.width + w.widget2.width)

        orig_widget = w.widget
        orig_widget2 = w.widget2
        w.widget2 = Widget()
        # this must be set last, because the rule don't exec for
        # `w.widget2 = Widget()` so the value won't match
        w.widget = Widget()
        self.assertEqual(w.value, w.widget.width + w.widget2.width)
        w.widget.width = 4864
        self.assertEqual(w.value, w.widget.width + w.widget2.width)
        orig_val = w.widget.width + w.widget2.width
        w.widget2.width = 34
        self.assertEqual(w.value, orig_val)
        orig_widget.width = 45674
        self.assertEqual(w.value, orig_val)
        orig_widget2.width = 756
        self.assertEqual(w.value, w.widget.width + w.widget2.width)

    def test_rebind_partial(self):
        self.rebind_partial_base(RebindWidget.apply_kv_test3, '*.widget')

    def test_rebind_partial2(self):
        self.rebind_partial_base(RebindWidget.apply_kv_test4, '*dget')

    def test_rebind_partial3(self):
        self.rebind_partial_base(RebindWidget.apply_kv_test5, ['*.widget'])

    def test_rebind_partial4(self):
        self.rebind_partial_base(
            RebindWidget.apply_kv_test6, ['*.widget', 'sfsd', '*cheese'])


class ManualKVWidget(BaseWidget):

    ctx = None

    def apply_kv_test(self):
        self.widget = Widget()
        self.widget2 = Widget()
        self.ctx = ctx = KVParserCtx()

        def manage_val(*largs):
            self.value = self.widget.width + self.widget2.width
        manage_val()

        rule = KVParserRule('self.widget.width + self.widget2.width')
        rule.callback = manage_val
        rule.callback_name = manage_val.__name__
        ctx.add_rule(rule)

        KV_apply_manual(
            ctx, self.apply_kv_test, locals(), globals(), rebind=True)


@skip_py2_decorator
class TestManualKV(TestBase):

    def test_manual(self):
        w = ManualKVWidget()
        w.apply_kv_test()

        self.assertEqual(w.value, w.widget.width + w.widget2.width)
        w.widget.width = 41
        self.assertEqual(w.value, w.widget.width + w.widget2.width)
        w.widget2.width = 872
        self.assertEqual(w.value, w.widget.width + w.widget2.width)

        orig_widget = w.widget
        orig_widget2 = w.widget2
        w.widget = Widget()
        w.widget2 = Widget()
        self.assertEqual(w.value, w.widget.width + w.widget2.width)
        w.widget.width = 782
        self.assertEqual(w.value, w.widget.width + w.widget2.width)
        w.widget2.width = 2748
        self.assertEqual(w.value, w.widget.width + w.widget2.width)
        orig_widget.width = 456
        self.assertEqual(w.value, w.widget.width + w.widget2.width)
        orig_widget2.width = 78
        self.assertEqual(w.value, w.widget.width + w.widget2.width)

        self.assertEqual(len(w.ctx.rebind_functions), 2)
        self.assertEqual(len(w.ctx.named_rules), 0)
        self.assertEqual(len(w.ctx.rules), 1)
        rule = w.ctx.rules[0]
        self.assertEqual(len(rule.bind_store_leaf_indices), 2)
        self.assertEqual(len(rule.bind_store), 4)
        self.assertIsNotNone(rule.callback)
        self.assertIsNone(rule.delay)
        self.assertIsNone(rule.name)
        self.assertIsNone(rule._callback)
        self.assertEqual(rule.largs, ())


class NoneLocalsWidget(BaseWidget):

    def apply_kv_test(self):
        widget = None
        with KVCtx():
            self.value @= widget.height

    def apply_kv_test2(self):
        self.widget = None
        with KVCtx():
            self.value @= self.widget.height

    def apply_kv_test3(self):
        self.widget = None
        with KVCtx():
            self.value @= self.widget.height if self.widget is not None else 55


@skip_py2_decorator
class TestNoneLocal(TestBase):

    def test_None_local(self):
        KV_f = KV()
        f = KV_f(NoneLocalsWidget.apply_kv_test)
        w = NoneLocalsWidget()
        with self.assertRaises(AttributeError):
            f(w)

    def test_None_local_attr(self):
        KV_f = KV()
        f = KV_f(NoneLocalsWidget.apply_kv_test2)
        w = NoneLocalsWidget()
        with self.assertRaises(AttributeError):
            f(w)

    def test_None_local_attr_protected(self):
        KV_f = KV()
        f = KV_f(NoneLocalsWidget.apply_kv_test3)
        w = NoneLocalsWidget()
        f(w)

        self.assertEqual(w.value, 55)
        w.widget = Widget()
        self.assertEqual(w.value, w.widget.height)
        w.widget.height = 9645
        self.assertEqual(w.value, w.widget.height)
        w.widget = None
        self.assertEqual(w.value, 55)

        w.widget = Widget()
        self.assertEqual(w.value, w.widget.height)
        w.widget.height = 128
        self.assertEqual(w.value, w.widget.height)
        w.widget = None
        self.assertEqual(w.value, 55)


@skip_py2_decorator
class TestASTWhitelist(TestBase):

    def test_ast_whitelist_minimal(self):
        from kivy.lang.compiler.ast_parse import \
            ParseKVBindTransformer, ParseCheckWhitelisted, parse_expr_ast
        whitelist = ParseKVBindTransformer.whitelist_opts['minimal']
        checker = ParseCheckWhitelisted(whitelist)

        checker.check_node_graph(parse_expr_ast('self.x'))
        for node, illegal in checker.node_has_illegal_parent.items():
            self.assertFalse(illegal)

        checker.check_node_graph(parse_expr_ast('self.z.h'))
        for node, illegal in checker.node_has_illegal_parent.items():
            self.assertFalse(illegal)

        checker.check_node_graph(parse_expr_ast('other.x'))
        for node, illegal in checker.node_has_illegal_parent.items():
            self.assertFalse(illegal)

    def test_ast_whitelist_minimal_dict(self):
        from kivy.lang.compiler.ast_parse import \
            ParseKVBindTransformer, ParseCheckWhitelisted, parse_expr_ast
        whitelist = ParseKVBindTransformer.whitelist_opts['minimal']
        checker = ParseCheckWhitelisted(whitelist)

        checker.check_node_graph(parse_expr_ast('self.x.y[self.z].f'))
        for node, illegal in checker.node_has_illegal_parent.items():
            self.assertFalse(illegal)

        checker.check_node_graph(parse_expr_ast('self.x.y[self.x.y].f'))
        for node, illegal in checker.node_has_illegal_parent.items():
            self.assertFalse(illegal)

    def test_ast_whitelist_minimal_list(self):
        from kivy.lang.compiler.ast_parse import \
            ParseKVBindTransformer, ParseCheckWhitelisted, parse_expr_ast
        whitelist = ParseKVBindTransformer.whitelist_opts['minimal']
        checker = ParseCheckWhitelisted(whitelist)

        checker.check_node_graph(parse_expr_ast('self.x.y[55].f'))
        for node, illegal in checker.node_has_illegal_parent.items():
            self.assertFalse(illegal)

    def test_ast_whitelist_minimal_illegal(self):
        from kivy.lang.compiler.ast_parse import \
            ParseKVBindTransformer, ParseCheckWhitelisted, parse_expr_ast
        whitelist = ParseKVBindTransformer.whitelist_opts['minimal']
        checker = ParseCheckWhitelisted(whitelist)

        checker.check_node_graph(parse_expr_ast('(self.x + self.y).z'))
        for node, illegal in checker.node_has_illegal_parent.items():
            if isinstance(node, ast.Name) and node.id == 'self' or \
                    isinstance(node, ast.Attribute) and \
                    node.attr in ('x', 'y'):
                self.assertFalse(illegal)
            else:
                self.assertTrue(illegal)


@skip_py2_decorator
class TestGenerateSource(TestBase):

    def test_simple(self):
        from kivy.lang.compiler.ast_parse import generate_source
        s = 'self.x + self.y'
        node = ast.parse(s)
        self.assertEqual(s, generate_source(node))

    def test_node_list(self):
        from kivy.lang.compiler.ast_parse import generate_source, ASTNodeList

        node1 = ast.parse('self.x')
        node2 = ast.parse('self.y')
        node_list = ASTNodeList()
        node_list.nodes = [node1, node2]

        self.assertEqual('self.x\nself.y', generate_source(node_list))

    def test_node_list_indent(self):
        from kivy.lang.compiler.ast_parse import generate_source, ASTNodeList

        node1 = ast.parse('if self.x:\n    55')
        node2 = ast.parse('name = self.y')
        node_list = ASTNodeList()
        node_list.nodes = [node1, node2]

        self.assertEqual(
            'if self.x:\n    55\nname = self.y', generate_source(node_list))

    def test_node_str_placeholder(self):
        from kivy.lang.compiler.ast_parse import \
            generate_source, ASTStrPlaceholder

        node = ASTStrPlaceholder()
        node.src_lines = ['self.x', 'name = self.y']
        self.assertEqual('self.x\nname = self.y', generate_source(node))

    def test_node_str_placeholder_indented(self):
        from kivy.lang.compiler.ast_parse import \
            generate_source, ASTStrPlaceholder

        node = ASTStrPlaceholder()
        node.src_lines = ['self.x', 'name = self.y']

        if_node = ast.parse('if self.z:\n    55')
        if_node.body[0].body[0].value = node
        self.assertEqual(
            'if self.z:\n\n    self.x\n    name = self.y',
            generate_source(if_node))

    def test_node_str_ref(self):
        from kivy.lang.compiler.ast_parse import \
            generate_source, ASTBindNodeRef

        s = 'if self.z:\n    55'
        if_node = ast.parse(s)
        ref = ASTBindNodeRef(False)
        ref.ref_node = if_node
        self.assertEqual(s, generate_source(ref))


class TestParseASTBind(TestBase):

    def test_ast_rule_None(self):
        from kivy.lang.compiler.ast_parse import \
            ParseKVBindTransformer, parse_expr_ast
        transformer = ParseKVBindTransformer(kv_syntax='minimal')

        with self.assertRaises(ValueError):
            transformer.update_graph([parse_expr_ast('self.x + self.y')], None)

    def test_ast_whitelist_minimal(self):
        from kivy.lang.compiler.ast_parse import \
            ParseKVBindTransformer, parse_expr_ast
        transformer = ParseKVBindTransformer(kv_syntax='minimal')

        transformer.update_graph([parse_expr_ast('self.x + self.y')], 'rule')

        self.assertEqual(len(transformer.nodes_by_rule), 1)
        self.assertEqual(len(transformer.nodes_by_rule[0]), 3)

        # don't know if x, or y is visited first, but the following test work
        # whether x or y was visited first as exact identity is not assumed
        # but, whichever is first, their graph and rule order is the same
        n0, n1, n2 = transformer.nodes_by_rule[0]

        self.assertIsNone(n0.leaf_rule)
        self.assertEqual(n1.leaf_rule, 'rule')
        self.assertEqual(n2.leaf_rule, 'rule')

        self.assertFalse(n0.is_attribute)
        self.assertTrue(n1.is_attribute)
        self.assertTrue(n2.is_attribute)

        self.assertEqual(n0.count, 2)
        self.assertEqual(n1.count, 1)
        self.assertEqual(n2.count, 1)

        self.assertFalse(n0.depends)
        self.assertEqual(set(n0.depends_on_me), {n1, n2})
        self.assertEqual(set(n1.depends), {n0})
        self.assertEqual(set(n2.depends), {n0})
        self.assertFalse(n1.depends_on_me)
        self.assertFalse(n2.depends_on_me)

    def test_ast_whitelist_minimal_multi_rules(self):
        from kivy.lang.compiler.ast_parse import \
            ParseKVBindTransformer, parse_expr_ast
        transformer = ParseKVBindTransformer(kv_syntax='minimal')

        transformer.update_graph([parse_expr_ast('self.x + self.y')], 'rule1')
        transformer.update_graph([parse_expr_ast('self.x + self.y')], 'rule2')

        self.assertEqual(len(transformer.nodes_by_rule), 2)
        self.assertEqual(len(transformer.nodes_by_rule[0]), 3)
        self.assertEqual(len(transformer.nodes_by_rule[1]), 2)

        # don't know if x, or y is visited first, but the following test work
        # whether x or y was visited first as exact identity is not assumed
        # but, whichever is first, their graph and rule order is the same
        n0, n1, n2 = transformer.nodes_by_rule[0]
        n3, n4 = transformer.nodes_by_rule[1]

        self.assertIsNone(n0.leaf_rule)
        self.assertEqual(n1.leaf_rule, 'rule1')
        self.assertEqual(n2.leaf_rule, 'rule1')

        self.assertFalse(n0.is_attribute)
        self.assertTrue(n1.is_attribute)
        self.assertTrue(n2.is_attribute)

        self.assertEqual(n0.count, 4)
        self.assertEqual(n1.count, 1)
        self.assertEqual(n2.count, 1)

        self.assertEqual(n3.leaf_rule, 'rule2')
        self.assertEqual(n4.leaf_rule, 'rule2')

        self.assertTrue(n3.is_attribute)
        self.assertTrue(n4.is_attribute)

        self.assertEqual(n3.count, 1)
        self.assertEqual(n4.count, 1)

        self.assertFalse(n0.depends)
        self.assertEqual(set(n0.depends_on_me), {n1, n2, n3, n4})
        self.assertEqual(set(n1.depends), {n0})
        self.assertEqual(set(n2.depends), {n0})
        self.assertEqual(set(n3.depends), {n0})
        self.assertEqual(set(n4.depends), {n0})
        self.assertFalse(n1.depends_on_me)
        self.assertFalse(n2.depends_on_me)
        self.assertFalse(n3.depends_on_me)
        self.assertFalse(n4.depends_on_me)

    def test_ast_whitelist_minimal_reuse_node(self):
        from kivy.lang.compiler.ast_parse import \
            ParseKVBindTransformer, parse_expr_ast
        transformer = ParseKVBindTransformer(kv_syntax='minimal')

        transformer.update_graph([parse_expr_ast('self.x[self.x].z')], 'rule')

        self.assertEqual(len(transformer.nodes_by_rule), 1)
        self.assertEqual(len(transformer.nodes_by_rule[0]), 4)

        # don't know if x, or y is visited first, but the following test work
        # whether x or y was visited first as exact identity is not assumed
        # but, whichever is first, their graph and rule order is the same
        n0, n1, n2, n3 = transformer.nodes_by_rule[0]

        self.assertIsNone(n0.leaf_rule)
        self.assertIsNone(n1.leaf_rule)
        self.assertIsNone(n2.leaf_rule)
        self.assertEqual(n3.leaf_rule, 'rule')

        self.assertFalse(n0.is_attribute)
        self.assertTrue(n1.is_attribute)
        self.assertFalse(n2.is_attribute)
        self.assertTrue(n3.is_attribute)

        self.assertEqual(n0.count, 1)
        self.assertEqual(n1.count, 1)
        self.assertEqual(n2.count, 1)
        self.assertEqual(n3.count, 1)

        self.assertFalse(n0.depends)
        self.assertEqual(set(n0.depends_on_me), {n1})
        self.assertEqual(set(n1.depends), {n0})
        self.assertEqual(set(n1.depends_on_me), {n2})
        self.assertEqual(set(n2.depends), {n1})
        self.assertEqual(set(n2.depends_on_me), {n3})
        self.assertEqual(set(n3.depends), {n2})
        self.assertFalse(n3.depends_on_me)

    def test_ast_whitelist_minimal_reuse_forked_node(self):
        from kivy.lang.compiler.ast_parse import \
            ParseKVBindTransformer, parse_expr_ast
        transformer = ParseKVBindTransformer(kv_syntax='minimal')

        transformer.update_graph([parse_expr_ast('self.x[self.y].z')], 'rule')

        self.assertEqual(len(transformer.nodes_by_rule), 1)
        self.assertEqual(len(transformer.nodes_by_rule[0]), 5)

        # don't know if x, or y is visited first, but the following test work
        # whether x or y was visited first as exact identity is not assumed
        # but, whichever is first, their graph and rule order is the same
        n0, n1, n2, n3, n4 = transformer.nodes_by_rule[0]

        self.assertIsNone(n0.leaf_rule)
        self.assertIsNone(n1.leaf_rule)
        self.assertIsNone(n2.leaf_rule)
        self.assertIsNone(n3.leaf_rule)
        self.assertEqual(n4.leaf_rule, 'rule')

        self.assertFalse(n0.is_attribute)
        self.assertFalse(n3.is_attribute)
        self.assertTrue(n1.is_attribute)
        self.assertTrue(n2.is_attribute)
        self.assertTrue(n4.is_attribute)

        # `self` is only counted once because it has only one leaf node which
        # tests nodes_under_leaf
        self.assertEqual(n0.count, 1)
        self.assertEqual(n1.count, 1)
        self.assertEqual(n2.count, 1)
        self.assertEqual(n3.count, 1)
        self.assertEqual(n4.count, 1)

        self.assertFalse(n0.depends)
        self.assertEqual(set(n0.depends_on_me), {n1, n2})
        self.assertEqual(set(n1.depends), {n0})
        self.assertEqual(set(n1.depends_on_me), {n3})
        self.assertEqual(set(n2.depends), {n0})
        self.assertEqual(set(n2.depends_on_me), {n3})
        self.assertEqual(set(n3.depends), {n1, n2})
        self.assertEqual(set(n3.depends_on_me), {n4})
        self.assertEqual(set(n4.depends), {n3})
        self.assertFalse(n4.depends_on_me)

    def test_ast_whitelist_minimal_reuse_forked_node_sum(self):
        from kivy.lang.compiler.ast_parse import \
            ParseKVBindTransformer, parse_expr_ast
        transformer = ParseKVBindTransformer(kv_syntax='minimal')

        transformer.update_graph(
            [parse_expr_ast('(self.x + self.y).z')], 'rule')

        self.assertEqual(len(transformer.nodes_by_rule), 1)
        self.assertEqual(len(transformer.nodes_by_rule[0]), 3)

        # don't know if x, or y is visited first, but the following test work
        # whether x or y was visited first as exact identity is not assumed
        # but, whichever is first, their graph and rule order is the same
        n0, n1, n2 = transformer.nodes_by_rule[0]

        self.assertIsNone(n0.leaf_rule)
        self.assertEqual(n1.leaf_rule, 'rule')
        self.assertEqual(n2.leaf_rule, 'rule')

        self.assertFalse(n0.is_attribute)
        self.assertTrue(n1.is_attribute)
        self.assertTrue(n2.is_attribute)

        # with minimal syntax, z is not a leaf, rather x and y are, so self has
        # two different leaves so its count is 2. tests nodes_under_leaf
        self.assertEqual(n0.count, 2)
        self.assertEqual(n1.count, 1)
        self.assertEqual(n2.count, 1)

        self.assertFalse(n0.depends)
        self.assertEqual(set(n0.depends_on_me), {n1, n2})
        self.assertEqual(set(n1.depends), {n0})
        self.assertEqual(set(n2.depends), {n0})
        self.assertFalse(n1.depends_on_me)
        self.assertFalse(n2.depends_on_me)

    def test_ast_whitelist_None_reuse_forked_node_sum(self):
        from kivy.lang.compiler.ast_parse import \
            ParseKVBindTransformer, parse_expr_ast
        transformer = ParseKVBindTransformer(kv_syntax=None)

        transformer.update_graph(
            [parse_expr_ast('(self.x + self.y).z')], 'rule')

        self.assertEqual(len(transformer.nodes_by_rule), 1)
        self.assertEqual(len(transformer.nodes_by_rule[0]), 5)

        # don't know if x, or y is visited first, but the following test work
        # whether x or y was visited first as exact identity is not assumed
        # but, whichever is first, their graph and rule order is the same
        n0, n1, n2, n3, n4 = transformer.nodes_by_rule[0]

        self.assertIsNone(n0.leaf_rule)
        self.assertIsNone(n1.leaf_rule)
        self.assertIsNone(n2.leaf_rule)
        self.assertIsNone(n3.leaf_rule)
        self.assertEqual(n4.leaf_rule, 'rule')

        self.assertFalse(n0.is_attribute)
        self.assertFalse(n3.is_attribute)
        self.assertTrue(n1.is_attribute)
        self.assertTrue(n2.is_attribute)
        self.assertTrue(n4.is_attribute)

        # with full syntax, there's only one leaf - z, so self has a count of 1
        # which tests nodes_under_leaf
        self.assertEqual(n0.count, 1)
        self.assertEqual(n1.count, 1)
        self.assertEqual(n2.count, 1)
        self.assertEqual(n3.count, 1)
        self.assertEqual(n4.count, 1)

        self.assertFalse(n0.depends)
        self.assertEqual(set(n0.depends_on_me), {n1, n2})
        self.assertEqual(set(n1.depends), {n0})
        self.assertEqual(set(n1.depends_on_me), {n3})
        self.assertEqual(set(n2.depends), {n0})
        self.assertEqual(set(n2.depends_on_me), {n3})
        self.assertEqual(set(n3.depends), {n1, n2})
        self.assertEqual(set(n3.depends_on_me), {n4})
        self.assertEqual(set(n4.depends), {n3})
        self.assertFalse(n4.depends_on_me)

    def ast_simple(self, s):
        from kivy.lang.compiler.ast_parse import \
            ParseKVBindTransformer, parse_expr_ast
        transformer = ParseKVBindTransformer(kv_syntax='minimal')

        transformer.update_graph([parse_expr_ast(s)], 'rule')

        self.assertEqual(len(transformer.nodes_by_rule), 1)
        self.assertEqual(len(transformer.nodes_by_rule[0]), 2)

        n0, n1 = transformer.nodes_by_rule[0]

        self.assertIsNone(n0.leaf_rule)
        self.assertEqual(n1.leaf_rule, 'rule')

        self.assertFalse(n0.is_attribute)
        self.assertTrue(n1.is_attribute)

        self.assertEqual(n0.count, 1)
        self.assertEqual(n1.count, 1)

        self.assertFalse(n0.depends)
        self.assertEqual(set(n0.depends_on_me), {n1, })
        self.assertEqual(set(n1.depends), {n0})
        self.assertFalse(n1.depends_on_me)

    def test_ast_simple(self):
        self.ast_simple('self.x')

    def test_ast_simple_duplicate(self):
        # this tests de-duplication by leaf_nodes_in_rule
        self.ast_simple('self.x + self.x')

    def test_ast_simple_duplicate_multiple_rules(self):
        from kivy.lang.compiler.ast_parse import \
            ParseKVBindTransformer, parse_expr_ast
        transformer = ParseKVBindTransformer(kv_syntax='minimal')

        # this tests de-duplication by leaf_nodes_in_rule for each rule
        transformer.update_graph([parse_expr_ast('self.x + self.x')], 'rule1')
        transformer.update_graph([parse_expr_ast('self.x + self.x')], 'rule2')

        self.assertEqual(len(transformer.nodes_by_rule), 2)
        self.assertEqual(len(transformer.nodes_by_rule[0]), 2)
        self.assertEqual(len(transformer.nodes_by_rule[1]), 1)

        # don't know if x, or y is visited first, but the following test work
        # whether x or y was visited first as exact identity is not assumed
        # but, whichever is first, their graph and rule order is the same
        n0, n1 = transformer.nodes_by_rule[0]
        n2, = transformer.nodes_by_rule[1]

        self.assertIsNone(n0.leaf_rule)
        self.assertEqual(n1.leaf_rule, 'rule1')
        self.assertEqual(n2.leaf_rule, 'rule2')

        self.assertFalse(n0.is_attribute)
        self.assertTrue(n1.is_attribute)
        self.assertTrue(n2.is_attribute)

        self.assertEqual(n0.count, 2)
        self.assertEqual(n1.count, 1)
        self.assertEqual(n2.count, 1)

        self.assertFalse(n0.depends)
        self.assertEqual(set(n0.depends_on_me), {n1, n2})
        self.assertEqual(set(n1.depends), {n0})
        self.assertEqual(set(n2.depends), {n0})
        self.assertFalse(n1.depends_on_me)
        self.assertFalse(n2.depends_on_me)

    def test_ast_multiple_graphs(self):
        from kivy.lang.compiler.ast_parse import \
            ParseKVBindTransformer, parse_expr_ast
        transformer = ParseKVBindTransformer(kv_syntax='minimal')

        transformer.update_graph([parse_expr_ast('self.x + other.x')], 'rule')

        self.assertEqual(len(transformer.nodes_by_rule), 1)
        self.assertEqual(len(transformer.nodes_by_rule[0]), 4)

        # don't know if self, or other is visited first, but the following
        # tests work whether self or other was visited first as exact identity
        # is not assumed but, whichever is first, their graph and rule order is
        # the same
        n0, n1, n2, n3 = transformer.nodes_by_rule[0]

        self.assertIsNone(n0.leaf_rule)
        self.assertEqual(n1.leaf_rule, 'rule')
        self.assertIsNone(n2.leaf_rule)
        self.assertEqual(n3.leaf_rule, 'rule')

        self.assertFalse(n0.is_attribute)
        self.assertTrue(n1.is_attribute)
        self.assertFalse(n2.is_attribute)
        self.assertTrue(n3.is_attribute)

        self.assertEqual(n0.count, 1)
        self.assertEqual(n1.count, 1)
        self.assertEqual(n2.count, 1)
        self.assertEqual(n3.count, 1)

        self.assertFalse(n0.depends)
        self.assertEqual(set(n0.depends_on_me), {n1, })
        self.assertEqual(set(n1.depends), {n0})
        self.assertFalse(n1.depends_on_me)

        self.assertFalse(n2.depends)
        self.assertEqual(set(n2.depends_on_me), {n3, })
        self.assertEqual(set(n3.depends), {n2})
        self.assertFalse(n3.depends_on_me)


cython_setup = '''
from distutils.core import setup
from Cython.Build import cythonize
from os.path import join, dirname, abspath

setup(
    ext_modules=cythonize(abspath(join(dirname(__file__), "{}")))
)
'''

cython_file = '''
#cython: binding=True

from kivy.uix.widget import Widget
from kivy.lang.compiler import KV, KVCtx

class MyWidget(Widget):

    @KV()
    def apply_kv(self):
        with KVCtx():
            self.x @= self.y
'''


@skip_py2_decorator
class TestCythonKV(TestBase):

    def setUp(self):
        super(TestCythonKV, self).setUp()
        from kivy.lang.compiler.kv import patch_inspect
        patch_inspect()

        cython_path = os.path.join(
            os.path.dirname(__file__), 'kv_tests', 'cython')
        self.cython_path = cython_path
        os.mkdir(cython_path)

        with open(os.path.join(cython_path, 'cython_kv.pyx'), 'w') as fh:
            fh.write(cython_file)

        with open(os.path.join(cython_path, 'setup.py'), 'w') as fh:
            fh.write(cython_setup.format('cython_kv.pyx'))

        import kivy.lang.compiler.runtime
        self.original_kvc_path = kivy.lang.compiler.runtime._kvc_path
        kivy.lang.compiler.runtime._kvc_path = cython_path

    def test_cython(self):
        setup_path = os.path.join(self.cython_path, 'setup.py')
        try:
            subprocess.check_output(
                [sys.executable or 'python', setup_path, 'build_ext',
                 '--inplace'], stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            print(e.output.decode('utf8'))
            raise

        sys.path.append(self.cython_path)
        kv_cython = importlib.import_module('cython_kv')
        w = kv_cython.MyWidget()
        w.apply_kv()

        self.assertEqual(w.x, w.y)
        w.y = 868
        self.assertEqual(w.x, 868)
        w.y = 370
        self.assertEqual(w.x, 370)

        sys.path.remove(self.cython_path)
        del sys.modules['cython_kv'], w, kv_cython
        import gc
        gc.collect()

    def tearDown(self):
        super(TestCythonKV, self).tearDown()
        from kivy.lang.compiler.kv import unpatch_inspect
        unpatch_inspect()

        import kivy.lang.compiler.runtime
        kivy.lang.compiler.runtime._kvc_path = self.original_kvc_path

        shutil.rmtree(self.cython_path, ignore_errors=True)


@skip_py2_decorator
class TestCythonKVDefault(TestBase):

    def setUp(self):
        super(TestCythonKVDefault, self).setUp()
        from kivy.lang.compiler.kv import patch_inspect
        patch_inspect()

        cython_path = os.path.join(
            os.path.dirname(__file__), 'kv_tests', 'cython')
        self.cython_path = cython_path
        os.mkdir(cython_path)

        with open(os.path.join(
                cython_path, 'cython_kv_default.pyx'), 'w') as fh:
            fh.write(cython_file)

        with open(os.path.join(cython_path, 'setup.py'), 'w') as fh:
            fh.write(cython_setup.format('cython_kv_default.pyx'))

    def test_cython_default(self):
        setup_path = os.path.join(self.cython_path, 'setup.py')
        try:
            subprocess.check_output(
                [sys.executable or 'python', setup_path, 'build_ext',
                 '--inplace'], stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            print(e.output.decode('utf8'))
            raise

        sys.path.append(self.cython_path)
        kv_cython = importlib.import_module('cython_kv_default')
        w = kv_cython.MyWidget()
        w.apply_kv()

        self.assertEqual(w.x, w.y)
        w.y = 868
        self.assertEqual(w.x, 868)
        w.y = 370
        self.assertEqual(w.x, 370)

        sys.path.remove(self.cython_path)
        del sys.modules['cython_kv_default'], w, kv_cython
        import gc
        gc.collect()

    def tearDown(self):
        super(TestCythonKVDefault, self).tearDown()
        from kivy.lang.compiler.kv import unpatch_inspect
        unpatch_inspect()

        shutil.rmtree(self.cython_path, ignore_errors=True)


class PyinstallerKVBase(TestBase):

    def setUp(self):
        super(PyinstallerKVBase, self).setUp()
        self.pinstall_path = os.path.join(
            os.path.dirname(__file__), 'kv_tests', 'pyinstaller')

    def get_env(self):
        env = os.environ.copy()
        env['KIVY_KVC_PATH'] = os.path.join(self.pinstall_path, 'kvc')
        env['__KIVY_PYINSTALLER_DIR'] = self.pinstall_path
        return env

    def do_packaging(self):
        env = self.get_env()

        try:
            # create kvc
            subprocess.check_output(
                'python main.py',
                cwd=self.pinstall_path, stderr=subprocess.STDOUT, env=env)
        except subprocess.CalledProcessError as e:
            print(e.output.decode('utf8'))
            raise

        try:
            # create pyinstaller package
            subprocess.check_output(
                'pyinstaller main.spec',
                cwd=self.pinstall_path, stderr=subprocess.STDOUT, env=env)
        except subprocess.CalledProcessError as e:
            print(e.output.decode('utf8'))
            raise

        try:
            # test package
            subprocess.check_output(
                os.path.join(self.pinstall_path, 'dist', 'main', 'main'),
                stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            print(e.output.decode('utf8'))
            raise

    def tearDown(self):
        super(PyinstallerKVBase, self).tearDown()

        shutil.rmtree(
            os.path.join(self.pinstall_path, '__pycache__'),
            ignore_errors=True)
        shutil.rmtree(
            os.path.join(self.pinstall_path, 'build'),
            ignore_errors=True)
        shutil.rmtree(
            os.path.join(self.pinstall_path, 'dist'),
            ignore_errors=True)
        shutil.rmtree(
            os.path.join(self.pinstall_path, 'kvc'),
            ignore_errors=True)
        shutil.rmtree(
            os.path.join(self.pinstall_path, 'project', '__pycache__'),
            ignore_errors=True)
        shutil.rmtree(
            os.path.join(self.pinstall_path, 'project', '__kvcache__'),
            ignore_errors=True)


@skip_py2_non_win
class TestPyinstallerKV(PyinstallerKVBase):

    def test_pyinstaller_kvc_path(self):
        self.do_packaging()


@skip_py2_non_win
class TestPyinstallerKVCache(PyinstallerKVBase):

    def get_env(self):
        env = super(TestPyinstallerKVCache, self).get_env()
        del env['KIVY_KVC_PATH']
        # use the cache rather than kvc path
        env['__KIVY_KV_USE_CACHE'] = '1'
        env['PYTHONPATH'] = \
            env.get('PYTHONPATH', '') + os.pathsep + self.pinstall_path
        return env

    def test_pyinstaller_cache(self):
        self.do_packaging()
