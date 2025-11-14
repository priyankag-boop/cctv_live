# cctv.spec
# One-file EXE bundling ffmpeg inside

import sys
from PyInstaller.utils.hooks import collect_submodules

hidden_imports = collect_submodules('requests') + collect_submodules('tkinter')

block_cipher = None

a = Analysis(
    ['cctv.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('ffmpeg/ffmpeg.exe', 'ffmpeg'),
        ('ffmpeg/ffprobe.exe', 'ffmpeg'),
        ('ffmpeg/ffplay.exe', 'ffmpeg'),
        # REMOVE config.yaml and cameras.json (YOUR REPO DOES NOT HAVE THEM)
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='cctv streamer',
    console=False,
    debug=False,
    strip=False,
    upx=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='cctv streamer',
)

app = BUNDLE(
    coll,
    name='cctv streamer.exe',
    icon=None,
)
