@echo off
del "kivy\core\skia\skia_graphics.cpp" 2>nul
del "kivy\core\skia\skia_graphics.cp311-win_amd64.pyd" 2>nul
python setup.py build_ext --inplace
python main.py