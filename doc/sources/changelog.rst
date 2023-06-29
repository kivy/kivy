.. _changelog:

Changelog
=========

2.2.1
=====

Highlights
----------

- [:repo:`8283`]: backport (#8276): Limit stencil to inner instructions on Image widget

Tests/ci
--------

- [:repo:`8288`]: backport (#8263): Increase timeout of httpbin tests to reduce risk of failures on CI runs

Documentation
-------------

- [:repo:`8252`]: backport (#8251): Ensures that jQuery is always installed (on newer sphinx versions is not the default)


2.2.0
=====

Highlights
----------

- [:repo:`7876`]: `Line`/`SmoothLine`: Fixes rendering issues related to corner radius and updates its order (`rounded_rectangle`) + add getter methods for `rounded_rectangle`, `rectangle`, `ellipse`, `circle`.
- [:repo:`7882`]: Re-implements the Bubble widget.
- [:repo:`7908`]: Speed up SmoothLine creation by ~2.5x
- [:repo:`7942`]: Config unicode support on Windows
- [:repo:`7988`]: Added support for KIVY_LOG_MODE
- [:repo:`8044`]: Add support for Python 3.11
- [:repo:`8056`]: New Feature: Add `BoxShadow` graphic instruction 🎉
- [:repo:`8115`]: Use `font_direction` and `font_script_name` from SDL2_ttf
- [:repo:`8144`]: Added property for mouse draggable tab scrollbar to TabbedPanel
- [:repo:`8162`]: `Label`: allow different values of left, top, right and bottom for `padding`.
- [:repo:`8169`]: `Image`: add `fit_mode` feature
- [:repo:`8096`]: Introduce build script for SDL dependencies and `KIVY_DEPS_ROOT`

Deprecated
----------

- [:repo:`7882`]: Re-implements the Bubble widget.

Breaking changes
----------------

- [:repo:`7876`]: `Line`/`SmoothLine`: Fixes rendering issues related to corner radius and updates its order (`rounded_rectangle`) + add getter methods for `rounded_rectangle`, `rectangle`, `ellipse`, `circle`.

Kv-lang
-------

- [:repo:`8021`]: Update builder.py

Misc
----

- [:repo:`7906`]: Replace deprecated logging.warn with logging.warning
- [:repo:`7913`]: fix(UrlRequest): Add "on_finish" and add alternative implementation
- [:repo:`7943`]: Fixes some E275 - assert is a keyword. + other minor PEP8 fixes
- [:repo:`7969`]: Config is not available when generating docs + Use `getdefault` instead of `has_option` + `get`

Widgets
-------

- [:repo:`7626`]: New Feature: Allow control how many lines to scroll at once using the mouse wheel on TextInput
- [:repo:`7882`]: Re-implements the Bubble widget.
- [:repo:`7905`]: Fix TextInputCutCopyPaste widget
- [:repo:`7925`]: Qwerty VKeyboard button fix( z, Q and W and ] ) on Linux(Ubuntu Focal Fossa)
- [:repo:`8109`]: Fix for changes of Splitter.strip_cls having no effect
- [:repo:`8144`]: Added property for mouse draggable tab scrollbar to TabbedPanel
- [:repo:`8169`]: `Image`: add `fit_mode` feature
- [:repo:`8202`]: Migrate `allow_stretch` and `keep_ratio` in widgets/examples by corresponding `fit_mode`

Core-app
--------

- [:repo:`7942`]: Config unicode support on Windows
- [:repo:`7958`]: Use AddLevelName in kivy.Logger to define TRACE
- [:repo:`7962`]: Refactored logging.ColoredFormatter to avoid deepcopy.
- [:repo:`7971`]: Support KivyLogMode environment variable for logging testing
- [:repo:`7973`]: Bump KIVY_CONFIG_VERSION and add a warning for future changes.
- [:repo:`7975`]: Light clean up of stderr handling code.
- [:repo:`7979`]: #7978: Don't monkey-patch logging.root
- [:repo:`7985`]: Handle non-strings in logs.
- [:repo:`7988`]: Added support for KIVY_LOG_MODE
- [:repo:`7989`]: Android Lifecycle convergence
- [:repo:`7994`]: Use urlopen instead of build_opener when fetching files from 'internet'. Removes some PY2 compat.
- [:repo:`8062`]: Use `find_spec`, `module_from_spec` and `exec_module` instead of `find_module` and `load_module` since are deprecated.

Core-providers
--------------

- [:repo:`7846`]: Fix VKeyboard missing with custom keyboard class
- [:repo:`7857`]: iOS camera provider enhancements
- [:repo:`7982`]: Use `SDL_WINDOWEVENT_DISPLAY_CHANGED` to notice about window switching display to update `_density` an `dpi`
- [:repo:`7999`]: Modify layout fix bug in how long text without space is cut 
- [:repo:`8025`]: Release the GIL when performing SDL_GL_SwapWindow call.
- [:repo:`8058`]: Makes Windows DPI aware of scale changes
- [:repo:`8076`]: New Feature: Always On Top
- [:repo:`8083`]: Allow changing `Window.fullscreen` and `Window.borderless` options after setup on iOS
- [:repo:`8115`]: Use `font_direction` and `font_script_name` from SDL2_ttf
- [:repo:`8142`]: New Feature: Allows to hide the taskbar icon
- [:repo:`8146`]: Fix memory issue on iOS 16.2 for AVMetadataObject (during QRCode scan)
- [:repo:`8147`]: Detect High DPI on Linux Desktop
- [:repo:`8162`]: `Label`: allow different values of left, top, right and bottom for `padding`.
- [:repo:`8171`]: Make VideoFFPy work with RTSP streams.
- [:repo:`8184`]: Revert "Detect High DPI on Linux Desktop"

Core-widget
-----------

- [:repo:`8035`]: Simplify Animation._unregister

Distribution
------------

- [:repo:`7837`]: Bump to 2.2.0.dev0
- [:repo:`7852`]: Build python 3.9 wheels for RPi
- [:repo:`7974`]: Bump SDL2, SDL_image, SDL_mixer, SDL_ttf versions to latest stable release
- [:repo:`8004`]: Bump kivy_deps.sdl2 and kivy_deps.sdl2_dev to 0.5.0
- [:repo:`8006`]: Use Platypus 5.4
- [:repo:`8043`]: Bump SDL2 to `2.24.1` on Linux and macOS
- [:repo:`8044`]: Add support for Python 3.11
- [:repo:`8050`]: Bump again SDL2 to 2.24.2 on Linux and macOS
- [:repo:`8070`]: Remove usage of `distutils` module which is deprecated and slated for removal in 3.12
- [:repo:`8096`]: Introduce build script for SDL dependencies and `KIVY_DEPS_ROOT`
- [:repo:`8155`]: Dependencies build tool: exit immediately on fail and allows to debug easier
- [:repo:`8173`]: Bump macOS dependencies versions on `tools/build_macos_dependencies.sh`
- [:repo:`8174`]: Bump Linux dependencies versions on `tools/build_linux_dependencies.sh`
- [:repo:`8176`]: Bump Windows dependencies via `kivy_deps` packages
- [:repo:`8178`]: Bump `cython_max` version
- [:repo:`8191`]: XCode 14.3 fails to build SDL if `MACOSX_DEPLOYMENT_TARGET` < `10.13`
- [:repo:`8203`]: Migrate from `autotools` to `cmake` for SDL2 linux dependencies
- [:repo:`8223`]: Perform RPi builds on `balenalib/raspberrypi3-*` images and skip `DISPMANX` API usage if can't be used [build wheel armv7l]
- [:repo:`8231`]: Bump version to `2.2.0rc1`

Documentation
-------------

- [:repo:`7870`]: Documentation: bump Gentoo install instructions
- [:repo:`7916`]: Fixes NO DOCUMENTATION (module kivy.uix.recycleview)
- [:repo:`7927`]: Fix minor typo in pong tutorial code comments
- [:repo:`7928`]: Add missing closing paren in hint text
- [:repo:`7929`]: Use consistent source code notes in pong tutorial
- [:repo:`7930`]: Purge trailing whitespace in docs source files
- [:repo:`7946`]: Add doc for `Canvas.add()`
- [:repo:`8026`]: Typo : missing coma in the doc
- [:repo:`8032`]: doc: Initial remarks on BSD compatibility.
- [:repo:`8034`]: Fix backticks typo in pong tutorial
- [:repo:`8039`]: Link to buildozer installation instructions instead of duplicating them
- [:repo:`8041`]: installation-osx.rst: Minor code formatting
- [:repo:`8088`]: Add support for sphinx `6.0.0`
- [:repo:`8089`]: Add a warning about `keyboard_suggestions` usage on Android
- [:repo:`8139`]: Improve docs about `BoxShadow` behavior and usage.
- [:repo:`8156`]: Docs: Update the Ubuntu prerequisites to build Kivy and its dependencies
- [:repo:`8175`]: Update Copyright and LICENSE dates
- [:repo:`8179`]: Update Python supported versions
- [:repo:`8181`]: :book: Grammar tweaks to focus docstrings
- [:repo:`8183`]: Docs: Fixes a typo (issue #7838)
- [:repo:`8229`]: Sphinx `7.0.0` is incompatible, use `<=6.2.1` for now
- [:repo:`8234`]: Docs review  for `RPi` installation and build instructions

Graphics
--------

- [:repo:`7860`]: Ellipse: update angle_start, angle_end to explicit floats
- [:repo:`7876`]: `Line`/`SmoothLine`: Fixes rendering issues related to corner radius and updates its order (`rounded_rectangle`) + add getter methods for `rounded_rectangle`, `rectangle`, `ellipse`, `circle`.
- [:repo:`7908`]: Speed up SmoothLine creation by ~2.5x
- [:repo:`8056`]: New Feature: Add `BoxShadow` graphic instruction 🎉
- [:repo:`8098`]: Fix `BoxShadow` shader crashing issue on Adreno GPUs
- [:repo:`8132`]: `BoxShadow`: Add `inset` feature
- [:repo:`8138`]: `BoxShadow`: Accept values for vertical and horizontal `spread_radius`
- [:repo:`8163`]: `Line`/`SmoothLine`: `ellipse` - fix behavior and add feature to allow closing line through center of ellipse
- [:repo:`8164`]: `Ellipse`: Handle the number of segments and avoid division by zero
- [:repo:`8170`]: Add svg rotation transform support
- [:repo:`8187`]: `Line`/`SmoothLine` - `ellipse`: Handle the number of segments to match `Ellipse`

Input
-----

- [:repo:`8027`]: Typo : German Keyboard is QWERTZ

Tests/ci
--------

- [:repo:`7847`]: Tests: ffpyplayer now ships cp310-* and Apple Silicon compatible wheels, so tests on the full version can be re-introduced.
- [:repo:`7854`]: Fixes 3.8.x pyenv install due to a recent change in clang [build wheel osx]
- [:repo:`7885`]: Our self-hosted Apple Silicon runner now has been migrated to actions/runner v2.292.0 which now supports arm64 natively
- [:repo:`7903`]: Migrate from probot/no-response to lee-dohm/no-response
- [:repo:`7917`]: When using pytest_asyncio for tests, function should be decorated with `pytest_asyncio.fixture`
- [:repo:`7972`]: Fix trivial typo in workflow.
- [:repo:`7987`]: Fix source typo in test_uix_bubbles.py
- [:repo:`8084`]: Switch from `ubuntu-18.04` to `ubuntu-latest` as `18.04` runners will be removed on 2023-01-12
- [:repo:`8093`]: Add `gstreamer1.0-plugins-good` for `autoaudiosink` availability during tests
- [:repo:`8099`]: Install twine only when needed [build wheel]
- [:repo:`8117`]: Upgrade GitHub Actions
- [:repo:`8120`]: [build wheel] Upgrade more GitHub Actions
- [:repo:`8121`]: GitHub Actions: Use current Python instead of hardcoded v3.9
- [:repo:`8126`]: Switch back to `macos-latest` instead of `macos-11`
- [:repo:`8129`]: Remove remaining nosetest settings in favor of pytest
- [:repo:`8157`]: Correct the flake8 pre-commit URL
- [:repo:`8217`]: `Generate-sdist` needs `packaging` as a dependency [build wheel win]

2.1.0
=====

Highlights
----------

- [:repo:`7270`]: Graphics: Check whether user updated GL instructions from external thread.
- [:repo:`7293`]: Properties: Add dynamic screen density/dpi support
- [:repo:`7371`]: KV: Allow using f-strings in KV-lang
- [:repo:`7424`]: Properties: Speed up bare widget creation (3X) and property dispatching/setting
- [:repo:`7587`]: Fix PermissionError when reconnecting mtdev input devices
- [:repo:`7637`]: Added Custom titlebar support
- [:repo:`7642`]: TextInput loading time optimisation for large texts
- [:repo:`7658`]: Feature: EventManagerBase
- [:repo:`7663`]: Add python3.10 in the ci configuration
- [:repo:`7678`]: Add support for Apple Silicon on CI/CD

Deprecated
----------

- [:repo:`7701`]: deprecate 'kivy.utils.SafeList'
- [:repo:`7786`]: WindowBase: Add on_drop_begin, on_droptext and on_drop_end events

Breaking changes
----------------

- [:repo:`6290`]: Widget: Fix signature of add/remove/clear_widget  to be consistent with base class
- [:repo:`7264`]: Camera: Change play default to False
- [:repo:`7356`]: Widget: Widget.clear_widgets empty widget list does not remove all children
- [:repo:`7437`]: TextInput: Remove broken and confusing `suggestion_text` property
- [:repo:`7744`]: Change default input_type to null. Add some warning regarding TYPE_TEXT_FLAG_NO_SUGGESTIONS
- [:repo:`7763`]: Removed Python3.6 from the supported ones, it reached EOL
- [:repo:`7820`]: Patch gst current release to look for dlls in correct place for win store

Kv-lang
-------

- [:repo:`7371`]: KV: Allow using f-strings in KV-lang
- [:repo:`7703`]: refactor kivy.lang

Misc
----

- [:repo:`7204`]: Kivy: print kivy's version even when not a release.
- [:repo:`7271`]: Inspector: Prevent circular import breaking Window
- [:repo:`7403`]: Exceptions: Fix typos in message
- [:repo:`7433`]: Source: Fix typos in source code
- [:repo:`7453`]: Screen: Added Oneplus 6t in screen module
- [:repo:`7701`]: deprecate 'kivy.utils.SafeList'

Packaging
---------

- [:repo:`7341`]: OSX: Use platform.machine() for osx version detection
- [:repo:`7605`]: PyInstaller hook: Replace modname_tkinter with 'tkinter'
- [:repo:`7781`]: PyInstaller develop version isn't needed anymore

Widgets
-------

- [:repo:`7049`]: Camera: Fix GI camera provider crash when no texture is available after loading
- [:repo:`7213`]: ScrollView: Match scroll effect stop condition to start condition.
- [:repo:`7261`]: Camera: Revert "Fixes crash during camera configuration"
- [:repo:`7262`]: RecycleGridLayout : Fix layout when number of widgets match number of columns
- [:repo:`7264`]: Camera: Change play default to False
- [:repo:`7322`]: Widget: fix export_to_png not passing arguments through
- [:repo:`7353`]: RecycleLayout: Allow setting x, y sizing of views independently
- [:repo:`7372`]: Focus: Allow modifiers (e.g. numlock) be present to tab cycle focus
- [:repo:`7383`]: Dropdown: Fix reposition in scrollview/recycleview
- [:repo:`7391`]: Factory: Registered TouchRippleBehavior and TouchRippleButtonBehavior with Factory
- [:repo:`7426`]: Dropdown: Ensure visibility on reposition
- [:repo:`7434`]: ModalView: code cleanup regarding detection of main-Window:
- [:repo:`7437`]: TextInput: Remove broken and confusing `suggestion_text` property
- [:repo:`7457`]: ScrollView: Fix for scroll bar areas blocking clicks when scroll is disabled with overscroll
- [:repo:`7471`]: Video: Add support for preview image
- [:repo:`7488`]: FocusBehavior: Fix assumption that modifiers is always a set.
- [:repo:`7520`]: Video: Fixed handling eos after unloading
- [:repo:`7527`]: Label: Fix label not displaying as disabled if it is disabled when created
- [:repo:`7548`]: Fixes issue #7514 ('auto_halign_r' referenced before assignment)
- [:repo:`7610`]: Added scroll from swipe feature in TextInput
- [:repo:`7612`]: Fixed unexpected overscrolling bug when using mouse wheel
- [:repo:`7615`]: Fixed unexpected overscrolling bug when using mouse wheel, complement to #7612
- [:repo:`7618`]: Fixed TextInput visual selection bugs while scrolling
- [:repo:`7621`]: Fixed inconsistent behavior of TextInput bubble and handles
- [:repo:`7622`]: Fixes TextInput cursor issues when resizing/scrolling
- [:repo:`7631`]: Fixes some bugs in the TextInput if the text is right-aligned or center-aligned and not multiline.
- [:repo:`7636`]: Textinput on double tap improvement
- [:repo:`7641`]: Textinput:  Fixes issues #7165, #7236, #7235
- [:repo:`7642`]: TextInput loading time optimisation for large texts
- [:repo:`7706`]: SettingColor: Change method name to get_color_from_hex
- [:repo:`7737`]: CodeInput: fixed disappearing lines after inserting text
- [:repo:`7740`]: TextInput: easier tokenize delimiters setting; quotes removed from default delimiters
- [:repo:`7775`]: Don't let 'ScrollEffect.reset()' set 'is_manual' to True
- [:repo:`7796`]: EventManagerBase: Fix indentation and typos in the doc
- [:repo:`7807`]: Textinput: Simplified the swipe feature logic. Fixed a bug that was preventing to show the select all / paste bubble
- [:repo:`7814`]: :zap: Prevent crash (overflow error) when scrollbar is hidden
- [:repo:`7816`]: VideoPlayer: Defer before the next frame the default thumbnail and annotations loading

Core-app
--------

- [:repo:`7173`]: Logger: Do not mutate log record, fixes #7062
- [:repo:`7245`]: Resources: Add a cache for resource_find
- [:repo:`7293`]: Properties: Add dynamic screen density/dpi support
- [:repo:`7300`]: Logger: Remove refactoring artifact
- [:repo:`7307`]: Logger: Remove purge log's randomized behavior
- [:repo:`7326`]: Command line: Fix disabling kivy cmd args
- [:repo:`7429`]: Clock: Print remaining events before next frame upon too much iteration error
- [:repo:`7505`]: EventLoopBase: Remove provider from auto-remove list
- [:repo:`7508`]: App: Process app quit event while paused
- [:repo:`7512`]: EventLoopBase: Start/stop event loop only once
- [:repo:`7749`]: collections fix for python 3.10
- [:repo:`7763`]: Removed Python3.6 from the supported ones, it reached EOL
- [:repo:`7771`]: Explain the '--' separator for option parsing.
- [:repo:`7810`]: Track whether the clock has started

Core-providers
--------------

- [:repo:`7228`]: Image: Fix PIL label rendering shadow
- [:repo:`7231`]: Keyboard: Add keyboard suggestions and fix input type on android
- [:repo:`7260`]: Camera: Use NSString instead of AVCaptureSessionPreset in order to support MacOS < 10.13
- [:repo:`7263`]: Camera: Added API to change avfoundation camera provider orientation
- [:repo:`7279`]: Window: prevent "empty" mousewheel events from breaking scrollview
- [:repo:`7290`]: Camera: improve avfoundation by using memoryview and re-scheduling the interval on framerate change
- [:repo:`7299`]: Window: Handle DPI Windows messages until SDL2 handles them
- [:repo:`7303`]: Camera: Fix AVFoundation provider to release the camera, start it async, and check if started before stopping it
- [:repo:`7339`]: Camera: Android camera focus mode fix
- [:repo:`7347`]: Window: Delay binding dpi until window is ready.
- [:repo:`7389`]: Mouse: Fix mouse being offset by 2 pixels vertically
- [:repo:`7390`]: SoundAndroidPlayer: Properly stop after playback completion
- [:repo:`7409`]: Window: Fix logging message
- [:repo:`7418`]: Video: Reduce latency from user interaction for ffpyplayer
- [:repo:`7467`]: Text: Raise when registering a font_regular with None
- [:repo:`7484`]: WindowBase: Add to_normalized_pos method
- [:repo:`7517`]: Core: Use importlib's __import__ for compatibility with patching
- [:repo:`7541`]: SoundLoader: Fix play calls not working in ffpyplayer after the first
- [:repo:`7620`]: removed print and added logging to flipVert
- [:repo:`7637`]: Added Custom titlebar support
- [:repo:`7647`]: WindowBase: Change type of clearcolor property to ColorProperty
- [:repo:`7648`]: WindowBase: Add transform_motion_event_2d method
- [:repo:`7688`]: Fix dds header comparison
- [:repo:`7726`]: Window.softinput_mode fix for "pan" and "below_target" modes when using kivy virtual keyboard.
- [:repo:`7744`]: Change default input_type to null. Add some warning regarding TYPE_TEXT_FLAG_NO_SUGGESTIONS
- [:repo:`7770`]: WindowBase: Update bind list of properties: system_size, size, width, height and center
- [:repo:`7778`]: WindowBase: Don't return motion event in transform_motion_event_2d method
- [:repo:`7786`]: WindowBase: Add on_drop_begin, on_droptext and on_drop_end events
- [:repo:`7793`]: WindowBase|WindowSDL: Add drop position for all on_drop_xxx events
- [:repo:`7795`]: WindowBase: Add *args to on_drop_xxx events

Core-widget
-----------

- [:repo:`6290`]: Widget: Fix signature of add/remove/clear_widget  to be consistent with base class
- [:repo:`7209`]: Animation: Allow canceling all animated widgets
- [:repo:`7356`]: Widget: Widget.clear_widgets empty widget list does not remove all children
- [:repo:`7424`]: Properties: Speed up bare widget creation (3X) and property dispatching/setting
- [:repo:`7439`]: Properties: Drop long number type and document numpy issues with NumericProperty
- [:repo:`7442`]: EventDispatcher: Removed/replaced all basestring occurrences with str
- [:repo:`7445`]: EventDispatcher: Rename method unregister_event_types to unregister_event_type
- [:repo:`7449`]: TextInput: Fix readonly mode preventing using cursor keys, wrapping, and more
- [:repo:`7459`]: Properties: Accept str-subclass where we accept strings
- [:repo:`7536`]: EventDispatcher: Add nicer error message for non-existing properties
- [:repo:`7658`]: Feature: EventManagerBase
- [:repo:`7774`]: Fix widget.disabled handling of value change of equal truthiness

Distribution
------------

- [:repo:`7257`]: Setup: Fix buggy detection of cython module name
- [:repo:`7362`]: Build: No oneliners in [options.extras_require]
- [:repo:`7663`]: Add python3.10 in the ci configuration
- [:repo:`7678`]: Add support for Apple Silicon on CI/CD
- [:repo:`7711`]: Add an option  to force a custom search path for SDL2 frameworks + fixes ARCHFLAGS
- [:repo:`7762`]: macOS deps: Update SDL to 2.0.20 and update SDL_ttf to 2.0.18
- [:repo:`7769`]: Add Linux AArch64 wheel build support
- [:repo:`7777`]: Bump to 2.1.0rc1
- [:repo:`7802`]: Bump to 2.1.0rc1
- [:repo:`7804`]: Use the `KIVY_RPI_VERSION` env variable to force the build of `egl_rpi` in non Raspi CI builds
- [:repo:`7813`]: Bump cython and kivy_deps versions to latest
- [:repo:`7820`]: Patch gst current release to look for dlls in correct place for win store
- [:repo:`7821`]: Bump to 2.1.0rc2
- [:repo:`7822`]: Bump to 2.1.0rc3

Documentation
-------------

- [:repo:`7010`]: Doc: Warn that decorated methods might not be bindable.
- [:repo:`7284`]: docs: fix simple typo, expressons -> expressions
- [:repo:`7286`]: Doc: Add negative size warning
- [:repo:`7288`]: Documentation: Updated prerequisites and supported python version for iOS
- [:repo:`7295`]: Doc cleanups
- [:repo:`7301`]: Doc: Add Kivy config example for inverted mtdev events
- [:repo:`7305`]: Slider: Fix step property docs
- [:repo:`7328`]: Added documentation for RecycleView viewclass statefullness,  including a warning, context paragraph, and minimal example
- [:repo:`7342`]: TabbedPanel: Doc calling `switch_to` from `__init__`
- [:repo:`7344`]: App: fix Trio example in docstring
- [:repo:`7358`]: Doc: Fix doc code formatting
- [:repo:`7359`]: Fix first doc line being ignored
- [:repo:`7366`]: Docs: use print() in docs, comment and generated code
- [:repo:`7392`]: Docs: Fix packaging-osx docs (homebrew)
- [:repo:`7432`]: Docs: Fix codespell found typos
- [:repo:`7435`]: Docs: check for "sphinx" in command line
- [:repo:`7441`]: Docs: Fix creating of docs of compoundselection.py
- [:repo:`7451`]: Docs: Fix Type Error when creating bytes from array in Python 3
- [:repo:`7481`]: Doc: Properties spelling fix
- [:repo:`7497`]: Docs: Use python3 super in example
- [:repo:`7560`]: Comment references the wrong layout
- [:repo:`7561`]: Typo on docs, missing "the"
- [:repo:`7580`]: Fix line number references in basic.rst
- [:repo:`7581`]: Fixes double word in docs
- [:repo:`7592`]: Fix missing word in doc/guide/events.rst
- [:repo:`7603`]: Fixes pong tutorial collision on the right side.
- [:repo:`7614`]: Fix install command for zsh
- [:repo:`7623`]: Sphinx: Use class instead of instance in add_lexer + Fixes search on sphinx>1.7.9
- [:repo:`7624`]: Sphinx: Fixes missing documentation_options
- [:repo:`7625`]: Update line number references in documentation
- [:repo:`7672`]: fix various docs
- [:repo:`7693`]: Remove wording and functions specific to Python 2
- [:repo:`7717`]: MotionEvent: Fix docstring in dispatch_done method to reference post_dispatch_input
- [:repo:`7752`]: Improves docs on mobile, fixes duplicated getting started
- [:repo:`7757`]: Update README.md
- [:repo:`7764`]: Update license year
- [:repo:`7766`]: Add support for older Sphinx versions
- [:repo:`7773`]: Docs review before release 2.1.0
- [:repo:`7790`]: made code examples user friendly; fixes #7720
- [:repo:`7799`]: Dark Theme support for docs
- [:repo:`7801`]: made Generic Prompt unselectable
- [:repo:`7815`]: MotionEvent: Fix indentation in module doc
- [:repo:`7826`]: add GitHub URL for PyPi
- [:repo:`7830`]: EventManager: Fix typo in module doc

Graphics
--------

- [:repo:`4854`]: Graphics: Add Sdl2 vsync
- [:repo:`7270`]: Graphics: Check whether user updated GL instructions from external thread.
- [:repo:`7277`]: SVG: Fix SVG instruction iteration for python 3.9.
- [:repo:`7455`]: Graphics: Only check for threading issues once graphics is initialized

Input
-----

- [:repo:`7387`]: Mouse: Update MouseMotionEventProvider to dispatch hover events
- [:repo:`7425`]: Mouse: Fix computation of relative touch position in MouseMotionEventProvider
- [:repo:`7492`]: MouseMotionEventProvider: Refactor of provider and tests
- [:repo:`7549`]: MouseMotionEventProvider: Add disable_hover property
- [:repo:`7587`]: Fix PermissionError when reconnecting mtdev input devices
- [:repo:`7644`]: MouseMotionEventProvider: Update doc of disable_hover property
- [:repo:`7659`]: MotionEvent: Fix scale_for_screen method
- [:repo:`7679`]: MotionEvent: Fix calculation of z values in scale_for_screen method
- [:repo:`7684`]: Enable pressure for touches in android (and ios?)
- [:repo:`7691`]: MotionEvent: Fix keeping of the previous normalized position
- [:repo:`7714`]: MouseMotionEventProvider: Update simulated touch graphics on window resize or rotate
- [:repo:`7785`]: Input providers: Assign type_id to MotionEvent subclasses

Tests/ci
--------

- [:repo:`7176`]: Dev: Add pre-commit.com framework hooks
- [:repo:`7292`]: Benchmarks: Add benchmarks option measurements to pytest
- [:repo:`7461`]: AsyncImageTestCase: Fix for test_reload_asyncimage method and cleanup
- [:repo:`7464`]: Makefile: Add test commands to show missing coverage lines
- [:repo:`7466`]: Tests: Increase test coverage
- [:repo:`7475`]: MouseHoverEventTestCase: Skip testing on Windows platform
- [:repo:`7483`]: MouseHoverEventTestCase: Enable some tests on Windows CI
- [:repo:`7493`]: GraphicUnitTest: Add clear_window_and_event_loop method
- [:repo:`7494`]: MouseHoverEventTestCase: Dispatching event on_cursor_leave to cleanup some tests
- [:repo:`7495`]: CI: Removed unused id_rsa.enc. ssh keys are in the secret env
- [:repo:`7502`]: MultitouchSimulatorTestCase: Don't render widgets in tests
- [:repo:`7509`]: CI: Switch rsa ssh key to ed25519 for server upload
- [:repo:`7513`]: Tests: Latest pyinstaller includes fixes for tests
- [:repo:`7515`]: GraphicUnitTest: Fix signature of tearDown method to use (*args, **kwargs)
- [:repo:`7516`]: MouseHoverEventTestCase: Removed skip of test methods on Windows CI
- [:repo:`7674`]: temporary force python3.9 use in the ci
- [:repo:`7676`]: Bump support-request to v2. Previous integration has been shut down.
- [:repo:`7760`]: Fixes benchmark tests on wheels
- [:repo:`7780`]: Updates action-gh-release and use the default token
- [:repo:`7784`]: Linux AArch64 wheel build optimization
- [:repo:`7794`]: Bring perf_test_textinput  inline with changes in TextInput
- [:repo:`7827`]: Increase timeout to avoid failing tests on windows-2022

2.0.0
=====

Highlights
----------

- [:repo:`6351`]: Core: Drop Python 2 support
- [:repo:`6368`]: Core: Add async support to kivy App
- [:repo:`7084`]: Dependencies: Add basic dependencies to install requirements

Breaking changes
----------------

- [:repo:`6351`]: Core: Drop Python 2 support.
- [:repo:`6368`]: Core: Add async support to kivy App
- [:repo:`6448`]: EventDispatcher: Move `__self__` from widget to EventDispatcher and fix tests.
- [:repo:`6467`]: Graphics: Change filename to source
- [:repo:`6469`]: ModalView: Updating ModalView to improve theming
- [:repo:`6607`]: Window: Fix SDL Keycode Typo
- [:repo:`6650`]: DropDown/ModalView: Make modal and dropdown consistent
- [:repo:`6677`]: Widget: Remove `id` from Widget.
- [:repo:`6678`]: ScrollView: Add always_enable_overscroll property on scrollview
- [:repo:`6721`]: Image: Remove gpl gif implementation
- [:repo:`6918`]: ColorProperty: Use ColorProperty instead of ListProperty for color property
- [:repo:`6937`]: Base: Rename `slave` to `embedded`
- [:repo:`6950`]: Cache: Raise KeyError if None is used as key in Cache

Kv-lang
-------

- [:repo:`6442`]: KV lang: Make it easy to copy Builder and Factory and make them all contexts.
- [:repo:`6548`]: Factory: Meaningful Error Message
- [:repo:`6880`]: KV: Use utf-8 encoding by default on reading .kv files. Fixes #5154

Misc
----

- [:repo:`6323`]: Loader: User agent was not correctly resolved.
- [:repo:`6658`]: Garden: Fixes incorrect path to kivy garden libs on iOS
- [:repo:`6703`]: Network: Fix https in python3.x
- [:repo:`6748`]: Network: Extend certifi usage to ios
- [:repo:`6922`]: WeakMethod: Fx and cleanup WeakMethod usage
- [:repo:`6931`]: VIM: Fix and improve vim syntax highlighting for kv lang
- [:repo:`6945`]: Cache: Don't double copy keys when purging cache by timeout
- [:repo:`6950`]: Cache: Raise KeyError if None is used as key in Cache
- [:repo:`6954`]: Network: Ignore ca_file on http scheme, fixes #6946
- [:repo:`7054`]: Networking: User Agent and Cookies added to UrlRequest

Packaging
---------

- [:repo:`6359`]: Packaging: Fix path by setting to bytes
- [:repo:`6643`]: PyInstaller: List kivy.weakmethod because pyinstaller doesn't see into cython files
- [:repo:`6772`]: PyInstaller: window_info is not included in x86 pyinstaller
- [:repo:`7080`]: OSX: Generate Kivy.app on the CI

Widgets
-------

- [:repo:`6288`]: TextInput: Cache `text` property in TextInput
- [:repo:`6362`]: Carousel: Let 'Carousel._curr_slide()' prepare for the situation where 'index' is None
- [:repo:`6365`]: Carousel: Let 'Carousel.remove_widget()' remove the container of the widget
- [:repo:`6372`]: Carousel: make 'Carousel.remove_widget()' not cause 'IndexError'
- [:repo:`6374`]: Carousel: Make 'Carousel' able to handle the case where 'loop == True' and 'len(slides) == 2'
- [:repo:`6436`]: ColorWheel: Remove bug in algorithm to compute arcs of colorwheel (#6435)
- [:repo:`6469`]: ModalView: Updating ModalView to improve theming
- [:repo:`6481`]: ScreenManager: Make clear_widgets correctly iterate over screens
- [:repo:`6542`]: TextInput: Fixes TextInput Bubble from diseappering immediately after it appears
- [:repo:`6543`]: TextInput: Fixes TextInput cursor "rendering" issue
- [:repo:`6574`]: TreeViewNode: Fix arrow pos and size
- [:repo:`6579`]: Slider: Horizontal value track is offset from the center of Slider
- [:repo:`6624`]: Filechooser: Use full path
- [:repo:`6650`]: DropDown/ModalView: Make modal and dropdown consistent
- [:repo:`6666`]: TextInput: Fix for crashes caused by text selection outside of TextInput area
- [:repo:`6678`]: ScrollView: Add always_enable_overscroll property on scrollview
- [:repo:`6741`]: GridLayout: Add 'orientation' property to GridLayout
- [:repo:`6815`]: Image: Fixes for Image and AsyncImage
- [:repo:`6859`]: Slider: Adding allow_stretch to Slider in style.kv
- [:repo:`6879`]: VKeyboard: Fix key_background_color property not used
- [:repo:`6897`]: RecycleView: Add behavior to set RV data using kv ids
- [:repo:`6905`]: FileChooser: Add font property
- [:repo:`6912`]: TextInput: Remove 'encode' argument from getter method of 'text' property of TextInput
- [:repo:`6918`]: ColorProperty: Use ColorProperty instead of ListProperty for color property
- [:repo:`6942`]: ScrollView: Don't crash when scrollview's content is the same size
- [:repo:`6971`]: Camera: Fix an inconsistency between docs and code on Camera
- [:repo:`6976`]: ModalView: Prevent modalview dismissal without on_touch_down
- [:repo:`6985`]: ScrollView: Fix scrollview scroll/effect recursion
- [:repo:`7009`]: TextInput: IME support for textinput
- [:repo:`7021`]: ColorProperty: Use ColorProperty for remaining color properites
- [:repo:`7032`]: ScreenManager: Fix typo in SlideTransition
- [:repo:`7069`]: ScrollView: Horizontal scrolling disabled if no overflow
- [:repo:`7074`]: Splitter: Fix handling offset
- [:repo:`7118`]: GridLayout : optimize GridLayout
- [:repo:`7129`]: TabbedPanel: Stop tab buttons from scrolling around
- [:repo:`7196`]: ScrollView: fix jumping to bottom when using scrollwheel.

Core-app
--------

- [:repo:`6351`]: Core: Drop Python 2 support.
- [:repo:`6368`]: Core: Add async support to kivy App
- [:repo:`6376`]: Cython: Set cython language_level to py3.
- [:repo:`6381`]: Inspector: Use sets to check if inspector should be activated.
- [:repo:`6404`]: App: Fix pausing without app instance
- [:repo:`6458`]: Core: Fix memory leaks by cleaning up after resources
- [:repo:`6540`]: Config: fix erroneous check of KIVY_NO_ENV_CONFIG
- [:repo:`6581`]: Dependencies: Bump max cython version
- [:repo:`6729`]: DDSFile: ddsfile.py fix for string/bytes comparing for py3
- [:repo:`6773`]: Clock: Add correct value of CLOCK_MONOTONIC for OpenBSD
- [:repo:`6798`]: Platform: Corrected platform detection on Android
- [:repo:`6910`]: Logger: Add encoding
- [:repo:`6926`]: Clock: Add clock lifecycle, better exception handling and other cleanup
- [:repo:`6937`]: Base: Rename `slave` to `embedded`
- [:repo:`6994`]: EventLoop: Don't do event loop stuff when stopped.
- [:repo:`7083`]: Core: Add _version.py and move updating version metadata to the CI
- [:repo:`7112`]: Python: Require python version >=3.6
- [:repo:`7132`]: Python: Add support for Python 3.9.
- [:repo:`7151`]: Dependencies: Bump cython to 0.29.21
- [:repo:`7178`]: Dependencies: Add dependency selection varaibles
- [:repo:`7181`]: Logging: Added color support for compatible terminals

Core-providers
--------------

- [:repo:`6384`]: Window: Allow window providers to indicate which gl backends they are compatible with
- [:repo:`6422`]: Label: Fixes multiline label w/ line_height < 1
- [:repo:`6433`]: Window: Center cache problem on MacOS
- [:repo:`6461`]: Audio: Fix playing audio streams from ffpyplayer
- [:repo:`6507`]: Text: Revert "Fixes multiline label w/ line_height < 1"
- [:repo:`6513`]: Text: Fix issue #6508 Multiline label w/ line_height < 1 renders badly (workaround)
- [:repo:`6515`]: Text: Fixes positioning (valign) issue when using max_lines
- [:repo:`6578`]: Window: Revert swap forced sync (#4219) as it causes performance issue
- [:repo:`6589`]: Window: Add the ability to show statusbar on iOS
- [:repo:`6603`]: Audio: Native audio support for Android
- [:repo:`6607`]: Window: Fix SDL Keycode Typo
- [:repo:`6608`]: Audio: Replace deprecated variables in audio providers
- [:repo:`6721`]: Image: Remove gpl gif implementation
- [:repo:`6743`]: Clipboard: xclip less verbose Kivy startup
- [:repo:`6754`]: Text: Properly raise errors reading a font
- [:repo:`6947`]: Image: Remove 'img_gif' entry from image_libs
- [:repo:`6988`]: Camera: Improve avfoundation camera implementation on iOS
- [:repo:`7071`]: Camera: Fixes crash during camera configuration
- [:repo:`7102`]: Audio: Added loop functionality for SoundAndroidPlayer

Core-widget
-----------

- [:repo:`5926`]: Animation: Fix kivy.animation.Sequence and kivy.animation.Parallel consistency
- [:repo:`6373`]: Properties: Allow observable list and dict dispatch to propagate exceptions.
- [:repo:`6441`]: EventDispatcher: Move Widget proxy_ref upwards to EventDispatcher
- [:repo:`6443`]: Property: Initialize KV created property with default value
- [:repo:`6448`]: EventDispatcher: Move `__self__` from widget to EventDispatcher and fix tests.
- [:repo:`6677`]: Widget: Remove `id` from Widget.
- [:repo:`6858`]: Effects: Fix update_velocity
- [:repo:`6917`]: ColorProperty: Re-add ColorProperty to __all__ list in properties.pyx module
- [:repo:`6930`]: Property: Use ObservableList as internal storage for ColorProperty
- [:repo:`6941`]: Property: Let ColorProperty accept arbitrary list types.
- [:repo:`6965`]: Property: Allow assignment of color names as values for ColorProperty
- [:repo:`6993`]: Property: Add kwargs to 'sort' method of ObservableList

Distribution
------------

- [:repo:`6354`]: Dependecy: Move cython version info to setup.cfg.
- [:repo:`6355`]: Dependency: kivy_deps need to be imported before any modules.
- [:repo:`6356`]: Dependency: Bump cython to 0.29.10 to fix CI building.
- [:repo:`6397`]: Install: Automatically discover kivy sub-packages
- [:repo:`6562`]: RPi: Autodetect when we are on a Raspberry Pi 4
- [:repo:`6568`]: CI: Cross compile wheel for armv7l (Raspberry Pi 4) using Github Actions CI
- [:repo:`6642`]: Install: Switch to using pyproject.toml and setup.cfg for metadata
- [:repo:`6656`]: Wheel: Don't package examples in the wheel
- [:repo:`6662`]: CI: Compile wheels for Raspberry Pi 1-3 using the CI
- [:repo:`6670`]: Dependencies: Fix CI PyPI upload and pin to latest kivy_deps versions.
- [:repo:`6674`]: Sdist: Cannot handle carriage return in description.
- [:repo:`6769`]: RPi: Kivy now works on the Raspberry Pi 4 without X11
- [:repo:`6774`]: Install: Build the extensions in parallel if the options has not been set
- [:repo:`6852`]: Platform: Fix android platform detection when using p4a
- [:repo:`6854`]: Install: Reuse `kivy_build` var (complements #6852)
- [:repo:`6891`]: Cython: Update to latest cython version
- [:repo:`6990`]: Installation: Make setuptools use its local distutils
- [:repo:`7084`]: Dependencies: Add min basic dependencies to install requirements.
- [:repo:`7110`]: Makefile: Detect python verion and gracefully fail on unsupported version
- [:repo:`7152`]: RPi: Stop building wheels for RPi stretch
- [:repo:`7154`]: Anconda: Respect SDKROOT and use_osx_frameworks
- [:repo:`7157`]: Makefile: Try python3 first as python may point to python2.
- [:repo:`7159`]: Makefile: Use python3 if it's present.
- [:repo:`7195`]: Inlcude doc in PR checklist

Documentation
-------------

- [:repo:`6352`]: Docs: force to use sphinx 1.7.9 to restore search
- [:repo:`6377`]: Docs: Embed func signatures in cython to help IDEs.
- [:repo:`6383`]: Doc: Create FUNDING.yml
- [:repo:`6389`]: Doc: Fix linux install docs and update garden instructions
- [:repo:`6398`]: Doc: Update clock.py - Corrected typo
- [:repo:`6399`]: Doc: Fix pip link
- [:repo:`6427`]: Doc: Add comment on required pip version
- [:repo:`6459`]: Docs: fix wrong highlights
- [:repo:`6466`]: Docs: Config docs update
- [:repo:`6478`]: Examples: Fix lack of white-space after ":" in pong.kv
- [:repo:`6479`]: Doc: Fix typos, grammar in install instructions
- [:repo:`6485`]: Doc: Fix KIVY_EVENTLOOP doc
- [:repo:`6491`]: Doc: Fix Widget.pos_hint doc
- [:repo:`6510`]: Doc: Few minor fixes in the doc.
- [:repo:`6511`]: Doc: Update note about kivy-ios python version
- [:repo:`6523`]: Doc: Remove reference to Kivy Designer
- [:repo:`6537`]: Doc: fix GridLayout doc
- [:repo:`6558`]: Examples: Fixed depreciated option for twisted, and sys.exc_call is only run in py2
- [:repo:`6625`]: Doc: Update CONTRIBUTING.md
- [:repo:`6636`]: Example: Missing directory replaced in colorpicker #6599
- [:repo:`6638`]: Docs: Fix typo
- [:repo:`6641`]: Doc: Fix TextInput typos cursor row/col
- [:repo:`6683`]: Doc: Fix spinner kv example
- [:repo:`6694`]: Doc: Fix css on docs
- [:repo:`6712`]: Doc: Revisit of the Windows installation instructions
- [:repo:`6714`]: Doc: Fix spelling errors
- [:repo:`6750`]: Doc: Update packaging-windows.rst
- [:repo:`6775`]: Doc: Fixed the gallery documentation
- [:repo:`6778`]: Doc: Updated Raspberry Pi 4 doc on HW acceleration
- [:repo:`6780`]: Doc: Make RPi SDL2 install instructions clear
- [:repo:`6813`]: Example: bugfix for 3D rendering example
- [:repo:`6821`]: Doc: Expand on the current logger docs
- [:repo:`6863`]: Doc: Add missing hid input parameter
- [:repo:`6868`]: Doc: iOS - migrates to the new install procedure
- [:repo:`6882`]: Example: Improved ScreenManager example
- [:repo:`6895`]: Doc: Add annotations to proxies.
- [:repo:`6924`]: Doc: Buildozer is now in Beta.
- [:repo:`6927`]: Doc: Improvements to kv lang docs
- [:repo:`6938`]: Doc: trigger_action warning / documentation updates
- [:repo:`6963`]: Doc: Correct comments to use proportion, not percent
- [:repo:`6969`]: Doc: Fix docs for on_dropfile
- [:repo:`6975`]: Doc: Update the dev installation instructions
- [:repo:`6977`]: Doc: Add some typing to clock
- [:repo:`6979`]: Doc: Remove duplicate python3-pip
- [:repo:`7002`]: Doc: Print about KIVY_NO_ARGS when printing usage.
- [:repo:`7022`]: Doc: Update doc for all instances of ColorProperty
- [:repo:`7038`]: Doc: Fix on_ref_press documentation
- [:repo:`7039`]: Doc: fixed typo in hbar doc string
- [:repo:`7043`]: Doc: fixed doc string
- [:repo:`7160`]: Examples: Add Recycleview examples
- [:repo:`7179`]: Docs: Switch to staging docs on kivy-website-docs
- [:repo:`7222`]: Docs: minor typo fix in layout docs
- [:repo:`7240`]: Docs: Re-write install docs.
- [:repo:`7241`]: Docs: Add changelog to docs

Graphics
--------

- [:repo:`6457`]: Graphics: Fix "Error in sys.excepthook"
- [:repo:`6467`]: Graphics: Change filename to source
- [:repo:`6472`]: Graphics: Fix relative import for the egl backend
- [:repo:`6533`]: Graphics: Fixes fbo/renderbuffer freeze on iOS
- [:repo:`6702`]: Graphics: Adding support for non-file SVGs
- [:repo:`6777`]: Graphics: Also set points _mode propery to LINE_MODE_POINTS
- [:repo:`6808`]: Graphics: Fix Svg consistency #6467
- [:repo:`6844`]: Graphics: Use GLES context when ES2 is forced
- [:repo:`6846`]: Graphics: Revert "Use GLES context when ES2 is forced"
- [:repo:`6978`]: Graphics: fix ignored alpha value in hsv mode

Input
-----

- [:repo:`6319`]: Mouse: Fix ctypes definition to work with other packages
- [:repo:`7065`]: Mouse: Added support for the mouse4 and mouse5 buttons

Tests/ci
--------

- [:repo:`6375`]: CI: Fix CI failure, 3.5.7 doesn't have compiled binaries.
- [:repo:`6390`]: CI: Python 3.5 doesn't seem to work anymore on travis bionic.
- [:repo:`6403`]: CI: Remove osx workarounds as it breaks the build.
- [:repo:`6415`]: Test: Add tests for coordinates translation
- [:repo:`6417`]: Test: Add preliminary support for coverage for kv files.
- [:repo:`6482`]: CI: Remove usage of KIVY_USE_SETUPTOOLS
- [:repo:`6503`]: CI: Fix rtd builds
- [:repo:`6514`]: Test: Add test method for touch to follow a widget's position
- [:repo:`6516`]: CI: Don't use the Window when computing dp during docs generation
- [:repo:`6554`]: CI: Build latest .DMG for osx app
- [:repo:`6556`]: CI: Update .travis.yml for osx app on master
- [:repo:`6565`]: Test: Add ability to specify offset from widget pos
- [:repo:`6570`]: CI: Enable Python 3.8 wheel generation for osx
- [:repo:`6595`]: Tests: Fix test failures in Python 3.8 (fixes #6594)
- [:repo:`6618`]: Test: Don't preset async_sleep
- [:repo:`6622`]: CI: Switch from Travis/Appveyor to GitHub Actions
- [:repo:`6659`]: CI: Use pip to build wheel so it uses pyproject.toml.
- [:repo:`6669`]: CI: Test generated wheels and sdist
- [:repo:`6673`]: CI: Latest twine doesn't support py3.5
- [:repo:`6681`]: CI: Switch to flake8 and fix PEP8 issues
- [:repo:`6682`]: CI: Create all the wheels before doing any uploads
- [:repo:`6771`]: GitHub: Update issue templates to new format
- [:repo:`6845`]: Tests: Fix failing tests
- [:repo:`6855`]: CI: Upgrade to actions/checkout@v2 & actions/setup-python@v2
- [:repo:`6892`]: Test: Fix failing coverage
- [:repo:`6940`]: CI: Fix linux SDL2
- [:repo:`6951`]: Tests: Refactors test_urlrequest.py
- [:repo:`7115`]: CI: Remove mcnotify integration
- [:repo:`7147`]: PEP8: Fix PEP8 issues
- [:repo:`7174`]: Tests: Warn that async app test framewrok may be removed from kivy.
- [:repo:`7201`]: CI: Test all wheel versions, not just one per OS
- [:repo:`7203`]: Tests: Ensure Bubble uses it's superclass's valid private API

1.11.1 (June 20, 2019)
============================

This release fixed some issues with the docs, the CI, and Kivy dependencies that was introduced in 1.11.0 (:repo:`6357`).

1.11.0 (June 1, 2019)
============================

Installation notes
------------------

Windows

- [:repo:`6324`]: We are transitioning the kivy Windows dependencies from the `kivy.deps.xxx` namespace stored under `kivy/deps/xxx` to the `kivy_deps.xxx` namespace stored under `kivy_deps/xxx`. Pip is sometimes not able to distinguish between these two formats, so follow the instructions below.
- If you're **not upgrading** Kivy, please make sure to pin your `kivy.deps.xxx==x.y.z` dependencies to the versions that was on pypi when your Kivy was released so that you don't get newer incompatible dependencies.
- If you're **upgrading** Kivy, manually uninstall all the `kivy.deps.xxx` dependencies because pip will not uninstall them when you're upgrading. Then re-install the `kivy_deps.xxx` dependencies as instructed on the Kivy website.
- If you're installing the **first time**, simply follow the instructions on Kivy's website.

Linux and macOS

- The new Linux wheels (:repo:`6248`) can be installed with just `pip install kivy`, however, just like on macOS it comes without the Gstreamer dependencies so it has no video and minor audio support. For video/audio support, please install ffpyplayer and set `KIVY_VIDEO=ffpyplayer` in the environment, or install kivy using an alternative method that provides these dependencies.

Highlights
----------

Support

- [:repo:`5947`]: We have moved from IRC to Discord. However, there's matrix integration if you are unable to use Discord. See https://kivy.org/doc/master/contact.html#discord.

Configuration

- [:repo:`6192`]: Support for environmental variables that control the config in the form of `KCFG_SECTION_KEY` has been added. E.g. setting `KCFG_KIVY_LOG_LEVEL=warning` in the environment is the same as calling `Config.set("kivy", "log_level", "warning")` or setting the `log_level` in the `kivy` section of the config to `warning`. Note that underscores are not allowed in the section names.
- Any key set this will way will take precedence on the loaded `config.ini` file. Support for this can be disabled by setting the enviornmental variable `KIVY_NO_ENV_CONFIG=1` and the environment will not be read for configuration options.

KV lang

- [:repo:`6257`]: A new KV-Python integration event that fires when all the KV rules of the widget has been applied, `on_kv_post`, has been added to the `Widget` class. This event fires for a widget when all the KV rules it participates in has been applied and `ids` has been initialized. Binding to this event will let you execute code for your widget without having to schedule the code for the next clock cycle.
- Similarly, a new `apply_class_lang_rules` method was added to `Widget` that is called in order to apply the KV rules of that widget class. Inheriting and overwriting that method will give you the oppertunity to execute code before any KV rules are applied.

Garden

- We are transitioning the Kivy garden flowers from the `kivy.garden.flower` namespace stored under `kivy/garden/flower` or `~/.kivy/garden` to the normal python package format `kivy_garden.flower` namespace stored under `kivy_garden/flower`. With the new configuration, garden flowers will be `pip` installable, support cython flowers, and not require the custom garden tool.
- We're hoping to transition all flowers to the new format, however, for now many flowers still require installation by the garden tool.
- For users, see https://kivy-garden.github.io/index.html#generalusageguidelines. For developers, see https://kivy-garden.github.io/index.html#developmentguidelines for how to start a new flower, and https://kivy-garden.github.io/index.html#guideformigratingflowersfromlegacystructure for how to migrate existing flowers to the new format.

Other

- [:repo:`6186`]: Live resizing has been added for desktop platforms that use the SDL2 window backend.


Deprecated
----------

- [:repo:`6313`]: Pygame has been deprecated. We urge users who have been using pygame to try SDL2 and our other providers. If there are any reasons why Pygame is used instead of SDL2 please let us know so we can fix them.
- Deprecation warnings have also been added to everything that has been deprecated in the past.

Breaking changes
----------------

- [:repo:`6095`]: Changed the Android version to use `App.user_data_dir` for the configuration and added a missing dot to the config file name.
- [:repo:`5340`]: Removed DropDown.dismiss in on_touch_down so it is only dismissed in on_touch_up.
- [:repo:`5990`, :repo:`6169`]: We now use pytest to run our tests rather than nose.
- [:repo:`5968`]: Listview and all its associated modules has finally be removed in favor of RecycleView.


Base
----

Cache

- [:repo:`5995`]: : use Logger.trace to prevent the purge flooding terminal in debug
- [:repo:`5988`]: Removed cache print statements

Config

- [:repo:`6333`]: Properly chceck that KIVY_NO_ENV_CONFIG is not set to zero.

Inspector

- [:repo:`5919`]: Let the Inspector browse into WeakProxy'd widgets

Logger

- [:repo:`6322`]: PermissionError is not defined in py2.

Multistroke

- [:repo:`5821`]: Increase timeout/sleep to increase test robustness

Network

- [:repo:`6256`]: Set cookie header workaround
- [:repo:`6083`]: Added the ability to stop (kill) the UrlRequest thread
- [:repo:`5964`]: Allow setting url agent for async image and urlrequest

Properties

- [:repo:`6223`]: Fix handling None values in DictProperty and ListProperty
- [:repo:`6055`]: Cache values of AliasProperty where possible
- [:repo:`5960`]: Fix Cython properties syntax
- [:repo:`5856`]: Update AliasProperty to cache value only if "cache" argument is set to True
- [:repo:`5841`]: fix issues with `disabled` aliasproperty

Storage

- [:repo:`6230`]: Update jsonstore.py

Tools

- [:repo:`6330`]: Create changelog_parser.py
- [:repo:`5797`]: fix syntax table for emacs kivy-mode

Utils

- [:repo:`6175`]: kivy.utils.rgba function bug fix for python 3 (used to crash)

CI
--

- [:repo:`6311`]: Fix versioning in CI and in kivy.
- [:repo:`6295`]: Add pep8 stage and name builds on travis
- [:repo:`6250`]: Disable wheel building on osx by not watching travis cron status.
- [:repo:`6187`]: Make travis brew update more reliable
- [:repo:`6148`]: Fix some travis errors
- [:repo:`5985`]: Remove notification webhook from travis
- [:repo:`5978`]: tell travis to use bionic instead of trusty for tests
- [:repo:`5977`]: Fix travis flaky test
- [:repo:`5973`]: try using xcode10 for travis, as we cannot reproduce the imageio issue locally
- [:repo:`5934`]: Fix repo path in github app config comment
- [:repo:`5845`]: fix osx wheels

Core
----

Camera

- [:repo:`6168`]: fix broken update to avfoundation
- [:repo:`6156`]: Adding fixes to support ios camera
- [:repo:`6119`]: Add support for opencv 4
- [:repo:`6051`]: Update camera_android.py; fixes camera for Python 3
- [:repo:`6033`]: adding division future import to prevent further fps bugs
- [:repo:`6032`]: ensure floating point math when calculating fps
- [:repo:`6027`]: Fix 5146
- [:repo:`5940`]: Set android camera to autofocus
- [:repo:`5922`]: Updated camera_opencv.py to use reshape(-1) instead of tostring()

Clipboard

- [:repo:`6178`]: Clipboard: fixes for nspaste

Image

- [:repo:`6194`]: imageio: fix jpg/png saving
- [:repo:`6193`]: Image: don't force iteration if we reuse the cache
- [:repo:`6142`]: Fixes SDL2 image loading (jpg)
- [:repo:`6122`]: Allow saving a core Image into BytesIO
- [:repo:`5822`]: AsyncImage test fix for Windows py2.7

Spelling

- [:repo:`5951`]: Add a warning about support for pyenchant on windows

Text

- [:repo:`5970`]: fix styles from latests PR
- [:repo:`5962`]: Pango + fontconfig/freetype2 text provider

Video

- [:repo:`6270`]: Suggest how to fix unable to create playbin error.
- [:repo:`6246`]: Disabled set_volume() in core.video.ffpyplayer play() function. Fix for #6210
- [:repo:`5959`]: Issue 5945

Window

- [:repo:`6283`]: Limit live resize to desktop
- [:repo:`6179`]: window: fix multiple resize sent, and always sent the GL size, never …
- [:repo:`6164`]: Removed default orientation hints on Android
- [:repo:`6138`]: Fix android's sensor orientation
- [:repo:`6133`]: Make top/left of window dispatch events on updates
- [:repo:`6107`]: Fixed fullscreen and orientation handling to work with SDL-2.0.9 on Android
- [:repo:`6092`]: Fix sdl close inconsistencies. closes #4194

Doc
---

- [:repo:`6343`]: Fix docs for the release
- [:repo:`6334`]: Add docs for linux wheels
- [:repo:`6316`]: Update doc of AliasProperty
- [:repo:`6296`]: Remove duplicate installation instructions.
- [:repo:`6282`]: example for adding, `background_color` to Label
- [:repo:`6217`]: add a few kv examples to widget docs
- [:repo:`6215`]: Added pillow as a required python library
- [:repo:`6214`]: Grammar tweaks
- [:repo:`6204`]: Update OSX Install instructions for MakeSymlinks
- [:repo:`6199`]: Replace "it's" with "its" in several places
- [:repo:`6198`]: Correct a grammar mistake in two places
- [:repo:`6189`]: Update docs referring the change from nose tests to pytest
- [:repo:`6185`]: Raises minimum OSX version for current DMG.
- [:repo:`6180`]: Updated version no. for SDL building
- [:repo:`6159`]: Update installation for RPI with notes for latest Raspian issues
- [:repo:`6129`]: typo in doc comments
- [:repo:`6124`]: Removed doc note about Python 3 on Android being experimental
- [:repo:`6069`]: : explain mechanics of size property
- [:repo:`6061`]: Fix rpi instructions
- [:repo:`6049`]: Lang widgets need to be capitalized
- [:repo:`6047`]: fix misspelling in docs
- [:repo:`6031`]: rewriting of installation instructions
- [:repo:`6023`]: Fix docstring example for Vector.rotate
- [:repo:`6016`]: : Add doc for transform_point
- [:repo:`5971`]: fix doc generation
- [:repo:`5953`]: FAQ about the "Unable to get Window: abort"
- [:repo:`5943`]: Fixed bounce
- [:repo:`5925`]: Fix Doc 'Input Management'
- [:repo:`5912`]: OS X to macOS in README
- [:repo:`5911`]: Maintain separate docs for different releases
- [:repo:`5910`]: Versioned docs
- [:repo:`5908`]: : corrected typo in docs
- [:repo:`5903`]: Correct iOS docs, add ref links
- [:repo:`5900`]: : fix typo in window docs
- [:repo:`5896`]: add missing versionadded to pagelayout's anim_kwargs
- [:repo:`5895`]: add an example for using UrlRequest
- [:repo:`5887`]: : Grammar tweaks to test docs
- [:repo:`5879`]: add instructions for Fedora dependencies
- [:repo:`5869`]: python basics
- [:repo:`5858`]: Fixed PEP8 in Pong examples
- [:repo:`5850`]: : Update for Python 3.7
- [:repo:`5848`]: Document the `data` parameter for add_json_panel()
- [:repo:`5846`]: Maintain separate docs for different releases
- [:repo:`5840`]: : Remove py34 substitutions in nightly lists
- [:repo:`5839`]: Docs: Fix Windows nightly wheel links
- [:repo:`5833`]: Docs: Add note about not yet available py3.7 packages
- [:repo:`5790`]: Removed checkbox doc info about colours outside 0-1 range
- [:repo:`5765`]: Update documentation for Clock.triggered decorator

Graphics
--------

- [:repo:`6269`]: Add ability to specify dash offsets for Line
- [:repo:`6267`]: actually return value of wrapped gil_dbgGetAttribLocation
- [:repo:`6247`]: Fixes broken lines vertices
- [:repo:`6232`]: Respect the alpha value when setting rgb.
- [:repo:`6112`]: declare `_filename` in svg.pxd
- [:repo:`6026`]: Support building against mesa video core drivers.
- [:repo:`6003`]: : fix invalid offset calculation if attribute is optimized out
- [:repo:`6000`]: : Prevent enabling vertex attribute that are not in the shader
- [:repo:`5999`]: : Fixes KIVY_GL_DEBUG=1
- [:repo:`5980`]: Issue #5956: Fix casts in texture.blit_buffer for ushort and uint types.
- [:repo:`5969`]: Fix version number and supports ARGB/BGRA
- [:repo:`5957`]: Fix matrix transformation for orthographic projection
- [:repo:`5952`]: Change order of CGL backend to prefer dynamic GL symbol loading
- [:repo:`5907`]: Better #4752 fix
- [:repo:`6145`]: img_tools.pxi: Support pitch alignment in bgr->rgb conversion

Highlight
---------

- [:repo:`6062`]: Activating Open Collective

Input
-----

- [:repo:`6286`]: Add caps and numlock to the modifiers
- [:repo:`6281`]: SetWindowLongPtrW ctypes prototype bug
- [:repo:`6264`]: Fix the ctrl bug in hidinput (Issue #4007)
- [:repo:`6153`]: MTDMotionEventProvider, set thread name
- [:repo:`6152`]: HIDInputMotionEventProvider, set thread name
- [:repo:`6012`]: Fix HIDMotionEvent log formatting
- [:repo:`5870`]: Provider matching for input postproc calibration
- [:repo:`5855`]: add missing mapping for `numpaddecimal`

Lang
----

- [:repo:`5878`]: Make kivy.graphics.instructions.Callback available from within Kv lan…

Lib
---

Osc

- [:repo:`5982`]: Removed kivy.lib.osc from setup.py packages
- [:repo:`5967`]: Since osc is now available through oscpy, remove old crappy oscapi code

Modules
-------

Screen

- [:repo:`6048`]: screen: add definition for OnePlus 3t
- [:repo:`5928`]: Add definition for the HUAWEI MediaPad M3 Lite 10 tablet

Showborder

- [:repo:`6005`]: add modules/showborder

Other
-----

- [:repo:`6303`]: Update license file year.

Packaging
---------

- [:repo:`6341`]: Bump cython max version.
- [:repo:`6329`]: Add Pyinstaller tests
- [:repo:`6310`]: Only delete files in kivy, properly detect git.
- [:repo:`6306`]: Fixes for PPA and CI
- [:repo:`6305`]: Re-enable building osx wheels and app
- [:repo:`6275`]: Add windows gst support without pkg-config.
- [:repo:`6268`]: Tested with cython 0.29.7
- [:repo:`6182`]: Update OSX SDL2/Image/Mixer/TTF to latest version
- [:repo:`6165`]: Include GStreamer in PyInstaller package
- [:repo:`6130`]: Removed python version specification from buildozer install
- [:repo:`6128`]: Fix reading description #6127
- [:repo:`6054`]: Add new "canonical" path for binary Mali driver
- [:repo:`6046`]: Added Arch Linux (ARM)
- [:repo:`6008`]: Allow to override build date with SOURCE_DATE_EPOCH
- [:repo:`5998`]: Change check for Cython to attempt fallback to setuptools on supporte…
- [:repo:`5966`]: Update with Cython 0.28.5
- [:repo:`5866`]: Add support for cross-compiling for the raspberry pi
- [:repo:`5834`]: Fix missing requirements for Python 3.6 64bit
- [:repo:`5826`]: Drop support for py3.3, which is EOL
- [:repo:`5820`]: automate .app/dmg creatio for both python2 and 3 on osx
- [:repo:`5793`]: Improve Makefile debug configuration
- [:repo:`5777`]: Update Cython to 0.28.3

Widgets
-------

Bubble

- [:repo:`6043`]: Configure Bubble's BackgroundImage's auto scale property

Carousel

- [:repo:`5975`]: fix missing touchModeChange renaming to touch_mode_change
- [:repo:`5958`]: Fix 5783 carousel looping
- [:repo:`5837`]: carousel - update add_widget with 'canvas' parameter

Checkbox

- [:repo:`6317`]: Fix checkbox state issues.
- [:repo:`6287`]: Fix CheckBox Python2 compatibility.
- [:repo:`6273`]: Fix "Object no attribute active" (Bug introduced via PR #4898)

Colorpicker

- [:repo:`5961`]: ColorPicker refactor to prevent multiples event firing

Filechooser

- [:repo:`6050`]: correction of a malfunctioning with ..\ in Windows platforms (function _generate_file_entries)
- [:repo:`6044`]: Limited FileChooserProgress text size to widget size

Modalview

- [:repo:`5781`]: Add 'on_pre_open' and 'on_pre_dismiss' events to ModalView

Pagelayout

- [:repo:`5868`]: anim_kwargs in PageLayout

Recycleview

- [:repo:`5963`]: Fix 5913 recycle view steals data

Scatter

- [:repo:`5983`]: Issue #5773: Ensure to dispatch on_transform_with_touch event when the angle change

Screen

- [:repo:`6347`]: add tests for #6338
- [:repo:`6346`]: Make switch_to accept already added screens.
- [:repo:`6344`]: Revert "[widgets/screen]Fix #3143"
- [:repo:`6279`]: Fix #3143

Scrollview

- [:repo:`6294`]: [ScrollView] Touch is in wrong coordinates
- [:repo:`6255`]: Fix " object has no attribute 'startswith' "
- [:repo:`6252`]: Attempt to fix nested scrollviews
- [:repo:`6020`]: Add smooth_scroll_end

Tabbedpanel

- [:repo:`6291`]: Fix bug in TabbedPanel.remove_widget method

Textinput

- [:repo:`6309`]: Fix TextInput shortcuts
- [:repo:`6249`]: Fix issues #6226 and #6227 in multiline-enabled TextInput
- [:repo:`6120`]: Corrected textinput key input detection to only use on_textinput
- [:repo:`6113`]: Made textinput ignore space keydown/keyup for space input

Treeview

- [:repo:`5844`]: fix #5815 uncomplete node unselection in treeview

Widget

- [:repo:`5972`]: fix widget tests for python2
- [:repo:`5954`]: Scale export to png


1.10.1 (July 8, 2018)
============================

Core
----

- [:repo:`4974`]: Video: update 'loaded' on new video, unload previous video
- [:repo:`5053`]: ffpyplayer video: update frame/position on seek if video paused
- [:repo:`5109`]: Add textedit event for text editing by IME
- [:repo:`5187`]: Fix Windows clipboard when pasting a file
- [:repo:`5206`]: Touchscreen fixes
- [:repo:`5220`]: Redeclare Svg.reload as throwing an exception.
- [:repo:`5222`]: Fix typo in SVG
- [:repo:`5233`]: svg improvements
- [:repo:`5252`]: Add support for shaped windows
- [:repo:`5264`]: Remove double list copy in Animation._update
- [:repo:`5265`]: Remove dead code for SDL2 windowresized event
- [:repo:`5281`]: Make App.on_config_change an event
- [:repo:`5298`]: Add support for saving flipped Textures
- [:repo:`5305`]: img_pygame: Fix loading of binary alpha formats
- [:repo:`5312`]: ffpyplayer video: disable builtin subtitles by default
- [:repo:`5313`]: ffpyplayer video: better video seek
- [:repo:`5324`]: window_sdl2: Fix memory leak in screenshot
- [:repo:`5325`]: text_sdl2: Fix very unlikely memory leak
- [:repo:`5328`]: Fix build with cython 0.26
- [:repo:`5355`]: handle_exception defaults to RAISE, not STOP
- [:repo:`5362`]: Raspbian stretch egl library fix
- [:repo:`5377`]: Let dpi formatting exceptions in kv propagate out from cython.
- [:repo:`5382`]: Fix Json+DictStore not raising error for non-existing folder + unittest
- [:repo:`5387`]: _text_sdl2.pyx: Don't clear pixel memory twice
- [:repo:`5389`]: Don t drop SDL_Dropfile event while in pause #5388
- [:repo:`5393`]: Forward kwargs to config parser.
- [:repo:`5396`]: Actually display multitouch emulation if sim set to True.
- [:repo:`5421`]: Fix host/port handling in UrlRequest
- [:repo:`5423`]: Add probesysfs option to include devices that offer core pointer functionality
- [:repo:`5435`]: Changed Logger.error to Logger.warning on android import
- [:repo:`5437`]: Purge KV lang TRACE logs on demand with environment variable
- [:repo:`5459`]: audio_sdl2: Update for mixer v2.0.2 support
- [:repo:`5461`]: Monkey patch PIL frombytes & tobytes, fixes #5460
- [:repo:`5470`]: Added 'frag_modelview_mat' uniform to address #180
- [:repo:`5535`]: Fix FileNotFoundError when sys path doesn't exist
- [:repo:`5539`]: Window info
- [:repo:`5555`]: python3 package of Pillow needs a updated Import
- [:repo:`5556`]: Fixed loading fonts with dot in name, fixed spelling in Russisn examle
- [:repo:`5576`]: window_x11: implement get_window_info()
- [:repo:`5577`]: window_x11: fix python3 TypeError
- [:repo:`5579`]: Fix Ctypes Clipboard error with embeded null character
- [:repo:`5593`]: Fix float division by zero
- [:repo:`5612`]: raise exception when trying to add Widget with a parent to Window
- [:repo:`5621`]: do not use the clock in __dealloc__ to prevent deadlock
- [:repo:`5624`]: Update LICENSE
- [:repo:`5664`]: Fixes renderbuffer leaking when creating Fbo
- [:repo:`5693`]: PiCamera-based camera provider for Raspberry Pi
- [:repo:`5703`]: Fixed format string mistake in Error Message
- [:repo:`5705`]: Check for activation before attaching to window. references #5645
- [:repo:`5716`]: Replace vendored lib/OSC and lib/oscAPI with oscpy.
- [:repo:`5778`]: Update extensions for ImageLoaderPIL
- fc2c3824a: Update properties.pxd
- 5bf0ff056: Properties: Allow custom comparator.
- cf7b55c1b: change opengl ids to unsigned ints
- 87897c489: Add on_textedit event to SDL2 Window (#5597)
- 4d9f19d08: Expose "absolute" options in HIDInputMotionEventProvider class
- ae3665c32: camera: fix __all__ export
- 53c2b4d63: picamera: fix for python2. Closes #5698
- d3d517dd2: Re-add `gi` camera provider.
- d175cf82c: Fix Inspector crash if shaped window is disabled
- 4deb3606d: Add sdl2 system cursors (#5308)
- f5161a248: Clean hanging code (#5232)
- b7906e745: Fix py2/py3 iteritems (#5194)
- 5961169c5: add versionadded tag for KIVY_BCM_DISPMANX_LAYER
- ebeb6c486: cache.py bug fixes (#5107)
- b4ab896b0: input: probesysfs: remove getconf dependency
- 58b9685da: @triggered: add cancel method
- f8194bb69: Add test units to ClockTestCase
- dafc07c0e: @triggered: Set default timeout=0
- 061891ce1: Add decorator for Clock.create_trigger()
- 1c855eb14: on_joy_ball is called with 2 position valuesc
- 1a20a3aef: Prioritize XClip for clipboard on Linux

Widgets
-------

- [:repo:`4905`]: Removed textinput cursor bug #3237
- [:repo:`5167`]: Add support for RST replace
- [:repo:`5200`]: Added `abs_tol` argument to isclose call to ensure no float edge cases
- [:repo:`5212`]: fix [:repo:`5184`]: ScrollView bar_margin affects also touch position
- [:repo:`5218`]: Add support for footnotes to RST
- [:repo:`5243`]: Fix for crash when setting is_focusable property in issue #5242
- [:repo:`5255`]: Fix race condition in AsyncImage
- [:repo:`5260`]: Disable emacs bindings for Alt-Gr (Ctrl+Alt) key
- [:repo:`5263`]: Avoid Animation.cancel_all(Window) that interfers with user animations
- [:repo:`5268`]: Fix crash when instantiating ActionView(use_separator=True)
- [:repo:`5335`]: issue #5333 - actionbar throws exception when resized
- [:repo:`5339`]: Rewrite ActionGroup from Spinner to Button+DropDown
- [:repo:`5370`]: Fix all ScreenManagers sharing the same transition
- [:repo:`5379`]: Allow negative values in textinput with filters.
- [:repo:`5413`]: Don't pass touch to children when outside the ScrollView.
- [:repo:`5418`]: Add text_validate_unfocus option to TextInput
- [:repo:`5445`]: Resize treeview collapse. closes #5426
- [:repo:`5455`]: Add TextInput cursor blinking control
- [:repo:`5472`]: export widget canvas to png including alpha values
- [:repo:`5484`]: DragBehavior: Transform window coordinates to parent coordinates befo…
- [:repo:`5567`]: EffectWidget: Correct typo 'setdefaults' to 'setdefault'
- [:repo:`5641`]: Fix LabelBase.register() to behave as documented
- [:repo:`5715`]: Let Layout.add_widget use the ``canvas`` argument
- [:repo:`5748`]: Add canvas argument to FloatLayout.add_widget
- [:repo:`5764`]: Fix #5761 AsyncImage reload() doesn't invalidate Loader Cache
- [:repo:`5632`]: Fixes #5632, typo of col instead of row.
- 9a8603d54: hotfix: Stop AccordionItem collapse animation
- a432e0d73: Let BoxLayout.add_widget use the ``canvas`` argument
- 37ccbfac2: pass an empty list for "buttons" param to create_touch
- 8da2272e5: Remove ineffective changes
- 2faa6a993: doc: Added default value to Scatter 'do_collide_after_children' property
- faa03f7e4: Gridlayout min size bounds check (#5278)
- 27e3b90ea: Fix touch passing down when overlapping TextInputs (#5189)
- 5e2b71840: Fix image size and comment handling in RST (#5197)
- b505b1d13: Add on_load to AsyncImage (#5195)
- 873427dbb: Add Slider.sensitivity (#5145)
- d06ea4da2: Deprecate the Widget's id property


Tests
-----

- [:repo:`5226`]: Add test for ScrollView bars
- [:repo:`5282`]: Add test for _init_rows_cols_sizes
- [:repo:`5346`]: Add unittest for ActionBar
- [:repo:`5368`]: Unittesting features
- [:repo:`5372`]: test_video.py: Fix misleading class name
- [:repo:`5374`]: Fix creating 'results' folder in GraphicUnitTest if not making screenshots
- [:repo:`5378`]: Add test for Inspector module, fix children order for ModalView
- [:repo:`5381`]: Add test for KV event/property + trailing space
- [:repo:`5399`]: Add unittest for Mouse multitouch simulator
- [:repo:`5433`]: Add simple guide for GraphicUnitTest
- [:repo:`5446`]: Add unittest for AsyncImage + remote .zip sequence
- [:repo:`5489`]: Add unittest for TextInput selection overwrite
- [:repo:`5607`]: Add unittest for Vector.segment_intersection floatingpoint error
- 6b93d8aa4: Fix unicode error
- c9ecb4017: Add test for RST replace

Docs
----

- [:repo:`5170`]: Fix typo in installation/windows.rst
- [:repo:`5177`]: Fix comments for paste in textinput.py
- [:repo:`5221`]: Docs: Link methods, remove empty title
- [:repo:`5227`]: Add gstreamer to ubuntu install
- [:repo:`5240`]: Settings in example are faulty
- [:repo:`5270`]: doc: add missing escape characters into Linux installation instructions
- [:repo:`5307`]: Docs: Explain handling Popup in KV
- [:repo:`5330`]: Docs: Rewrite system cursor
- [:repo:`5424`]: Add notice about Kivy.app not being available for download
- [:repo:`5439`]: OSX Install Instruction Update - Cython explicit version
- [:repo:`5458`]: Add docs for setting Window.shape_mode
- [:repo:`5518`]: less renaming
- [:repo:`5519`]: oxford
- [:repo:`5520`]: Documentation consistency
- [:repo:`5521`]: redundant 'as'
- [:repo:`5522`]: widget's
- [:repo:`5523`]: terser
- [:repo:`5524`]: tighten
- [:repo:`5559`]: Docs: Add note about MemoryError for kivy.deps.gstreamer
- [:repo:`5600`]: Fixed one letter documentation typo (in example)
- [:repo:`5626`]: Fix typo in docs.
- [:repo:`5695`]: Docs: Add warning about using Texture before application start
- 12487a24f: Remove tree; doesn't look good with website CSS
- bb07d95e9: Clarify Windows alternate location installation
- d6d8a2405: Doc: Fix parsed literal block in installation docs
- 4d4ee413c: Doc: added 18.04 to dev install docs
- 5f6c66eba: Doc: Fixed typo in animation.py
- 285162be5: Kivy is available on Macports directly
- 94d623f91: Doc: changed disabled state docs for widget to more standard form
- e029bed41: Doc: tweak to uix/spinner.py docs
- 86b6e19d8: Doc: tweaks to cython version installation instructions
- ef745c2fe: Doc: remove specifying cython version, list working cython vs. kivy versions. references #5674
- 0ccd8ccd9: Doc: tweaks to modules/console.py
- 90448cbfa: Doc: revisions to modules/console.py
- 73f99351c: Doc: added explanation for Builder.unload filename parameter
- 67fb972ee: Doc: refinements to actionbar.py
- 96252c9ad: Doc: refinements to actionbar docs
- 917a1b4a2: Update installation-osx.rst
- a3251fd79: Doc: clarified angle offering for python 3.5+
- 0fbac3bdb: Doc: tweaks to actionbar docs
- 0ec9530b3: Doc: additions to ActionBar docs
- 1aa431539: Fix stencil's documentation
- 51d172500: Doc: corrected typo in recycleview layout docs
- 6af68c41f: Doc: Added link to toggle button image
- e7d171393: Doc: Added togglebutton image to docs
- 0ea6e95df: Doc: Added 16.04 dependencies listing
- 0cc3a9812: Update debian installation doc
- 22aa73f55: Docs: Remove "-dev" version in versionchanged
- c07f97179: Docs: Fetch cython version from setup.py (#5302)
- 2ad58a9a0: Doc: cleanup, added doc strign for RecycleLayout to make linkable
- 493a4a985: Doc: tweaks to the recycleview docs
- 114c1a026: Doc: Grammer tweaks to /doc/sources/guide/graphics.rst and kivy/core/window/__init__.py
- 3d243629f: Doc: petty grammar tweaks to kicy/core/window/__init__.py
- 7cdf9b3fd: Doc: corrected the kkivy/core/window/keyboard_anim_args docs to more accurately reflect defaults
- c5eb87974: Docs: removed the 'None' default value as it is actualy ''
- c090c6370: Doc: corrected path for AliasProperty in RecycleViewBehavior
- 24647bd9c: Doc: added heirarchical namespacing to treeview items
- 6f0639a25: Docs: Fix note indentation after code block
- 7daea785f: Doc: added description of rotation property value for kivy.uix.scatter
- ac0d28f1f: Reorder osx packaging methods
- 19d9d9d81: Doc: tweaks to grammar for RoundedRectangle graphics instruction
- cdee22eaa: Doc: tweaks to grammar for RoundedRectangle graphics instruction
- c6b2fe309: Fix nightly links.
- 242beb39a: Update android virtual machine documentation
- fa1e0b283: Deprecate the vm.
- bd392abca: Remove vm link.
- a6ee7605c: Add info about kivy_examples.
- 97f3096cc: Doc: remove leftover USE_OSX_FRAMEWORKS env var
- b4ce25698: doc: setting KIVY_OSX_FRAMEWORKS=0 during installation is not needed anymore
- e5126afce: doc: use latest Cython version for macOS and do not force reinstallation
- bd98d81bc: docs: remove warning about unavailable wheels on Windows
- f1b412d9a: Docs: Fix examples PPA command; Cython for v1.10.0
- 333f15845: Doc: Fix Mesh docstring (#5806)

Examples:
---------
- [:repo:`5026`]: Update Twisted Framework Example to Py3
- [:repo:`5173`]: Fix shapecollisions example for py2
- [:repo:`5486`]: Rotate monkey head smoothly
- [:repo:`5487`]: Update codeinput.kv
- [:repo:`5564`]: Update basic.rst
- [:repo:`5611`]: typo fix in docs example
- e658c65ce: Fix animation transition around the unit circle in Android compass example
- 4de0599a8: Update joystick example

Misc:
-----

- [:repo:`4984`]: Allow changing kivy dispmanx layer in the Raspberry Pi
- [:repo:`5285`]: fix install_twisted_reactor for python3 (_threadedselect is now inclu…
- [:repo:`5350`]: tools/kviewer: Fixed it working on python3
- [:repo:`5525`]: Switch to manual KV trace purging
- [:repo:`5763`]: Add kivy/core/window/window_info.c to .gitignore
- 98e944277: Updated copyright year in doc index
- b39c84bc0: pep8 fixes
- 8143c6be9: Add -- to separate Atlas module options
- d054d5665: Add -- to --use-path option in documentation
- 38ed32f2b: Create CODE_OF_CONDUCT.md
- fa01246c8: long overdue update to the kv syntax highlight for vim
- 0c63c698f Fix licensing issues (#5786)

Packaging:
----------

- [:repo:`5366`]: Fix 'git' not found in setup.py
- [:repo:`5392`]: Fix setup.py under python2
- [:repo:`5466`]: Introduce no support for Cython 0.27 - 0.27.2
- [:repo:`5584`]: Added Python 3.6 to setup.py categories
- [:repo:`5627`]: Add setupconfig.py to packagedata
- [:repo:`5747`]: Updated minimum cython version
- 10530bbfc: Added missing comma in package_data list
- f66f34023: setup: fix error about gl_mock that doesn't exist anymore
- d462a70f9: setup: fix cython rebuilding all graphics even if it has been already done. Closes #4849
- aaca07b20: Fix missing kivy.tools in setup.py (#5230)

CI:
---

- [:repo:`5229`]: Appveyor: switch DO_WHEELS to True
- [:repo:`5406`]: Fixes for Cython 0.27
- d5e0ccc00: comment out failing mingw appveyor builds
- 71cbd4c40: fixes for osx builders in travis
- 55200ee1a: workaround to make inspector tests pass without blocking window
- 002e46f7d: travis.yml: add semi-colon
- f1693863e: travis.yml: add sudo to easy_install
- 9f71b38a4: travis.yml: try easy_install pip to fix missing command error
- bae09d913: travis.yml: Make TRAVIS_OS_NAME detection consistent
- 94db03ed3: Prevented warnings for repeated loading for travis Inspector test cases
- 61e05c113: Fix travis build error in inpector.py, line 382
- cd592c1e8: Fixed Pep8 violations (fix travis build 3676 moans)
- a736f287a: Remove fixed version of cython from .travis.yml
- 87ae2145c: Removed outdated line from .travis.yml
- 30fd00fa8: Restore cython=-=0.26.1 for appveyor builds
- 5c4b8ed14: Downgrade Cython to 0.26.1 for builds
- 484b2f788: Upload wheels directly to server (#5175)
- e2c309416: travis.yml add back missing ";"
- 2fc9cf521: add back pip installation in osx travis build
- 7f5d9a4b4: use travis_retry for coveralls, in case it fails randomly
- e12d21667: fix again osx travis build (pip command not found)
- 3d41f1da1: Update .travis.yml
- 642e029a8: Add docutils to Travis deps
- ce6d54e2f: Add wheel generation support for osx and Linux.
- 36e029aec: Upload sdist and examples.
- 2e400aa41: Quote filenames [build wheel]
- 04bfcff4d: Give better wheel upload path [build wheel win]
- 8167ff410: Fix wheel building on all platforms (#5812)



1.10.0 (May 7, 2017)
============================

Breaking changes
----------------

- [:repo:`3891`] ButtonBehavior.always_release defaults to False, so by default a release outside the button is ignored.
- [:repo:`4132`] ButtonBehavior.MIN_STATE_TIME was removed and instead has been added to the config. Each button and dropdown now has their own configurable min_state_time property that defaults to the config value.
- [:repo:`4168`] kivy.metrics.metrics was removed, use kivy.metrics.Metrics instead.
- [:repo:`4211`] TextInput.background_disabled_active was removed, the normal background is used instead.
- [:repo:`4254`] kivy.utils.platform is now a string describing the platform and not a callable.
- [:repo:`4603`] Made App.on_pause default to return True.
- [:repo:`4819`] Remove kivy module extension support - it wasn't used.
- [:repo:`4224`] Remove pygst (audio, video, camera), gi (audio, video) and videocapture (camera) providers. Use gstplayer or ffpyplayer instead (https://kivy.org/docs/guide/environment.html#restrict-core-to-specific-implementation)
- [:repo:`5011`, :repo:`4828`] added support for opencv 2 and 3 (camera)
- [:repo:`5033`] Clock trigger call doesn’t return True (or anything) anymore, use `is_triggered` instead.
- [:repo:`5088`] Change the auto scale option in BorderImage from bool to string with multiple scaling options.

Core
----

Audio

- Add FLAC to GstPlayer extensions
- [:repo:`4372`] Added pitch shifting to audio using sdl2
- [:repo:`4853`] Add 'mp4' support to audio with gstplayer
- [:repo:`4875`] Added note that to seek, sound must be playing

Clipboard

- Detect correct Activity regardless of bootstrap (android)
- [:repo:`3990`] Store clipboard contents for gtk3 (ClipboardManager spec)
- [:repo:`4093`] Make clipboard_android work for both old and new toolchain
- [:repo:`4371`] Fix version warning for clipboard_gtk3
- Fix Python 3.5-x64 Windows clipboard, see asweigart/pyperclip#25
- [:repo:`5152`] Fixed crash on python3, due to items not being subscriptable

Image

- Add JPE to supported sdl2 image extensions
- [:repo:`3971`] Fix stopping an image animation with value of -1 for anim_delay
- [:repo:`4186`] Accept data URIs for image filename
- [:repo:`4708`] Get actual image format instead of extension (imghdr)
- [:repo:`4728`] Use PILImage.frombytes when PILImage.fromstring gives an exception
- [:repo:`4753`, :repo:`4727`] Image saving using 'save()' throws error
- [:repo:`5155`] Fix unicode image source in Python 2

Text

- [:repo:`3888`] Fix PIL deprecated tostring() scrambling the text
- [:repo:`3896`] Add font rendering options - hinting, kerning, blending (sdl2)
- [:repo:`3914`] Add underline and strikethrough styling for Label and MarkupLabel
- [:repo:`4265`, :repo:`3816`] Implement text outline for sdl2
- [:repo:`4012`] Fix label color handling
- [:repo:`4047`, :repo:`4043`] Fix alpha rendering of text color for pygame
- [:repo:`4063`] Performance improved for comparing an entire string for Label
halign and valign
- Add 'center' as an alias of 'middle' for Label.valign
- Register all /usr/share/fonts subfolders
- [:repo:`4625`] Add ellipsis styling for markup label
- [:repo:`4813`, :repo:`2412`] Change default font to core.text.DEFAULT_FONT
- [:repo:`4846`] Allow skipping italic, bold and bolditalic for the default_font
config option
- [:repo:`4858`, :repo:`4589`, :repo:`3753`] Add is_shortened to Label

Video

- [:repo:`4345`] ffpyplayer provider was updated to work with the latest FFPyPlayer codebase.
- [:repo:`5052`] Fix ffpyplayer img.to_memoryview returning None

Window

- [:repo:`3890`] turn Window.focus into a read-only property
- set Window.focus to false when the window is started in a hidden state
- [:repo:`3919`] SDL2/Android: fixes pause/resume crash using sdl2 bootstrap on
android
- sdl2/android: redo fix on_pause/on_resume for SDL2 bootstrap. No more
freeze on resume.
- [:repo:`3947`] release gil when polling for sdl events
- [:repo:`4104`] window_sdl2: fix title and icon_filename to accept bytes or str
- [:repo:`4207`] add map_key/unmap_key, automatically map android back key
- [:repo:`4209`] Add SDL2 window events
- [:repo:`4217`] Fix Window resizing for X11
- [:repo:`4239`] X11: honor borderless configuration
- [:repo:`4310`] X11: implement on_title
- [:repo:`4316`] Animate the window content based on `softinput_mode`, introducing
keyboard_padding and keyboard_anim_args
- [:repo:`4403`, :repo:`4377`] Take care to account for `density` for mouse_pos
- [:repo:`4468`] Prevent buffer crash on RPi if window was closed
- [:repo:`4631`, :repo:`4423`] Fixes keycode typo
- [:repo:`4665`] Add softinput_mode handling for SDL2
- [:repo:`4707`] Add grab mouse in sdl2 window
- [:repo:`4851`] Add Window position manipulation
- [:repo:`4919`] Disable SDL2's accelerometer-as-joystick behaviour
- [:repo:`4921`] Add an allow_screensaver property for Window
- [:repo:`4952`] Add multiple joysticks support
- [:repo:`5019`] Add note for elevated use of on_dropfile
- [:repo:`5048`] Fix missing sys.stdout.encoding when piped or frozen

Data
----

Keyboards

- [:repo:`4334`] Add German keyboard layout

Style.kv

- Fix disabled_color for markup
- [:repo:`3925`, :repo:`3922`] Fix FileListEntry text alignment
- [:repo:`3864`] Avoid end-dev setting ColorWheel internal values
- [:repo:`4176`] Change TextInput images for selection handles
- [:repo:`4364`] Fix missing sp() in style.kv
- [:repo:`4447`, :repo:`4416`] Fix filechooser size text align
- Filechooser: Align size labels with the table header
- [:repo:`4558`] Separate image and button in Switch
- [:repo:`4732`] Hide Image if no app_icon in ActionPrevious

Base
----

- [:repo:`3955`] Deprecate the interactive launcher
- [:repo:`4427`, :repo:`4361`] Fix multiprocessing.freeze_support()
- [:repo:`4449`] Store kivy_home_dir as a unicode string in python 2
- Make gif loader last (Gif loader is slow and should be used if PIL or FFPY providers don't work)
- Gst should be imported first since it cannot use sdl2's zlib but sdl2 can use gst's zlib
- [:repo:`4737`] Remove sdl2 presplash after initialised (needs android package)
- [:repo:`4874`] Add Include folder to get_includes()
- [:repo:`4949`] Normalize version

Animation

- [:repo:`4223`, :repo:`4222`] Implement cancel_property on animation's Sequence
- [:repo:`4494`] Update ClutterAlpha URL in AnimationTransition
- [:repo:`4563`] Draw animation every frame by default, use step=0 instead of 1 / 60.0
- [:repo:`4643`] Animation object is passed with the event docs <<< REMOVE?
- [:repo:`4696`, :repo:`4695`] Remove sequential animations from Animation._instances when
complete

App

- [:repo:`4075`] Fix missing path separator
- [:repo:`4636`, :repo:`4634`] App.stop() clear window children only if window exists

Compat

- [:repo:`4617`] Add isclose to compat based on py3.5 function

Clock

- [:repo:`3603`] Add clock to compat
- Include clock changes for freebsd
- [:repo:`4531`] Bump max_iteration to 20

Config

- [:repo:`4813`] Add variable for default_font
- [:repo:`4921`] Add variable for allow_screensaver

EventDispatcher

- [:repo:`3736`, :repo:`3118`] Make widget kwargs passing higher priority than kv

Factory

- [:repo:`3975`] Remove duplicate definition of SelectableView
- [:repo:`4046`] Register missing properties in factory
- [:repo:`4108`] Update factory registers (RecycleView, RecycleBoxLayout)

Graphics

- [:repo:`3866`] Allow Line.points definition to be a mix of lists/tuples
- [:repo:`3970`] Fix upload uniform without calling useprogram
- [:repo:`4208`] Fix error in Line.rectangle documentation
- [:repo:`4554`] Allow requesting graphics instruction update
- [:repo:`4556`] Segmenats is 180 everywhere and in the docs
- what is that? -> a37c8dd, 6dd8c5e
- [:repo:`4700`, :repo:`4683`] Reactivate free calls in smoothline
- [:repo:`4837`] Restore gl/gles selection at compile-time
- [:repo:`4873`] path changes for config.pxi
- [:repo:`4913`, :repo:`4912`] Fix missing 'return' in get method for Mesh `mode` property
- [:repo:`5030`] Fix BorderImage border ordering description
- [:repo:`5091`] Fix get_pixel_color for py3

Lang

- [:repo:`3909`] Add apply_rules to BuilderBase
- [:repo:`3984`] Refactored lang.py - moved into its own module
- Fix missing global_idmap in new kivy.lang refactor
- [:repo:`4013`] New ColorProperty and rgba function
- [:repo:`4015`] More robust kv string detection
- [:repo:`4073`, :repo:`4072`] Split imports on all whitespace
- [:repo:`4187`] Fix Parser.execute_directive() not using resource_find() for including directive
- [:repo:`4301`] Fix parser not continuing after warning
- [:repo:`4358`] Allow spaces before colons for classes, properties
- [:repo:`4583`] Use consistent 'Lang' for logs instead of 'Warning'
- [:repo:`4615`] Fix profiling tool HTML output generation
- Catch TypeError in dump_builder_stats
- [:repo:`5054`] Fix inconistent naming if kv files are not unloaded
- [:repo:`5068`] Unload matching rules
- [:repo:`5153`] Fix KV include for quoted paths

Lib

- [:repo:`4122`] Add 'with oscLock' in sendBundle to always release lock
- Correctly use oscLock in sendMsg
- [:repo:`3695`] Extend OSC library
- Fix py2 print in OSC
- [:repo:`4433`] OSC - convert to bytes for python3
- Ctypes supported on Android

Loader

- [:repo:`4359`] Fix Exception on remote image
- [:repo:`4545`, :repo:`4366`] Fix Asyncimage on error

Logger

- [:repo:`4057`, :repo:`4039`] Properly format log text
- [:repo:`4375`] Fix handling of PermissionError for logger.purge_logs
- [:repo:`4400`] Recognize {rxvt,rxvt-unicode}-256color as color capable
- [:repo:`4404`] Use a shorter field width for non-colored output
- [:repo:`4538`] Fix "no isatty() method" errors
- [:repo:`5067`] Replace hardcoded value `maxfiles` with config setting


Multistroke

- [:repo:`4803`] Fix a silly multistroke crash

Network

- [:repo:`2772`] Handle proxy servers in UrlRequest
- [:repo:`4297`] Fix py3 returning wrong results
- [:repo:`4448`] Fix url in UrlRequest

Parser

- [:repo:`4011`] List supported input formats for parse_color
- [:repo:`4021`] Append alpha for 3 digit hex colors

Properties

- [:repo:`4013`] New ColorProperty and rgba function
- [:repo:`4304`] AliasProperty should update when underlying prop changes even if cache is True
- [:repo:`4314`] Don't cache until first dispatch, otherwise it's never dispatched if read before the dispatch
- [:repo:`4623`] Fix grammar in exceptions
- [:repo:`4627`] Allow conversion from strings without trailing units
- [:repo:`5135`] Add py3 object.__init__() reference to properties

Resources

- [:repo:`4490`] Return `abspath` in `resource_find`.

Input
-----

- [:repo:`3915`, :repo:`2701`] Don't offset WM_TOUCH with caption size when fullscreen
- [:repo:`4045`, :repo:`4040`] Late import window for wm_touch
- [:repo:`4318`, :repo:`4309`] Fix touch scaling for WM_TOUCH
- [:repo:`4468`] Fix HIDinput to dispatch events from main thread and don't eat escape
- [:repo:`4501`] Add on_stop to recorder
- [:repo:`4621`] Fix mtdev provider max_touch_minor option
- Fix MTDev crashing if 'x' and 'y' are not in args
- Fix MTDev crashing if touch not in last_touches
- [:repo:`4725`, :repo:`4413`, :repo:`4682`] Catch permission errors in MTDev
- [:repo:`4923`] Prevent an attempt to import AndroidJoystick with SDL2

Modules
-------

- [:repo:`5143`] Fix listing modules via `-m list`

Monitor

- [:repo:`4567`] Fix monitor drawing issues after window resize
- Code cleanup

Screen

- [:repo:`4396`] Add a lot of new devices

Touchring, Cursor

- [:repo:`4721`, :repo:`3097`] Touchring and Cursor are now two modules

WebDebugger

- Use events size function instead of list comprehension

Joycursor

- [:repo:`5094`] Add JoyCursor module

Storage
-------

- [:repo:`4269`] Fix clear() not syncing the storage file
- [:repo:`4722`] Add JSON dump indention and sort_keys option to JSONStorage

Widgets
-------

- Deprecate ListView
- [:repo:`4944`] Deprecate modules pertaining to ListView (AbstractView, Adapters)
- [:repo:`4108`] Integrate Recycleview into Kivy
- Add warnings about RecycleView being experimental
- [:repo:`4617`] Adds size_hint_min/max to widgets

ActionBar

- [:repo:`3128`] Introduce ActionGroup.dropdown_width property
- [:repo:`4347`, :repo:`4119`] Fix ActionView layout more dense/packed after increase of width
- [:repo:`4441`] Fix dismiss in ActionGroup
- [:repo:`4891`, :repo:`4867`] Fix Actionview window maximize/minimize bug
- [:repo:`5049`] Fix ActionDropDown.on_touch_down

AnchorLayout

- [:repo:`4628`] Fix asymmetric padding list

Behaviors

- [:repo:`3900`] Add CoverBehavior
- [:repo:`4258`] Allow keeping direct ref in knspace, fix crash when child knspace attr is None but parent doesn't have attr
- [:repo:`4509`] Fix CompoundSelectionBehavior example
- [:repo:`4598`, :repo:`4593`] Fix ToggleButton released with allow_no_selection=False in CompoundSelection
- [:repo:`4599`] Add text_entry_timeout to CompoundSelection
- [:repo:`4600`] Allow all chars that are not e.g. arrow, and fix holding down key in CompoundSelection
- Don't return true when already selected in CompoundSelection
- [:repo:`4782`, :repo:`4484`] Allow unselect an item when multiselect is False in CompoundSelection
- [:repo:`4850`, :repo:`4817`] Add CompoundSelectionBehavior.touch_deselect_last property
- [:repo:`4897`, :repo:`4816`] Make _get_focus_* methods public in FocusBehavior
- [:repo:`4981`, :repo:`4979`] Fix typo in CompoundSelection

Carousel

- [:repo:`4081`, :repo:`2087`] Fix repeating addition of widget
- Use is operator for identity comparison
- [:repo:`4522`] Fix carousel scrollview children touch_move

CheckBox

- [:repo:`4266`] Add checkbox color

CodeInput

- [:repo:`3806`] Add EmacsBehavior to CodeInput
- [:repo:`3894`] Rename active_key_bindings to key_bindings
- [:repo:`3898`] Remove CodeInput.key_binding

Dropdown

- [:repo:`4112`, :repo:`4092`] Convert absolute coordinates of the touch.pos to relative
coordinates of self.attach_to(dropdown's button)
- [:repo:`4511`] Fix dropdown and spinner dismissing issue
- [:repo:`4550`, :repo:`4353`] Rework of #4353 DropDown.max_height
- [:repo:`4805`, :repo:`4730`] Fix first click in ActionGroup

FileChooser

- [:repo:`3710`] Fix directory selection double-selecting
- [:repo:`4200`] Handle children's size_hints equal to zero
- [:repo:`5010`] Fix a crash when using a file as the path

GestureSurface

- [:repo:`3945`] Remove line_width
- [:repo:`4779`] Fix collision check for on_touch_move
- [:repo:`4034`] Don't limit size to cols/rows_minimum, but treat it as real min.
- [:repo:`4035`] Respect size_hint in gridlayout

Image

- [:repo:`4510`] Fix py2 ASCII error
- [:repo:`4534`] Removed long tracebacks
- [:repo:`4545`, :repo:`4549`] Asyncimage on error

Label

- [:repo:`3946`] Fix label rendering options
- [:repo:`3963`, :repo:`3959`] Show disabled_color when disabled=True for markup label

ListView

- Include ListItemReprMixin
- Add note about possible deprecation of ListView
- [:repo:`2729`] Don't require a text argument for CompositeListItems

ModalView

- [:repo:`4136`] Fix model center not syncing with window center
- [:repo:`4149`, :repo:`4148`] Fix modal background not resizing
- [:repo:`4156`] Fix incorrect ModalView position after window resize
- [:repo:`4261`] Don't return ModalView instance in open and dismiss methods

PageLayout

- [:repo:`4042`] Fixed bug if zero or one widgets are in pagelayout
- Code style improvement

ScreenManager

- [:repo:`4107`] Fix Screen removal leaving screen.parent property != None
- [:repo:`3924`] Don't generate a new screen name for existing screens
- [:repo:`4111`, :repo:`4107`, :repo:`2655`] Remove the last screen and leave ScreenManager in a valid state
- Don't check the Screen parent type, it can only be a ScreenManager
- [:repo:`4464`] Fix SwapTransition not scaling
- Add missing import of Scale
- [:repo:`5032`] Add CardTransition to ScreenManager

ScrollView

- [:repo:`3926`, :repo:`3783`] Fix scroll distance bug
- [:repo:`4014`] Revert accidental non-pep8 scrollview changes
- [:repo:`4032`] Fix ScrollView not properly ignoring touch_up
- [:repo:`4067`] All touches that don't scroll should be skipped in touch move
- [:repo:`4180`] Scroll to touch pos if the touch is within the scrollbar but does not collide with the handle
- [:repo:`4235`] Make sure import does not load a window
- [:repo:`4455`, :repo:`4399`] Focused widget inside ScrollView should unfocus on tap
- [:repo:`4508`, :repo:`4477`] Always pop the touch
- [:repo:`4565`, :repo:`4564`] Fix scrollview click registering on PC
- [:repo:`4633`] Postpone scroll_to if the viewport has pending layout operation
- [:repo:`4646`] Fix on_scroll_move to obey scroll_distance
- [:repo:`4653`] Add checks to start scroll if do_scroll enabled for axis
- Add size_hint_min/max support to ScrollView
- Use viewport's size_hint
- Fix ScrollView ignoring scroll_y, scroll_x being set from outside

Settings

- Fix string_types double import
- [:repo:`3625`] Add show_hidden and dirselect to SettingPath

Slider

- [:repo:`4028`] Fix Slider.value exceeding Slider.max
- [:repo:`4127`, :repo:`4124`, :repo:`4125`] Change use of dimension conversion in Slider
- Add styling properties for Slider widget
- Added value_track* properties

Spinner

- Ensure Spinner text is updated when text_autoupdate changes
- Autoupdate spinner text only if the current text is not between the new values
- [:repo:`4022`] Add option to sync Spinner dropdown children heights
- Update Spinner.text if empty, without comparing values
- [:repo:`4511`] Don't re add all widgets upon resize, it just lead to infinite size calc.
- Fix type and don't used children directly since it could be modified
- [:repo:`4547`] Fixes opening for empty values

StackLayout

- [:repo:`4236`] Fix stacklayout not sizing if children is empty
- [:repo:`4579`, :repo:`4504`] Fix stackLayout children rearranging themselves unexpectedly when their parent's size changes

TabbedPanel

- [:repo:`4559`] Fix scrolling in TabbedPanel
- [:repo:`4601`] Remove tab limit

TextInput

- [:repo:`3935`] Altered get_cursor_from_xy to intuitively place cursor
- [:repo:`3962`] Add TextInput.password_mask to customize the password placeholder
- [:repo:`4009`] hint_text in TextInput shows when focused and no text entered
- [:repo:`4024`] Always show the textinput cursor at the moment of touch
- [:repo:`4048`] Use a trigger when resetting the textinput cursor state
- [:repo:`4055`] Implement wrapping of continuous text in textinput
- [:repo:`4088`, :repo:`4069`] Fix disabled backspace
- Fix infinite loop when width is negative
- Don't reset focus when focus changes
- [:repo:`4204`] hint_text decode text by default
- [:repo:`4227`, :repo:`4169`] Push flags correctly for linebreak in _split_smart
- [:repo:`4367`, :repo:`4244`] Don't try to split lines shorter than 1px
- [:repo:`4445`] Prevent an infinite loop when trying to fit an overlong word
- [:repo:`4453`] Fix text going off-screen while wrapping
- [:repo:`4560`, :repo:`3765`] Fix app crashing on do_cursor_movement('cursor_end') on empty text
- [:repo:`4632`, :repo:`4331`] Clear selection_text directly
- [:repo:`4712`] Fixed space input under SDL2 for some Android keyboards
- [:repo:`4745`] Add cursor_width to TextInput
- [:repo:`4762`, :repo:`4736`] Prevent setting suggestion_text crashes if text is empty string and canvas is not setup yet
- [:repo:`4784`] Made sure Selector gets on_touch_down only once
- [:repo:`4836`] Fix Bubble not reachable on Android when touch in textinput is near the borders
- [:repo:`4844`, :repo:`3961`] Fix not working BubbleButton on_touch_up
- [:repo:`5100`] Fix TextInput crash when text, focus is set and enter pressed at same time

TreeView

- [:repo:`4561`] Add TreeView.deselect_node()

Video

- [:repo:`4961`] Fix on_duration_change typo

Videoplayer

- [:repo:`4920`] Replace old video with CC0 licensed video

VKeyboard

- [:repo:`4900`] Add font_size for key text size
- [:repo:`5020`] Fix file/kblayout opening

Widget

- [:repo:`4121`, :repo:`3589`] Check if canvas was found in parent canvas for export_to_png
- [:repo:`3529`] Rebind Widget.parent by default
- [:repo:`4584`, :repo:`4497`] Avoid being behind parent's canvas when inserting a widget at last index

Tools
-----

Highlighting

- Update Emacs mode to modern way of enabling newline and indent

Packaging

- [:repo:`4840`, :repo:`4811`] Fixed get_deps_minimal crash in Python3

PEP8checker

- Add shebang again
- [:repo:`4798`] Update pep8.py to version 2.2.0
- Add E402 to pep8 ignore list
- Normalize paths excluded from style checks
- Match start of folder paths during pep8 check
- Ignore E741 and E731
- Exclude dir kivy/tools/pep8checker
- Delete sample_for_pep8.py
- Remove stylereport target from Makefile
- Print error count during style check instead of passing it as exit code
- Ignore style issues in kivy/deps

Report

- Fix StringIO for py2, raw_input/input, crash if GL not available. Add more detailed platform checking. Warn the user the gist is pasted anonymously.
- Made ConfigParser py2/3 compatible

Doc
---

- [:repo:`4271`, :repo:`2596`] Fix docs build on Windows
- [:repo:`4237`] Add screenshots for widgets
- Tons of doc fixes thanks to the awesome community
- Special Thanks to ZenCODE for his awesome work on improving the doc

Examples
--------

- [:repo:`3806`] Add EmacsBehavior example
- [:repo:`3866`] Fix examples/canvas/lines.py example
- [:repo:`4268`] Fix takepicture requirements, use android.mActivity instead of autoclass
- Add RecycleView example
- [:repo:`4573`] Add clipboard example
- [:repo:`4513`] Add an examples for Window.on_dropfile
- [:repo:`4807`] Add example for various color input
- [:repo:`4862`] Add joystick example
- [:repo:`4883`] Fix attribution in examples/widgets/lists
- [:repo:`4925`] Replace images with CC0
- Fix KVrun example
- Fix Settings example
- Fix tabbed showcase example
- [:repo:`5022`] Revert SmoothLine in example
- [:repo:`5027`] Fix unicode error in KeyboardListener example
- [:repo:`5035`] Added KV example for CoverBehavior
- Fix camera example - save image with extension
- [:repo:`5079`] Add shape collision example
- Fix examples gallery
- Fix SVG example - scale with only one value
- [:repo:`5075`, :repo:`4987`] Split examples into separate wheel for windows

Unit Tests
----------

- Adapt ListView selection test to new behavior
- Add test for TextInput focused while being disabled
- [:repo:`4223`, :repo:`4222`] Add a test for issue #4222
- [:repo:`4227`] Add test case for word break
- [:repo:`4321`, :repo:`4314`] Internal alias property details should not be assumed and tested
- [:repo:`4624`] Fix test_wordbreak fail on Retina Mac
- Add simple tests for JsonStore options
- [:repo:`4821`] Fix test_fonts file deleting
- Use almost equal for float assert
- Clipboard should only accept unicode
- [:repo:`5115`] Replace Pygame with SDL2 for image comparing test
- [:repo:`5111`] Add test for Fbo.get_pixel_color

Packaging
---------

- Tons of more fixes that weren’t mentioned here, details of which can be gathered from http://github.com/kivy/kivy


Migration
---------

- [:repo:`3594`] Remove KEX (extension) support
- [:repo:`3891`, :repo:`3312`] ButtonBehavior.always_release default to False
- [:repo:`4132`] Include a min delay before dismissing
- [:repo:`4168`] Remove deprecated kivy.metrics.metrics
- [:repo:`4211`] Remove TextInput.background_disabled_active
- [:repo:`4224`] Remove deprecated video and audio providers: pygst, pyglet and pygi
- [:repo:`4254`] kivy.utils.platform is a string and it's not callable anymore
- [:repo:`4603`, :repo:`4796`] Made on_pause default to True


1.9.1 (Jan 1, 2016)
============================
`Changelog published here <https://groups.google.com/forum/#!topic/kivy-users/7LTIHnRCuG4>`_.

1.9.0 (Apr 3, 2015)
============================

Core
----

- [:repo:`2280`] When core critically fails to load a lib, print all the exceptions.
- [:repo:`2488`] Sdl2 support
- [:repo:`2800`] core:core_register_lib: make sure libs are registered in order mentioned...


Audio

- [:repo:`1926`] handle URL's with parameters
- [:repo:`2131`] fix bug with sound state in audio_gstplayer.py
- [:repo:`2278`] fix socket leak in gstplayer
- [:repo:`2125`] gstplayer: fix audio/video volume handling, as setting only once in load() doesnt work after stop().
- [:repo:`3004`] audio: Fixed the get_pos method
- core/audio: accept m4a as input format.
- core/audio: add pygame m4a for android
- audio: fix leak in SDL implementation (iOS)


Camera

- a couple of fixes for camera/avfoundation


Clipboard

- [:repo:`2258`] Clipboard: move `copy` and `paste` methods from `TextInput` to `core.clipboard` implementation.
- [:repo:`2743`] os specific clipboard
- core:clipboard_pygame is able to paste unicode text
- fix clipboard_pygame.py to encode only for py2


Image

- [:repo:`1963`] texture: add icolorfmt parameters to define alternative color format storage.
- [:repo:`2085`] add .jpe to the supported extensions for providers that supports jpeg
- [:repo:`2358`] Add ffpyplayer provider for image
- [:repo:`2037`] PIL: detect and use frame disposal method
- [:repo:`2556`] core:img_io add py3 support, img_sdl2 add save support
- [:repo:`2232`] convert image data to a bytearray to more consistently get color info
- [:repo:`2170`] Fix image unicode issues
- [:repo:`2645`] img_pil:check for attribute's existance before accessing it. closes #2641
- [:repo:`2695`] add optional flipped param to pil image save
- [:repo:`2718`] uix:Image introduce `anim_loop` property
- [:repo:`2826`] allow In-memory image loading
- [:repo:`2834`] fixes zip files not loaded by ImageLoaderPygame
- [:repo:`2836`] core:Image:zip_loader start using the new functions for loading from memory
- [:repo:`2403`] Update Imageio.pyx with fox for cython.21
- [:repo:`2282`] core/imageio: dont advertise to support gif cause we are not able to animate it
- core/image: remove rowlength slot
- imageio: accelerate bgra->rgba conversion using Accelerate framework


Text

- [:repo:`1998`] use a more natural method to check if self._text is unicode.
- [:repo:`2050`] Workaround for pygame font issue with unicode filesnames.
- [:repo:`2166`] Use correct options to finish of markup layout
- [:repo:`2259`] Fixed issue where anchors not reporting correct position
- [:repo:`2248`] [core/text] When stip is False allow space to remain on last line if it fits.
- [:repo:`2225`] Use int for texture size, otherwise it'd never equal to the actual texture size.
- [:repo:`2677`] fix stripping for wrapped text
- [:repo:`2696`] add unicode error handling to core text
- [:repo:`2673`] use available system fonts
- [:repo:`2840`] Fix text stripping issues
- [:repo:`2891`] Change the default font from DroidSans to Roboto
- [:repo:`2897`] Update readme, font files and kv as part of moving to Roboto
- [:repo:`3014`] core/text: allow others font extension to be loaded
- core.text: Make sure colorformat is specified while blitting texture.
- Align text flush with justify.


Video

- [:repo:`1629`] Add ffpyplayer provider.
- [:repo:`2125`] gstplayer: fix audio/video volume handling, as setting only once in load() doesnt work after stop().
- [:repo:`2275`] video: fix video.unload called when position is changing.
- [:repo:`2962`] Video fixes


Window

- [:repo:`1904`] Exit on escape changes
- [:repo:`2130`] Add on_request_close event to window to check before the window is closed
- [:repo:`2148`] Add read-only tag to WindowBase width and height properties
- [:repo:`2329`] Import glReadPixels from the correct place. Fixes #2032
- [:repo:`2359`] add __self__ property to Window
- [:repo:`2384`] Wrong 'F3' key value.
- [:repo:`2386`] respect keyboard height when providing window height in softinput resize mode
- [:repo:`2564`] joystick support with sdl2
- [:repo:`2662`] Window.screenshot python 3 fix
- [:repo:`2688`] Add `pause_on_minimize` config option
- [:repo:`2689`] core: window_pygame fix conflict with command_mode and ctrl+a
- [:repo:`3047`] Joystick support on WindowPygame
- [:repo:`3092`] Don't add force to kwargs since it's not a prop.
- [:repo:`3115`] X11: fix CWOverrideRedirect handling
- [:repo:`3147`] `on_textinput` event for handling text input events from IME, and other custom input methods
- [:repo:`2590`] Add maximize, minimize, restore, hide and show methods for SDL2 Window
- [:repo:`3200`] Add window_state Config option


Base
----

- [:repo:`2528`] allow customizing the location of the Kivy config data
- [:repo:`2873`] environment: add an option to prevent parsing command line argument as kivy arguments.


App

- [:repo:`2171`] Add root_window property to App class


Animation

- [:repo:`1959`] animation: copy the original value to correctly animate list/tuple/dict.
- [:repo:`2739`] unbind on_anim1_complete in Sequence
- [:repo:`3100`] fix animation with new WeakProxy objects
- [:repo:`2458`] animation: fix crash when widget is gone. (also #2561, #2676)


Atlas

- [:repo:`1841`] atlas: Avoids the "Too many open files" error in case of a large number of input fil
- [:repo:`3042`] Atlas fixes (#2822 and accept glob patterns)


Config

- [:repo:`1937`] Add ConfigParserProperty
- [:repo:`1937`] Add remove_callback method to ConfigParser
- [:repo:`2122`] Config.set can now convert ints to string in Python3
- [:repo:`2030`] Add warning about Settings.on_config_change() value type
- [:repo:`2127`] Placement of import config critical to opening window size.
- [:repo:`2228`] Add largs in config register func.
- [:repo:`2288`] add upgrade method to ConfigParser
- [:repo:`2122`] config: ensure python3 configparser will always set strings.
- [:repo:`2351`] Get the configparse object when obj is created if it exists already.
- [:repo:`2932`] Get the configparse object during linking if it exists already.
- Add ConfigParserProperty and remove_callback method to ConfigParser.


Clock

- [:repo:`2072`] Only execute events that have not been removed.
- [:repo:`2310`] Make Clock thread safe.
- [:repo:`2315`] Use class object for hash instead of the class method
- [:repo:`2330`] Use wrap to give correct name to mainthread wrapped func. Fixes #2027.


EventDispatcher

- [:repo:`2069`] Add kwargs to dispatch.
- [:repo:`2566`] Enable cyclic garbage collection to EventObservers.
- [:repo:`2724`] assert that event callbacks are actually callable
- [:repo:`2797`] Restore internal EventObservers to use python objects instead of structs.
- [:repo:`2899`] Forward args when creating property.
- event: try to fix events compilation with older cython
- Make explicit dependance of event and properties pxd files.
- Propogate exceptions from EventObservers methods.
- _event only depends on prop.pxd and prop.pyx.
- Fix use after free when unbinding a currently dispatching function. Also, don;t dispatch callbacks added during a dispatch


Factory

- [:repo:`2052`] Warn when factory tries to re-register an existing class with different bases


Gesture

- [:repo:`2058`] Add bbox_margin as a property of GestureSurface


Graphics

- [:repo:`1899`] Adding enforcement of the wanted graphics system (GL/GLES)
- [:repo:`1876`] Fixed UnicodeDecodeError for bad closed-source Intel drivers
- [:repo:`1946`] add a RoundedRectangle instruction
- [:repo:`1876`] fix shader for intel drivers
- [:repo:`1996`] created method flip_horizontal() for kivy.graphics.texture.Texture
- [:repo:`2186`] Use memoryviews for blit_buffer
- [:repo:`2352`] Fix cython shader 'python temp coercion' exception.
- [:repo:`2421`] Fix line joints when doing a PI angle
- [:repo:`2430`] Add gles_limits env variable.
- [:repo:`1600`] texture: enforce the Texture.blit_* colorfmt/bufferfmt to be the same as the texture, if we have GLES_LIMITS activated
- [:repo:`2440`] Tesselator
- [:repo:`2414`] Add SmoothLine reload_observer. Fixes #2377
- [:repo:`2266`] add debug method for recursive updates
- [:repo:`2554`] fix line circle angles
- [:repo:`2170`] Fix image unicode issues
- [:repo:`2428`] Fix bgr conversion memory leak
- [:repo:`2630`] fix size issue for 3D models loaded in kivy
- [:repo:`2809`] Default gles_limits to whether we're on desktop.
- [:repo:`2784`] Added property name setters in Color __init__
- [:repo:`3030`] Matrix: add get method to retrieve the current matrix
- [:repo:`3040`] Matrix: add a put method to directly set matrix value
- [:repo:`1600`] texture: enforce the Texture.blit_* colorfmt/bufferfmt to be the same as the texture, if we have GLES_LIMITS activated
- graphics: fixes for cython 0.20.2 (old version) and remove gcc warning.
- [:repo:`2445`] shader: correctly ask for the length of the info. Maybe this is why the odoo crash.
- sdl2/texture: fix compilation for older cython with python3
- texture: fix invalid color conversion for texture when introduced icolorfmt (need double check with SMAA).
- [:repo:`2857`] graphics/context: release shaders the same way we do for others graphics
- shader: fix for python3


Interactive Launcher

- [:repo:`1847`] interactive.py illegally lists instance methods in __slots__


Lang

- [:repo:`1920`] Allows comments in kv after a root level decleration
- [:repo:`2094`] Fixes to not include comments when binding kv properties.
- [:repo:`2083`] create Observable class to allow creating bindable objects for kv
- [:repo:`2235`] include inner traceback in BuilderException
- [:repo:`2269`] Create BooleanProperty if a bool is given for the kv property.
- [:repo:`2174`] Introduces rebind keyword for some properties to enable dynamic rebinding
- [:repo:`2317`] Ignore key exceptions when binding kv rules.
- [:repo:`2533`] kv binding optimization
- [:repo:`2639`] fix unicode and Builder in Python 2
- [:repo:`2908`] kvlang: Fix binding issues
- [:repo:`2864`] lang: fix_double include. closes #2821
- [:repo:`3012`] py3: Python 3 doesn't have ClassType anymore.
- [:repo:`3068`] Improved error when canvas instructions are added after child widgets in kv
- lang: fixes invalid name (mixed typo between cache_match and match_case)


Loader

- [:repo:`1918`] loaders: guess extension from mime type
- [:repo:`1928`] Loader: allow override via URL fragment
- possibility to load image from a buffer, and make the loader GIL-free


Logger

- [:repo:`1660`] Logger logs the version of python in use.
- [:repo:`1948`] Fix displaying logs on debug level by default
- [:repo:`2169`] Make log_dir absolute path checking cross-platform
- [:repo:`2167`] Add config callback to change the log file when the config log_dir/log_name change.


Network

- [:repo:`1975`] Decode byte string result when using Python 3


Properties

- [:repo:`2141`] Made NumericProperty work with unicode strings.   References Issue #2078
- [:repo:`2321`] add default read-only setter to AliasProperty
- [:repo:`2747`] Add force_dispatch option to properties
- [:repo:`2812`] prevent dispatch in ReferenceListProperty.setitem if values haven't changed
- [:repo:`3088`] use WeakMethod for property bindings
- [:repo:`3106`] raise AttributeError on missing property


Storage

- [:repo:`1938`] Added persistence to DictStore using pickle
- [:repo:`2815`] fix bad params for async storage


Input
-----

HIDInput

- [:repo:`2638`] hidinput: add late import and fix closure error
- [:repo:`3072`] Fixed two bugs with incompatibilities with python3 in hidinput.py.
- [:repo:`3109`] keyboard management: add missing keys
- [:repo:`3124`] keyboard: add alt as modifier


Keyboard

- [:repo:`1917`] introduce `keyboard_height` and `softinput_mode` property that can be set to `''` or `pan` or
- [:repo:`1930`] VKeyboard: add key repeat on long press
- [:repo:`1932`] VKeyboard: add extended layouts
- [:repo:`1967`] Fix setting exit_on_escape atribute on on_keyboard method


MTDev

- mtdev: fix a crash when a finger is already on the touchscreen at the application start
- mtdev: fix a race condition where we received 2 tracking code id for the same slot within the same SYN_REPORT


MotionEvent

- [:repo:`2292`] handle weakproxy objects in MotionEvent.grab()


Mouse

- [:repo:`2132`] Adds simulated touch as a profile option
- [:repo:`2333`] Make multitouch sim enabled by default and add multitouch_on_demand to config to disable it


PostProc



Modules
-------

Inspector

- [:repo:`1897`] Make property list draggable by scrollbar too [modules-inspector]
- [:repo:`1949`] Make state normal on 'inspect' toggle button when inspector is deactivated
- [:repo:`2387`] Inspector: handle bad properties/values
- [:repo:`2521`] Fix inspector scrollview
- [:repo:`2618`] let inspector view the Window object
- [:repo:`2720`] fix inspector for touch devices


Recorder

- [:repo:`2344`] fix recorder module imports


Behaviors
---------

ButtonBehavior

- [:repo:`2531`] ButtonBehavior: enforce minimum down state time


CompoundSelectBehavior

- [:repo:`1957`] Adds a CompoundSelection behavior class
- [:repo:`2154`]  Fixes #2140  Syntax error
- [:repo:`3122`] Fixes #3120 Keyboard behavior in select_for_key_down elides over pauses, combining keys


FocusBehavior

- [:repo:`1909`] initial focus behavior
- [:repo:`2708`] uix:FocusBehavior make sure changing focus for previous and next don't clash


ToggleButtonBehavior

- [:repo:`2557`] uix:ToggleButton Behavior: make it consistent with ButtonBehavior


Widgets
-------

- [:repo:`1887`] Added export_to_png method to Widget
- [:repo:`2452`] Fix for stencil not being applied when using export_to_png()
- [:repo:`3098`] add WeakProxy with comparison
- update add_widget exception message


ActionBar

- [:repo:`1839`] fix android crash in ActionBar
- [:repo:`3107`] make icons scale properly in actionbar


AnchorLayout

- [:repo:`1981`] Add padding between layout and children
- [:repo:`2483`] anchorlayout: fix positioning and remove size change when the children is bigger than the layout itself
- uix:AnchorLayout improve `do_layout` to account for changes in `padding`.


BoxLayout

- [:repo:`2588`] BoxLayout honour padding when using pos_hint


Bubble

- [:repo:`2318`] Bubble, makes arrow use soft pixels instead of hard ones, for device independant result
- [:repo:`2536`] uix:bubble: don't assign to window when using limit_to


Carousel

- [:repo:`2542`] Fix carousel crash on load_next if empty, replace float(nan) with None
- [:repo:`3067`] Fixed carousel calculation that had switched w, h


CheckBox

- [:repo:`2336`] Use ToggleButtonBehavior
- [:repo:`2424`] Always change the CheckBox state on press
- [:repo:`2484`] uix:checkbox introduce `allow_no_selection` property
- [:repo:`2880`] Add background properties for checkbox


CodeInput

- [:repo:`2316`] Use proper cid in codeinput cache.
- [:repo:`2874`] add an easier way to use different pygments styles for the CodeInput widget.


Dropdown

- [:repo:`2429`] Ensure that container is set before everything for dropdown. Fixes issue with dynamic declared dropbox in kv.
- [:repo:`2429`] Ensure that container is set before everything for dropdown.
- [:repo:`2126`] uix:DropDown check for collision with the widgets dropdown is attached to while dismissing.


EffectWidget

- [:repo:`2095`] Added AdvancedEffectBase
- [:repo:`2095`] Added source property to EffectBase
- [:repo:`2095`] Add new EffectWidget uix module


FileChooser

- [:repo:`2106`] Fix problem with list(bool) in filechooser.py
- [:repo:`2338`] Catch None in filechooser when iterating files.
- [:repo:`2366`] uix:FileChooser fix multiselect behavior consistent, honor dirselect.
- [:repo:`2523`] FileChooserIconView: scroll to top when entries cleared
- [:repo:`2525`] add multi-view file chooser
- [:repo:`3060`] Fixed filechooser path incorrectly updated when going to parent directory
- uix:FileChooser make use of abspath to store current path.


Image

- [:repo:`2286`] uix:Image delayed importing of loader. Import it only when used


Label

- [:repo:`1878`] Label: Shorten the string only if it's larger than texture size.
- [:repo:`1935`] Improve text rendering algorithm, fully implement padding, implement justify everywhere
- [:repo:`1907`] Correct label padding to be positive, not negative.
- [:repo:`1944`] Fix shorten to work the old way for now with the update text algo
- [:repo:`2175`] Shorten fixes
- [:repo:`2251`] Clear refs and anchors when clearing text. Fixes #2250.
- [:repo:`2238`] Keep the markup color attribute after creation. Fixes #2210.


ListView

- [:repo:`1973`] dictadapter update sorted_keys when data is updated
- [:repo:`2090`] Allow VariableListProperty to accept any list derivative
- [:repo:`2091`] Use dp for filechooserlistview instead of sp
- [:repo:`2420`] Changed ListAdapter cls to accept string
- [:repo:`2598`] fix ListItem* repr for python 2
- [:repo:`2782`] bind listview adapter triggers on adapter change
- [:repo:`1972`] dictadapter: fix unit tests related to it.


PageLayout

- [:repo:`1871`] fix pagelayout assumes fullscreen for swipe threshold calculation
- [:repo:`3007`] Fix PageLayout indexing issues.


Popup

- [:repo:`2825`] allow horizontal align for popup title
- [:repo:`3104`] Don't create a prop named popup in content. Fixes #3103.


RelativeLayout

- [:repo:`2444`] Old kv rules for Relative Layout removed


RstDocument

- [:repo:`1989`] Allow reloading rst files and allow source to be ''
- [:repo:`2162`] make rst underline color configurable
- Allow setting source to empty string to clear text, if it wasnt empty before.


Scatter

- [:repo:`2206`] Add on_bring_to_front event to Scatter
- [:repo:`2714`] fixes Scatter crash on windows


ScatterPlaneLayout

- [:repo:`2682`] widgets: add new ScatterPlaneLayout,


ScreenManager

- [:repo:`1943`]  Add attribute to change fbo transparency in FadeTransition
- [:repo:`1985`] moved `remove_screen(self.screen_out)` to `_on_complete`
- [:repo:`2005`] Swap docstrings in screenmanager.py
- [:repo:`2804`] provide better exception message when Screen is added to its current manager
- [:repo:`2946`] screenmanager: swap up/down SlideTransition
- [:repo:`2749`] prevent flicker when using shader transitions
- [:repo:`3080`] screenmanager: screen's layout is fixed before on_enter is dispatched.
- fix initial screen position in screenmanager


ScrollView

- [:repo:`1866`] Fix scrolling on empty scrollview.
- [:repo:`2296`] Add bar_inactive_color property for ScrollView
- [:repo:`2328`] When mouse scrolling, don't pass it on to children. Fixes #2031.
- [:repo:`2362`] update _scroll_x_mouse and _scroll_y_mouse to fix scrollview jumping
- [:repo:`2371`] fix nested scrollviews
- [:repo:`2526`] Fix scrollbar scroll touches
- [:repo:`2522`] fix horizontal scrolling with mouse wheel/touchpad
- [:repo:`3089`] Fix scrollview crash on multitouch events
- [:repo:`3131`] fix ScrollView._apply_transform
- increase scrollbar width


Settings

- [:repo:`2036`]  Automatically focus SettingString textinput when popup opens
- [:repo:`2074`] Made settings popup sizes dynamic and sensible


Slider

- [:repo:`2769`] Minor fix in slider.py. slider.value now set to slider.min at init
- [:repo:`3021`] change slider default padding to sp(16) to match sp(32) size of slider cursor.


Splitter

- [:repo:`2000`] Splitter: Added rescale_with_parent property
- [:repo:`2000`] Added splitter options to keep within parent bounds and to rescale with the parent
- fix `rescale_with_parent` property name in docstring


StackLayout

- [:repo:`2653`] Fix stacklayout size hint
- [:repo:`2803`] properly handle StackLayout size_hint and spacing


TextInput

- [:repo:`2332`] Fix TextInput bubble not following cursor position on window resize.
- [:repo:`1954`] TextInput space stripping fixed, should now account correctly for kerning in cursor positioning
- [:repo:`1913`] use a blank 1x1 texture for empty line
- [:repo:`1954`] Fix textinput space stripping
- [:repo:`1969`] Fix TextInput padding_x being ignored when calculating cursor position
- [:repo:`1997`] Add cursor_color property for TextInput
- [:repo:`2008`] Selection handles
- [:repo:`2055`]  Introduce input_filter to TextInput to allow only e.g. int, float inputs
- [:repo:`2267`] minimum_height depends on line_height
- [:repo:`2302`] Prevent cache clash for textinput width between password = True/False.
- [:repo:`2349`] ensure _win is set when updating graphics
- [:repo:`2369`] Fixed textinput height calculation based on padding
- [:repo:`2331`] Keep correct cursor pos when resizing. Fixes #2018.
- [:repo:`2357`] uix:TextInput move checking for command modes out of `insert_text`
- [:repo:`2283`] correctly calculate texture coordinates when erasing at the end of a long line, fixes #508
- [:repo:`2389`] fix textinput scroll direction
- [:repo:`2390`] make textinput play nice in scatter and scrollview
- [:repo:`2332`] uix:TextInput fix bubble positioning.
- [:repo:`2612`] Update textinput.py to improve pg_move speed
- [:repo:`3063`] move TextInput handles/bubble to window with transformation
- uix:TextInput use int not round, pageup/down was still crashing


TreeView

- [:repo:`1901`] properly unset the selected_node attribute for TreeView


VideoPlayer

- [:repo:`1890`] Fix VideoPlayer state inaccurate after end of stream
- [:repo:`1879`] Fixes problems with seeking and length for the gst audio player
- [:repo:`1893`] Fix VideoPlayer not responding to source change
- [:repo:`2275`] Fix issue where a frame might load after video.unload() is called
- [:repo:`2866`] image_overlay_play and image_loading attributes of VideoPlayer fixed


Platforms
---------

Android

- [:repo:`1869`] Changing Sound.volume should now have an effect on Android
- [:repo:`1947`] core:Clipboard ensure clipboard works on older android versions.
- [:repo:`2471`] skip processing some about touch when not touching screen on android
- [:repo:`3119`] Fixes crash using latest pyjnius
- [:repo:`2710`] fix android and ios rotation


iOS

- [:repo:`2754`] Fixes typo in system font directory path on iOS
- [:repo:`2413`] ios/simulator: fix color inconsistency for text rendering
- [:repo:`2710`] fix android and ios rotation
- [:repo:`1792`] ios: fix initial window display / sizing issue / redisplay issue.


Linux

- [:repo:`1830`] X11 compilation improvements


OSX

- [:repo:`2010`] Added save flipped image implementation on MacOS


Raspberry Pi

- [:repo:`2382`] Simple keyboard implementation for raspberry pi.
- [:repo:`2581`] Solving issues #2373 and #2364 on rpi running archlinux
- [:repo:`2656`] support rpi touchscreen
- [:repo:`1302`] rpi: add stencil support when creating the egl context.


Libs
----

GSTPlayer

- [:repo:`2200`] fix for #2129 automatic pause in gstplayer after a few frames
- [:repo:`2466`] Made local variable reference to fix cython 0.21
- [:repo:`2722`] gstplayer: fix invalid size passed when we have a row stride (width * 3 not a multiple of 4).
- [:repo:`2454`] gstplayer: fix deadlock when changing the volume on linux / pulseaudio.


libtess2

- [:repo:`2440`] added libtess2
- backport a libtess2 fixes found in others forks to prevent a infinite loop (not all of them :()


OSC

- [:repo:`2314`] OscAPI: Changed error check on dispatch, to avoid hidding program errors as well as osc errors
- [:repo:`2806`] various cleanup in osc.py
- [:repo:`3114`] osc convert data to bytes before packing
- [:repo:`3149`] Osc fixes


Tools
-----

- [:repo:`2621`] Pep8 checker fix
- [:repo:`2960`] Add new checks to kivy/tools/pep8.py
- [:repo:`3116`] report.py sends report to https://gist.github.com/
- Add a tool to generate all the icons version your application needs, Google Play, App Store, Amazon Store, and for all devices (mdpi->xxxhdpi, iPhone/iPad/iTunes).
- texturecompress: use a POT size of PVRTC (same for width/height), otherwise the OSX texturecompress will fail.
- icons: fix icon generation for iPadx2


Compatibility
-------------

Twisted

- [:repo:`1805`] better twisted integration
- [:repo:`1805`] Multiple cycles of install/uninstall of Twisted Reactor

Sublime Text

- [:repo:`2033`] Fix Syntax Highlighting for Sublime Text

Emacs

- [:repo:`2207`] emacs integration: Disable indent-tabs-mode in kivy-mode.el.


Examples
--------

- [:repo:`1987`] Python3 and pep8 fixes for 3d rendering example
- [:repo:`2007`] Correct config example
- [:repo:`2020`] Fix shadertree example for python3
- [:repo:`2066`] make touchtracer use pressure if available
- [:repo:`2058`] $N-Protractor multistroke recognizer and demo app
- [:repo:`2376`] Added texture example, showcasing wrap and tex_coord manipulation
- [:repo:`2360`] fix android/takepicture for samsung galaxy S4
- [:repo:`2742`] Create app_suite demo
- [:repo:`2704`] change video example so it works when tried on an android phone
- [:repo:`2813`] Kivycatalog fix: prevent extra spinner events
- [:repo:`2814`] handle invalid font paths in CodeInput example
- [:repo:`2886`] Added miscellaneous examples folder and a first entry
- [:repo:`2924`] KivyCatalog LabelContainer demo update, clearer labels
- [:repo:`2944`] Fix escape exiting on unfocus in kivycatalog
- [:repo:`2956`] Add documentation to examples/animation/animate.py
- [:repo:`2955`] Add description to examples/3Drendering/main.py
- [:repo:`2957`] Add documentation to examples/camera/main.py
- [:repo:`2963`] Documentation for examples/canvas/bezier.py
- [:repo:`2964`] Updated examples/audio/main.py docstring
- [:repo:`2965`] Update examples/canvas/canvas_stress.py with docs and new button
- [:repo:`2966`] Add examples/canvas/circle.py docstring
- [:repo:`2967`] examples/canvas/clearbuffers.py changes and rename.
- [:repo:`2969`] examples/canvas/lines.py Add docstring.
- [:repo:`2971`] Added examples/canvas/lines_extended.py docstring
- [:repo:`2972`] Add documentation to examples/canvas/mesh.py
- [:repo:`2976`] Fix examples/ PEP8 errors. Mostly white space
- [:repo:`2979`] examples/canvas/multitexture.py documentation
- [:repo:`2981`] examples/canvas/rotation.py Added docstring
- [:repo:`2982`] examples/canvas/tesselate.py: Add docstring, logging, update display.
- [:repo:`2973`] Create and document examples/canvas/mesh_manipulation.py
- [:repo:`3008`] py3 division fix in mesh example
- [:repo:`3125`] multitexture example: Original texture is displayed along with combined texture
- [:repo:`1869`] example: add slider volume for audio examples
- fix audio example
- shadereditor: allow to use another image in command line


Unit Tests
----------

- [:repo:`2422`] fix test_keep_data so that it looks up the texture
- [:repo:`2862`] Updated test of kivy.utils to 100% (platform detection)
- [:repo:`2950`] Update testing and documentation of utils.py
- [:repo:`2953`] Get kivy/tests/test_graphics.py to clean up results.png
- tests: add the possibility to run tests without internet (use NONETWORK=1 make test)
- python 3 tests fixes (Fix filechooser unicode test,  vector test)
- fix benchmarks, update benchmark.py
- Audio tests were failing on OSX/Windows


Packaging
---------

- [:repo:`2855`] add .pxd and .pxi files to package
- [:repo:`2867`] Use the correct build path when generating files in setup.py
- [:repo:`2883`] Print warning when executed shell command does not return code 0
- [:repo:`2888`] avoid make distclean to error when git is missing
- [:repo:`2914`] show warning/error for cython versions
- [:repo:`2911`] packaging: Fix licensing and extras
- [:repo:`2959`] Simplify pip install (resolves kivy/kivy#2958)
- [:repo:`3015`] fixes #3011 some files always rebuilt at make
- [:repo:`3041`] Use distutils for cython version comparision.
- [:repo:`2934`] Add both src and build paths to setup.py for generating setupconfig and co.
- [:repo:`3101`] handle LooseVersion == str comparisons in py3
- Fixes for Cython 0.21
- setup: fix python3
- py3 compatibility fix for osx packaging
- setup.py: changes to not force SDL2 or GStreamer if they are explicitly disabled + reduce the code that generates configuration.
- [:repo:`2879`] setup: fixes issues with gstreamer autodetection / compilation.
- osx packaging fixes
- Don't remove debian subdirectory if it exists on git cleanup.
- [:repo:`2299`] [:repo:`2324`] conflict with debian repository


Miscellaneous
-------------

- [:repo:`2760`] Style Guide/Pep8 fixes
- [:repo:`2961`] Fix spacing and long lines. 'make style' is now clean.
- [:repo:`2975`] Modify Makefile's 'make style' to check entire tree
- python 3 fixes (unich/chr), throughout codebase


Doc
---

- [:repo:`2679`] doc: add a Common Pitfalls section to RelativeLayout
- [:repo:`2751`] Doc fix to clarify kv property behaviour (fixes #2374)
- [:repo:`2763`] doc: corrected and improved size_hint doc
- [:repo:`2785`] doc: Clarified button background_color
- [:repo:`2764`] remove old doc about fixed fmt, short explanations of fmt param
- [:repo:`2787`] doc: colour -> color fixes
- [:repo:`2824`] Removed experimental tag from pause mode, screenmanager
- [:repo:`2893`] fix default font_size value in docstring
- [:repo:`2909`] doc: Added clarification to Color docstring
- [:repo:`2919`] rebuild cython code to build up to date doc
- [:repo:`2922`] Close Issue #2921 - build doc failure
- [:repo:`2950`] Update testing and documentation of utils.py
- [:repo:`2927`] Fix the default of border property (in PageLayout) in the documentation
- [:repo:`3022`] Create gallery of examples.
- [:repo:`3043`] Document combining behavior with other widgets. Fixes #2995.
- [:repo:`3082`] doc: Add links to source, Circle and Rectangle in the pong tutorial
- [:repo:`3031`] document automatic dependencies some more.
- make doc autobuild.py work under python 3
- Added scroll effect info to scrollview doc
- added explanation for AsyncImage
- added background example to uix.widget
- revisions to uix/relativelayout.py
- fixed typos in uix/widget.py
- add argument for code-block
- Document TextInput filtering.
- Rst fixes
- pagelayout: fix documentation
- Added custom keyboard example
- Improved coverage of dynamic classes
- added warning for ordering of dynamic classes
- Minor improvements to stencil_instructions
- Added appropriate documentaion for eos
- Updated garden to explain kivy-garden module
- revisions to graphics/vertex_instructions.pyx
- Add more details in stacklayout doc
- add instructions for Raspberry Pi
- update gettingstarted image to add raspberry pi
- grammar correction in uix/widget.py
- changed to standard version tagging
- restored python highlighting to remove red error surrounds
- layout/tag fixes to uix/gridlayout.py
- corrected versionchanged spacing + small grammar corrections
- Make the doc makefile work on windows.
- update settings documentation
- revisions to sources/guide/lang.rst
- autobuild: Return an empty string for missing summary lines. Can't compare None to string
- replace template documentation in guide by dynamic class one
- made function names more obvious in kivy/_event.pyx
- Replaced jquery-ui.min.js with uniminified versions.
- Document fixes to label padding.
- Document that widgets created before load_file was called doesn't have styling.
- Document line_height vs minimum_height of TextInput
- added event bubbling explanation to the widget class
- examples: add a camera example (easy for testing the camera widget)
- added observation for on_touch_move and on_touch_up events
- fixed code example for the storage module
- Fixed a typo in the firstwidget.rst tutorial.
- fixed typo in kivy.storage example
- uix:Image improve FullImage Example
- corrected canvas descriptions and link
- added warning note, to help others not to waste 2 hours on a pygame bug on OSX
- Mention <app_name> folder creation in user_data_dir docs
- Added matrix docs
- Add note about twisted on iOS
- Add Contribution section to readme
- Fix label ref example
- Update supported python version.
- Add note about fully qualified path for iOS packaging
- Add dt description on Clock docs
- Clarify Config.set corner case
- add notes on packaging re py2/py3
- Links for Twisted echo server examples were broken, fixed the links
- Changing the sample json url
- fix obstrusive versionadded
- Adding instructions how to install Pygame for python3
- Add note about mouse_pos to motion event
- example: add slider volume for audio examples. #1869
- corrected inaccuracies in uix/widget.py
- added link to selection_mode in adapter/listadapter.py
- revisions to adapters/models.py
- more concise introduction for uix/listview.py
- simplified example in uix/listview.py
- fixed example, made more minimal
- revisions to uix/listview.py
- removed extraneous code from example in uix/listview.py
- grammar tweaks to uix/listview.py
- tweaks to uix/listview.py
- linked property names to property docs for uix/listview.py
- fixed args_converter link in uix/listview.py
- added links to uix/listview.py docs
- Fix EventDispatcher docs.
- added link, clarified cls/ctx in uix/listview.py
- tweaked example, removed repeated explanations in uix/listview.py
- stripped out invalid referral, inessential detail, added link to uix/listview.py
- stripped out repetition, more concise wording to uix/listview.py
- corrected imports in example in uix/listview.py
- tweaks to uix/listview.py
- added note on intializing selection for the ListAdapter
- corrected explanation for multiple selection
- pep8 in example in uix/listview.py
- property name in docstring
- typo fix in splitter.py
- doc autobuild.py work under python 3
- fixed list numbering, clarified wording in lang.py
- changed examples redefining Widget in lang.py
- eloborated on ids in lang.py
- added dot sytax for ids to lang.py
- escaped backslash, spelling corrections to lang.py
- added proper escaping to example in graphics/texture.py
- added warning about animation the same property to animation.py
- removed redundant space in animation.py
- doc syntax error for relativelayout
- rt "fix doc syntax error for relativelayout"
- moved addition note to the corresponding property
- Fixed defaultvalue name in docstrings
- tweaks to uix/pagelayout.py
- fixed formatting in graphics/vertex_instructions.pyx
- docs to use focused vs focus. Fixes #2725.
- refinements to uix/__init__.py
- clarified bahaviors in uix/__init__.py
- grammar tweaks to README.md
- tweaks to CONTRIBUTING.md
- revisions to CONTRIBUTING.md
- fixed unmatched string literal in core/text/__init__py
- added missing layouts to uix/__init__.py
- added missing comma to uix/__init__.py
- specify icon spec for various OS
- added PageLayout to 'getting started' guide
- added ScatterLayout to 'getting started' guide
- integrated layout links into descriptions
- added links, gramma improvements to kivy/weakmethod.py
- revisions to vector.py
- added module description
- grammar tweaks to utils.py
- explanded on utils docs, simplified platform
- explained preference for ObjectProperty



1.8.0 (Jan 30, 2014)
============================

- Python 3.3 compatibility

Core
----

- [:repo:`1631`] Extend core_select_lib to be used for other libs other than just kivy.core
- [:repo:`1678`] Gracefully exit if no core provider is found
- [:repo:`1740`] Dynamically lookup the class when a string is set for various widget with _cls properties

Audio

- [:repo:`1196`] Fix sound looping issues
- [:repo:`1209`] Fix audio issues on iOS
- [:repo:`1311`, :repo:`1269`] Fix volume property
- New GstPlayer backend

Camera

- [:repo:`1369`, :repo:`1053`, :repo:`65`] New avfoundation Camera provider for Mac OSX

Clipboard

- Introduce native clipboard provider for Android
- Add only the correct provider depending on the platform

Image

- [:repo:`1696`] Improve reload of images on context reload
- [:repo:`1809`] Use resource_find to load images
- Image/texture: add `flipped` parameter for `save` method

Text

- [:repo:`1186`] Various fixes for managing proper GL reload on GL context change
- [:repo:`1274`] Fix unicode handling in shorten routine
- [:repo:`1334`] Make shorten work with single words
- [:repo:`1376`] Label: add `max_lines` to limit the number of lines rendered in a label
- [:repo:`796`] Pygame provider: Try to use ftfont before font
- Fix for handling unicode font names

Video

- [:repo:`1490`] Fix detection or uri
- Introduce GstPlayer backend replacing pygst and pygi
- Make sure video stop and play works on Windows

Window

- [:repo:`1253`] Change default clearcolor to (0, 0, 0, 1)
- [:repo:`1408`] Avoid multiple binding to keyboard
- [:repo:`1455`, :repo:`1711`] Improve screenshot method
- [:repo:`1667`] Fix bad-looking icon on Windows 7
- [:repo:`1830`] X11 window provider improvements. Introduction of KIVY_WINDOW_ABOVE and NETWM_PID
- Fix handling of escape key

Base
----

App

- [:repo:`1233`] Fix title change not reflecting on ui after `build`
- [:repo:`1546`] Raise a default exception when app.root is not of type `Widget`
- Adds new methods to display/configure Settings panel
- New properties for configuring Kv file search
- Changed to consistently use Properties for configuration

Animation

- [:repo:`1547`, :repo:`1682`] Avoid duration=0 animations from crashing the app
- Fix leak caused by cancel() not releasing widget reference

Atlas

- [:repo:`1285`] Allow generation of an atlas with path info in the ids from the command line
- Update command line to allow padding and size specification with "WIDTHxHEIGHT"

Config

- Various fixes for default values on Windows and Linux.
- [:repo:`1084`] Fix for allowing unicode string / path in Settings
- [:repo:`1537`] Add option to not exit app on escape

Clock

- New properties for tracking frame time
- Introduce @mainthread decorator for working with threads
- Allow clock events to be canceled, utilizing `cancel` method

EventDispatcher

- [:repo:`1315`] Make sure disabling multi-touch emulation works
- [:repo:`1335`] Fix touch ring persistence when using multiple virtual keyboards
- [:repo:`1338`] Reverse the order of dispatching event stack
- Introduce `events` and `get_property observers()` method that returns a dict of properties/events and a list of methods that are bound to them

Factory

- [:repo:`1223`] Allow unregistering of widgets
- [:repo:`1726`, :repo:`1729`, :repo:`1277`] Raise appropriate error when trying to access a non-existent class

Gesture

- [:repo:`1790`] Use BytesIO for internal encoding/compression instead of StringIO

Graphics

- [:repo:`1199`] Fix Python Bindings
- [:repo:`1337`] Allow graphics instructions to be animated
- [:repo:`1345`] Allow 3D picking
- [:repo:`1393`] Texture fix repeating texture loss while GL context reload
- [:repo:`1422`] FBO use memoryview instead of buffer
- [:repo:`1488`] Added VBO support for glDrawElements and glVertexAttribute
- [:repo:`1529`] Ellipse - Faster algorithm when drawing circle
- [:repo:`1551`] Introduce segment_intersection
- [:repo:`1671`] Support member for origin in rotate constructor
- [:repo:`1723`] Use ctypes to display a dialog on win32 instead of win32ui
- [:repo:`955`] Correctly deallocate shader sources
- Force npot texture allocation with GPUs that only support npot
- Shaders: Fix loss of precision that breaks rendering
- Shaders: Support array

Lang

- [:repo:`1028`, :repo:`1734`, :repo:`302`] Allow app.kv_directory to work
- [:repo:`1234`] Use resource_find to find the filename
- [:repo:`1388`] Fix various memory leaks
- [:repo:`1519`] Instead of creating an ObjectProperty for every new property declared in Kv lang, detect it’s type and instantiate relevant Numeric/String/List/DictProperty
- [:repo:`991`] Add warning if Kv file is loaded multiple times
- Allow `_` to be checked as if it was a key.value property

Logger

- [:repo:`1721`] Python3 compatibility fixes
- [:repo:`825`] Ensure arguments to the logger are strings
- Force logging.root to use Kivy Logger instance. Fixes infinite loop

Network

- [:repo:`1248`] Introduce `decode` property. Makes decoding optional
- [:repo:`1316`, :repo:`1224`, :repo:`1221`, :repo:`1286`] UrlRequest: various improvements
- [:repo:`1457`] Make sure parameters aren’t removed
- [:repo:`1719`] OSC: Fix usage for client
- Introduce `file_path` argument

Properties

- [:repo:`1243`] Make BoundedNumeric Property more accurate
- [:repo:`1389`] Allow individual elements of ReferenceListProperty to be changed
- [:repo:`1468`] Stop DictProperty from deleting key if value is None
- Introduce `VariableListProperty`
- Properly return result in ObservableDict.setdefault

Input
-----

- [:repo:`1119`] Fix touch offset on various touch screen hardware
- [:repo:`1489`] New input provider for Leap Motion
- Add support for tuio/2dblb(CCV 15)
- Introduce MotionEvent.`last__motion_event`

PostProc

- [:repo:`1204`] Fix double tap and triple tap detection
- [:repo:`1348`] Fix double and triple tap detection on Windows


Modules
-------

- [:repo:`1668`] Add late configuration if module has been added manually before the window creation

Inspector

- [:repo:`1549`, :repo:`1684`] Fix inspection of elements in popup. by looking at ModalView before other elements
- [:repo:`1361`, :repo:`1365`] Allow position of inspector to be adjustable

Recorder

- [:repo:`1800`] Introduce `F6` shortcut to play last record in a loop

Screen

- [:repo:`1448`] Add support for scale
- [:repo:`1687`, :repo:`1686`] Fix all resolutions to be landscape
- Remove 25dp from height to simulate the Android systemui bar

WebDebugger

- [:repo:`1819`] WebDebugger: Display instant value of each box

Widgets
-------

- [:repo:`1238`] PageLayout: A simple multi-page layout allowing flipping through pages using borders
- [:repo:`1264`] ActionBar: Mimics Android’s own ActionBar appearance and mechanisms
- [:repo:`1471`] Behaviors: ButtonBehavior, ToggleButtonBehavior ,DragBehavior
- SandBox (experimental): Runs itself and its children in an exception-catching sandbox

Accordion

- [:repo:`1249`] Stop empty accordion from accessing it’s first child
- [:repo:`1340`] Fix select method

Bubble

- [:repo:`1273`] Honor `arrow_pos` when passed as a arg in constructor.
- Introduce`show_arrow` property

Button

- [:repo:`1212`] Introduce `trigger_action()` for triggering the button programmatically

Carousel

- Introduce `load_slide` method to animate the provided slide in/out
- Introduce `anim_type` property to be able to choose the type of animation

CheckBox

- [:repo:`1695`] Fix active state in group

CodeInput

- Minor rendering fixes
- Use MonoSpace font by default

Dropdown

- Delay container binding, allow it to be used in Kv
- [:repo:`1450`] Introduce `on_dismiss` event
- Pressing escape when dropdown is active now dismisses the dropdown
- Make auto-dismiss of dropdown optional. Introduces `auto_dismiss` property

FileChooser

- [:repo:`1476`] Fix inability to browse up to the root path
- [:repo:`1758`] Prevent infinite loop
- [:repo:`1780`] Fix incorrect selections caused by touch offset
- [:repo:`1818`, :repo:`1829`] Fix unicode issues. Now, path defaults to a unicode string
- Abstracted filesystem access
- If a path is expected to contain non unicode-decodable characters, a bytes path string should be used. Otherwise, unicode paths are preferred

Image

- [:repo:`1561`] Don’t crash if an invalid image is loaded

ListView

- [:repo:`1303`, :repo:`1304`] Set ListItemButton background_color
- [:repo:`1396`, :repo:`1397`] Accepts objects inheriting from list or tuple in SimpleListAdaptor
- [:repo:`1788`] Fix None, int comparison

Popup

- Introduce `title_color` property

Progressbar

- Avoid dev/zero when max is zero

RstDoc

- Introduce `background_color` property

Scatter

- [:repo:`1459`] Minor fixes for scaling
- [:repo:`1797`] Fix div by 0 issue where touch itself was chosen as anchor
- [:repo:`947`] Fix scale being dispatched again due to error in floating point calculation
- Various fixes for transformation

ScreenManager

- [:repo:`1750`] Add NoTransition transition
- [:repo:`573`, :repo:`1045`] Introduce `switch_to` method fixes for
- Fix Shader-based transitions, allowing them to work in non-fullscreen mode
- New Screen transitions, mimicking Android
- Reduce default transition duration and set default transition to SlideTransition
- Set clear color to be transparent

ScrollView

- [:repo:`1387`] Show scrollbars only when viewport is scrollable
- [:repo:`1463`] Refactor kinect constants
- [:repo:`1478`, :repo:`1567`] Introduce bars scrolling for desktop type behavior
- [:repo:`1604`] Fix overscroll on low FPS
- Accelerated scrolling by default using Matrix instead of moving the child
- Introduce `bar_pos`, `bar_side_x` and `bar_side_y` properties allowing the user to control where the the bars are displayed
- Introduce `scroll_wheel_distance` property

Slider, Spinner

- DPI fixes making the widget aware of screen metrics

Splitter

- [:repo:`1655`, :repo:`1658`] Make double tap on border alternate between max/min size
- [:repo:`1656`, :repo:`1672`, :repo:`1673`, :repo:`1810`, :repo:`1812`] Miscellaneous fixes
- [:repo:`1657`] Don’t allow negative sizes
- Make sure splitter remains between min/max_size when these properties are changing

Settings

- [:repo:`1228`] Fix for allowing unicode path
- [:repo:`1556`] Made SettingsString textinput scale independent
- [:repo:`1590`] Prevent import of SettingsWithSpinner when custom class is used
- Fixes for SettingsPanel that allows it to adjust to mobile screens
- Fix handling of numeric input
- Made various behaviors (settings popups, fonts) more scale independent
- Make the default tab active in SettingsWithTabbedPanel
- Now includes different Settings widgets, suitable for different devices

StackLayout

- [:repo:`1390`] Simply `do_layout`

TabbedPanel

- [:repo:`1402`] Introduce `strip_image` and `strip_border` properties to allow skinning the TabbedPanelStrip
- [:repo:`1799`] Honor index while inserting TabbedPanelHeader
- Fix bug when selected tab is removed before switching to it

TextInput

- [:repo:`1496`] Introduce `allow_copy`,  to allow the user to choose whether Textinput allows copy or not
- [:repo:`1632`, :repo:`1717`] Fixes for selection offset issues
- [:repo:`1639`, :repo:`1500`] Make sure cursor remains inside TextInput
- [:repo:`1647`] Introduction of  Handles for selection on mobile enabled by `use_handles`property
- [:repo:`1697`] Introduce `Keyboard_mode` to allow custom management of keyboard
- [:repo:`1702`] `copy`, `cut`, `paste` methods to allow the user to manage clipboard operations
- [:repo:`1774`] Fixes for voice input
- Introduce `line_spacing`
- Introduce `minimum_height` property to be used in conjunction with scrollview
- Introduction of `input_type` property that is used to specify the kind of IME to request from the OS
- Introduction of `keyboard_suggestion` allowing native keyboards on Android to show word suggestions
- Various fixes for cut/copy/paste
- Various `Unicode` fixes. Textinput now maintains a unicode sandwich

Videoplayer

- [:repo:`1275`] Fix looping
- [:repo:`1823`] Ensure vdeo is loaded before loading the state

Vkeyboard

- [:repo:`958`] Fix custom layout usage
- [:repo:`1333`] Don’t dispatch touch to other widgets while moving
- [:repo:`1404`] Introduce dual keyboard mode `systemanddock`and `systemandmulti`
- `Layout` property can directly point to a JSON file name now

Widget

- [:repo:`1209`] Introduce `disabled` property
- [:repo:`1452`] Add children= argument to clear_widgets()

Platforms
---------

RaspberryPi

- [:repo:`1241`] Fix installation of vidcore_lite for RPi
- Add support for “relative” hid input as mouse
- Fix configuration generation, and fix hidinput provider for multitouch hardware
- Introduce new window provider specifically for RPi

Tools
-----

- [:repo:`1352`] Improvements to highlighting file for emacs
- [:repo:`1527`, :repo:`1538`] Move Kivy Garden to it’s own repository
- [:repo:`1807`] support for using hidinput to display mouse cursor
- Make Garden Tool Python 3 compatible

Doc
---

- Tons of doc fixes thanks to the awesome community
- Special Thanks to ZenCODE for his awesome work on improving the doc

Examples
--------

- Various redesign, fixes and improvements making examples fit better on mobile
- New Kivy Showcase, designed to fit much better on mobile devices
- New `Take Picture` example to demonstrate how to use startActivtyForResult and how to get the result with python-for-android android.activity module
- Rework compass example to work with py4a and remove all broken code

Unit Tests
----------

- [:repo:`1226`] New test for testing unicode font names
- [:repo:`1544`] Add unit tests for Vector class
- [:repo:`1828`] Unicode Filechooser tests
- [:repo:`823`] Add test case for issue
- Improve tests with new proxy_ref
- Various tests introduced to test Python3 port

Packaging
---------

- Tons of fixes and new packages for Python 3
- [:repo:`1540`] Various fixes for Windows launcher
- [:repo:`1599`] Various fixes for installation on 32 bit Mac OSX



1.7.2 (Aug 4, 2013)
============================

- [:repo:`1270`] Fix slowdown in graphics pipeline during gc
- [:repo:`1253`] Change Window.clearcolor to 0, 0, 0, 1
- [:repo:`1311`, :repo:`1269`] Fix audio volume property
- Add audio loop property for Sound object
- Fix leak when using Animation.cancel() method
- Fix few leaks related to Kv language


1.7.1 (May 28, 2013)
============================

- [:repo:`1192`] "Black label" issue on old phone
- [:repo:`1186`] Reloading mipmapped label
- [:repo:`1204`] doubletap/tripletap for windows hardware
- First-time configuration generation for linux/windows


1.7.0 (May 13, 2013)
============================

Core
----

- [:repo:`1020`] new App.user_data_dir, where user can store app state
- [:repo:`1047`] new markup subscript/superscript
- [:repo:`1145`] fix numpad keys mapping in Window
- Animation starts the timer at the first frame instead on start()
- Enhance clock calculation to have less glitch and be closer to 60 FPS.
- New VariableListProperty property that support 1, 2 or 4 values. used for padding, spacing...
- No more crash if no video core provider have been found
- Refactoring event declaration, use __events__ instead of register_event_type()
- Refactoring properties storage into a Cython class instead of a dict

Graphics
--------

- [:repo:`1014`] force Context.gc() to dealloc gl resources
- add etc1 support for textures
- fix Buffer memory allocation for block with the same size
- fixes to support GL from Android emulator
- fix shader warning when both vertex and fragment are set
- new Fbo.pixels
- new Matrix.project() for 3d to 2d transformation
- new RenderContext use_parent_modelview and use_parent_projection
- new Texture.pixels and Texture.save(fn)

Widgets
-------

- [:repo:`1005`] new Popup.title_size for title font size
- [:repo:`1018`] better Slider support for padding
- [:repo:`1021`] fix widget insertion with/without canvas.before
- [:repo:`1032`] fix Carousel animation when looping between 2 slides
- [:repo:`1052`] fix TextInput to allow ctrl+c work in readonly
- [:repo:`1091`] fix StackLayout spacing in multiple orientations
- [:repo:`1122`] improve splitter dragging
- [:repo:`1140`] fix ScreenManager when rotation is applied
- [:repo:`1148`] avoid freezing when a ModalView is open twice
- fix DPI issues on Slider
- introduce ScrollView effect, such as DampingScrollView and OpacityScrollview
- introducing ScatterLayout (which is same as RelativeLayout, but based on Scatter)
- new ColorPicker widget
- new Scatter.translation_touches to allow translation only with X touches
- refactoring RelativeLayout with only translation
- refactoring ScrollView, improved performance and behavior
- TextInput now use double and triple tap to select word and line
- TextInput select the whole text on 4 touches
- Various changes for padding, spacing, for supporting 1, 2 or 4 values

Lang
----

- introduce prefix '-' to avoid applying previous rules
- new Dynamic classes, Templates are now deprecated

Inputs
------

- fix doubletap behavior
- new tripletap post-processor module

Others
------

- [:repo:`1023`] better inspector widget selection
- [:repo:`1024`] add font-size demo to showcase
- [:repo:`1038`] fix Gstreamer sound.seek()
- [:repo:`1125`] more fixes on listview examples
- [:repo:`849`] new kivywinescript to execute kivy python within wine
- Garden project! Including kivy.garden and garden script
- new kivy.storage api for storage abstraction (experimental)
- Refactoring documentation
- tons of documentation fixes by Zen-CODE!



1.6.0 (Mar 10, 2013)
============================

Core
----

- [:repo:`1001`] Add justify support for text alignment
- [:repo:`828`] Fixed descriptor error in EventDispatcher.getattr
- [:repo:`886`] Fixes memory leak when log_enable = 0 in config
- [:repo:`895`] Fixes network image reloading
- [:repo:`902`] Fixes Python strings for 2.6
- [:repo:`920`] Fixes ImageIO crash if image cannot be loaded
- [:repo:`985`] Fixes zip loader to skip errors
- Add support for GIF transparency in PIL
- Core logs are now reduced, and traceback is available only in trace
- Enhance Clock to accept only callable() in schedule methods
- EventDispatcher can be weak-referenced
- Fixes image reloading when Window is resized on OSX
- Fixes Window fullscreen, even when the config is "auto"
- Fixes Window.screenshot for rotated window
- Improve Kv: avoid to parse on_* expression, just exec them.
- New MotionEvent.is_mouse_scrolling
- Rework Loader internals, limit to 2 threads workers and images upload per frames

Graphics
--------

- [:repo:`913`] Fixes Line.ellipse/circle instructions
- Add Texture support for paletted texture
- Add Texture support for PVRTC (iOS and PowerVR GPU only)
- Enhanced vertex format to allow custom format.
- Fixes crash on the Adreno 200 GPU / Android - force POT texture
- Reworked graphics vertex instructions to support custom format as well

Widgets
-------

- [:repo:`863`] Improve ListView usage with Kv language
- [:repo:`865`] New Bubble.limit_to for limiting the bubble position
- [:repo:`868`] Fixes Slider positioning when padding is used
- [:repo:`883`] Fixes empty markup rendering
- [:repo:`916`] Fixes cursor positionning in CodeInput
- [:repo:`921`] Fixes Scrollview scrolling with mousewheel if it's disabled
- [:repo:`928`] Image log an error when an image cannot be loaded
- [:repo:`937`] Fixes BoxLayout.pos_hint for children
- [:repo:`940`] Enhance TextInput bubble for long-press and readonly
- [:repo:`941`] Fixes ProgressBar value boundaries
- [:repo:`954`] Fixes GridLayout children size_hint
- [:repo:`959`] Add ListAdapter.data property to allow changing the data
- [:repo:`961`] Fixes ScreenManager green color to black in ShaderTransition
- [:repo:`966`] New TextInput placeholder
- [:repo:`989`] Fixes Carousel positioning and reduce calculations
- Add mousewheel support on Slider
- Enhance TabbedPanel to allow no default tab
- Fixes for TextInput rendering glitch
- Fixes RelativeLayout.clear_widgets()
- Fixes ScrollView gesture ability on X when scrollview is Y only (and the inverse)
- Fixes TextInput wrapping
- New (Async)Image.nocache no prevent caching (data, texture)
- New Screen events: on_pre_enter/enter/pre_leave/leave
- New ScreenManager.has_screen() method

Others
------

- Fixes inspector crash
- iOS: Updated SDL, launch images are now supported
- New 3D rendering example with lightning and a monkey
- Tons of fixes on Documentation !


1.5.1 (Dec 13, 2012)
============================

Widgets
-------

- [:repo:`847`] Avoid to react on scrollleft/right on Button + FileChooser

Graphics
--------

- [:repo:`856`] Fix Line instruction

Examples
--------

- [:repo:`848`, :repo:`855`] Fix Kivy catalog to work from a different cwd


1.5.0 (Dec 9, 2012)
============================

Core
----

- [:repo:`731`] BoundedNumericProperty can have float bounds
- [:repo:`755`] Fix SetWindowLongPtr on 32/64 Windows
- [:repo:`768`] Fix AsyncImage loader on iOS
- [:repo:`778`] Prevent the Pygame parachute if we don't have the required
GL version. Instead, show a msgbox.
- [:repo:`779`] Better DPI support, with new sp and dp units
- [:repo:`783`] New screen module for simulating different DPI devices
- [:repo:`789`] Fix on_resize dispatch on Windows and OSX
- Allow multiple providers in Kivy env variables
- Fix line off-by-one issue in Kv errors
- New errorhandler/errorvalue in Property class
- New experimental X11 window provider, that support transparent
window.
- Normalize android pressure and radius
- Reduce gstreamer audio/video out-of-sync
- Support ability to stop/restart the EventLoop


Graphics
--------

- [:repo:`481`] Avoid error in case of multiple Canvas.rremove()
- [:repo:`610`] Add more information when GLEW fail to initialize
- [:repo:`671`] Allow source unicode filename in BindTexture
- [:repo:`790`] Allow to change Stencil operators
- Avoid BGRA-&gt;RGBA conversion for OSX if the GPU support BRGA.
- Fix issue with Cython 0.14, "by" is now considered as a keyword
- Line: add bezier and bezier_precision properties
- Line: fix missing ellipse/circle/rectangle in the Line constructor
- Texture: always flip the texture vertically for Image and Label


Widgets
-------

- [:repo:`618`] Raise exception if ScreenManager.start() is called twice
- [:repo:`648`] Avoid touch event propagation on ScreenManager transition
- [:repo:`662`] Enhance TextInput performance
- [:repo:`706`] Fix pos_hint Boxlayout calculation
- [:repo:`725`] Fix collapse management in Accordion
- [:repo:`734`] Fix widget opacity when passed in the constructor
- [:repo:`736`] Fix slider bug when min &lt; 0, max &lt; 0 and step &gt; 0
- [:repo:`737`] Better swipe gesture detection for Carousel
- [:repo:`747`] Honor index in Carousel.add_widget() (and Bubble)
- [:repo:`750`] New CodeInput widget
- [:repo:`771`] Dispatch modalview.on_open after animation
- [:repo:`785`] Allow event binding in Widget constructor
- [:repo:`819`] Fix canvas positioning when inserting at first position
- [:repo:`824`] Add top-to-bottom + right-to-left Stacklayout orientations.
- [:repo:`832`] Fix shorten routine
- Automatically register new Widget classes in Factory
- Enhance ScrollView scrolling
- Fix Carousel API, containers are now hidden, and
slides/current_slide/previous_slide/next_slide are the user
widgets.
- Fix Label.color property for markup labels
- Multiples fixes to TabbedPanel (tab_strip, unbind, tab selection)


Others
------

- [:repo:`670`] New compass demo for Android using sensors
- Many many fixes on the documentation, thanks for all the PR!
- New KivyCatalog example: interactive Kv editor
- Started Guide 2.0


1.4.1 (Sep 30, 2012)
============================

Core
----

- [:repo:`625`] Extend NumericProperty to support DPI notation
- [:repo:`660`] Add callbacks support on ConfigParser for a (section, key)
- [:repo:`666`] Fix Markup text disapear on GL reloading
- [:repo:`678`] Enhance UrlRequest for small chunks, callbacks and GC
- [:repo:`679`] New Audio.get_pos()
- [:repo:`680`] Fix key translations on Keyboard
- Force on_parent dispatching for children in a kv rule
- Expose 'app' instance keyword in Kv language

Graphics
--------

- [:repo:`686`] Added opacity support in the graphics pipeline
- Enhanced Line instruction that support width, joint, cap.
- Added Line.circle/ellipse/rectangle properties

Widgets
-------

- [:repo:`664`] Fix TextInput crashes is some cases
- [:repo:`686`] New Widget.opacity property
- [:repo:`690`] New TextInput.background_normal/active
- [:repo:`694`] Fix Slider value when min and step &gt; 0
- [:repo:`676`] Fix Carousel.remove_widget()
- [:repo:`669`] Fix SettingNumeric with int/float values
- [:repo:`698`] Enhance BoxLayout to support pos_hint
- Fix ModalView background property


Windows
-------

- [:repo:`675`] Fix WM_Touch / WM_Pen for 32 bits / 64 bits

Others
------

- [:repo:`462`] Fixes gstreamer packaging with PyInstaller
- [:repo:`659`] Updated documentation concerning PyInstaller 2.0


1.4.0 (Sep 02, 2012)
============================

Core
----

- [:repo:`513`] Fix nested template
- [:repo:`547`] Fix url loader with querystring
- [:repo:`576`] Markup text can be vertically aligned
- [:repo:`585`] Enhance add_widget() to raise an Exception on multiple parents
- [:repo:`642`] Support of smb:// in url loader with pysmb
- Enhance AliasProperty to cache the result if use_cache is set to True
- Enhance App.get_application_config() to get a correct config filename on all platforms
- Fix Animation.stop_all() + new Animation.cancel()
- Fix Property.unbind() for bounded methods

Graphics
--------

- [:repo:`516`] Fix crash when loading 1bit image
- [:repo:`546`] Fix Quad() initialization

Widgets
-------

- [:repo:`543`] Fix multiple content in TabbedPanel from Kv
- [:repo:`549`] Enhance TabbedPanel to introduce default_tab_class
- [:repo:`562`] Popup can now define the content in Kv
- [:repo:`593`] Enhance TextInput with select_all() and select_text() methods
- [:repo:`658`] Fix usage of Camera within Kv
- Enhanced VideoPlayer to have pause ability and state property
- Enhance Image widget to add keep_data for further pixel collision detection
- New Carousel widget
- New Checkbox widget
- New Dropdown widget
- New ModalView widget
- New RelativeLayout, identical from FloatLayout with relative coordinates
- New ScreenManager widget for changing views with transitions
- New Slider.step property
- New Spinner widget

Windows
-------

- [:repo:`621`] Fix ghost touch due to a raise condition
- Add python scripts into the PATH
- Enhance input wm_touch/pen to be compatible with 64bits
- Severals fixes around window resizing

Others
------

- New Getting Started
- Tons of documentation typo, fixes. Really, a ton.


1.3.0 (Jun 19, 2012)
============================

Core
----

- [:repo:`420`] Fix pygame error when texture is too large
- [:repo:`450`] Updated Sound class to use Kivy properties
- [:repo:`467`] New Sound.length
- [:repo:`484`] New kivy.interactive module: doesn't break REPL anymore
- [:repo:`487`] Make default values in properties optionals
- [:repo:`489`] Replaced all relative import with absolute imports
- [:repo:`498`] Fixes Image to allow re-loading of image from disk
- [:repo:`503`] Renamed unicode parameter to codepoint in all on_key_*
events
- Changed default screenshot to be PNG instead of JPEG
- Enhance Kv lang rules lookup
- Enhance Label initialitazion
- Fixes crash on App when the configuration file cannot be read
- Fixes for graphics reloading mechanism, force the GC before
flushing GL
- New default UI theme
- New KIVY_NO_CONFIG, KIVY_NO_FILELOG, KIVY_NO_CONSOLELOG env
variables
- New kivy.utils.escape_markup() to escape untrusted text when
markup=True
- Support MacOSX clipboard

Graphics
--------

- [:repo:`118`] Fixes for glColorMask on android
- [:repo:`447`] Add new ClearColor and ClearBuffers instructions
- [:repo:`463`] Fixes glGetIntegerv with new Cython
- [:repo:`479`] Fixes for Translate instance when args passed in on
creation
- Avoid drawing of empty VBO
- Enhance Stencil instruction, you can nest up to 128 layers instead
of 8
- Fixes crash when texture is empty (0px width or height)
- Fixes Point instruction when new point is appended
- Fixes to enable support of NPOT texture on android/ios platform

Widgets
-------

- [:repo:`401`] New Scatter.do_collide_after_children property
- [:repo:`419`] New TabbedPanel widget
- [:repo:`437`] New TextInput.readonly property
- [:repo:`447`] Fix popup background resizing when Window resize
- [:repo:`480`] Fixes StackLayout size_hint missing calculation
- [:repo:`485`] Fixes VideoPlayer scrollbar with multitouch
- [:repo:`490`] Fixes ToggleButton memory leak
- Add FileChooser.file_encodings for a better unicode conversion
- Better handling of mousewheel in Button
- Delayed Label texture creation
- Enhance RST widget to support :align: in image directive
- Fixes RST widget to use document root for loading images and
videos
- New Popup.dismiss(animation) attribute to disable the fadeout when
dismiss
- New RstDocument.goto(reference) for scrolling the document to a
specific section
- New Undo/Redo for TextInput

Android
-------

- Map BACK key to ESCAPE by default
- Partial fixes for black screen after wake-up

Windows
-------

- Fixes preference order for the camera provider
- Fixes some GL crash on Windows due to missing dynamic lookup of
some functions (glGenerateMipMap, glGenFramebuffers, ...)


1.2.0 (Apr 2, 2012)
============================

Core
----

- [:repo:`325`] New Window.mouse_pos to get the main mouse position anytime
- [:repo:`427`] Improved markup positioning with glpyhs+kerning
- Avoid rendering of empty text lines
- Fixed setter() and getter() EventDispatcher methods
- Implement new Dropfile event, to be able to open files on macosx
- Optimized texture upload from 3 to 1 upload in somes cases
- The system/Window can now "pause" the application if the app support it

Graphics
--------

- Disable mipmapping for people using Desktop GL kivy &lt; 3.0
- Enhanced graphics engine to support OpenGL reloading / context-lost
- Optimized shaders uniform upload if not used
- Optimized VBO drawing by using a GPU buffer for storing indices

Modules
-------

- [:repo:`415`] Recorder now record keyboards events
- [:repo:`309`] Fixes for inspector / memory leak
- New webdebugger module for having statistics on the current running app

Widget
------

- [:repo:`331`] New VideoPlayer widget: Video + controls buttons, annotations and
fullscreen
- [:repo:`411`] Propagate touchs to children for Label and Button
- [:repo:`412`] Removed redundant background_texture on Bubble
- [:repo:`416`] New background_color and foreground_color to TextInput
- [:repo:`429`] New password mode to TextInput
- [:repo:`431`] Fixes clipboard for linux, works perfect on linux, windows and mac
- [:repo:`439`] Improve performance on TextInput dealing with large text
- Enhanced FileChooser to delay the file creation over the time, and display
a progression bar if it's too slow.
- Enhance FileChooser to animate when scrollwheel is used
- Enhance scrollview to animate when scrollwheel is used
- Fixed Bubble not listening to color changes
- New FileChooser.rootpath to restrict file browsing
- New scrollview scrollbar (not touchable)
- New ".. video::" directive in the RstDocument widget
- New Video.seek() method
- Updated filechooser icon theme

Examples
--------

- [:repo:`405`] New examples dealing with unicode

Others
------

- [:repo:`404`] Fixes for msvc9 compilation errors
- [:repo:`424`] Fixed pyinstaller packaging for macosx
- Add installation instructions for mageia
- New instructions for packaging on iOS


1.1.1 (Feb 15, 2012)
============================

Core
----

- [:repo:`403`] Pygame audio loader doesn't work (in addition to camera opencv provider)


1.1.0 (Feb 13, 2012)
============================

Core
----

- [:repo:`319`] Allow dynamic changes to url in Loader
- [:repo:`371`] Allow BoundedNumericProperty to have custom min/max per widget
- [:repo:`373`] Allow Property.dispatch() to be called from Python
- [:repo:`376`] Fix list.reverse() in ListProperty
- [:repo:`386`] Fix GC with Clock triggered events
- [:repo:`306`] Fix video uri support with gstreamer
- Add support for italic/bold text in core/text
- Better traceback when an exception happen within kv
- Enhance properties exceptions
- Fixes for camera frame update
- Fixes for python-for-android project
- Fixes list/dict properties on pop/popitem method
- Merged android-support branch to master
- New Atlas class for merging png/jpeg and acces with atlas://
- New SettingPath in settings
- New markup text rendering: "[b]Hello[/b] [color=ff0000]World[/color]"
- New on_pause handler in App: used in android for sleeping
- Removed text/cairo rendering, ttf doesn't work.
- Various speedup on cython files

Graphics
--------

- [:repo:`375`] Fix clear_color in Fbo
- [:repo:`64`] New Mesh instruction for custom 2D mesh
- Fix black screenshot on GLES devices
- Fix warnings of cython compilation + debian issues

Modules
-------

- [:repo:`389`] Fix missing image for Touchring
- New recorder module: you can save and replay touch events

Input
-----

- [:repo:`366`] Fix time_end never set for all providers except mouse
- [:repo:`377`] Removed TUIO provider by default in configuration

Lang
----

- [:repo:`364`] Fixes for unicode BOM in .kv
- Rewrite kvlang parser / builder: improved performance + fixes some design
issues.

Widget
------

- [:repo:`317`, :repo:`334`, :repo:`335`] Fix AsyncImage when source is empty or already loaded
- [:repo:`318`] Fix textinput auto scroll
- [:repo:`386`] Scatter will not accept touches if none of transformations are enabled
- [:repo:`395`] Enhance doc for label/textinput about unicode chars
- Enhance FileChooser for feedback when item is selected
- Enhance FileChooser to have a directory selection mode
- Enhance Popup with more properties for styling
- Fixes for Textinput focus
- Fixes Layout when parent are changing
- Fix for not propagating touch events in Popup
- Fix Textinput with invalid selection when releasing shift key
- New Bubble widget, for displaying contextual menu
- New Copy/Cut/Paste menu in Textinput using Bubble
- New RstDocument widget, for rendering RST text

Examples
--------

- New RST_Editor example for playing with RstDocument rendering
- Various examples fixes due to new kv lang restrictions

Others
------

- [:repo:`333`] Fixes for allowing omnicompletion in vim
- [:repo:`361`, :repo:`379`, :repo:`381` ,:repo:`387`] Lots of documentations fixes from contributors!
- [:repo:`367`] Fixes for pip+virtualenv installation
- Fixes for pep8 and pyflakes
- New architecture diagram
- New documentation layout
- New pong tutorial
- Repository moved to github.com/kivy/kivy


1.0.9 (Nov 14, 2011)
============================

Core
----

- [:repo:`307`] Fixes invalid video start (play=True)
- [:repo:`308`] Fixes memleak in gstreamer video providers
- Enhance properties for introspection
- Enhance Windows to use new Property from EventDispatcher
- Fixes crash when text rendering is 0 width
- Move properties discovery in EventDispatcher instead of Widget

Graphics
--------

- [:repo:`300`] Use rgba mode for Line/Bezier dash mode

Modules
-------

- New inspector module (firebug like for Kivy)

Input
-----

- Disable mactouch input provider by default on OSX

Lang
----

- [:repo:`293`] Fixes multiline properties

Widget
------

- [:repo:`287`] Fixes invalid positioning of StackLayout with spacing
- [:repo:`292`] Fixes Image iteration when anim_delay=-1
- [:repo:`303`] Fixes for crash with ScrollView without viewport
- Add visibility of minimum_width/height/size for TextInput
- Fixes crash when text of textinput is None

Android
-------

- [:repo:`294`] Fixes android package for Android SDK rev14

Examples
--------

- [:repo:`291`] New Sequenced images examples


1.0.8 (Oct 24, 2011)
============================

Core
----

- [:repo:`205`] Fixes invalid label rendering when text changes
- [:repo:`212`] Fixes asynchronous loader when pygame is used
- [:repo:`216`] Fixes window icon when filename for special charset
- [:repo:`220`] Add audio support for Android
- [:repo:`221`] Add video support for Android using ffmpeg-android project
- [:repo:`240`] Fixes modules usage on android (pyo/pyc are accepted)
- Add kivy.resources.resource_remove_path
- Enhance event dispatching
- Enhance gobject support, reduced gstreamer lag
- Enhance UrlRequest to report download progression
- Fixes BoundedNumericProperty that wasn't working anymore
- Fixes configuration upgrade
- New GIF support, or images inside ZIP files
- New kivy.utils.format_bytes_to_human function
- New kivy.utils.platform to determine on which platform we are
- Rewrite video/gstreamer to use playbin2, no more issues with video/audio


Graphics
--------

- [:repo:`1`] Add Bezier instruction
- [:repo:`201`] Fixes deletion of vbo/fbo that happen outside main context
- [:repo:`207`] Removed LineWidth instruction, wasn't working at all
- [:repo:`271`] Fixes Line instruction crash when we have less than 2 x, y
- Add Batch.clear_data
- Enhance Bezier and Line to add a stipple mode
- Enhance graphics compilation
- Fixes for Ellipse angle_start/angle_end

Input
-----

- Enhance mouse provider to provide button index in touch event

Lang
----

- [:repo:`227`] Add Builder.unload_file() to remove kv definitions
- Enhance lang by compile() part of the kv before eval/exec

Widget
------

- [:repo:`206`] Fixes video eos property
- [:repo:`217`] Fixes texture position when textinput widget is moving
- [:repo:`224`] Add scroll_timeout/distance/friction configuration
- [:repo:`225`] Allow stream url for Video widget
- [:repo:`276`] Fixes scrollview with grabbed touch
- Add Button.background_color, Button.border
- Enhance Widget to add property introspection
- Fixes popup position when window size is changed
- New Accordion widget
- New Image.keep_ratio property
- New native support for mousewheel in ScrollView
- New ProgressBar widget
- New VKeyboard widget
- Fixes layout with conflicting usage of minimum_size and size_hint.
(Note: layout will not update its size if no size_hint are set.)

Examples
--------

- [:repo:`214`] Add example of twister integration with kivy
- Add FboFloatFayout widget to demonstrate how to optimize widget tree
- New audio demo with 8bit sounds
- New demo with custom shape and custom collision func
- New Gesture example

Modules
-------

- Enhance touchring to support alpha and scale


Documentation
-------------

- Lots of documentation fixes, typo, rewording...
- Started translation for differents languages
- Add easing images in animation
- Add instructions about how to remove kivy


1.0.7 (Jul 16, 2011)
============================
`Announcement <https://groups.google.com/d/topic/kivy-dev/feofn6ebhSs/discussion>`_

Core
----

- [:repo:`32`] Implement window rotation (0,90,180,270)
- [:repo:`150`] Fix to prevent gcc bug on Mageia
- [:repo:`153`] Add packaging doc and hooks for Windows and MacOSX
- [:repo:`155`] Replaced import in class methods with late binding
- [:repo:`157`] Implement Label.valign support
- [:repo:`166`] Prevent to open too many fonts at the same time
- [:repo:`184`] Remove unlink() in properties, not needed anymore
- [:repo:`186`] Fixes extension support for MacOSX
- Disable window resizing until we are OpenGL context resistant
- Enhance extensions wizard and auto-created setup.py
- Enhance pixels from pygame surface
- Enhance properties list to prevent memory leak
- Enhance properties to store data inside Widget class
- Fixes for Audio class creation
- Fixes for Clock dictionnary crashes
- Fixes for volume usage on gstreamer video implementation
- Fixes infinite loop when we hit max iteration
- Fixes ordering of Window.add_widget
- Fixes to avoid resync error with gstreamer
- New DDS Image loader using new S3TC support
- New DictProperty property

Graphics
--------

- [:repo:`27`] Implement mipmap support
- [:repo:`130`] Implement caching for Shader source/compilation result
- [:repo:`161`] Prevent to upload texture twice when NPOT is supported
- [:repo:`182`] Fix Rotation.angle caching with degrees/radians
- [:repo:`190`] Fix crash when too many vertices are pushed in VBO
- Enhance Ellipse to add angle_start/angle_end properties
- Enhance GridLayout to have minimum and default size per col/row
- Enhance logging of OpenGL capabilities
- Enhance texture memory by using native NPOT if available
- Enhance texture upload by using the best pixel packing
- Fixes Color.hsv property crashes
- Fixes for GLES2 by using GL_UNSIGNED_SHORT in VBO
- Fixes some typo on OpenGL wrapper
- New $HEADER$ token that can be used in fragment/vertex shader code
- New OpenGL Utils module for checking texture capabilities and others
- New S3TC texture support
- New Texture.colorfmt property

Input
-----

- Enhance Wacom support on linux platform
- Fix leak/slowdown in MouseMotionEvent

Lang
----

- [:repo:`189`] Fixes for not allowing dot in properties name
- Concat property value when the value is shifted to one level
- Enhance key resolution ([x for x in list] can be used now.)
- Enhance module/class resolution at import

Widget
------

- [:repo:`139`] Add TreeView.remove_node()
- [:repo:`143`] Fix crash when group is changing on ToggleButton
- [:repo:`146`] Fix invalid calculation for Image.norm_image_size
- [:repo:`152`] Fix Camera.play property
- [:repo:`160`] Prevent label creation until text is set
- [:repo:`178`] Set default values only on properties
- Enhance ScrollView to have kind of kinetic movement
- Fixes calculation of Stacklayout.size with padding
- Fixes FloatLayout relayout when children size* is changing
- Fixes for initial Label.font_name assignement
- Fixes to prevent call of on_release twice
- Fix ScrollView with grab events
- New Image.allow_stretch property
- New Popup (modal popup) widget
- New Settings widget
- New Switch widget
- New Widget.uid property

Examples
--------

- New tiny shader editor demo

Documentation
-------------

- [:repo:`17`] Enhance all cythonized classes documentation
- [:repo:`84`] Add previous/next link in the bottom of the documentation
- [:repo:`153`] Enhance Environment documentation
- [:repo:`159`] Remove warning on unimplemented Template in lang
- [:repo:`191`] Fix logo link to go to http://kivy.org/
- [:repo:`192`] Add PDF download link in sidebar
- Added vim highlighter
- Enhanced documentation widget with images
- Enhance OpenGL wrapper documentation with Kronos website links
- Rework documentation for Graphics part
- Several typo fixes


1.0.6 (May 3, 2011)
============================
`Announcement <https://groups.google.com/d/topic/kivy-dev/E6pbzLxWFgg/discussion>`_

Core
----

- [:repo:`109`] Logger write stderr to his file now
- [:repo:`113`] Support window resizing
- [:repo:`115`] Correctly parse 'OpenGL ES 2.0' now
- [:repo:`62`] Add kv_directory to load kv from another directory in App
- [:repo:`66`] Take care of dependencies for Makefile and setup.py
- Bump initial width/height to 800x600
- Fix test of callback for Clock.unschedule
- Speedup logger trace call using __debug__
- Speedup Widget creation by caching properties attributes

Graphics
--------

- [:repo:`129`] Fixes stencil usage in another stencil
- [:repo:`28`] Fixes to enable canvas drawing only when something changes
- Allow to retrigger event inside a callback in Clock
- Fixes in Fbo to not create Fbo with depthbuffer by default
- Fixes in shader to prevent too much name lookup with matrix
- Fixes memory leak and use __dealloc__ instead of __del__ in python
- Fixes to reduce OpenGL call (test down from 644 to 495 gl call)
- Fixes to reduce python overhead in Shader
- Fixes to use trigger for releasing texture

Input
-----

- [:repo:`132`] Fixes for WM_Touch

Lang
----

- [:repo:`131`] Allow the usage of "id" in template
- Add #:set <key> <expr> directive, can be used for global const
- Better exception when a class cannot be instanciate in Kv lang

Widget
------

- [:repo:`107`] Fixes for win32/shortcuts textinput widget
- [:repo:`116`] Fixes in filechooser to avoid crashing on unreadable dir
- Add "color" property for Image, to tint the source image
- Change "orientation" for Stacklayout + implement lr-tb, tb-lr
- Fixes FloatLayout for handling child's position changes
- Fixes for stacklayout calculation when padding is used
- Fixes for usage of minimum_size in layout
- Fixes for win32 platform in filechooser

Examples
--------

- Add Scatter examples in showcase
- Rework demos to have the same background + icon + title bar

Documentation
-------------

- [:repo:`122`, :repo:`136`] Add missing documentation for treeview, allownone
- [:repo:`124`] Add send-to method for starting kivy app on Windows
- [:repo:`126`] Cleanup old documentation
- [:repo:`127`] Add jinja2 as deps for android
- Add "Designing with kv" in user guide
- Add instructions for packaging app on Android
- Fixes on_touch_down in architecture documentation

Windows platform
----------------

- [:repo:`137`] Improve kivy.bat to execute kivy file or cmd (thx remip)
- Add win32file as a dependency, needed for filechooser

Android platform
-----------------

- [:repo:`119`] Move configuration into the directory of the application
- [:repo:`121`] Fixes for black screen on some device at start
- [:repo:`128`] Fixes to not handle input before application start
- [:repo:`134`] Fixes to correctly show splashscreen
- Avoid the dispatch of touches if they don't move
- Support of {request,release}_keyboard on Window
- Temporary disable glColorMask call for android,
unexpected crash happen in the internals of android gl



1.0.5 (April 16, 2011)
============================
`Announcement <http://groups.google.com/group/kivy-dev/browse_thread/thread/5e6aba158671722f>`_

Core
----

- [:repo:`106`] New title/icon properties in App class to set title/icon
of the Windows
- [:repo:`92`] Fixes to detect recursion in Kivy language
- [:repo:`52`] Update Kivy icon for 512, 256, 128, 64, 32 pixels size
- [:repo:`49`, :repo:`41`] Add videocapture support for Windows platform
- [:repo:`17`] New template support in Kivy language
- [:repo:`6`] New lang directive: #:import <alias> <package>
- Clean setup.py and update packages
- Disable gstreamer/camera on Mac OSX
- Enhance and speedup Clock internals
- Enhance properties exception message with its name
- Fixes for logger with ascii/unicore
- Fixes for OpenCV Camera provider on Mac OSX
- Fixes many part of lang / widget related to properties
- Fixes python path on Mac OSX
- Fixes to support jpeg extension in Pygame image loader
- Fixes to support only extensions with read support in PIL image
loader
- New -c/--config section:key:value to change the configuration
- New Clock.create_trigger (replace unschedule/schedule_once)
- New exception if Python 32 bits is used on Mac OSX
- New extensions system (experimental)
- Removed kivy.utils.curry, use functools.partial instead.

Graphics
--------

- [:repo:`89`] Add documentation for Color class
- Fixes for bgr-&gt;rgb conversion
- Fixes for matrix multiplication order and matrix internals

Input
-----

- [:repo:`87`] Fix retaintouch postproc
- Fixes for the mouse provider using disable_on_activity

Widget
------

- [:repo:`40`] Fixes for scatter.[center_x, center_y, top, right]
- [:repo:`47`] Fixes for scatter usage inside scatter
- [:repo:`79`] Correctly update child when size_hint/pos_hint is updated
- [:repo:`94`] Fixes graphicals glitch when using Layout*
- Clean hacks for add_widget/remove_widget in Widget
- Fixes for correctly honnor Scatter.do_scale
- Fixes for ScrollView.scroll_timeout
- New alternating line colors for TreeView
- New FileChooser widget (experimental)
- New on_text_validate event for TextInput
- New shorten property for Label
- New StackLayout widget (experimental)

Documentation
-------------

- [:repo:`69`, :repo:`88`] Fix ubuntu installation and installation execution
- [:repo:`86`] New FAQ entry: pip installation failed
- [:repo:`98`] New FAQ entry: undefined symbol: glGenerateMipmap
- Reword kivy language API



1.0.4-beta (March 20, 2011)
============================
`Announcement <http://groups.google.com/group/kivy-dev/browse_thread/thread/bb5734e29f23683e>`_

Core
----

- [:repo:`70`] Fixes for video_gstreamer to prevent memory leak
- [:repo:`78`] Fixes for ListProperty: correctly observe inplace changes
- New Window.request_keyboard / Window.release_keyboard
- New kv lang callback: <event> or on_<propname> will be binded
as a callback of the widget
- Fixes for 1 sec video/audio delay issue
- Fixes to allow Animation on a subset of a dict
- Fixes to make AliasProperty.dispatch working properly
- Fixes for kv lang to correctly inherith rules from an Widget
with multiples bases
- Fixes on App to add the root widget before dispatching on_start

Graphics
--------

- [:repo:`76`, :repo:`77`] Fixes to prevent blank screen
- Fixes for glReadPixels to prevent reading outside the bounds
- New BindTexture.index to allow binding on another unit
- New Callback() instruction, to call a Python func
- New Canvas.ask_update() to force update of the Canvas
- New minimal opengl version check
- New StencilPush, StencilUse, StencilPop instructions
- Rework and speedup Buffer/VBO internals

Input
-----

- Fixes for dejitter postproc

Widget
------

- [:repo:`71`] Fix Image ratio calculation
- [:repo:`74`] New GridLayout widget
- [:repo:`75`] Fix Label.font_color
- Fixes for Video.volume to make it work
- Fixes in BoxLayout
- Fixes Label.font_name attribute to use resource_find()
- New ScrollView widget
- New TextInput widget
- New TreeView widget
- New Label.text_size: control the size of the text texture
- New Video.eos property: control if the video should be
paused or loop at the end

Examples
--------

- New demo/pictures example (photo viewer)
- New kinect example (linux only, need libfreenect)
- New widgets/stencilcanvas example
- New widgets/videoplayer example
- Updated demo/showcase to use TreeView

Documentation
-------------

- New PDF version of the documentation, generated with buildbot
and published at http://kivy.org/docs/pdf/Kivy-latest.pdf
- New "Your First Widget" section in the Programming Guide
- Severals part of the documentation have been fixed and reworded

Others
------

- [:repo:`81`] Add missing gstreamer binaries to the Windows build
- [:repo:`82`] Fixes to remove all unused and obsolete modules
- New OpenGL debug compilation now print arguments
- Fixes for opengl debug compilation on MacOSX
- Fixes for Windows crash if the icon is not found
- Fixes for Windows glitch on touchtracer



1.0.3-alpha (Feb 22, 2011)
============================
`Announcement <http://groups.google.com/group/kivy-dev/browse_thread/thread/72dd6615d10faff2>`_

Core
----

- [:repo:`34`] Fixes lang for invalid detection of floating number
- [:repo:`45`] New clearcolor property in Window
- [:repo:`55`] New CMD+Q and CMD+W support in OSX
- [:repo:`61`] ListProperty is now able to observe inplace changes
- [:repo:`63`] Fixes for PIL loader
- Fixes for AliasProperty: dispatch the observer set return True
- Fixes for Camera and Video, reporting an error with Texture
- Fixes on Window dispatch on_close event when the window is closed
- Fixes to use the user canvas if it's set
- New Clock.get_boottime()
- New kivy.tools.report tools, can be used for debugging install
- Removed old attributes in Label
- Removed setuptools and nose dependencies in setup.py

Graphics
--------

- [:repo:`46`] No more glitch when the Label have no text
- [:repo:`56`, :repo:`44`] Fixes for adding/removing BindTexture automatically
- [:repo:`57`] Texture min/mag_filter and wrap are string, not gl const
- Canvas.clear() don't clear before and after context now
- New error checking for Shader compilation and linking
- New RenderContext.shader to access on internal shader class
- New Shader fs, vs and success to change glsl source code
- Reduce shader header, and removing unused varying + uniform

Input
-----

- [:repo:`59`] Fixes for Tuio, 2Dcur wasn't accepted as a Touch

Widget
------

- New center_x, center_y value for Widget.pos_hint
- New design (button, slider and fonts)

Examples
--------

- Add shader/plasma.py for an example of custom shader usage
- Add shader/treeshader.py for an example of custom shader for
widget rendering.

Documentation
-------------

- Various fixes everywhere
- Add working devices for android
- Add a section about how to report an issue

Android
-------

- Fix crash for devices with more than 4 touches

Others
------

- [:repo:`50`] Versionning portable-deps for OSX
- Add unit tests for Point and Ellipse
- New keybinding module, with only F12 to take screenshot



1.0.2-alpha (Feb 10, 2011)
============================
`Announcement <http://groups.google.com/group/kivy-dev/browse_thread/thread/eccaaf38fdf84a17>`_

Core
----

- New kivy.require() method to require a minimum kivy version
- New App.stop() method
- [:repo:`22`] Autodetection of GLES2 support
- Speedup Kivy language callbacks
- Reduce text memory footprint using new luminance_alpha format
- Remove old vsync/fps token in Configuration, use maxfps.
- FPS is limited to 60 by default now.
- Fixes for pip installer

Graphics
--------

- New Ellipse.segments property
- Support of luminance + luminance_alpha color format in texture
- Speedup of internals classes (VBO, VertexBatch, Buffer)
- [:repo:`42`, :repo:`48`] Fixes and activate graphics compiler
- Fixes compilation for Linux + ATI card

Documentation
-------------

- [:repo:`54`] Enhance Vector documentation
- Installation for Windows, MacOSX, Linux and Android
- Fixes Quickstart

Widgets
-------

- New layouts: FloatLayout, GridLayout and AnchorLayout

Examples
--------

- Fixes for touchtracer to make it run on android

Android
-------

- Initial release of Android Kivy launcher.
- You need Android 2.2 + OpenGL ES 2.0 support
- Tested on Motorola Droid 1, Motorola Droid 2, Samsung Galaxy Tab,
Xperia 10.


1.0.0 (Feb 1, 2011)
============================
`Announcement <http://groups.google.com/group/kivy-dev/browse_thread/thread/631a838dcbd8e654>`_

* Running on Windows, MacOSX, Linux and Android
* Same application code for all platforms
* Graphics API on top of OpenGL ES 2.0
* Uniform access to Audio, Camera, Video, Text rendering, Spelling
* Native input support: Tuio, WM_Touch, MacOSX MT, mtdev, wacom...
* Multitouch widgets: Label, Button, Image, Scatter, Video, Camera...
* Stable and documented API
* Extensive documentation at http://kivy.org/docs/
* Continuous integration via buildbot (coverage and gl unit tests)
