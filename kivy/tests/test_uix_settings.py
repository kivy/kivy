import json

import pytest

from kivy.config import ConfigParser
from kivy.uix.settings import Settings


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
