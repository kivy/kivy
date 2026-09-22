import gc
import json
import sys

import pytest

from kivy.config import ConfigParser
from kivy.uix.settings import Settings, SettingsWithSidebar


def test_settings_create_json_panel_errors():
    config = ConfigParser()

    with pytest.raises(
        Exception, match="You must specify either the filename or data"
    ):
        Settings().create_json_panel("Demo", config, filename=None, data=None)

    with pytest.raises(
        ValueError, match="The first element must be a list"
    ):
        data = json.dumps({"key": "value"})
        Settings().create_json_panel("Demo", config, filename=None, data=data)

    with pytest.raises(
        ValueError, match="One setting are missing the \"type\" element"
    ):
        data = json.dumps([{"key": "value"}])
        Settings().create_json_panel("Demo", config, filename=None, data=data)

    with pytest.raises(
        ValueError, match="No class registered to handle the <testunknown> type"
    ):
        data = json.dumps([{"type": "testunknown"}])
        Settings().create_json_panel("Demo", config, filename=None, data=data)


def test_settings_sidebar_destructor_does_not_collide():
    """A sidebar row must not reuse its panel's widget uid.

    https://github.com/kivy/kivy/issues/9381
    """
    config = ConfigParser()
    settings = SettingsWithSidebar()
    settings.add_json_panel(
        "Demo",
        config,
        data=json.dumps([{"type": "title", "title": "Section"}]),
    )

    labels = [
        child for child in settings.interface.menu.buttons_layout.children
        if child.__class__.__name__ == "SettingSidebarLabel"
    ]
    assert len(labels) == 1
    label = labels[0]
    panel = settings.interface.content.panels[label.panel_uid]
    assert label.panel_uid == panel.uid
    assert label.uid != panel.uid
    # KV may already have done this. Touch both so each destructor is registered.
    label.proxy_ref
    panel.proxy_ref

    unraisable = []
    previous_hook = sys.unraisablehook

    def _hook(arg):
        unraisable.append(arg)

    sys.unraisablehook = _hook
    try:
        del settings, labels, label, panel
        gc.collect()
    finally:
        sys.unraisablehook = previous_hook

    key_errors = [
        item.exc_value for item in unraisable
        if isinstance(item.exc_value, KeyError)
    ]
    assert key_errors == []
