import json

import pytest

from kivy.config import ConfigParser
from kivy.uix.settings import Settings, SettingNumeric
from kivy.uix.textinput import TextInput
import unittest


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


class SettingNumericTest(SettingNumeric):

    def __init__(self, panel):
        print("SettingNumericTest")
        self.panel = panel
        self.section = "Section"
        self.key = "Key"
        self.value = "0"
        self.textinput = TextInput(
            text=self.value, font_size='24sp', multiline=False,
            size_hint_y=None, height='42sp'
        )
        super(SettingNumericTest, self).__init__()


class TestSettingNumeric(unittest.TestCase):

    @pytest.fixture(autouse=True, scope="class")
    def setup_once(self, request):
        config = ConfigParser()
        config.setdefaults('Section', {'Key': 0})

        request.cls.panel = Settings().create_json_panel("TestSettingNumeric", config, filename=None, data="""
            [
                {
                    "type": "title", 
                    "title": "Title"
                },
                {
                    "type": "numeric", 
                    "title": "Numerical value",
                    "desc": "Set a mumeric value",
                    "section": "Section", 
                    "key": "Key"
                }
            ]"""
        )


    @pytest.fixture(autouse=True, scope="function")
    def setup(self):
        self.settingNumeric = SettingNumericTest(self.panel)
        self.settingNumeric.value = "10"


    def test_validate_int(self):
        self.settingNumeric.textinput.text = "42"
        self.settingNumeric._validate(None)
        self.assertEqual(self.settingNumeric.value, "42")


    def test_validate_float(self):
        self.settingNumeric.textinput.text = "3.414592695"
        self.settingNumeric._validate(None)
        self.assertEqual(self.settingNumeric.value, "3.414592695")


    def test_validate_scientific(self):
        self.settingNumeric.textinput.text = "1.77e-09"
        self.settingNumeric._validate(None)
        self.assertEqual(self.settingNumeric.value, "1.77e-09")


    def test_invalidate_str(self):
        self.settingNumeric.textinput.text = "hello"
        self.settingNumeric._validate(None)
        self.assertEqual(self.settingNumeric.value, "10")

