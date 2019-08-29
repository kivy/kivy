import pytest


def rule_exists(builder, cls_name):
    from itertools import dropwhile
    key = cls_name.lower()
    try:
        next(dropwhile(lambda v: v[0].key != key, builder.rules))
    except StopIteration:
        return False
    return True


def test_rule_exists():
    from kivy.lang import Builder
    assert not rule_exists(Builder, 'Widget')
    assert rule_exists(Builder, 'StencilView')

    name = 'UnknownName'
    assert not rule_exists(Builder, name)
    Builder.load_string('<{}>'.format(name), filename=name)
    assert rule_exists(Builder, name)
    Builder.unload_file(name)
    assert not rule_exists(Builder, name)


class Test_tmp_builder:
    '''test_load() has to be excuted before test_restored()'''

    name = 'UnknownWidget'

    def test_load(self, tmp_builder):
        from kivy.factory import Factory
        from kivy.lang import Builder
        assert tmp_builder is Builder
        assert rule_exists(Builder, 'StencilView')

        name = self.name
        assert not rule_exists(Builder, name)
        Builder.load_string('<{}@Widget>:'.format(name))
        assert rule_exists(Builder, name)
        assert name in Factory.classes

    def test_restored(self):
        from kivy.factory import Factory
        from kivy.lang import Builder
        name = self.name
        assert not rule_exists(Builder, name)
        assert name not in Factory.classes
