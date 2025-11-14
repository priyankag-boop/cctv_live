# cctv.spec

# One-file, windowed EXE with ffmpeg bundled inside.
# This supports your auto-detect scripts, RTSP checking, and mount naming.

import sys
from PyInstaller.utils.hooks import collect_submodules

# Collect all hidden imports automatically (Tkinter, requests, etc)
hidden_imports = collect_submodules('requests') + collect_submodules('tkinter')

block_cipher = None

a = Analysis(
    ['cctv.py'],  # Your main script
    pathex=[],
    binaries=[],
    datas=[
        ('ffmpeg/ffmpeg.exe', 'ffmpeg'),
        ('ffmpeg/ffprobe.exe', 'ffmpeg'),
        
        ('ffmpeg/ffplay.exe', 'ffmpeg'),
        ('config.yaml', '.'),        # <- if you have config
        ('cameras.json', '.'),       # <- if you use JSON for camera list
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='cctv streamer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False   # NO console → double-click friendly
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='cctv streamer'
)

app = BUNDLE(
    coll,
    name='cctv streamer.exe',
    icon=None
)
