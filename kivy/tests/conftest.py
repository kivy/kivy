import pytest
import os

kivy_eventloop = os.environ.get('KIVY_EVENTLOOP', 'asyncio')

try:
    from .fixtures import kivy_app
except SyntaxError:
    # async app tests would be skipped due to async_run forcing it to skip so
    # it's ok to fail here as it won't be used anyway
    pass

if kivy_eventloop != 'trio':
    @pytest.fixture()
    def nursery():
        pass


def pytest_runtest_makereport(item, call):
    # from https://docs.pytest.org/en/latest/example/simple.html
    if "incremental" in item.keywords:
        if call.excinfo is not None:
            parent = item.parent
            parent._previousfailed = item


def pytest_runtest_setup(item):
    # from https://docs.pytest.org/en/latest/example/simple.html
    if "incremental" in item.keywords:
        previousfailed = getattr(item.parent, "_previousfailed", None)
        if previousfailed is not None:
            pytest.xfail("previous test failed (%s)" % previousfailed.name)
