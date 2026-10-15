from kivy import cache as cache_module
from kivy.cache import Cache


def test_object_timeout_does_not_leak_to_following_cache_entry(monkeypatch):
    current_time = [0.0]

    class FakeClock:
        @staticmethod
        def get_time():
            return current_time[0]

    monkeypatch.setattr(cache_module, "Clock", FakeClock)
    category = "test_object_timeout_does_not_leak"
    Cache.register(category, timeout=None)

    try:
        Cache.append(category, "timed", "timed", timeout=10)
        Cache.append(category, "untimed", "untimed")
        current_time[0] = 20

        Cache._purge_by_timeout(dt=0.5)

        assert Cache.get(category, "timed") is None
        assert Cache.get(category, "untimed") == "untimed"
    finally:
        Cache.remove(category)
        Cache._categories.pop(category, None)
