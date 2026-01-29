App-Specific KIVY_HOME Configuration
=====================================

Overview
--------
This example demonstrates how to configure KIVY_HOME for app-specific 
configuration directories. By default, Kivy stores configuration, logs, 
and modules in a shared ~/.kivy directory. This example shows how to 
give each application its own isolated environment.


When to Use This
----------------
Use this approach when:

1. Developing multiple Kivy applications on the same system
   - Each app needs separate configuration
   - Prevents configuration conflicts between apps

2. Deploying desktop applications
   - Professional apps should have isolated settings
   - Follows platform conventions (AppData, Application Support, etc.)

3. Testing and development
   - Test with clean configuration without affecting other apps
   - Easy to reset settings (just delete app-specific directory)


How It Works
------------
1. set_app_name() is called BEFORE importing Kivy
2. KIVY_HOME environment variable is set to: <user_data_dir>/.kivy
3. Kivy reads KIVY_HOME and stores config/logs there
4. Each app gets its own isolated directory structure


Directory Structure
-------------------
After calling set_app_name('MyApp'), you'll get:

Windows:
    %APPDATA%/myapp/.kivy/config.ini
    %APPDATA%/myapp/.kivy/logs/

macOS:
    ~/Library/Application Support/myapp/.kivy/config.ini
    ~/Library/Application Support/myapp/.kivy/logs/

Linux:
    ~/.local/share/myapp/.kivy/config.ini
    ~/.local/share/myapp/.kivy/logs/


Usage in Your App
-----------------
Copy set_kivy_home.py to your project and use it like this:

    from set_kivy_home import set_app_name  # BEFORE kivy import!
    set_app_name('MyApp')
    
    from kivy.app import App  # Now Kivy uses app-specific paths
    
    class MyApp(App):
        pass
    
    MyApp().run()


Important Notes
---------------
- set_app_name() MUST be called before importing ANY Kivy modules
- If KIVY_HOME is already set (env variable), this does nothing
- On mobile (iOS/Android), this does nothing (already app-specific)
- App name is normalized: lowercase, 'app' suffix removed
- The .kivy directory is created automatically


Relationship to user_data_dir
------------------------------
- App.user_data_dir: Application data storage directory
- KIVY_HOME: Kivy framework config/logs (subdirectory of user_data_dir)

Best practice: KIVY_HOME should be user_data_dir/.kivy
This keeps all application-specific data together.


Running the Demo
----------------
    python demo_app.py

The demo will display all configuration paths and show that KIVY_HOME
is properly set to an app-specific directory.


Further Reading
---------------
- Kivy Configuration: https://kivy.org/doc/stable/guide/config.html
- Environment Variables: https://kivy.org/doc/stable/guide/environment.html
- App.user_data_dir: https://kivy.org/doc/stable/api-kivy.app.html
