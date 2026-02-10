"""
Demo: KIVY_DESKTOP_PATH_ID Usage
=================================

Shows how KIVY_DESKTOP_PATH_ID creates user-friendly directory names
that are easy for end users to identify.
"""

import os
os.environ['KIVY_DESKTOP_PATH_ID'] = 'My Photo Editor'

from textwrap import dedent
from kivy import kivy_home_dir
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import StringProperty

kv = """
BoxLayout:
    orientation: 'vertical'
    padding: '20dp'
    spacing: '10dp'

    Label:
        text: 'KIVY_DESKTOP_PATH_ID Demo'
        size_hint_y: None
        height: '48dp'
        font_size: '20sp'
        bold: True

    ScrollView:
        Label:
            text: app.info_text
            size_hint_y: None
            height: self.texture_size[1]
            text_size: self.width, None
            halign: 'left'
            valign: 'top'

    Button:
        text: 'Print Paths'
        size_hint_y: None
        height: '48dp'
        on_release: app.print_paths()
"""


class DesktopPathIdDemoApp(App):
    info_text = StringProperty('')

    def build(self):
        return Builder.load_string(kv)

    def on_start(self):
        path_id = os.environ.get('KIVY_DESKTOP_PATH_ID', 'Not set')

        # KIVY_HOME is constructed as user_data_dir/.kivy
        kivy_home = kivy_home_dir
        config_path = os.path.join(kivy_home, 'config.ini')
        logs_path = os.path.join(kivy_home, 'logs')

        self.info_text = dedent(f"""
            Path Identifier: {path_id}

            user_data_dir: {self.user_data_dir}

            user_cache_dir: {self.user_cache_dir}

            KIVY_HOME: {kivy_home}

            Config File: {config_path}

            Logs Directory: {logs_path}

            Notice:
            - Path ID is normalized for filesystem safety
            - Special characters are replaced with underscores
            - Users see clear, recognizable directory names
            - Makes app data easy to identify and manage
            - Config and logs are in the .kivy subdirectory

            Try This:
            1. Change the path_id at the top of this file
            2. Run again to see different directory names
            3. Navigate to the directories to see them created
            """).strip()

    def print_paths(self):
        kivy_home = kivy_home_dir
        config_file = os.path.join(kivy_home, 'config.ini')
        logs_directory = os.path.join(kivy_home, 'logs')

        print("\n" + "=" * 60)
        print("KIVY_DESKTOP_PATH_ID Configuration")
        print("=" * 60)
        print(f"Path ID: {os.environ.get('KIVY_DESKTOP_PATH_ID')}")
        print(f"user_data_dir: {self.user_data_dir}")
        print(f"user_cache_dir: {self.user_cache_dir}")
        print(f"KIVY_HOME: {kivy_home}")
        print(f"Config file: {config_file}")
        print(f"Logs directory: {logs_directory}")
        print("=" * 60 + "\n")


if __name__ == '__main__':
    DesktopPathIdDemoApp().run()
