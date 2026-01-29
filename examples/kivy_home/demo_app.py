"""
Demo: App-Specific KIVY_HOME Configuration
===========================================

This example demonstrates how to set KIVY_HOME to an app-specific directory
BEFORE importing Kivy. This ensures your application has isolated configuration,
logs, and cache directories.

Key Points:
    1. set_app_name() must be called BEFORE importing kivy
    2. KIVY_HOME will be set to: <user_data_dir>/.kivy
    3. Config, logs, and modules will be stored there
    4. Each app gets its own isolated environment

Try running this multiple times with different app names to see separate
configurations created.
"""

# CRITICAL: Import and call set_app_name BEFORE importing kivy
from set_kivy_home import set_app_name

set_app_name('KivyHomeDemo')

# Now safe to import Kivy
import os
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import StringProperty


kv = """
BoxLayout:
    orientation: 'vertical'
    padding: '20dp'
    spacing: '10dp'

    Label:
        text: 'App-Specific KIVY_HOME Demo'
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
        text: 'Print Paths to Console'
        size_hint_y: None
        height: '48dp'
        on_release: app.print_paths()
"""


class KivyHomeDemoApp(App):
    info_text = StringProperty('')

    def build(self):
        return Builder.load_string(kv)

    def on_start(self):
        """Display configuration paths when app starts."""
        kivy_home = os.environ.get('KIVY_HOME', 'Not set')
        user_data_dir = self.user_data_dir
        if kivy_home != 'Not set':
            config_path = os.path.join(kivy_home, 'config.ini')
            logs_dir = os.path.join(kivy_home, 'logs')
        else:
            config_path = 'N/A'
            logs_dir = 'N/A'

        self.info_text = f"""
Configuration Paths:

KIVY_HOME:
{kivy_home}

Config File:
{config_path}

Logs Directory:
{logs_dir}

App.user_data_dir:
{user_data_dir}

Notice:
- KIVY_HOME should be under user_data_dir
- Config, logs, and modules are stored in KIVY_HOME
- This ensures each app has isolated settings
- Each app gets its own directory based on its name

Try This:
1. Run this demo
2. Change 'KivyHomeDemo' to another name in the code
3. Run again - see separate directories created
        """.strip()

    def print_paths(self):
        """Print paths to console for easy copy/paste."""
        kivy_home = os.environ.get('KIVY_HOME', 'Not set')
        if kivy_home != 'Not set':
            config_file = os.path.join(kivy_home, 'config.ini')
            logs_directory = os.path.join(kivy_home, 'logs')
        else:
            config_file = 'N/A'
            logs_directory = 'N/A'

        print("\n" + "=" * 60)
        print("App-Specific Configuration Paths")
        print("=" * 60)
        print(f"KIVY_HOME:        {kivy_home}")
        print(f"Config file:      {config_file}")
        print(f"Logs directory:   {logs_directory}")
        print(f"user_data_dir:    {self.user_data_dir}")
        print("=" * 60 + "\n")


if __name__ == '__main__':
    KivyHomeDemoApp().run()
