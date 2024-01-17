'''
Spinner unit tests
=================
author: Anthony Zimmermann (Anthony.Zimmermann@protonmail.com)
'''

from kivy.tests.common import GraphicUnitTest

from kivy.uix.spinner import TextInputSpinner

test_options = ["One", "Two", "Three", "THREE", "tree"]

test_params_case_sensitive = {
    "o": ["Two"],
    "O": ["One"],
    "t": ["tree"],
    "T": ["Two", "Three", "THREE"],
    "e": ["One", "Three", "tree"],
    "on": [],
    "Tw": ["Two"],
    "tw": [],
    "tW": [],
    "th": [],
    "ree": ["Three", "tree"],
    "Tee": [],
    "REE": ["THREE"],
    "thrEe": [],
}

test_params_case_insensitive = {
    "o": ["One", "Two"],
    "O": ["One", "Two"],
    "t": ["Two", "Three", "THREE", "tree"],
    "T": ["Two", "Three", "THREE", "tree"],
    "e": ["One", "Three", "THREE", "tree"],
    "on": ["One"],
    "Tw": ["Two"],
    "tw": ["Two"],
    "tW": ["Two"],
    "th": ["Three", "THREE"],
    "ree": ["Three", "THREE", "tree"],
    "REE": ["Three", "THREE", "tree"],
    "Tee": [],
    "thrEe": ["Three", "THREE"],
}

test_params_custom_filter = {
    "o": ["One", "Two"],
    "O": ["One", "Two"],
    "t": ["Two", "Three", "THREE", "tree"],
    "T": ["Two", "Three", "THREE", "tree"],
    "e": ["One", "Three", "THREE", "tree"],
    "on": ["One"],
    "Tw": ["Two"],
    "tw": ["Two"],
    "tW": ["Two"],
    "th": ["Three", "THREE"],
    "ree": ["Three", "THREE", "tree"],
    "REE": ["Three", "THREE", "tree"],
    "Tee": ["Three", "THREE", "tree"],
    "thrEe": ["Three", "THREE"],
}


class TextInputSpinnerTest(GraphicUnitTest):

    def test_live_filtering_case_sensitive(self):

        textinput_spinner = TextInputSpinner(
            live_filter=True,
            filter_case_sensitive=True,
            values=test_options,
        )
        self.render(textinput_spinner)

        for current_text, expected in test_params_case_sensitive.items():
            print(
                "current_text: {}, expected_filtered_options: {}".format(
                    current_text,
                    expected,
                )
            )
            textinput_spinner.text = current_text
            assert textinput_spinner.values == expected

    def test_live_filtering_case_insensitive(self):

        textinput_spinner = TextInputSpinner(
            live_filter=True,
            filter_case_sensitive=False,
            values=test_options,
        )
        self.render(textinput_spinner)

        for current_text, expected in test_params_case_insensitive.items():
            print(
                "current_text: {}, expected_filtered_options: {}".format(
                    current_text,
                    expected,
                )
            )
            textinput_spinner.text = current_text
            assert textinput_spinner.values == expected

    def test_live_filtering_deactivated(self):

        textinput_spinner = TextInputSpinner(
            live_filter=False,
            values=test_options,
        )
        self.render(textinput_spinner)

        for current_text, expected in test_params_case_sensitive.items():
            print(
                "current_text: {}, expected_filtered_options: {}".format(
                    current_text,
                    expected,
                )
            )
            textinput_spinner.text = current_text
            assert textinput_spinner.values == test_options

    def test_live_filtering_with_custom_filter(self):

        def custom_filter(current_text, option):
            current_text = current_text.lower()
            option = option.lower()
            while len(current_text) > 0 and len(option) > 0:
                if current_text[0] == option[0]:
                    current_text = current_text[1:]
                option = option[1:]
            return len(current_text) == 0

        textinput_spinner = TextInputSpinner(
            live_filter=True,
            values=test_options,
        )
        textinput_spinner.filter_function = custom_filter
        self.render(textinput_spinner)

        for current_text, expected in test_params_custom_filter.items():
            print(
                "current_text: {}, expected_filtered_options: {}".format(
                    current_text,
                    expected,
                )
            )
            textinput_spinner.text = current_text
            assert textinput_spinner.values == expected
