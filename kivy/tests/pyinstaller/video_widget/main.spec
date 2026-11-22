# -*- mode: python -*-

block_cipher = None
from kivy_deps import sdl3, glew
from kivy.tools.packaging.pyinstaller_hooks import (
    runtime_hooks, hookspath, get_gstreamer_datas)
import os

deps = list(sdl3.dep_bins + glew.dep_bins)
try:
    import ffpyplayer
    deps.extend(ffpyplayer.dep_bins)
except ImportError:
    pass
print('deps are: ', deps)
# GStreamer's official wheels (kivy[gstreamer]), for the gstplayer provider.
gst_datas = get_gstreamer_datas()
print('gstreamer wheels are: ', gst_datas)


a = Analysis(['main.py'],
             pathex=[os.environ['__KIVY_PYINSTALLER_DIR']],
             binaries=[],
             datas=gst_datas,
             hiddenimports=[],
             hookspath=[os.environ['__KIVY_PYINSTALLER_DIR']],
             runtime_hooks=runtime_hooks(),
             excludes=['numpy',],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='main',
          debug=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               *[Tree(p) for p in deps],
               strip=False,
               upx=True,
               name='main')
