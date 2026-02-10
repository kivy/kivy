KIVY_DESKTOP_PATH_ID Environment Variable
==========================================

Overview
--------
KIVY_DESKTOP_PATH_ID sets a user-facing, human-readable application title
for your directories on desktop platforms. This makes it easy for end users
to identify which application owns which directories when browsing their
filesystem.

It replaces App.name in the construction of:
- KIVY_HOME directory
- App.user_data_dir
- App.user_cache_dir

Why Use This
------------
When users navigate to their AppData (Windows), Library (macOS), or
.local/share (Linux) folders, they see a clear, recognizable name like
"My Photo Editor" instead of a technical identifier like "photoeditorapp".

This improves the user experience by:
- Making directories easily identifiable
- Using familiar branding/app name
- Helping users locate app data when needed
- Providing professional, user-friendly paths

Usage
-----
Set the environment variable BEFORE importing Kivy:

    import os
    os.environ['KIVY_DESKTOP_PATH_ID'] = 'My Photo Editor'

    from kivy.app import App

Path Construction
-----------------
The value is normalized for filesystem safety:
- Invalid characters (/\:*?"<>|) replaced with underscore
- Spaces replaced with underscores
- Results in: <user_data_dir>/<normalized_id>/.kivy

Priority Order
--------------
1. KIVY_DESKTOP_PATH_ID (highest priority)
2. KIVY_HOME environment variable
3. Virtual environment detection
4. App.name (fallback)

Platform Behavior
-----------------
Desktop (Windows, macOS, Linux):
- Uses KIVY_DESKTOP_PATH_ID if set
- Logs warning if not set

Mobile (iOS, Android):
- Ignores KIVY_DESKTOP_PATH_ID
- Always uses App.name or system paths
- File systems are not user-browsable

Note for Mobile Developers:
- If developing a mobile app on a desktop platform, you can set
  KIVY_DESKTOP_PATH_ID to any value to suppress the warning
- The variable will have no effect on your mobile app
- This prevents the warning during development

Example Paths
-------------
With KIVY_DESKTOP_PATH_ID='My Photo Editor':

Windows:
  %APPDATA%/My_Photo_Editor/.kivy (config, logs, mods, icon)
  %APPDATA%/My_Photo_Editor (user_data_dir)
  %LOCALAPPDATA%/My_Photo_Editor/Cache (user_cache_dir)

macOS:
  ~/Library/Application Support/My_Photo_Editor/.kivy (config, logs, mods, icon)
  ~/Library/Application Support/My_Photo_Editor (user_data_dir)
  ~/Library/Caches/My_Photo_Editor (user_cache_dir)

Linux:
  ~/.local/share/My_Photo_Editor/.kivy (config, logs, mods, icon)
  ~/.local/share/My_Photo_Editor (user_data_dir)
  ~/.cache/My_Photo_Editor (user_cache_dir)

Compare to default (using App.name='PhotoEditorApp'):
  %APPDATA%/photoeditor/.kivy (less user-friendly)

Running the Demo
----------------
    python demo_app.py

Try changing the path_id in demo_app.py to see different paths.

Common Use Cases
----------------
1. Professional Desktop Applications
   Set to your branded application name so users see familiar names
   when browsing their system.

2. Multiple Versions
   Use different identifiers for beta vs. production versions:
   - 'My App' for production
   - 'My App Beta' for beta testing

3. Company Applications
   Include your company name for clear identification:
   - 'Acme Corp Document Editor'
   - 'Acme Corp Photo Tool'

Best Practices
--------------
1. Use clear, recognizable names that match your app branding
2. Keep names concise but descriptive
3. Avoid special characters that need normalization
4. Test on all target platforms to verify paths
5. Document the path structure for user support

Further Reading
---------------
- Kivy Configuration: https://kivy.org/doc/stable/guide/config.html
- Environment Variables: https://kivy.org/doc/stable/guide/environment.html
- App.user_data_dir: https://kivy.org/doc/stable/api-kivy.app.html
