# -*- mode: python -*-

block_cipher = None
from kivy_deps import sdl2, glew
from kivy.tools.packaging.pyinstaller_hooks import runtime_hooks, hookspath
import os

deps = list(sdl2.dep_bins + glew.dep_bins)
try:
    import ffpyplayer
    deps.extend(ffpyplayer.dep_bins)
except ImportError:
    pass
try:
    from kivy_deps import gstreamer
    deps.extend(gstreamer.dep_bins)
except ImportError:
    pass
print('deps are: ', deps)


a = Analysis(['main.py'],
             pathex=[os.environ['__KIVY_PYINSTALLER_DIR']],
             binaries=[],
             datas=[],
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
