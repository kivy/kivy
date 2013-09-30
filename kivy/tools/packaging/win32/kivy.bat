@ECHO off
setlocal
set kivy_portable_root=%~dp0
ECHO botstrapping Kivy @ %kivy_portable_root%


IF DEFINED kivy_paths_initialized (GOTO :runkivy)

ECHO Setting Environment Variables:
ECHO #################################

set GST_REGISTRY=%kivy_portable_root%gstreamer\registry.bin
ECHO GST_REGISTRY
ECHO %GST_REGISTRY%
ECHO ---------------

set GST_PLUGIN_PATH=%kivy_portable_root%gstreamer\lib\gstreamer-0.10
ECHO GST_PLUGIN_PATH:
ECHO %GST_PLUGIN_PATH%
ECHO ---------------

set PATH=%kivy_portable_root%;%kivy_portable_root%Python;%kivy_portable_root%Python\Scripts;%kivy_portable_root%gstreamer\bin;%kivy_portable_root%MinGW\bin;%PATH%
ECHO PATH:
ECHO %PATH%
ECHO ----------------------------------

set PYTHONPATH=%kivy_portable_root%kivy;%PYTHONPATH%
ECHO PYTHONPATH:
ECHO %PYTHONPATH%
ECHO ----------------------------------

SET kivy_paths_initialized=1
ECHO ##################################


:runkivy

ECHO done bootstraping kivy...have fun!\n
IF (%1)==() GOTO SHELL
ECHO running "python.exe %*" \n
python.exe  %*
IF %errorlevel% NEQ 0 (PAUSE)
GOTO END
:SHELL
ECHO.
ECHO -----------------------------------------------------------------------
ECHO - Running a shell, you can browse kivyexamples and launch apps with: -
ECHO - python app.py -
ECHO -----------------------------------------------------------------------
ECHO.
cmd /K PROMPT $P$Q
:END
endlocal
