import pytest
try:
    from .fixtures import kivy_app
except SyntaxError:
    # async app tests would be skipped due to async_run forcing it to skip so
    # it's ok to fail here as it won't be used anyway
    pass

try:
    import pytest_asyncio

    @pytest.fixture()
    def nursery():
        pass
except ImportError:
    try:
        import trio
        from pytest_trio import trio_fixture
    except ImportError:
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
